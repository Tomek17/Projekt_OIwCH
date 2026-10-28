"""Gate: grid independence via the Grid Convergence Index (GCI) with Richardson extrapolation.

Status: implemented (F4).

Procedure: Celik, I.B., Ghia, U., Roache, P.J., Freitas, C.J., Coleman, H., Raad, P.E. (2008),
"Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications",
J. Fluids Eng. 130(7), 078001. (Written from the agent's knowledge of the paper; to be checked against
the paper before the report.)

Index 1 = finest grid, 3 = coarsest. h = (1 / N)^(1/2) in 2D, N = number of cells.
  r21 = h2/h1, r32 = h3/h2, e21 = phi2 - phi1, e32 = phi3 - phi2, s = sign(e32/e21)
  p = |ln|e32/e21| + q(p)| / ln r21,   q(p) = ln((r21^p - s) / (r32^p - s))   (fixed-point iteration)
  phi_ext = (r21^p phi1 - phi2) / (r21^p - 1),  e_a = |(phi1 - phi2) / phi1|
  GCI_fine = Fs e_a / (r21^p - 1)
Convergence type from R = e21/e32: 0 < R < 1 monotonic, R < 0 oscillatory, R > 1 divergent.
Only monotonic convergence gives a GCI here; the other cases are reported, not forced into a number.

Observed-order check (F4d, requested by the student): an observed order p far above the formal order of the
scheme (2nd order here) suggests the grids are not in the asymptotic range, and the GCI is then likely
optimistic. p above `max_observed_order` (config/qa_thresholds.yaml) is a FAIL. If the threshold is not set,
the gate is NOT_RUN (never a silent pass).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from nacacfd.qa.base import GateOutcome, GateResult

NAME = "gci"


def representative_h(n_cells: int) -> float:
    return (1.0 / n_cells) ** 0.5


def compute_gci(h: list, phi: list, safety_factor: float, max_iter: int = 200) -> dict:
    """h, phi ordered fine -> coarse (3 values each). Returns a dict; 'gci_fine' is None unless monotonic."""
    h1, h2, h3 = h
    p1, p2, p3 = phi
    if not h1 < h2 < h3:
        raise ValueError("h must be ordered fine -> coarse (increasing)")
    r21, r32 = h2 / h1, h3 / h2
    e21, e32 = p2 - p1, p3 - p2
    out = {"r21": r21, "r32": r32, "e21": e21, "e32": e32, "phi": [p1, p2, p3], "h": [h1, h2, h3]}
    if e21 == 0 or e32 == 0:
        out.update(convergence="exact_or_insensitive", p=None, phi_ext=None, e_a=abs(e21 / p1) if p1 else None,
                   gci_fine=None)
        return out
    R = e21 / e32
    out["R"] = R
    if R < 0:
        out.update(convergence="oscillatory", p=None, phi_ext=None, gci_fine=None)
        return out
    if R >= 1:
        out.update(convergence="divergent", p=None, phi_ext=None, gci_fine=None)
        return out
    s = math.copysign(1.0, e32 / e21)
    p = abs(math.log(abs(e32 / e21))) / math.log(r21)
    for _ in range(max_iter):
        q = math.log((r21 ** p - s) / (r32 ** p - s))
        p_new = abs(math.log(abs(e32 / e21)) + q) / math.log(r21)
        if abs(p_new - p) < 1e-10:
            p = p_new
            break
        p = p_new
    phi_ext = (r21 ** p * p1 - p2) / (r21 ** p - 1)
    e_a = abs((p1 - p2) / p1)
    out.update(convergence="monotonic", p=p, phi_ext=phi_ext, e_a=e_a,
               gci_fine=safety_factor * e_a / (r21 ** p - 1))
    return out


def check_gci(study_dir, thresholds: dict, alpha_case: str, levels=("fine", "medium", "coarse")) -> GateResult:
    """GateResult for one angle of attack of a 3-level study in runs/<experiment>/<alpha_case>_<level>/.

    Needs all three cases to have passed their per-case gates (otherwise NOT_RUN: comparing unconverged or
    rejected solutions would make the GCI meaningless). PASS only if CL and CD both converge monotonically
    and GCI_fine is below the thresholds.
    """
    t = thresholds["gates"][NAME]
    study_dir = Path(study_dir)
    cases = [study_dir / f"{alpha_case}_{lvl}" for lvl in levels]
    max_p = t.get("max_observed_order")
    thr = {"max_gci_fine_cl_percent": t["max_gci_fine_cl_percent"],
           "max_gci_fine_cd_percent": t["max_gci_fine_cd_percent"], "safety_factor": t["safety_factor"],
           "max_observed_order": max_p}
    if max_p is None:
        return GateResult(NAME, GateOutcome.NOT_RUN, threshold=thr,
                          reason="max_observed_order not set in config/qa_thresholds.yaml (needs the student)")
    for c in cases:
        if not (c / "results.json").exists() or not (c / "mesh_info.json").exists():
            return GateResult(NAME, GateOutcome.NOT_RUN, threshold=thr, reason=f"{c.name}: results or mesh info missing")
        qa = json.loads((c / "qa_report.json").read_text())
        bad = [g["name"] for g in qa["gates"] if g["name"] != NAME and g["outcome"] != "pass"]
        if bad:
            return GateResult(NAME, GateOutcome.NOT_RUN, threshold=thr,
                              reason=f"{c.name}: per-case gates not passed ({', '.join(bad)})")
    n = [json.loads((c / "mesh_info.json").read_text())["statistics"]["elements"] for c in cases]
    h = [representative_h(k) for k in n]
    res = [json.loads((c / "results.json").read_text()) for c in cases]
    value = {"cells": n}
    problems = []
    for q, lim in (("CL", t["max_gci_fine_cl_percent"]), ("CD", t["max_gci_fine_cd_percent"])):
        g = compute_gci(h, [r[q] for r in res], t["safety_factor"])
        value[q] = g
        if g["gci_fine"] is None:
            problems.append(f"{q}: {g['convergence']} convergence, no GCI")
        elif 100 * g["gci_fine"] > lim:
            problems.append(f"{q}: GCI_fine {100 * g['gci_fine']:.2f}% > {lim}%")
        if g["p"] is not None and g["p"] > max_p:
            problems.append(f"{q}: observed order p {g['p']:.2f} > {max_p} (not asymptotic, GCI unreliable)")
    evidence = str(study_dir / f"gci_{alpha_case}.json")
    Path(evidence).write_text(json.dumps(value, indent=2) + "\n")
    if problems:
        return GateResult(NAME, GateOutcome.FAIL, value, thr, evidence, "; ".join(problems))
    return GateResult(NAME, GateOutcome.PASS, value, thr, evidence)
