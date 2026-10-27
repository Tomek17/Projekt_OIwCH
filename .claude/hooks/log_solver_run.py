#!/usr/bin/env python3
"""PostToolUse hook (Bash): append one JSON line to docs/agent_log/runs.log for every solver run.

Triggers on commands containing `nacacfd run`, `nacacfd qa` or `SU2_CFD`. The case outcome itself is
recorded by the pipeline in runs/; this log is an audit trail of what the agent launched and when.
Never blocks (always exits 0).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TRIGGERS = ("nacacfd run", "nacacfd qa", "SU2_CFD")


def main() -> int:
    try:
        event = json.load(sys.stdin)
        cmd = (event.get("tool_input") or {}).get("command", "")
        if not any(t in cmd for t in TRIGGERS):
            return 0
        resp = event.get("tool_response") or {}
        project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
        line = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session": event.get("session_id"),
            "command": cmd,
            "interrupted": resp.get("interrupted") if isinstance(resp, dict) else None,
            "stderr_tail": (resp.get("stderr") or "")[-300:] if isinstance(resp, dict) else None,
        }
        log = project_dir / "docs" / "agent_log" / "runs.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as f:
            f.write(json.dumps(line) + "\n")
    except Exception as exc:  # a logging hook must never break the agent's work
        print(f"log_solver_run hook error: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
