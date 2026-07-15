import asyncio
import json
import os
import shutil
from agents.discovery import discover_modules, filter_by_prompt, SOURCE_DIR, OUTPUT_DIR, WORKSPACE_ROOT as DISC_ROOT
from agents.qa import validate_files
from agents.report import save_report
from agents.scaffold import build_project_scaffold, merge_llm_files
from llm_client import generate_response, stream_response, extract_json_from_text

# ── Agent names used for UI visualization ────────────────────────────────────
AGENTS = ["discovery", "planner", "conversion", "qa"]

WORKSPACE_ROOT = "/Users/lilnhan/Documents/GitHub/god-3000/workspace"
MAX_QA_RETRIES = 2


def _clear_output_dir():
    """
    Wipe workspace/new/ before a fresh run so stale converted files
    don't count as 'already done' during this session.
    Keeps workspace/source/ untouched.
    """
    if os.path.isdir(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _read_source_file(form_path: str) -> str:
    """
    Read the raw content of a source file from disk.
    Searches: exact path, workspace root, source/ subdir.
    Returns empty string if not found.
    """
    candidates = [
        os.path.join(DISC_ROOT, form_path),          # relative to workspace root
        os.path.join(SOURCE_DIR, os.path.basename(form_path)),  # in source/
        form_path,                                   # absolute path as-is
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass
    return ""


class Orchestrator:
    def __init__(self, workspace_path: str, user_prompt: str = ""):
        self.workspace_path = workspace_path
        self.user_prompt = user_prompt
        self.queue = asyncio.Queue()
        self.approval_event = asyncio.Event()
        self.plan = ""
        self.feedback = ""

        # Dedicated memory per agent
        self.memories = {
            "discovery": [],
            "planner":   [],
            "conversion": [],
            "qa":         [],
        }

    # ── Helper: emit an agent_update event ───────────────────────────────────
    async def _agent(self, name: str, status: str, thought: str = ""):
        """
        status: 'idle' | 'thinking' | 'done' | 'error'
        """
        await self.queue.put({
            "type":   "agent_update",
            "agent":  name,
            "status": status,
            "thought": thought,
        })

    # ── Helper: emit a pipeline step banner ──────────────────────────────────
    async def _info(self, msg: str):
        await self.queue.put({"type": "info", "message": msg})

    # ─────────────────────────────────────────────────────────────────────────
    async def run(self):
        """
        Pipeline:
          [Clear /new/] → Discovery → NLP Plan → [Human Review] → Conversion → QA → Done
        """
        await self._info("Starting Orchestrator pipeline...")

        # ── Clear previous output so skip-detection starts fresh ──────────
        _clear_output_dir()
        await self._info("🧹 Cleared previous output (workspace/new/).")

        # ── Reset all agents to idle ──────────────────────────────────────
        for a in AGENTS:
            await self._agent(a, "idle")

        # ════════════════════════════════════════════════════════════════════
        # STAGE 1: Discovery
        # ════════════════════════════════════════════════════════════════════
        await self._agent("discovery", "thinking", "Scanning workspace for source modules...")
        await self.queue.put({
            "type": "module_status",
            "module": "discovery_worker",
            "status": "converting",
            "retry_count": 0,
        })
        await asyncio.sleep(0.5)

        discovery_result = discover_modules(self.workspace_path)
        self.memories["discovery"].append(f"Discovered: {json.dumps(discovery_result)}")

        pending  = discovery_result.get("pending",  len(discovery_result["modules"]))
        skipped  = discovery_result.get("skipped",  0)
        skipped_names = discovery_result.get("skipped_modules", [])

        await self._agent(
            "discovery", "done",
            f"Found {discovery_result['total']} module(s) — {pending} pending, {skipped} already done"
        )
        await self._info(
            f"Discovery: {discovery_result['total']} module(s) total. "
            f"{pending} to convert, {skipped} already done."
        )
        if skipped_names:
            await self._info(f"⏭ Skipping already converted: {', '.join(skipped_names)}")

        if pending == 0:
            await self._info("✅ All modules already converted. Nothing to do.")
            await self.queue.put({"type": "done"})
            return

        # ── Filter migration_order by NLP prompt ──────────────────────────
        filtered_order = filter_by_prompt(discovery_result, self.user_prompt)
        if filtered_order != discovery_result["migration_order"]:
            # User specified specific files
            await self._info(
                f"🎯 Prompt targets specific module(s): {', '.join(filtered_order)}"
            )
            discovery_result["migration_order"] = filtered_order
        else:
            await self._info(
                f"📋 Processing all {len(filtered_order)} pending module(s)."
            )
        await self.queue.put({
            "type": "module_status",
            "module": "discovery_worker",
            "status": "done",
            "retry_count": 0,
        })

        # ════════════════════════════════════════════════════════════════════
        # STAGE 2: NLP Planner + Human-in-the-Loop
        # ════════════════════════════════════════════════════════════════════
        while True:
            await self._agent("planner", "thinking", "Generating implementation plan from user goal...")
            await self._info("Analyzing NLP and generating Implementation Plan for review...")

            prompt = (
                f"User Migration Goal: {self.user_prompt}\n\n"
                f"Discovered modules:\n{json.dumps(discovery_result, indent=2)}\n\n"
                f"User Feedback (if refining): {self.feedback}\n\n"
                "Create a DETAILED migration implementation plan in Markdown. "
                "Include: "
                "(1) Objective; "
                "(2) Migration Scope with module list and complexity; "
                "(3) System Architecture overview (Discovery → NLP Planner → Conversion Agent → QA Validator → Report Generator); "
                "(4) Orchestrator pipeline flow (step-by-step with ASCII diagram); "
                "(5) Per-module Detailed Steps: Pre-migration analysis, Conversion, QA; "
                "(6) Test Strategy: unit tests for controllers, integration tests, .NET compatibility tests; "
                "(7) Output structure: what files/folders are generated; "
                "(8) Risk & Mitigation table."
            )
            system = "You are an expert AI migration architect. Output a clean, concise markdown plan."

            try:
                response = await generate_response(prompt, system)
                self.plan = response.content[0].text
                self.memories["planner"].append(f"Plan generated: {self.plan[:200]}...")
                await self._agent("planner", "done", "Plan ready — awaiting human review.")
            except Exception as e:
                self.plan = f"**Fallback Plan (LLM Error):** {str(e)}\n\n- Migrate all identified modules sequentially."
                await self._agent("planner", "error", f"LLM error: {str(e)[:80]}")

            await self.queue.put({"type": "review_required", "plan": self.plan})

            # Wait for human verification
            self.approval_event.clear()
            await self.approval_event.wait()

            if self.feedback == "":
                await self._info("Plan VERIFIED by human. Proceeding with execution...")
                await self._agent("planner", "done", "Plan approved ✅")
                break
            else:
                await self._info(f"Refining plan based on feedback: {self.feedback}")
                await self._agent("planner", "thinking", f"Refining: {self.feedback[:60]}...")

        # ════════════════════════════════════════════════════════════════════
        # STAGE 3: Conversion + QA per module
        # ════════════════════════════════════════════════════════════════════
        for module_name in discovery_result["migration_order"]:
            module_data = next(
                (m for m in discovery_result["modules"] if m["form_name"] == module_name),
                None
            )
            if not module_data:
                continue

            # Read actual source file content
            source_code = _read_source_file(module_data["form"])
            source_preview = source_code[:3000] if source_code else "(source file not readable)"

            # Read related COBOL files
            cobol_snippets = []
            for cbl_path in module_data.get("cobol_programs", [])[:3]:
                cbl_content = _read_source_file(cbl_path)
                if cbl_content:
                    cobol_snippets.append(
                        f"--- {cbl_path} ---\n{cbl_content[:1500]}"
                    )

            # ── Conversion ────────────────────────────────────────────────
            await self.queue.put({
                "type": "module_status",
                "module": f"conversion_{module_name}",
                "status": "converting",
                "retry_count": 0,
            })
            await self._agent("conversion", "thinking", f"Converting {module_name} → C# .NET MVC...")
            await self._info(f"Conversion Agent thinking about migration plan for: {module_name}...")

            qa_errors_context = ""
            json_data = None

            for attempt in range(1 + MAX_QA_RETRIES):
                retry_note = f" (retry {attempt}/{MAX_QA_RETRIES})" if attempt > 0 else ""
                if attempt > 0:
                    await self._agent("conversion", "thinking",
                                      f"Re-converting {module_name}{retry_note} based on QA feedback...")
                    await self._info(f"⟳ Retrying conversion for {module_name}{retry_note}...")
                    await self.queue.put({
                        "type": "module_status",
                        "module": f"conversion_{module_name}",
                        "status": "converting",
                        "retry_count": attempt,
                    })

                conversion_history = "\n".join(self.memories["conversion"])
                cobol_section = ("\n\n[Related COBOL Source]\n" + "\n\n".join(cobol_snippets)) if cobol_snippets else ""
                prompt = f"""
[Your Memory — Previous Conversions]
{conversion_history or "None yet."}

[Active Task{retry_note}]
Convert the following VB module to C# .NET MVC.

Module: {module_name}
Complexity Score: {module_data.get('complexity_score', 0.5)}

[Source Code — {module_name}]
```
{source_preview}
```
{cobol_section}

{f"[QA Errors to Fix]{chr(10)}{qa_errors_context}" if qa_errors_context else ""}

Instructions:
1. Carefully read the ACTUAL source code above — do not guess or assume.
2. Think through the migration step by step.
3. At the END of your response, output ALL generated files in a SINGLE ```json block:
```json
{{
  "files": [
    {{
      "path": "Controllers/{module_name}Controller.cs",
      "content": "// Full C# code here"
    }},
    {{
      "path": "Views/{module_name}/Index.cshtml",
      "content": "<!-- Razor view here -->"
    }}
  ]
}}
```
IMPORTANT: The ```json block MUST be the very last thing in your response.
"""
                system = (
                    "You are a professional code migration agent. "
                    "Always end with a single ```json block containing all generated files. "
                    "Do not split JSON across multiple blocks."
                )

                # Stream thinking to UI
                full_response = ""
                stream_error = None
                async for chunk in stream_response(prompt, system):
                    if chunk.startswith("[STREAM_ERROR]:"):
                        stream_error = chunk[len("[STREAM_ERROR]:"):].strip()
                        break
                    full_response += chunk
                    await self.queue.put({"type": "text_delta", "content": chunk})

                if stream_error:
                    await self._agent("conversion", "error",
                                      f"Stream failed: {stream_error[:80]}")
                    await self._info(f"⚠️ LLM streaming failed for {module_name}: {stream_error}")
                    break

                # Extract JSON
                json_data = extract_json_from_text(full_response)
                if json_data is None:
                    await self._agent("conversion", "error",
                                      "No JSON block found in output.")
                    await self._info(
                        f"⚠️ No JSON block found for {module_name} on attempt {attempt + 1}."
                    )
                    qa_errors_context = "Previous attempt produced no JSON file block. Please ensure you end with the ```json block."
                    continue  # retry

                # ── QA Validation ──────────────────────────────────────────
                await self._agent("qa", "thinking",
                                  f"Validating output for {module_name}...")
                await self._info(f"🔬 QA Agent validating generated files for {module_name}...")
                await self.queue.put({
                    "type": "qa_start",
                    "module": module_name,
                })

                files = json_data.get("files", [])
                qa_result = validate_files(files)

                if qa_result["valid"]:
                    await self._agent("qa", "done",
                                      f"QA passed ✅ ({len(files)} file(s))")
                    await self._info(
                        f"✅ QA passed for {module_name}. "
                        + (f"Warnings: {'; '.join(qa_result['warnings'])}" if qa_result["warnings"] else "No warnings.")
                    )
                    await self.queue.put({"type": "qa_pass", "module": module_name})
                    break  # done — go to save

                else:
                    errs = "; ".join(qa_result["errors"])
                    await self._agent("qa", "error",
                                      f"QA FAIL: {errs[:80]}")
                    await self._info(
                        f"❌ QA failed for {module_name} (attempt {attempt + 1}): {errs}"
                    )
                    await self.queue.put({
                        "type": "qa_fail",
                        "module": module_name,
                        "errors": qa_result["errors"],
                    })
                    qa_errors_context = "QA Errors:\n" + "\n".join(f"- {e}" for e in qa_result["errors"])
                    self.memories["qa"].append(f"QA failed for {module_name}: {errs}")
                    json_data = None  # don't save bad files

            # ── Save valid files ──────────────────────────────────────────────
            if json_data is not None:
                self.memories["conversion"].append(
                    f"Converted {module_name}. Output summary: {full_response[:300]}..."
                )

                output_dir = os.path.join(WORKSPACE_ROOT, "new", module_name)
                os.makedirs(output_dir, exist_ok=True)

                # Generate MVC Scaffold and merge LLM outputs
                p_name, ns, scaffold_files = build_project_scaffold(module_name)
                llm_files = json_data.get("files", [])
                final_files = merge_llm_files(scaffold_files, llm_files, p_name, ns)

                saved      = []
                saved_items = []
                for file_item in final_files:
                    orig_path = file_item["path"]
                    content = file_item["content"]
                    
                    # Ensure subdirectories exist
                    sub_dir  = os.path.dirname(orig_path)
                    dest_dir = os.path.join(output_dir, sub_dir) if sub_dir else output_dir
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    file_path = os.path.join(output_dir, orig_path)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    rel_path = os.path.relpath(file_path, WORKSPACE_ROOT)
                    await self.queue.put({"type": "file_update",  "path": rel_path})
                    await self.queue.put({"type": "file_created", "path": rel_path, "module": module_name})
                    saved_items.append({
                        "path":    orig_path,
                        "content": content,
                    })
                    saved.append(orig_path)

                # ── Generate HTML report ───────────────────────────────────
                try:
                    report_path = save_report(
                        output_dir  = output_dir,
                        module_name = module_name,
                        files       = saved_items,
                        qa_result   = qa_result,
                    )
                    rel_report = os.path.relpath(report_path, WORKSPACE_ROOT)
                    await self.queue.put({
                        "type":   "report_created",
                        "path":   rel_report,
                        "module": module_name,
                    })
                    await self._info(f"📊 Report saved → {rel_report}")
                    loadWorkspace_needed = True
                except Exception as rep_err:
                    await self._info(f"⚠️ Report generation failed: {rep_err}")

                await self._agent("conversion", "done",
                                  f"Saved {len(saved)} file(s) + report → new/{module_name}/")
                await self._info(
                    f"✅ Generated {len(saved)} file(s) for {module_name} → workspace/new/{module_name}/"
                )

            await self.queue.put({
                "type": "module_status",
                "module": f"conversion_{module_name}",
                "status": "done",
                "retry_count": 0,
            })

        # ════════════════════════════════════════════════════════════════════
        # DONE
        # ════════════════════════════════════════════════════════════════════
        for a in AGENTS:
            await self._agent(a, "done")
        await self.queue.put({"type": "done"})
