"""Loading and validating experiment YAML files and QA thresholds.

Status: implemented and unit-tested in F0 (pure Python, no CFD involved).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_THRESHOLDS = REPO_ROOT / "config" / "qa_thresholds.yaml"

TURBULENCE_MODELS = {"SA", "SST"}
MESH_LEVELS = {"coarse", "medium", "fine", "xfine"}
MESH_SOURCES = {"file", "gmsh"}
GEOMETRY_VARIANTS = {"standard_closed_te", "standard_open_te"}
_NACA_RE = re.compile(r"^NACA\d{4,5}$")


class ConfigError(ValueError):
    """Raised when an experiment or threshold file is malformed."""


@dataclass(frozen=True)
class Experiment:
    """One experiment = one YAML file in experiments/."""

    name: str
    airfoil: str
    alpha_deg: list[float]
    reynolds: float
    mach: float
    turbulence_model: str
    mesh_level: str
    required_gates: list[str]
    solver: dict[str, Any] = field(default_factory=dict)
    mesh: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    geometry_variant: str = "standard_closed_te"
    mesh_levels: list[str] = field(default_factory=list)  # non-empty = grid study, one case per level


def _require(data: dict, key: str, source: str) -> Any:
    if key not in data:
        raise ConfigError(f"{source}: missing required key '{key}'")
    return data[key]


def load_experiment(path: str | Path) -> Experiment:
    """Read and validate an experiment YAML. Raises ConfigError on any problem."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")

    airfoil = str(_require(data, "airfoil", str(path))).upper().replace(" ", "")
    if not _NACA_RE.match(airfoil):
        raise ConfigError(f"{path}: airfoil must look like NACA0012 or NACA23012, got {airfoil!r}")

    alpha = _require(data, "alpha_deg", str(path))
    if not isinstance(alpha, list) or not alpha:
        raise ConfigError(f"{path}: alpha_deg must be a non-empty list")
    alpha = [float(a) for a in alpha]

    reynolds = float(_require(data, "reynolds", str(path)))
    mach = float(_require(data, "mach", str(path)))
    if reynolds <= 0:
        raise ConfigError(f"{path}: reynolds must be positive")
    if not 0 < mach < 1:
        raise ConfigError(f"{path}: mach must be in (0, 1) for this project")

    model = str(_require(data, "turbulence_model", str(path))).upper()
    if model not in TURBULENCE_MODELS:
        raise ConfigError(f"{path}: turbulence_model must be one of {sorted(TURBULENCE_MODELS)}")

    level = str(_require(data, "mesh_level", str(path))).lower()
    if level not in MESH_LEVELS:
        raise ConfigError(f"{path}: mesh_level must be one of {sorted(MESH_LEVELS)}")

    mesh = dict(data.get("mesh") or {})
    source = mesh.get("source", "gmsh")
    if source not in MESH_SOURCES:
        raise ConfigError(f"{path}: mesh.source must be one of {sorted(MESH_SOURCES)}")
    if source == "file" and not (mesh.get("path") and mesh.get("sha256")):
        raise ConfigError(f"{path}: mesh.source 'file' needs mesh.path and mesh.sha256")
    mesh["source"] = source

    variant = str(data.get("geometry_variant") or "standard_closed_te")
    if variant not in GEOMETRY_VARIANTS:
        raise ConfigError(f"{path}: geometry_variant must be one of {sorted(GEOMETRY_VARIANTS)}"
                          " (the NASA TMR variant is not implemented: definition not verified)")

    levels = [str(x).lower() for x in (data.get("mesh_levels") or [])]
    if any(x not in MESH_LEVELS for x in levels):
        raise ConfigError(f"{path}: mesh_levels entries must be in {sorted(MESH_LEVELS)}")
    if levels and source != "gmsh":
        raise ConfigError(f"{path}: mesh_levels (grid study) needs mesh.source: gmsh")

    gates = _require(data, "required_gates", str(path))
    if not isinstance(gates, list) or not gates:
        raise ConfigError(f"{path}: required_gates must be a non-empty list")

    return Experiment(
        name=str(_require(data, "name", str(path))),
        airfoil=airfoil,
        alpha_deg=alpha,
        reynolds=reynolds,
        mach=mach,
        turbulence_model=model,
        mesh_level=level,
        required_gates=[str(g) for g in gates],
        solver=dict(data.get("solver") or {}),
        mesh=mesh,
        notes=str(data.get("notes") or ""),
        geometry_variant=variant,
        mesh_levels=levels,
    )


def load_thresholds(path: str | Path = DEFAULT_THRESHOLDS) -> dict[str, Any]:
    """Read config/qa_thresholds.yaml. Every gate section must have a 'status' field."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "gates" not in data:
        raise ConfigError(f"{path}: expected a top-level 'gates' mapping")
    for name, section in data["gates"].items():
        if not isinstance(section, dict) or "status" not in section:
            raise ConfigError(f"{path}: gate '{name}' must have a 'status' field")
    return data
