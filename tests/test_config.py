from pathlib import Path

import pytest

from nacacfd.config import ConfigError, load_experiment, load_thresholds


@pytest.mark.parametrize("name", ["naca0012_a5_smoke.yaml", "naca0012_validation.yaml"])
def test_example_experiments_load(repo_root, name):
    exp = load_experiment(repo_root / "experiments" / name)
    assert exp.airfoil == "NACA0012"
    assert exp.turbulence_model == "SA"
    assert exp.required_gates


def test_thresholds_load_and_every_gate_has_status(repo_root):
    data = load_thresholds(repo_root / "config" / "qa_thresholds.yaml")
    assert {"mesh_quality", "wall_yplus", "convergence", "gci", "validation", "physics_flags"} <= set(data["gates"])


def test_validation_tolerance_is_deliberately_undefined(repo_root):
    # The tolerance must be chosen after seeing the reference data, not invented up front.
    gate = load_thresholds(repo_root / "config" / "qa_thresholds.yaml")["gates"]["validation"]
    assert gate["status"] == "undefined" and gate["cl_tolerance"] is None


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "exp.yaml"
    p.write_text(text)
    return p


BASE = """
name: t
airfoil: NACA0012
alpha_deg: [0, 5]
reynolds: 6.0e6
mach: 0.15
turbulence_model: SA
mesh_level: medium
required_gates: [convergence]
"""


def test_valid_minimal_experiment(tmp_path):
    exp = load_experiment(_write(tmp_path, BASE))
    assert exp.alpha_deg == [0.0, 5.0]


@pytest.mark.parametrize("old,new", [
    ("airfoil: NACA0012", "airfoil: clark-y"),
    ("mach: 0.15", "mach: 1.5"),
    ("turbulence_model: SA", "turbulence_model: k-epsilon"),
    ("mesh_level: medium", "mesh_level: huge"),
    ("alpha_deg: [0, 5]", "alpha_deg: []"),
    ("required_gates: [convergence]", "required_gates: []"),
    ("reynolds: 6.0e6", "reynolds: -1"),
])
def test_bad_experiments_are_rejected(tmp_path, old, new):
    with pytest.raises(ConfigError):
        load_experiment(_write(tmp_path, BASE.replace(old, new)))
