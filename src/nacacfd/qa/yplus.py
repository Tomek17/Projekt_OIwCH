"""Gate: wall y+ from the converged solution (SU2 surface CSV), not only from the a-priori estimate.

Status: implemented (F2).
"""

from __future__ import annotations

from pathlib import Path

from nacacfd.qa.base import GateOutcome, GateResult
from nacacfd.runner.convergence import read_surface

NAME = "wall_yplus"
YPLUS_COLUMNS = ("Y_Plus", "Y_PLUS", "y_plus")


def check_yplus(case_dir, thresholds: dict) -> GateResult:
    surf = Path(case_dir) / "surface_flow.csv"
    t = thresholds["gates"][NAME]
    if not surf.exists():
        return GateResult(NAME, GateOutcome.NOT_RUN, reason="surface_flow.csv missing")
    cols = read_surface(surf)
    col = next((c for c in YPLUS_COLUMNS if c in cols), None)
    if col is None or not cols[col]:
        return GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(surf),
                          reason=f"no y+ column in surface CSV (columns: {sorted(cols)})")
    yp = cols[col]
    value = {"max": max(yp), "mean": sum(yp) / len(yp), "n_points": len(yp)}
    thr = {"target_max": t["target_max"], "fail_above": t["fail_above"]}
    if value["max"] > t["fail_above"]:
        return GateResult(NAME, GateOutcome.FAIL, value, thr, str(surf),
                          f"max y+ {value['max']:.3f} > {t['fail_above']}")
    note = ""
    if value["max"] > t["target_max"]:
        note = f"max y+ {value['max']:.3f} above target {t['target_max']} but below fail limit {t['fail_above']}"
    return GateResult(NAME, GateOutcome.PASS, value, thr, str(surf), note)
