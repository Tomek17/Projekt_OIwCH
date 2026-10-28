"""Figures for the report.

Status: plot_polar implemented (F5 prep). Valid points are filled, every other status is drawn hollow and
labelled with its status; nothing is dropped. Reference data is drawn only if a loaded reference is passed
(none exists yet: data must come from the student, see interventions I-001).
"""

from __future__ import annotations


def plot_polar(polar, reference=None, out_path=None):
    """Plot CL(alpha), CD(alpha), CL(CD) from collect_polar() rows. `reference`: dict with optional lists
    'alpha_cl' [(alpha, CL)], 'cl_cd' [(CD, CL)] and a 'label'. Returns the matplotlib figure."""
    import matplotlib  # noqa: PLC0415 (only in the image)

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(15, 4.5))
    ok = [r for r in polar if r["status"] == "valid"]
    bad = [r for r in polar if r["status"] != "valid"]
    for rows, style, label in ((ok, dict(marker="o", ls="-"), "SU2 SA, valid"),
                               (bad, dict(marker="o", ls="none", mfc="none"), "SU2 SA, not valid")):
        if not rows:
            continue
        a = [r["alpha_deg"] for r in rows]
        a1.plot(a, [r["CL"] for r in rows], color="C0", label=label, **style)
        a2.plot(a, [r["CD"] for r in rows], color="C0", label=label, **style)
        a3.plot([r["CD"] for r in rows], [r["CL"] for r in rows], color="C0", label=label, **style)
    for r in bad:
        a1.annotate(r["status"], (r["alpha_deg"], r["CL"]), fontsize=7, xytext=(3, -10), textcoords="offset points")
    if reference:
        lab = reference.get("label", "reference")
        if reference.get("alpha_cl"):
            a1.plot(*zip(*reference["alpha_cl"]), "s", color="C3", ms=4, label=lab)
        if reference.get("cl_cd"):
            a3.plot(*zip(*reference["cl_cd"]), "s", color="C3", ms=4, label=lab)
    a1.set(xlabel="alpha [deg]", ylabel="CL", title="CL(alpha)")
    a2.set(xlabel="alpha [deg]", ylabel="CD", title="CD(alpha)")
    a3.set(xlabel="CD", ylabel="CL", title="CL(CD)")
    for ax in (a1, a2, a3):
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=130)
    return fig
