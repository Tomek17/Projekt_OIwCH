"""2D mesh generation with Gmsh (boundary-layer mesh around the airfoil, far field).

Status: STUB (not implemented). Every function raises NotImplementedError.
"""

from __future__ import annotations


def first_cell_height(reynolds: float, target_yplus: float, chord: float = 1.0):
    """Estimate the first wall-cell height for a target y+ from a flat-plate skin-friction correlation (cite the correlation used). TODO F2."""
    raise NotImplementedError("TODO: first_cell_height")


def build_mesh(coords, level: str, out_dir, options: dict):
    """Build a C-grid or hybrid mesh with Gmsh and write it in SU2 format. Return the mesh path. TODO F2."""
    raise NotImplementedError("TODO: build_mesh")


def mesh_statistics(mesh_path):
    """Return element count and quality metrics (e.g. Gmsh SICN/gamma) as a dict. TODO F3."""
    raise NotImplementedError("TODO: mesh_statistics")

