"""NACA 4- and 5-digit airfoil coordinates.

Note: the NASA TMR NACA 0012 case uses a modified definition with a closed trailing edge.
Read the exact definition from the TMR source before implementing it; implement both variants with tests.

Status: STUB (not implemented). Every function raises NotImplementedError.
"""

from __future__ import annotations


def naca4_coordinates(code: str, n_points: int, closed_te: bool = False):
    """Return (x, y) arrays for a 4-digit NACA airfoil, chord 1, cosine spacing. TODO F2."""
    raise NotImplementedError("TODO: naca4_coordinates")


def naca5_coordinates(code: str, n_points: int, closed_te: bool = False):
    """Return (x, y) arrays for a 5-digit NACA airfoil. TODO F6."""
    raise NotImplementedError("TODO: naca5_coordinates")

