"""Gate: agreement with experimental reference data.

Status: implemented (F5).

Tolerance (student's decision 2026-11-02, decision card): `tolerance_mode: reference_spread`. At each point the
tolerance is the spread (max - min) of the experimental series in the reference file at that point, e.g. the
80/120/180 grit series of Ladson: CL compared at equal alpha, CD at equal CL, pre-stall branch only.
The tolerance therefore comes from the experiment, not from the simulation results.
NOT_RUN (never a silent pass) when: the reference file fails the SOURCE.md sha256 check, the mode is not set in config/qa_thresholds.yaml, the point is outside the
reference range, fewer than two series cover the point, or the case has no coefficients.
"""

from __future__ import annotations

from nacacfd.postprocess.compare import ladson_at, load_reference
from nacacfd.qa.base import GateOutcome, GateResult

NAME = "validation"


def check_validation(polar_rows: list[dict], reference_file, thresholds: dict) -> dict[str, GateResult]:
    """Return {case: GateResult} for polar rows (collect_polar() / polar.csv dicts with case, alpha_deg, CL, CD)."""
    t = thresholds["gates"][NAME]
    mode = t.get("tolerance_mode")
    try:
        zones = load_reference(reference_file)
    except ValueError as e:
        return {r["case"]: GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(reference_file), reason=str(e))
                for r in polar_rows}
    results = {}
    for r in polar_rows:
        case, alpha = r["case"], float(r["alpha_deg"])
        if mode != "reference_spread":
            results[case] = GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(reference_file),
                                       reason=f"validation tolerance_mode not set (got {mode!r})")
            continue
        if r.get("CL") in (None, "") or r.get("CD") in (None, ""):
            results[case] = GateResult(NAME, GateOutcome.NOT_RUN, reason="no CL/CD for this case")
            continue
        cl, cd = float(r["CL"]), float(r["CD"])
        ref = ladson_at(zones, alpha, cl)
        problems, value, thr = [], {}, {}
        for q, mine, key in (("CL", cl, "CL"), ("CD", cd, "CD_at_CL")):
            vals = [v[key] for v in ref.values() if v[key] is not None]
            if len(vals) < 2:
                problems.append(f"{q}: only {len(vals)} reference series cover this point")
                continue
            mid, tol = (max(vals) + min(vals)) / 2, max(vals) - min(vals)
            # Pass if the result lies inside the experimental band [min, max]: |mine - mid| <= spread / 2.
            value[f"{q}_deviation_from_band_centre"] = mine - mid
            value[f"{q}_reference_min_max"] = [min(vals), max(vals)]
            thr[f"{q}_half_spread"] = tol / 2
        if problems and not value:
            results[case] = GateResult(NAME, GateOutcome.NOT_RUN, evidence=str(reference_file),
                                       reason="; ".join(problems))
            continue
        fails = [f"{q} {value[f'{q}_deviation_from_band_centre']:+.5f} outside +/-{thr[f'{q}_half_spread']:.5f}"
                 for q in ("CL", "CD") if f"{q}_half_spread" in thr
                 and abs(value[f"{q}_deviation_from_band_centre"]) > thr[f"{q}_half_spread"]]
        outcome = GateOutcome.FAIL if fails else (GateOutcome.NOT_RUN if problems else GateOutcome.PASS)
        results[case] = GateResult(NAME, outcome, value=value, threshold=thr, evidence=str(reference_file),
                                   reason="; ".join(fails + problems))
    return results
