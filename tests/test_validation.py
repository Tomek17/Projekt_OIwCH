"""Validation gate on synthetic reference files: provenance check, band logic, honest NOT_RUN cases."""

import hashlib

import pytest

from nacacfd.postprocess.compare import interp, load_reference, pre_stall
from nacacfd.qa.base import GateOutcome
from nacacfd.qa.validation import check_validation

REF = """# synthetic test data, not from any experiment
variables="alpha, deg","cl","cd"
zone, t="A"
0 0.0 0.0080
10 1.00 0.0120
16 1.50 0.0200
18 0.90 0.1500
zone, t="B"
0 0.0 0.0082
10 1.02 0.0124
16 1.54 0.0210
18 1.00 0.1600
"""


def make_ref(tmp_path, listed=True):
    f = tmp_path / "ref.dat"
    f.write_text(REF)
    digest = hashlib.sha256(f.read_bytes()).hexdigest() if listed else "0" * 64
    (tmp_path / "SOURCE.md").write_text(f"| ref.dat | synthetic | {digest} |\n")
    return f


def thr(mode="reference_spread"):
    return {"gates": {"validation": {"tolerance_mode": mode, "cl_tolerance": None, "cd_tolerance": None}}}


def row(alpha, cl, cd, case="c"):
    return {"case": case, "alpha_deg": alpha, "CL": cl, "CD": cd}


def test_interp_never_extrapolates():
    assert interp([0, 1], [0, 2], 0.5) == 1.0
    assert interp([0, 1], [0, 2], 1.5) is None


def test_pre_stall_stops_at_cl_max():
    rows = [[0, 0.0, 0], [16, 1.5, 0], [18, 0.9, 0]]
    assert pre_stall(rows)[-1][0] == 16


def test_reference_without_matching_hash_is_refused(tmp_path):
    f = make_ref(tmp_path, listed=False)
    with pytest.raises(ValueError):
        load_reference(f)
    r = check_validation([row(10, 1.01, 0.0122)], f, thr())
    assert r["c"].outcome is GateOutcome.NOT_RUN and "sha256" in r["c"].reason


def test_inside_band_passes_outside_fails(tmp_path):
    f = make_ref(tmp_path)
    # at alpha 10 the CL band is [1.00, 1.02]; CD at CL 1.01 is between the two series
    assert check_validation([row(10, 1.01, 0.0122)], f, thr())["c"].outcome is GateOutcome.PASS
    r = check_validation([row(10, 1.05, 0.0122)], f, thr())["c"]
    assert r.outcome is GateOutcome.FAIL and "CL" in r.reason


def test_mode_not_set_is_not_run(tmp_path):
    f = make_ref(tmp_path)
    assert check_validation([row(10, 1.01, 0.0122)], f, thr(None))["c"].outcome is GateOutcome.NOT_RUN


def test_point_beyond_reference_stall_is_not_run(tmp_path):
    # alpha 18 is past the CL maximum of both series: no pre-stall reference, so no verdict
    f = make_ref(tmp_path)
    r = check_validation([row(18, 1.7, 0.03)], f, thr())["c"]
    assert r.outcome is GateOutcome.NOT_RUN
