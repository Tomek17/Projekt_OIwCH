"""Per-case flags for suspicious physics (never hide, always flag).

Status: implemented (F2) for single-case checks: non-finite or negative CD, solver crash.
Near-stall detection needs the whole polar, so it is an experiment-level check (F5), not part of this gate.
Oscillating forces are caught by the convergence gate (stabilisation window).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from nacacfd.qa.base import GateOutcome, GateResult

NAME = "physics_flags"


def check_physics(case_dir, thresholds: dict) -> GateResult:
    res_path = Path(case_dir) / "results.json"
    if not res_path.exists():
        return GateResult(NAME, GateOutcome.NOT_RUN, reason="results.json missing")
    r = json.loads(res_path.read_text())
    if r.get("solver_exit_code") not in (0, None):
        return GateResult(NAME, GateOutcome.FAIL, {"solver_exit_code": r["solver_exit_code"]}, None,
                          str(res_path), f"solver exited with code {r['solver_exit_code']}")
    cl, cd = r.get("CL"), r.get("CD")
    if cl is None or cd is None or not (math.isfinite(cl) and math.isfinite(cd)):
        return GateResult(NAME, GateOutcome.FAIL, {"CL": cl, "CD": cd}, None, str(res_path),
                          "missing or non-finite force coefficients")
    if thresholds["gates"][NAME].get("flag_negative_cd", True) and cd < 0:
        return GateResult(NAME, GateOutcome.FAIL, {"CD": cd}, {"CD": ">= 0"}, str(res_path), "negative drag")
    return GateResult(NAME, GateOutcome.PASS, {"CL": cl, "CD": cd,
                                               "near_stall_check": "experiment-level, not in this gate"},
                      None, str(res_path))
