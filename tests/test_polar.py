import json

import pytest

from nacacfd.cli import main
from nacacfd.postprocess.polars import collect_polar


def make_case(root, name, alpha, cl, status, gates=()):
    d = root / name
    d.mkdir()
    (d / "results.json").write_text(json.dumps({"alpha_deg": alpha, "CL": cl, "CD": 0.01, "CM": 0.0, "status": status}))
    (d / "qa_report.json").write_text(json.dumps({"gates": [{"name": n, "outcome": o} for n, o in gates]}))


def test_collect_polar_keeps_invalid_points_and_sorts(tmp_path):
    make_case(tmp_path, "a+10.00", 10.0, 1.08, "invalid", [("wall_yplus", "fail"), ("convergence", "pass")])
    make_case(tmp_path, "a+05.00", 5.0, 0.55, "valid", [("convergence", "pass")])
    (tmp_path / "_attempts").mkdir()
    rows = collect_polar(tmp_path)
    assert [r["alpha_deg"] for r in rows] == [5.0, 10.0]
    assert rows[1]["status"] == "invalid" and rows[1]["not_passed"] == "wall_yplus:fail"
    assert rows[0]["not_passed"] == ""


def test_report_writes_csv_and_png(tmp_path):
    pytest.importorskip("matplotlib")
    make_case(tmp_path, "a+05.00", 5.0, 0.55, "valid")
    make_case(tmp_path, "a+10.00", 10.0, 1.08, "incomplete", [("gci", "not_run")])
    assert main(["report", str(tmp_path)]) == 0
    assert (tmp_path / "polar.csv").read_text().count("\n") == 3
    assert (tmp_path / "polar.png").stat().st_size > 0
