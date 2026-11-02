"""Comparison of CFD results with reference data.

Status: implemented (F5). Read-only: reference files are never modified.
TMR files are Tecplot-style text: '#' comments, a `variables=` line, `zone, t="..."` headers, numeric rows.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def load_reference(path) -> dict[str, list[list[float]]]:
    """Read a reference file only if the SOURCE.md next to it lists the file's sha256 (provenance check).

    Raises ValueError for data without a source record or with a different hash (edited or replaced file).
    """
    path = Path(path)
    source = path.parent / "SOURCE.md"
    if not source.exists():
        raise ValueError(f"no SOURCE.md next to {path}: reference data without a source is refused")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest not in source.read_text():
        raise ValueError(f"sha256 of {path.name} ({digest[:12]}...) is not listed in {source}")
    return read_zones(path)


def read_zones(path) -> dict[str, list[list[float]]]:
    """Return {zone title: rows of floats}, in file order."""
    zones: dict[str, list[list[float]]] = {}
    cur = None
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.lower().startswith("variables"):
            continue
        if s.lower().startswith("zone"):
            cur = s.split("=", 1)[1].strip().strip('"') if "=" in s else s
            zones[cur] = []
            continue
        zones.setdefault(cur, []).append([float(x) for x in s.split()])
    return zones


def interp(xs, ys, x):
    """Linear interpolation; None outside the data range (never extrapolates)."""
    pts = sorted(zip(xs, ys))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def pre_stall(rows: list[list[float]]) -> list[list[float]]:
    """Rows up to and including the CL maximum (column 1), so interpolation never crosses the stall drop."""
    i = max(range(len(rows)), key=lambda k: rows[k][1])
    return rows[: i + 1]


def ladson_at(zones: dict, alpha: float, cl: float) -> dict:
    """Per-series reference values at our point: CL at the same alpha, CD at the same CL (pre-stall branch)."""
    out = {}
    for name, rows in zones.items():
        ps = pre_stall(rows)
        out[name] = {"CL": interp([p[0] for p in ps], [p[1] for p in ps], alpha),
                     "CD_at_CL": interp([p[1] for p in ps], [p[2] for p in ps], cl)}
    return out
