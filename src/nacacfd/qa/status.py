"""The ONLY place where a case gets status "valid".

Rule: a case is "valid" only if every required gate is present and PASS.
Any FAIL -> "invalid". Any required gate missing or NOT_RUN (and no FAIL) -> "incomplete".

Status: implemented and unit-tested in F0. This is the core guarantee of the project;
changing it is a human checkpoint.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from nacacfd.qa.base import GateOutcome, GateResult

VALID = "valid"
INVALID = "invalid"
INCOMPLETE = "incomplete"


def assign_status(results: Iterable[GateResult], required: Iterable[str]) -> tuple[str, list[str]]:
    """Return (status, reasons). Reasons list every failed, missing or not-run gate."""
    by_name = {r.name: r for r in results}
    reasons: list[str] = []
    failed = False
    incomplete = False

    for name in required:
        r = by_name.get(name)
        if r is None:
            incomplete = True
            reasons.append(f"{name}: missing")
        elif r.outcome is GateOutcome.FAIL:
            failed = True
            reasons.append(f"{name}: FAIL: {r.reason}")
        elif r.outcome is GateOutcome.NOT_RUN:
            incomplete = True
            reasons.append(f"{name}: not run: {r.reason}")

    # A failure in a non-required gate is still reported, but does not change the status.
    for name, r in by_name.items():
        if name not in set(required) and r.outcome is GateOutcome.FAIL:
            reasons.append(f"{name} (not required): FAIL: {r.reason}")

    if failed:
        return INVALID, reasons
    if incomplete:
        return INCOMPLETE, reasons
    return VALID, reasons


def apply_status(case_dir: str | Path, required: Iterable[str]) -> str:
    """Read <case>/qa_report.json, write status + reasons into <case>/results.json. Returns status."""
    case_dir = Path(case_dir)
    report = json.loads((case_dir / "qa_report.json").read_text())
    gates = [GateResult.from_dict(g) for g in report.get("gates", [])]
    status, reasons = assign_status(gates, list(required))

    results_path = case_dir / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    results["status"] = status
    results["status_reasons"] = reasons
    results_path.write_text(json.dumps(results, indent=2) + "\n")
    return status
