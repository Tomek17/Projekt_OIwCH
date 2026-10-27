import pytest

from nacacfd.airfoil.mesh_gmsh import first_cell_height, mesh_options, mesh_statistics
from nacacfd.airfoil.naca import naca4_coordinates


def test_first_cell_height_scaling():
    h = first_cell_height(6e6, 1.0)
    assert 1e-6 < h < 1e-5
    assert first_cell_height(6e6, 2.0) == pytest.approx(2 * h)
    assert first_cell_height(1e6, 1.0) > h  # lower Re -> thicker first cell


def test_levels_refine():
    c, m, f, x = (mesh_options({}, lvl, 6e6) for lvl in ("coarse", "medium", "fine", "xfine"))
    assert c["n_surface_points_eff"] < m["n_surface_points_eff"] < f["n_surface_points_eff"] < x["n_surface_points_eff"]
    assert x["first_cell_height"] < f["first_cell_height"] < m["first_cell_height"] < c["first_cell_height"]
    assert x["bl_growth_ratio_eff"] < f["bl_growth_ratio_eff"] < m["bl_growth_ratio_eff"] < c["bl_growth_ratio_eff"]


def test_mesh_statistics(tmp_path):
    p = tmp_path / "m.su2"
    p.write_text("NDIME= 2\nNELEM= 3\n5 0 1 2 0\n9 0 1 3 2 1\n9 1 4 5 3 2\nNPOIN= 6\n")
    assert mesh_statistics(p) == {"elements": 3, "points": 6, "triangles": 1, "quads": 2}


def test_build_mesh_in_image(tmp_path):
    gmsh = pytest.importorskip("gmsh")  # only inside the Docker image
    from nacacfd.airfoil.mesh_gmsh import build_mesh

    up, lo = naca4_coordinates("NACA0012", 81, closed_te=True)
    opts = mesh_options({"n_surface_points": 40, "bl_thickness_chords": 0.01}, "medium", 6e6)
    stats = mesh_statistics(build_mesh(up, lo, "medium", tmp_path, opts))
    assert stats["quads"] > 0 and stats["triangles"] > 0
    text = (tmp_path / "mesh.su2").read_text()
    assert "MARKER_TAG= airfoil" in text and "MARKER_TAG= farfield" in text
    assert gmsh is not None


def test_open_trailing_edge_rejected_by_mesher(tmp_path):
    pytest.importorskip("gmsh")
    from nacacfd.airfoil.mesh_gmsh import build_mesh

    up, lo = naca4_coordinates("NACA0012", 41, closed_te=False)
    with pytest.raises(ValueError):
        build_mesh(up, lo, "medium", tmp_path, mesh_options({}, "medium", 6e6))
