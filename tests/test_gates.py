"""Per-case QA gates on synthetic SU2-like files, including deliberately broken inputs that must be rejected."""

import json
import math
from pathlib import Path

import pytest

from nacacfd.config import load_thresholds
from nacacfd.qa.base import GateOutcome
from nacacfd.qa.convergence import check_convergence
from nacacfd.qa.mesh import check_mesh_quality
from nacacfd.qa.physics_flags import check_physics
from nacacfd.qa.report import run_case_gates
from nacacfd.qa.yplus import check_yplus


@pytest.fixture
def thr(repo_root):
    return load_thresholds(repo_root / "config" / "qa_thresholds.yaml")


def write_history(case: Path, rho, cl, cd):
    lines = ['"Inner_Iter","rms[Rho]","CL","CD","CMz"']
    lines += [f"{i},{r},{a},{b},0.0" for i, (r, a, b) in enumerate(zip(rho, cl, cd))]
    (case / "history.csv").write_text("\n".join(lines) + "\n")


def converged_series(n=1000):
    rho = [-4.0 - 9.0 * i / (n - 1) for i in range(n)]
    cl = [0.56 + 0.1 * math.exp(-i / 50) for i in range(n)]
    cd = [0.011 + 0.01 * math.exp(-i / 50) for i in range(n)]
    return rho, cl, cd


# --- convergence ------------------------------------------------------------------------------------------
def test_convergence_pass(tmp_path, thr):
    write_history(tmp_path, *converged_series())
    assert check_convergence(tmp_path, thr).outcome is GateOutcome.PASS


def test_convergence_cl_near_zero_needs_reference_magnitude(tmp_path, thr):
    # alpha 0: CL settles at ~1e-7 with noise 1e-8, fully converged otherwise.
    rho, _, cd = converged_series()
    cl = [1e-7 + 1e-8 * (-1) ** i for i in range(len(rho))]
    write_history(tmp_path, rho, cl, cd)
    thr["gates"]["convergence"].pop("cl_reference_magnitude", None)
    assert check_convergence(tmp_path, thr).outcome is GateOutcome.FAIL
    thr["gates"]["convergence"]["cl_reference_magnitude"] = 0.1
    r = check_convergence(tmp_path, thr)
    assert r.outcome is GateOutcome.PASS and r.value["cl_relative_range"] == pytest.approx(2e-8 / 0.1)


def test_convergence_rejects_small_residual_drop(tmp_path, thr):
    rho, cl, cd = converged_series()
    rho = [-4.0 - 2.0 * i / (len(rho) - 1) for i in range(len(rho))]  # only 2 orders
    write_history(tmp_path, rho, cl, cd)
    r = check_convergence(tmp_path, thr)
    assert r.outcome is GateOutcome.FAIL and "residual drop" in r.reason


def test_convergence_rejects_oscillating_lift(tmp_path, thr):
    rho, cl, cd = converged_series()
    cl = [0.56 + 0.01 * math.sin(i / 10) for i in range(len(cl))]  # residual fine, CL oscillates
    write_history(tmp_path, rho, cl, cd)
    r = check_convergence(tmp_path, thr)
    assert r.outcome is GateOutcome.FAIL and "CL relative range" in r.reason


def test_convergence_truncated_run_is_not_judged(tmp_path, thr):
    write_history(tmp_path, *converged_series(n=300))  # shorter than the 500-iteration window
    assert check_convergence(tmp_path, thr).outcome is GateOutcome.NOT_RUN


def test_convergence_rejects_divergence(tmp_path, thr):
    rho, cl, cd = converged_series()
    cl[-1] = float("nan")
    write_history(tmp_path, rho, cl, cd)
    assert check_convergence(tmp_path, thr).outcome is GateOutcome.FAIL


def test_convergence_missing_history(tmp_path, thr):
    assert check_convergence(tmp_path, thr).outcome is GateOutcome.NOT_RUN


