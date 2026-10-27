"""SU2 configuration file generation from a template + experiment settings.

Status: implemented (F2). Every value comes from the experiment YAML or from SOLVER_DEFAULTS below.
"""

from __future__ import annotations

from pathlib import Path
from string import Template

TEMPLATE_DIR = Path(__file__).parent / "templates"
DEFAULT_TEMPLATE = "su2_rans_compressible.cfg"

# Defaults taken from SU2 v8.5.0 TestCases/rans/naca0012/turb_NACA0012_sa.cfg, except max_iterations
# (that file uses 99999 with a restart). Override any of them in the experiment YAML under `solver:`.
SOLVER_DEFAULTS = {
    "freestream_temperature_K": 300.0,
    "cfl": 1000.0,
    "max_iterations": 20000,
    "residual_minval": -12,
    # SU2 does not test convergence before CONV_STARTITER, so this acts as a minimum iteration count.
    # It must exceed the convergence gate's stabilisation window (500) plus the start-up transient.
    "min_iterations": 1000,
    "n_procs": 4,
}


def solver_settings(experiment) -> dict:
    """Experiment `solver:` values on top of SOLVER_DEFAULTS; None in the YAML means 'use the default'."""
    settings = dict(SOLVER_DEFAULTS)
    settings.update({k: v for k, v in experiment.solver.items() if v is not None})
    return settings


def render_config(experiment, alpha_deg: float, mesh_path, out_path) -> Path:
    """Write an SU2 .cfg for one case and return its path."""
    s = solver_settings(experiment)
    template = Template((TEMPLATE_DIR / s.get("template", DEFAULT_TEMPLATE)).read_text())
    sa_line = ""  # standard SA, no options (see decisions D-010)
    text = template.substitute(
        turbulence_model=experiment.turbulence_model,
        sa_options_line=sa_line,
        mach=experiment.mach,
        alpha_deg=alpha_deg,
        freestream_temperature_K=s["freestream_temperature_K"],
        reynolds=experiment.reynolds,
        cfl=s["cfl"],
        max_iterations=int(s["max_iterations"]),
        residual_minval=s["residual_minval"],
        min_iterations=int(s["min_iterations"]),
        mesh_filename=Path(mesh_path).name,
    )
    out_path = Path(out_path)
    out_path.write_text(text)
    return out_path
