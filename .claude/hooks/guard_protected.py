#!/usr/bin/env python3
"""PreToolUse hook: block agent writes to protected files and hand-written "valid" statuses in runs/.

Reads the hook JSON from stdin. Exit code 2 blocks the tool call and shows stderr to the agent.
Override (human only): start Claude Code with NACACFD_ALLOW_PROTECTED_EDITS=1 in the environment.

Limitation: the Bash check is a heuristic (pattern match). It catches obvious writes, not every possible one.
The real guarantee for "valid" is nacacfd.qa.status.assign_status(); this hook is a second layer.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROTECTED_PREFIXES = ("data/reference/",)
PROTECTED_FILES = ("config/qa_thresholds.yaml",)
VALID_STATUS_RE = re.compile(r"""["']?status["']?\s*[:=]\s*["']?valid\b""", re.IGNORECASE)
BASH_WRITE_RE = re.compile(r"(>|\btee\b|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bchmod\b|write_text|open\()")


def _rel(path: str, project_dir: Path) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(project_dir.resolve())
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def _is_protected(rel: str) -> bool:
    return rel in PROTECTED_FILES or any(rel.startswith(pref) for pref in PROTECTED_PREFIXES)


def check(event: dict, project_dir: Path) -> str | None:
    """Return a block reason, or None to allow."""
    tool = event.get("tool_name", "")
    ti = event.get("tool_input", {}) or {}

    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        rel = _rel(path, project_dir)
        if _is_protected(rel):
            return f"{rel} is protected (reference data / QA thresholds). Ask the student first; see CLAUDE.md."
        if not rel.startswith("runs/"):
            return None
        texts = [ti.get("content", ""), ti.get("new_string", ""), ti.get("new_source", "")]
        texts += [e.get("new_string", "") for e in ti.get("edits", []) or []]
        if any(VALID_STATUS_RE.search(t or "") for t in texts):
            return ("Writing status 'valid' by hand is forbidden. Only nacacfd.qa.status.assign_status() "
                    "may set it, after all QA gates passed (CLAUDE.md hard rule 3).")

    if tool == "Bash":
        cmd = ti.get("command", "")
        touches_protected = any(p in cmd for p in PROTECTED_PREFIXES + PROTECTED_FILES)
        if touches_protected and BASH_WRITE_RE.search(cmd):
            return "This command seems to modify protected files (reference data / QA thresholds). Ask the student first."
        if VALID_STATUS_RE.search(cmd) and BASH_WRITE_RE.search(cmd):
            return "Writing status 'valid' from the shell is forbidden; use the QA pipeline."
    return None


def main() -> int:
    if os.environ.get("NACACFD_ALLOW_PROTECTED_EDITS") == "1":
        return 0
    event = json.load(sys.stdin)
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    reason = check(event, project_dir)
    if reason:
        print(f"BLOCKED by guard_protected hook: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
