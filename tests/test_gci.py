import json
import math

import pytest

from nacacfd.config import load_thresholds
from nacacfd.qa.base import GateOutcome
from nacacfd.qa.gci import check_gci, compute_gci, representative_h


def synthetic(p_true=2.0, r=2 ** 0.5, exact=0.5, c=0.1, h1=0.01):
    h = [h1, h1 * r, h1 * r * r]
    return h, [exact + c * hi ** p_true for hi in h]


def test_recovers_order_and_extrapolated_value():
    h, phi = synthetic(p_true=2.0)
    g = compute_gci(h, phi, 1.25)
    assert g["convergence"] == "monotonic"
    assert g["p"] == pytest.approx(2.0, rel=1e-6)
    assert g["phi_ext"] == pytest.approx(0.5, rel=1e-9)


def test_unequal_refinement_ratios():
    h = [0.01, 0.014, 0.021]
    phi = [0.5 + 0.1 * x ** 1.5 for x in h]
    g = compute_gci(h, phi, 1.25)
    assert g["p"] == pytest.approx(1.5, rel=1e-6)


def test_oscillatory_and_divergent_are_not_given_a_gci():
    h = [0.01, 0.014, 0.02]
    assert compute_gci(h, [0.50, 0.52, 0.49], 1.25)["convergence"] == "oscillatory"
    assert compute_gci(h, [0.50, 0.51, 0.515], 1.25)["convergence"] == "divergent"
    assert compute_gci(h, [0.50, 0.52, 0.49], 1.25)["gci_fine"] is None


def test_order_of_h_is_checked():
    with pytest.raises(ValueError):
        compute_gci([0.03, 0.02, 0.01], [1, 2, 3], 1.25)


def test_representative_h():
    assert representative_h(10000) == pytest.approx(0.01)


def make_study(tmp_path, cl, cd, cells=(80000, 40000, 20000), case_gates_ok=True):
    for lvl, a, b, n in zip(("fine", "medium", "coarse"), cl, cd, cells):
        d = tmp_path / f"a+05.00_{lvl}"
        d.mkdir()
        (d / "results.json").write_text(json.dumps({"CL": a, "CD": b}))
        (d / "mesh_info.json").write_text(json.dumps({"statistics": {"elements": n}}))
        outcome = "pass" if case_gates_ok else "fail"
        (d / "qa_report.json").write_text(json.dumps({"gates": [{"name": "convergence", "outcome": outcome}]}))


@pytest.fixture
def thr(repo_root):
    return load_thresholds(repo_root / "config" / "qa_thresholds.yaml")


def test_gate_pass_on_well_converged_study(tmp_path, thr):
    h = [representative_h(n) for n in (80000, 40000, 20000)]
    make_study(tmp_path, [0.56 + 0.5 * x ** 2 for x in h], [0.0100 + 0.5 * x ** 2 for x in h])
    assert check_gci(tmp_path, thr, "a+05.00").outcome is GateOutcome.PASS


def test_gate_fails_on_oscillation(tmp_path, thr):
    make_study(tmp_path, [0.56, 0.57, 0.55], [0.0100, 0.0101, 0.0102])
    r = check_gci(tmp_path, thr, "a+05.00")
    assert r.outcome is GateOutcome.FAIL and "oscillatory" in r.reason


def test_gate_not_run_if_a_level_failed_its_case_gates(tmp_path, thr):
    make_study(tmp_path, [0.56, 0.57, 0.58], [0.010, 0.011, 0.012], case_gates_ok=False)
    assert check_gci(tmp_path, thr, "a+05.00").outcome is GateOutcome.NOT_RUN


def test_gate_fails_on_large_gci(tmp_path, thr):
    h = [representative_h(n) for n in (80000, 40000, 20000)]
    make_study(tmp_path, [0.56 + 300 * x ** 1 for x in h], [0.0100 + 0.5 * x ** 2 for x in h])
    r = check_gci(tmp_path, thr, "a+05.00")
    assert r.outcome is GateOutcome.FAIL and "CL: GCI_fine" in r.reason
    assert math.isfinite(r.value["CL"]["gci_fine"])
