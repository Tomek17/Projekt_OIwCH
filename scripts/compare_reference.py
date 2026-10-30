"""Compare a computed polar with TMR experimental data files (Tecplot-style .dat with zones), F5.

Reads only; the reference files are never modified. Reports differences, does NOT set any status:
the validation tolerances are undefined in config/qa_thresholds.yaml until the student sets them.
Usage: python scripts/compare_reference.py POLAR_CSV CLCD_LADSON_DAT [CL_GREGORY_DAT] OUT_DIR
"""

import csv
import json
import sys
from pathlib import Path


def read_zones(path):
    """Return {zone title: [[floats], ...]} from a TMR .dat file (lines starting with # are comments)."""
    zones, cur = {}, None
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
    """Linear interpolation on a monotonic x range; None outside it (no extrapolation)."""
    pts = sorted(zip(xs, ys))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def pre_stall(rows):
    """Rows up to (and including) the CL maximum, so interpolation never crosses the stall drop."""
    i = max(range(len(rows)), key=lambda k: rows[k][1])
    return rows[: i + 1]


def main(polar_csv, clcd_dat, *rest):
    out = Path(rest[-1]); out.mkdir(parents=True, exist_ok=True)
    gregory = read_zones(rest[0]) if len(rest) > 1 else {}
    polar = [r for r in csv.DictReader(open(polar_csv))]
    ladson = read_zones(clcd_dat)
    table = []
    for r in polar:
        a, cl, cd = float(r["alpha_deg"]), float(r["CL"]), float(r["CD"])
        row = {"alpha_deg": a, "CL": cl, "CD": cd, "status": r["status"]}
        for name, z in ladson.items():
            ps = pre_stall(z)
            cl_ref = interp([p[0] for p in ps], [p[1] for p in ps], a)
            cd_ref = interp([p[1] for p in ps], [p[2] for p in ps], cl)  # drag compared at equal CL
            row[f"CL_ladson_{name}"] = cl_ref
            row[f"dCL_{name}"] = None if cl_ref is None else cl - cl_ref
            row[f"CD_at_CL_ladson_{name}"] = cd_ref
            row[f"dCD_counts_{name}"] = None if cd_ref is None else (cd - cd_ref) * 1e4
        table.append(row)
    (out / "comparison.json").write_text(json.dumps({"polar": str(polar_csv), "reference": str(clcd_dat),
                                                     "rows": table}, indent=1))
    names = list(ladson)
    print("alpha  CL_su2   " + "  ".join(f"dCL[{n}]" for n in names) + "   " + "  ".join(f"dCD[{n}] cnt" for n in names))
    for t in table:
        f = lambda v, fmt: "   n/a  " if v is None else format(v, fmt)
        print(f"{t['alpha_deg']:5.1f} {t['CL']:.4f}  " + "  ".join(f(t[f'dCL_{n}'], '+.4f') for n in names)
              + "   " + "  ".join(f(t[f'dCD_counts_{n}'], '+7.1f') for n in names) + f"  {t['status']}")

    import matplotlib  # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8))
    ok = [t for t in table if t["status"] == "valid"]
    bad = [t for t in table if t["status"] != "valid"]
    for i, (n, z) in enumerate(ladson.items()):
        mk = "sv^"[i % 3]
        a1.plot([p[0] for p in z], [p[1] for p in z], mk, ms=5, mfc="none", color="0.35", label=f"Ladson {n}")
        a2.plot([p[2] for p in z], [p[1] for p in z], mk, ms=5, mfc="none", color="0.35", label=f"Ladson {n}")
    for n, z in gregory.items():
        a1.plot([p[0] for p in z], [p[1] for p in z], "x", color="0.6", label="Gregory (digitized)")
    for rows, kw, lab in ((ok, dict(marker="o", ls="-"), "SU2 SA, valid"),
                          (bad, dict(marker="o", ls="none", mfc="white"), "SU2 SA, not valid")):
        a1.plot([t["alpha_deg"] for t in rows], [t["CL"] for t in rows], color="C0", label=lab, **kw)
        a2.plot([t["CD"] for t in rows], [t["CL"] for t in rows], color="C0", label=lab, **kw)
    a1.set(xlabel="alpha [deg]", ylabel="CL", title="CL(alpha), NACA 0012, M 0.15, Re 6e6")
    a2.set(xlabel="CD", ylabel="CL", title="CL(CD)", xlim=(0.0, 0.045))
    for ax in (a1, a2):
        ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "polar_vs_experiment.png", dpi=130)


if __name__ == "__main__":
    main(*sys.argv[1:])
