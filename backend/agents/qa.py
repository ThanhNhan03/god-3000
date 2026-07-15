"""
QA Validation Agent
────────────────────
Checks generated files for obvious issues and returns a structured result.
The orchestrator uses this after each conversion to decide whether to retry.
"""

import re
from typing import List, Dict, Any


def validate_files(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a list of generated file dicts: [{path, content}, ...]
    Returns:
        {
            "valid": bool,
            "errors": ["description", ...],
            "warnings": ["description", ...]
        }
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not files:
        errors.append("No files were generated.")
        return {"valid": False, "errors": errors, "warnings": warnings}

    for item in files:
        path: str = item.get("path", "")
        content: str = item.get("content", "")

        # ── Empty file ────────────────────────────────────────────────────
        if not content.strip():
            errors.append(f"'{path}' is empty.")
            continue

        # ── C# / CS files ────────────────────────────────────────────────
        if path.endswith(".cs"):
            brace_balance = content.count("{") - content.count("}")
            if brace_balance != 0:
                errors.append(
                    f"'{path}' has unbalanced braces "
                    f"(open={content.count('{')}, close={content.count('}')})."
                )
            if "namespace" not in content:
                warnings.append(f"'{path}' has no namespace declaration.")
            if "class " not in content:
                warnings.append(f"'{path}' has no class declaration.")

        # ── CSHTML / Razor views ─────────────────────────────────────────
        elif path.endswith(".cshtml"):
            if "@model" not in content and "@Model" not in content:
                warnings.append(f"'{path}' Razor view has no @model directive.")

        # ── JSON files ───────────────────────────────────────────────────
        elif path.endswith(".json"):
            try:
                import json
                json.loads(content)
            except Exception as e:
                errors.append(f"'{path}' is invalid JSON: {e}")

        # ── Generic: check for placeholder stubs ─────────────────────────
        placeholder_patterns = [
            r"TODO",
            r"FIXME",
            r"throw new NotImplementedException",
            r"// Generated",
        ]
        found = [p for p in placeholder_patterns if re.search(p, content)]
        if found:
            warnings.append(
                f"'{path}' contains placeholder/stub markers: {', '.join(found)}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
