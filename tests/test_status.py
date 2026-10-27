import json

import pytest

from nacacfd.qa.base import GateOutcome, GateResult
from nacacfd.qa.status import INCOMPLETE, INVALID, VALID, apply_status, assign_status

REQ = ["mesh_quality", "wall_yplus", "convergence"]


def g(name, outcome, reason="r"):
    return GateResult(name=name, outcome=GateOutcome(outcome), reason=reason)


def test_all_pass_is_valid():
    status, reasons = assign_status([g(n, "pass") for n in REQ], REQ)
    assert status == VALID and reasons == []


def test_one_fail_is_invalid():
    gates = [g("mesh_quality", "pass"), g("wall_yplus", "fail", "max y+ 3.1"), g("convergence", "pass")]
    status, reasons = assign_status(gates, REQ)
    assert status == INVALID
    assert any("wall_yplus" in r and "3.1" in r for r in reasons)


def test_missing_gate_is_never_valid():
    status, reasons = assign_status([g("mesh_quality", "pass"), g("wall_yplus", "pass")], REQ)
    assert status == INCOMPLETE and "convergence: missing" in reasons


def test_not_run_gate_is_never_valid():
    gates = [g("mesh_quality", "pass"), g("wall_yplus", "pass"), g("convergence", "not_run", "no history")]
    assert assign_status(gates, REQ)[0] == INCOMPLETE


def test_fail_wins_over_incomplete():
    assert assign_status([g("mesh_quality", "fail")], REQ)[0] == INVALID


def test_non_required_failure_is_reported_but_does_not_block():
    gates = [g(n, "pass") for n in REQ] + [g("validation", "fail", "off by a lot")]
    status, reasons = assign_status(gates, REQ)
    assert status == VALID and any("validation (not required)" in r for r in reasons)


def test_fail_without_reason_is_rejected():
    with pytest.raises(ValueError):
        GateResult(name="x", outcome=GateOutcome.FAIL)


def test_apply_status_writes_results_json(tmp_path):
    report = {"gates": [g(n, "pass").to_dict() for n in REQ[:2]]}
    (tmp_path / "qa_report.json").write_text(json.dumps(report))
    (tmp_path / "results.json").write_text(json.dumps({"CL": 0.5}))
    assert apply_status(tmp_path, REQ) == INCOMPLETE
    results = json.loads((tmp_path / "results.json").read_text())
    assert results["CL"] == 0.5 and results["status"] == INCOMPLETE
