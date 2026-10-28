"""Plot a grid study: surface Cp per level and CL/CD vs representative cell size h, with the GCI extrapolation.

Usage (in the image): python scripts/plot_grid_study.py runs/<experiment> <alpha_case> <out.png>
Reads only files written by the pipeline (results.json, mesh_info.json, surface_flow.csv, gci_<alpha>.json,
qa_report.json). Status: written for F4f, used to make the figure shown to the student.
"""

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main(study: str, alpha_case: str, out: str) -> None:
    study = Path(study)
    cases = sorted(study.glob(f"{alpha_case}_*"), key=lambda c: -json.loads((c / "mesh_info.json").read_text())["statistics"]["elements"])
    gci = json.loads((study / f"gci_{alpha_case}.json").read_text())
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4.5))
    for c in cases:
        r = json.loads((c / "results.json").read_text())
        n = json.loads((c / "mesh_info.json").read_text())["statistics"]["elements"]
        rows = list(csv.DictReader(open(c / "surface_flow.csv")))
        key = lambda name: next(k for k in rows[0] if k.strip().strip('"') == name)  # noqa: E731
        x = [float(row[key("x")]) for row in rows]
        cp = [float(row[key("Pressure_Coefficient")]) for row in rows]
        ax1.plot(x, cp, ".", ms=1.5, label=f"{c.name.split('_')[-1]} ({n:,} cells, {r['status']})")
    ax1.invert_yaxis()
    ax1.set(xlabel="x/c", ylabel="Cp", title=f"Surface Cp, {alpha_case}")
    ax1.legend(markerscale=6, fontsize=8)
    for ax, q in ((ax2, "CL"), (ax3, "CD")):
        g = gci[q]
        ax.plot(g["h"], g["phi"], "o-", label="GCI levels")
        if g.get("phi_ext") is not None:
            ax.plot([0], [g["phi_ext"]], "s", label=f"Richardson extrapolation (p = {g['p']:.2f})")
            ax.set_title(f"{q}: GCI_fine = {100 * g['gci_fine']:.2f} %, {g['convergence']}")
        else:
            ax.set_title(f"{q}: {g['convergence']}, no GCI")
        ax.set(xlabel="h = (1/N)^(1/2)", ylabel=q, xlim=(0, None))
        ax.legend(fontsize=8)
    fig.suptitle(f"{study.name}: NACA 0012, M 0.15, Re 6e6, SA. Not validated against experiment.", fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=130)


if __name__ == "__main__":
    main(*sys.argv[1:4])
