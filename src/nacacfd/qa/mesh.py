"""Gate: mesh quality, from SU2's own mesh quality statistics in the solver log.

Status: implemented (F2): minimum orthogonality angle. Aspect ratio outside the boundary layer is
not checked yet (threshold undefined in config/qa_thresholds.yaml), and that is stated in the result.
"""

from __future__ import annotations

from pathlib import Path

from nacacfd.qa.base import GateOutcome, GateResult
from nacacfd.runner.convergence import read_mesh_quality

NAME = "mesh_quality"
ORTHO = "Orthogonality Angle (deg.)"


def check_mesh_quality(case_dir, thresholds: dict) -> GateResult:
    log = Path(case_dir) / "solver.log"
    t = thresholds["gates"][NAME]
    if not log.exists():
        return GateResult(NAME, GateOutcome.NOT_RUN, reason="solver.log missing")
    q = read_mesh_quality(log)
    if ORTHO not in q:
        return GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(log),
                          reason="SU2 mesh quality table not found in solver.log")
    min_ortho = q[ORTHO]["min"]
    limit = t["min_orthogonality_angle_deg"]
    value = {"min_orthogonality_angle_deg": min_ortho, "su2_quality_table": q,
             "aspect_ratio_check": "not implemented (threshold undefined)"}
    if min_ortho < limit:
        return GateResult(NAME, GateOutcome.FAIL, value, {"min_orthogonality_angle_deg": limit}, str(log),
                          f"min orthogonality angle {min_ortho:.2f} deg < {limit} deg")
    return GateResult(NAME, GateOutcome.PASS, value, {"min_orthogonality_angle_deg": limit}, str(log))
