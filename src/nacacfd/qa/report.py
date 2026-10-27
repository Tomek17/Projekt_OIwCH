"""Run the per-case gates, write qa_report.json and let qa.status assign the status.

Status: implemented (F2).
"""

from __future__ import annotations

import json
from pathlib import Path

from nacacfd.config import load_thresholds
from nacacfd.qa.base import GateOutcome, GateResult
from nacacfd.qa.convergence import check_convergence
from nacacfd.qa.mesh import check_mesh_quality
from nacacfd.qa.physics_flags import check_physics
from nacacfd.qa.status import apply_status
from nacacfd.qa.yplus import check_yplus

CASE_GATES = {
    "mesh_quality": check_mesh_quality,
    "wall_yplus": check_yplus,
    "convergence": check_convergence,
    "physics_flags": check_physics,
}


def run_case_gates(case_dir, required: list[str], thresholds: dict | None = None) -> str:
    """Evaluate all per-case gates, write <case>/qa_report.json, apply the status; return the status.

    Required gates that are not per-case (e.g. gci, validation) are reported as NOT_RUN here,
    so a case that requires them can never become valid from this function alone.
    """
    case_dir = Path(case_dir)
    thresholds = thresholds or load_thresholds()
    results: list[GateResult] = []
    for name, fn in CASE_GATES.items():
        try:
            results.append(fn(case_dir, thresholds))
        except Exception as exc:  # a crashing gate must not look like a passing gate
            results.append(GateResult(name, GateOutcome.NOT_RUN, reason=f"gate crashed: {exc!r}"))
    for name in required:
        if name not in CASE_GATES:
            results.append(GateResult(name, GateOutcome.NOT_RUN, reason="not a per-case gate; evaluated later"))
    report = {"thresholds_version": thresholds.get("version"), "required": required,
              "gates": [r.to_dict() for r in results]}
    (case_dir / "qa_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return apply_status(case_dir, required)
