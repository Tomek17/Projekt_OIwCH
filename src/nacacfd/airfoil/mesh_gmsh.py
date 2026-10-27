"""2D hybrid mesh with Gmsh: quad boundary layer around the airfoil, triangles outside, circular far field.

Status: implemented (F2b), tested for NACA 0012 with a closed trailing edge.
Design: hybrid rather than a structured C-grid, because the Gmsh BoundaryLayer field handles the sharp
trailing edge (fan) automatically and the code stays short. Consequence for F4: refinement is controlled by
scaling all sizes together (LEVELS), not by an exact structured refinement ratio; the GCI uses the
representative cell size h = (1/N)^(1/2) computed from the actual cell counts.
"""

from __future__ import annotations

import math
from pathlib import Path

# Mesh level -> scale factor s applied to ALL sizes (surface spacing, first cell, boundary-layer growth,
# wake and far-field cell size), so the levels are systematically refined (needed for GCI, F4).
# Refinement ratio between neighbouring levels: sqrt(2) in each direction, ~2 in cell count.
# "medium" (s = 1) is the reference level used in F2.
LEVELS = {"coarse": 2 ** 0.5, "medium": 1.0, "fine": 2 ** -0.5}

MESH_DEFAULTS = {
    "target_yplus": 1.0,
    "farfield_radius_chords": 100.0,
    "n_surface_points": 200,      # per side (upper/lower), at level "medium"
    "bl_growth_ratio": 1.15,
    "bl_thickness_chords": 0.03,
    "farfield_size_chords": 10.0,
    "le_te_bump": 0.2,            # Gmsh 'Bump' coefficient: < 1 clusters points at both ends of each side
    "wake_size_chords": 0.05,     # cell size along the wake line behind the trailing edge
    "wake_length_chords": 10.0,
}


def first_cell_height(reynolds: float, target_yplus: float, chord: float = 1.0) -> float:
    """First wall-cell height for a target y+ from the 1/7-power-law flat-plate skin friction
    Cf = 0.026 Re^(-1/7) (commonly attributed to White, Fluid Mechanics; citation to verify).

    y = y+ * nu / u_tau with u_tau = U sqrt(Cf / 2), in chord units: y / c = y+ / (Re sqrt(Cf / 2)).
    This is an a-priori estimate only; the y+ gate checks the real value from the solution.
    """
    cf = 0.026 * reynolds ** (-1.0 / 7.0)
    return target_yplus * chord / (reynolds * math.sqrt(cf / 2.0))


def mesh_options(mesh: dict, level: str, reynolds: float) -> dict:
    opts = dict(MESH_DEFAULTS)
    opts.update({k: v for k, v in mesh.items() if k not in ("source",) and v is not None})
    s = LEVELS[level]
    opts["level_scale"] = s
    opts["n_surface_points_eff"] = int(round(opts["n_surface_points"] / s))
    opts["first_cell_height"] = first_cell_height(reynolds, opts["target_yplus"]) * s
    # Geometric growth r per layer -> r**s keeps the boundary layer thickness with ~1/s times the layers.
    opts["bl_growth_ratio_eff"] = opts["bl_growth_ratio"] ** s
    opts["farfield_size_eff"] = opts["farfield_size_chords"] * s
    opts["wake_size_eff"] = opts["wake_size_chords"] * s
    return opts


