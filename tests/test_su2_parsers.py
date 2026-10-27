from nacacfd.runner.convergence import read_mesh_quality, read_su2_version, solver_reported_converged

LOG = """|   / __| | | |_  )   Release 8.5.0 "Harrier"                           |
|    Orthogonality Angle (deg.)|        81.4478|             90|
|     CV Face Area Aspect Ratio|        1.00305|    2.39147e+07|
|           CV Sub-Volume Ratio|              1|        4.15802|
|      Convergence Field     |     Value    |   Criterion  |  Converged |
+-----------------------------------------------------------------------+
|                    rms[Rho]|      -12.0024|         < -12|         Yes|
"""


def test_parsers(tmp_path):
    p = tmp_path / "solver.log"
    p.write_text(LOG)
    q = read_mesh_quality(p)
    assert q["Orthogonality Angle (deg.)"]["min"] == 81.4478
    assert q["CV Face Area Aspect Ratio"]["max"] == 2.39147e07
    assert read_su2_version(p) == "8.5.0"
    assert solver_reported_converged(p) is True


def test_crashed_log(tmp_path):
    p = tmp_path / "solver.log"
    p.write_text("Error Exit\n")
    assert solver_reported_converged(p) is None and read_mesh_quality(p) == {}