# --- y+ ---------------------------------------------------------------------------------------------------
def write_surface(case: Path, yplus, col="Y_Plus"):
    rows = ['"PointID","x","y","' + col + '"'] + [f"{i},0,0,{v}" for i, v in enumerate(yplus)]
    (case / "surface_flow.csv").write_text("\n".join(rows) + "\n")


@pytest.mark.parametrize("yplus,outcome", [
    ([0.3, 0.8], GateOutcome.PASS),
    ([0.3, 1.5], GateOutcome.PASS),   # above target, below the fail limit: pass with a note
    ([0.5, 3.1], GateOutcome.FAIL),   # first cell too thick
])
def test_yplus(tmp_path, thr, yplus, outcome):
    write_surface(tmp_path, yplus)
    r = check_yplus(tmp_path, thr)
    assert r.outcome is outcome
    if max(yplus) > 1.0:
        assert r.reason


def test_yplus_missing_column_is_not_a_pass(tmp_path, thr):
    write_surface(tmp_path, [0.5], col="Pressure")
    assert check_yplus(tmp_path, thr).outcome is GateOutcome.NOT_RUN


# --- mesh quality -----------------------------------------------------------------------------------------
def write_log(case: Path, ortho_min):
    (case / "solver.log").write_text(
        "|           Mesh Quality Metric|        Minimum|        Maximum|\n"
        f"|    Orthogonality Angle (deg.)|        {ortho_min}|             90|\n"
        "|     CV Face Area Aspect Ratio|        1.00305|    2.39147e+07|\n")


def test_mesh_quality_pass_and_fail(tmp_path, thr):
    write_log(tmp_path, 81.4478)
    assert check_mesh_quality(tmp_path, thr).outcome is GateOutcome.PASS
    write_log(tmp_path, 12.0)
    assert check_mesh_quality(tmp_path, thr).outcome is GateOutcome.FAIL


def test_mesh_quality_without_table_is_not_a_pass(tmp_path, thr):
    (tmp_path / "solver.log").write_text("crashed before mesh statistics\n")
    assert check_mesh_quality(tmp_path, thr).outcome is GateOutcome.NOT_RUN


# --- physics flags ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("results,outcome", [
    ({"solver_exit_code": 0, "CL": 0.56, "CD": 0.011}, GateOutcome.PASS),
    ({"solver_exit_code": 0, "CL": 0.56, "CD": -0.002}, GateOutcome.FAIL),
    ({"solver_exit_code": 1}, GateOutcome.FAIL),
    ({"solver_exit_code": 0, "CL": None, "CD": None}, GateOutcome.FAIL),
])
def test_physics(tmp_path, thr, results, outcome):
    (tmp_path / "results.json").write_text(json.dumps(results))
    assert check_physics(tmp_path, thr).outcome is outcome


# --- whole case -------------------------------------------------------------------------------------------
def make_good_case(case: Path):
    write_history(case, *converged_series())
    write_surface(case, [0.4, 0.9])
    write_log(case, 80.0)
    (case / "results.json").write_text(json.dumps({"solver_exit_code": 0, "CL": 0.56, "CD": 0.011}))


def test_good_case_is_valid(tmp_path, thr):
    make_good_case(tmp_path)
    req = ["mesh_quality", "wall_yplus", "convergence", "physics_flags"]
    assert run_case_gates(tmp_path, req, thr) == "valid"
    assert json.loads((tmp_path / "results.json").read_text())["status"] == "valid"


def test_case_requiring_gci_cannot_be_valid_from_case_gates(tmp_path, thr):
    make_good_case(tmp_path)
    assert run_case_gates(tmp_path, ["convergence", "gci"], thr) == "incomplete"


def test_one_bad_gate_makes_case_invalid(tmp_path, thr):
    make_good_case(tmp_path)
    write_surface(tmp_path, [0.4, 3.1])
    req = ["mesh_quality", "wall_yplus", "convergence", "physics_flags"]
    assert run_case_gates(tmp_path, req, thr) == "invalid"
