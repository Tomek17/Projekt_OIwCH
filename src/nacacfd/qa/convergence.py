"""Gate: residual drop AND stabilisation of force coefficients.

Status: implemented (F2).
- residual drop = rms[Rho] at the first iteration minus rms[Rho] at the last (orders of magnitude, log10);
- stabilisation = (max - min) / |mean| of CL and CD over the last `window_iterations` iterations;
- a run shorter than the window is NOT_RUN (cannot be judged), never silently judged on a shorter window.
"""

from __future__ import annotations

import math
from pathlib import Path

from nacacfd.qa.base import GateOutcome, GateResult
from nacacfd.runner.convergence import read_history

NAME = "convergence"


def _rel_range(xs: list[float], ref: float | None = None) -> float:
    """(max - min) / max(|mean|, ref). `ref` keeps the measure meaningful when the mean is ~0 (CL at alpha 0)."""
    denom = max(abs(sum(xs) / len(xs)), ref or 0.0)
    if denom == 0:
        return math.inf
    return (max(xs) - min(xs)) / denom


def check_convergence(case_dir, thresholds: dict) -> GateResult:
    hist = Path(case_dir) / "history.csv"
    t = thresholds["gates"][NAME]
    if not hist.exists():
        return GateResult(NAME, GateOutcome.NOT_RUN, reason="history.csv missing")
    h = read_history(hist)
    for col in ("rms[Rho]", "CL", "CD"):
        if col not in h or not h[col]:
            return GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(hist), reason=f"column {col} missing")
    n = len(h["CL"])
    window = int(t["window_iterations"])
    thr = {"min_residual_drop_orders": t["min_residual_drop_orders"], "window_iterations": window,
           "cl_max_relative_range": t["cl_max_relative_range"], "cd_max_relative_range": t["cd_max_relative_range"],
           "cl_reference_magnitude": t.get("cl_reference_magnitude")}
    drop = h["rms[Rho]"][0] - h["rms[Rho]"][-1]
    value = {"n_iterations": n, "residual_drop_orders": drop,
             "rms_rho_first": h["rms[Rho]"][0], "rms_rho_last": h["rms[Rho]"][-1]}
    if any(not math.isfinite(x) for x in h["CL"][-1:] + h["CD"][-1:] + h["rms[Rho]"][-1:]):
        return GateResult(NAME, GateOutcome.FAIL, value, thr, str(hist), "non-finite values (diverged)")
    if n < window:
        return GateResult(NAME, GateOutcome.NOT_RUN, value, thr, str(hist),
                          f"only {n} iterations, shorter than the stabilisation window {window}")
    value["cl_relative_range"] = _rel_range(h["CL"][-window:], t.get("cl_reference_magnitude"))
    value["cd_relative_range"] = _rel_range(h["CD"][-window:])
    problems = []
    if drop < t["min_residual_drop_orders"]:
        problems.append(f"residual drop {drop:.2f} < {t['min_residual_drop_orders']} orders")
    if value["cl_relative_range"] > t["cl_max_relative_range"]:
        problems.append(f"CL relative range {value['cl_relative_range']:.2e} > {t['cl_max_relative_range']:.0e}")
    if value["cd_relative_range"] > t["cd_max_relative_range"]:
        problems.append(f"CD relative range {value['cd_relative_range']:.2e} > {t['cd_max_relative_range']:.0e}")
    if problems:
        return GateResult(NAME, GateOutcome.FAIL, value, thr, str(hist), "; ".join(problems))
    return GateResult(NAME, GateOutcome.PASS, value, thr, str(hist))
