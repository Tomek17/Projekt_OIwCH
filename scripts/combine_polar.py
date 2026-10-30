"""Combine the laptop polar with the longer near-stall reruns into one final polar (F5).

Rows from later experiment directories replace rows of earlier ones at the same angle. Replaced rows are not
dropped silently: they are listed in polar_superseded.csv. Status values are copied from each
case's results.json (set by assign_status), never edited here.
Usage (inside the image): python scripts/combine_polar.py OUT_DIR EXP_DIR [EXP_DIR ...]
"""

import sys
from pathlib import Path

from nacacfd.postprocess.plots import plot_polar
from nacacfd.postprocess.polars import collect_polar, write_polar_csv


def main(out_dir, *exp_dirs):
    final, superseded = {}, []
    for d in exp_dirs:
        for row in collect_polar(d):
            row["case"] = f"{Path(d).name}/{row['case']}"
            if row["alpha_deg"] in final:
                superseded.append(final[row["alpha_deg"]])
            final[row["alpha_deg"]] = row
    rows = [final[a] for a in sorted(final)]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_polar_csv(rows, out / "polar.csv")
    write_polar_csv(superseded, out / "polar_superseded.csv")
    plot_polar(rows, out_path=out / "polar.png")
    for r in rows:
        print(f"{r['alpha_deg']:5.1f} {r['case']:40s} CL={r['CL']:.6f} CD={r['CD']:.7f} {r['status']} {r['not_passed']}")
    print(f"superseded: {[r['case'] for r in superseded]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