def build_mesh(upper, lower, level: str, out_dir, options: dict) -> Path:
    """Build the mesh with Gmsh and write <out_dir>/mesh.su2 with markers 'airfoil' and 'farfield'.

    upper/lower: lists of (x, y) from the leading edge to a closed trailing edge (shared end points).
    `options` must come from mesh_options(). Returns the mesh path.
    """
    import gmsh  # noqa: PLC0415 (only available in the image)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    o = options
    if math.dist(upper[-1], lower[-1]) > 1e-12:
        raise ValueError("build_mesh needs a closed trailing edge (use closed_te=True)")

    gmsh.initialize(["-nt", "1"])
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("airfoil")
        geo = gmsh.model.geo
        le = geo.addPoint(*upper[0], 0)
        te = geo.addPoint(*upper[-1], 0)
        up_pts = [le] + [geo.addPoint(x, y, 0) for x, y in upper[1:-1]] + [te]
        lo_pts = [le] + [geo.addPoint(x, y, 0) for x, y in lower[1:-1]] + [te]
        c_up = geo.addSpline(up_pts)
        c_lo = geo.addSpline(lo_pts)

        R = o["farfield_radius_chords"]
        center = geo.addPoint(0.5, 0, 0)
        f_pts = [geo.addPoint(0.5 + R * math.cos(a), R * math.sin(a), 0, o["farfield_size_eff"])
                 for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
        arcs = [geo.addCircleArc(f_pts[i], center, f_pts[(i + 1) % 4]) for i in range(4)]
        outer = geo.addCurveLoop(arcs)
        inner = geo.addCurveLoop([c_up, -c_lo])
        surf = geo.addPlaneSurface([outer, inner])

        n = o["n_surface_points_eff"]
        for c in (c_up, c_lo):
            geo.mesh.setTransfiniteCurve(c, n, "Bump", o["le_te_bump"])
        geo.synchronize()

        gmsh.model.addPhysicalGroup(1, [c_up, c_lo], name="airfoil")
        gmsh.model.addPhysicalGroup(1, arcs, name="farfield")
        gmsh.model.addPhysicalGroup(2, [surf], name="fluid")

        field = gmsh.model.mesh.field
        bl = field.add("BoundaryLayer")
        field.setNumbers(bl, "CurvesList", [c_up, c_lo])
        field.setNumber(bl, "Size", o["first_cell_height"])
        field.setNumber(bl, "Ratio", o["bl_growth_ratio_eff"])
        field.setNumber(bl, "Thickness", o["bl_thickness_chords"])
        field.setNumber(bl, "Quads", 1)
        field.setNumbers(bl, "FanPointsList", [te])
        field.setAsBoundaryLayer(bl)

        # Background size: fine near the airfoil and along the wake, growing towards the far field.
        surf_size = 1.0 / n
        d_af = field.add("Distance")
        field.setNumbers(d_af, "CurvesList", [c_up, c_lo])
        field.setNumber(d_af, "Sampling", 400)
        t_af = field.add("Threshold")
        field.setNumber(t_af, "InField", d_af)
        field.setNumber(t_af, "SizeMin", 2 * surf_size)
        field.setNumber(t_af, "SizeMax", o["farfield_size_eff"])
        field.setNumber(t_af, "DistMin", o["bl_thickness_chords"])
        field.setNumber(t_af, "DistMax", R)
        wake_end = geo.addPoint(1.0 + o["wake_length_chords"], 0, 0)
        wake = geo.addLine(te, wake_end)
        geo.synchronize()
        d_w = field.add("Distance")
        field.setNumbers(d_w, "CurvesList", [wake])
        field.setNumber(d_w, "Sampling", 400)
        t_w = field.add("Threshold")
        field.setNumber(t_w, "InField", d_w)
        field.setNumber(t_w, "SizeMin", o["wake_size_eff"])
        field.setNumber(t_w, "SizeMax", o["farfield_size_eff"])
        field.setNumber(t_w, "DistMin", 0.05)
        field.setNumber(t_w, "DistMax", 5.0)
        mn = field.add("Min")
        field.setNumbers(mn, "FieldsList", [t_af, t_w])
        field.setAsBackgroundMesh(mn)
        for opt in ("Mesh.MeshSizeExtendFromBoundary", "Mesh.MeshSizeFromPoints", "Mesh.MeshSizeFromCurvature"):
            gmsh.option.setNumber(opt, 0)
        gmsh.option.setNumber("Mesh.Algorithm", 6)  # Frontal-Delaunay for the triangles

        gmsh.model.mesh.generate(2)
        path = out_dir / "mesh.su2"
        gmsh.write(str(path))
        return path
    finally:
        gmsh.finalize()


def mesh_statistics(mesh_path) -> dict:
    """Element counts by type from an SU2 mesh file (2D: 5 = triangle, 9 = quadrilateral)."""
    counts: dict[str, int] = {}
    names = {"5": "triangles", "9": "quads"}
    lines = Path(mesh_path).read_text().splitlines()
    i = next(k for k, line in enumerate(lines) if line.startswith("NELEM="))
    nelem = int(lines[i].split("=")[1])
    for line in lines[i + 1:i + 1 + nelem]:
        t = names.get(line.split()[0], line.split()[0])
        counts[t] = counts.get(t, 0) + 1
    npoin = next(int(line.split("=")[1].split()[0]) for line in lines if line.startswith("NPOIN="))
    return {"elements": nelem, "points": npoin, **counts}
