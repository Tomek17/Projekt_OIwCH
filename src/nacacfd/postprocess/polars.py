"""Collect per-case coefficients into polars.

Status: collect_polar and write_polar_csv implemented (F5 prep). Every case is kept, with its status and the
gates that did not pass, so an invalid point can be shown as invalid but never silently dropped.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

FIELDS = ["case", "alpha_deg", "CL", "CD", "CM", "status", "not_passed"]


def collect_polar(experiment_dir) -> list[dict]:
    """Return one row per case directory that has a results.json, sorted by angle of attack."""
    rows = []
    for case in sorted(Path(experiment_dir).iterdir()):
        res = case / "results.json"
        if not case.is_dir() or case.name.startswith("_") or not res.exists():
            continue
        r = json.loads(res.read_text())
        qa_path = case / "qa_report.json"
        gates = json.loads(qa_path.read_text())["gates"] if qa_path.exists() else []
        rows.append({
            "case": case.name,
            "alpha_deg": r["alpha_deg"],
            "CL": r.get("CL"),
            "CD": r.get("CD"),
            "CM": r.get("CM"),
            "status": r["status"],
            "not_passed": ";".join(f"{g['name']}:{g['outcome']}" for g in gates if g["outcome"] != "pass"),
        })
    return sorted(rows, key=lambda row: (row["alpha_deg"], row["case"]))


def write_polar_csv(rows: list[dict], out_path) -> Path:
    out_path = Path(out_path)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return out_path
