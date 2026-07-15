"""
Discovery Agent
───────────────
Recursively scans the ENTIRE workspace (root + source/) to find ALL migratable files.
Groups related files into modules.
Skips modules that have already been converted (output exists in workspace/new/).
"""

import os
import re

WORKSPACE_ROOT = "/Users/lilnhan/Documents/GitHub/god-3000/workspace"
SOURCE_DIR     = os.path.join(WORKSPACE_ROOT, "source")
OUTPUT_DIR     = os.path.join(WORKSPACE_ROOT, "new")

# ── File type categories ──────────────────────────────────────────────────────
# PRIMARY: each of these becomes its own module to convert
PRIMARY_EXTS = {".frm", ".bas", ".cls", ".cbl", ".cpy", ".cbi", ".cob", ".pco"}

# SUPPORT: associated files (linked to a primary module by name)
SUPPORT_EXTS = {".cbl", ".cpy", ".cbi", ".cob"}

# Skip entirely
IGNORE_EXTS  = {".md", ".txt", ".pdf", ".png", ".jpg", ".jpeg",
                ".gif", ".zip", ".gitkeep", ".log", ".exe", ".dll"}
IGNORE_DIRS  = {"__pycache__", ".git", "node_modules", "bin", "obj", "new"}


def _already_converted(form_name: str) -> bool:
    """Return True if workspace/new/<form_name>/ already contains at least one file."""
    output_path = os.path.join(OUTPUT_DIR, form_name)
    if not os.path.isdir(output_path):
        return False
    for _, _, files in os.walk(output_path):
        if files:
            return True
    return False


def _scan_roots() -> tuple[list[str], list[str]]:
    """
    Walk workspace root AND source/ subdirectory.
    Returns:
        primary_files  — all files with PRIMARY_EXTS (relative to WORKSPACE_ROOT)
        support_files  — all COBOL/support files found (relative to WORKSPACE_ROOT)
    """
    primary  = []
    support  = []
    seen     = set()

    scan_roots = [WORKSPACE_ROOT, SOURCE_DIR]
    for root in scan_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

            for fname in filenames:
                if fname.startswith("."):
                    continue
                full = os.path.join(dirpath, fname)
                if full in seen:
                    continue
                seen.add(full)

                ext = os.path.splitext(fname)[1].lower()
                if ext in IGNORE_EXTS:
                    continue

                rel = os.path.relpath(full, WORKSPACE_ROOT)

                if ext in PRIMARY_EXTS:
                    primary.append(rel)
                    if ext in SUPPORT_EXTS:
                        support.append(rel)  # COBOL files can be both
                elif ext in SUPPORT_EXTS:
                    support.append(rel)

    return primary, support


def _complexity(form_path: str, support_files: list[str]) -> float:
    stem  = os.path.splitext(os.path.basename(form_path))[0].lower()
    linked = [s for s in support_files if stem in os.path.basename(s).lower()]
    score  = 0.4 + 0.15 * len(linked) + 0.05 * min(len(stem), 5)
    return round(min(score, 1.0), 2)


def discover_modules(workspace_path: str = WORKSPACE_ROOT) -> dict:
    """
    Scan the entire workspace and return all modules that still need migration.
    Top-level directories inside source/ are treated as full project modules.
    Loose files are treated as individual modules.
    """
    modules = []
    seen_names = set()

    # 1. Discover folder-level modules inside source/
    if os.path.isdir(SOURCE_DIR):
        for item in os.listdir(SOURCE_DIR):
            item_path = os.path.join(SOURCE_DIR, item)
            if os.path.isdir(item_path) and item not in IGNORE_DIRS:
                form_name = item
                support = []
                for root, _, files in os.walk(item_path):
                    for f in files:
                        if not f.startswith(".") and os.path.splitext(f)[1].lower() not in IGNORE_EXTS:
                            support.append(os.path.relpath(os.path.join(root, f), WORKSPACE_ROOT))
                
                modules.append({
                    "form":             item_path,
                    "form_name":        form_name,
                    "support_files":    support,
                    "complexity_score": 0.8,
                    "already_done":     _already_converted(form_name)
                })
                seen_names.add(form_name)

    # 2. Discover loose files
    primary_files, support_files = _scan_roots()

    for form_path in sorted(primary_files):
        form_name = os.path.basename(form_path)

        # Skip if it is already part of a folder-module
        if any(os.path.abspath(form_path).startswith(os.path.abspath(m["form"])) for m in modules if os.path.isdir(m["form"])):
            continue

        # Deduplicate: prefer source/ copy over workspace root copy
        if form_name in seen_names:
            if SOURCE_DIR.replace(WORKSPACE_ROOT + os.sep, "") in form_path:
                modules = [m for m in modules if m["form_name"] != form_name]
            else:
                continue
        seen_names.add(form_name)

        stem  = os.path.splitext(form_name)[0].lower()

        # Related support files
        related = [
            s for s in support_files
            if s != form_path and (
                stem in os.path.basename(s).lower()
                or os.path.basename(s).lower() in stem
            )
        ]
        related = [r for r in related if os.path.basename(r) != form_name]

        already_done = _already_converted(form_name)

        modules.append({
            "form":             form_path,
            "form_name":        form_name,
            "support_files":    related,
            "complexity_score": _complexity(form_path, support_files),
            "already_done":     already_done,
        })

    pending_modules  = [m for m in modules if not m["already_done"]]
    skipped_modules  = [m for m in modules if m["already_done"]]

    return {
        "modules":         modules,
        "migration_order": [m["form_name"] for m in pending_modules],
        "skipped_modules": [m["form_name"] for m in skipped_modules],
        "total":           len(modules),
        "pending":         len(pending_modules),
        "skipped":         len(skipped_modules),
    }


def filter_by_prompt(discovery_result: dict, user_prompt: str) -> list[str]:
    """
    Parse the user's NLP prompt and return a filtered migration_order
    containing ONLY the modules the user explicitly mentions.

    If no specific file is mentioned, return the full migration_order.
    """
    prompt_lower = user_prompt.lower()
    all_pending  = discovery_result.get("migration_order", [])

    mentioned = []
    for form_name in all_pending:
        stem = os.path.splitext(form_name)[0].lower()
        # Match: full filename or stem (without extension) in prompt
        if form_name.lower() in prompt_lower or stem in prompt_lower:
            mentioned.append(form_name)

    return mentioned if mentioned else all_pending
