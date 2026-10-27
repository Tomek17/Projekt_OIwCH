import re

import pytest

from nacacfd.airfoil.su2_config import render_config
from nacacfd.config import ConfigError, load_experiment
from nacacfd.runner.case import CaseExistsError, case_name, run_case


def test_render_config(repo_root, tmp_path):
    exp = load_experiment(repo_root / "experiments" / "naca0012_a5_su2grid.yaml")
    cfg = render_config(exp, 5.0, tmp_path / "mesh.su2", tmp_path / "config.cfg").read_text()
    assert "${" not in cfg
    assert re.search(r"^AOA= 5.0$", cfg, re.M)
    assert re.search(r"^MACH_NUMBER= 0.15$", cfg, re.M)
    assert re.search(r"^KIND_TURB_MODEL= SA$", cfg, re.M)
    assert re.search(r"^MESH_FILENAME= mesh.su2$", cfg, re.M)
    assert re.search(r"^CONV_STARTITER= 1000$", cfg, re.M)  # must exceed the 500-iteration window


def test_case_name():
    assert case_name(5.0) == "a+05.00" and case_name(-2.5) == "a-02.50"


def test_file_mesh_needs_checksum(tmp_path):
    p = tmp_path / "e.yaml"
    p.write_text("name: t\nairfoil: NACA0012\nalpha_deg: [5]\nreynolds: 6e6\nmach: 0.15\nturbulence_model: SA\n"
                 "mesh_level: coarse\nmesh: {source: file, path: x.su2}\nrequired_gates: [convergence]\n")
    with pytest.raises(ConfigError):
        load_experiment(p)


def test_existing_results_are_never_overwritten(repo_root, tmp_path):
    exp = load_experiment(repo_root / "experiments" / "naca0012_a5_su2grid.yaml")
    (tmp_path / "results.json").write_text("{}")
    with pytest.raises(CaseExistsError):
        run_case(exp, 5.0, tmp_path)
