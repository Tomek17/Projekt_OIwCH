"""Read SU2 output files: history, solver log, surface CSV.

Status: implemented (F2), tested on SU2 v8.5.0 output.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


def _read_csv_columns(path) -> dict[str, list[float]]:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = [h.strip().strip('"') for h in next(reader)]
        cols: dict[str, list[float]] = {h: [] for h in header}
        for row in reader:
            if not row:
                continue
            for h, v in zip(header, row):
                cols[h].append(float(v))
    return cols


def read_history(history_path) -> dict[str, list[float]]:
    """Parse SU2 history.csv into columns keyed by the SU2 column name (e.g. 'Inner_Iter', 'rms[Rho]', 'CL')."""
    return _read_csv_columns(history_path)


def read_surface(surface_csv_path) -> dict[str, list[float]]:
    """Parse SU2 surface_flow.csv (one row per wall point)."""
    return _read_csv_columns(surface_csv_path)


_QUALITY_RE = re.compile(r"\|\s*(Orthogonality Angle \(deg\.\)|CV Face Area Aspect Ratio|CV Sub-Volume Ratio)"
                         r"\|\s*([-+0-9.eE]+)\|\s*([-+0-9.eE]+)\|")


def read_mesh_quality(solver_log_path) -> dict[str, dict[str, float]]:
    """Extract SU2's 'Mesh Quality Metric' table from the solver log: {metric: {'min':..., 'max':...}}."""
    out: dict[str, dict[str, float]] = {}
    for line in Path(solver_log_path).read_text(errors="replace").splitlines():
        m = _QUALITY_RE.search(line)
        if m:
            out[m.group(1)] = {"min": float(m.group(2)), "max": float(m.group(3))}
    return out


def read_su2_version(solver_log_path) -> str | None:
    m = re.search(r"Release ([0-9.]+)", Path(solver_log_path).read_text(errors="replace"))
    return m.group(1) if m else None


def solver_reported_converged(solver_log_path) -> bool | None:
    """True/False from SU2's final 'Convergence Field' table; None if the table is missing (e.g. crash)."""
    text = Path(solver_log_path).read_text(errors="replace")
    m = re.search(r"Convergence Field.*?\n(?:.*\n)*?\|\s*rms\[Rho\]\|[^|]*\|[^|]*\|\s*(Yes|No)\|", text)
    if not m:
        return None
    return m.group(1) == "Yes"
