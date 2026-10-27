"""NACA 4-digit airfoil coordinates.

Status: 4-digit implemented (F2b). 5-digit: stub (F6).

Formula: the standard NACA 4-digit thickness and camber lines (Abbott & von Doenhoff, "Theory of Wing
Sections", 1959). Thickness:
    y_t = 5 t (0.2969 sqrt(x) - 0.1260 x - 0.3516 x^2 + 0.2843 x^3 + a4 x^4),
with a4 = -0.1015 (original, small finite trailing-edge thickness) or a4 = -0.1036 (closed trailing edge,
a widely used modification). The NASA TMR NACA 0012 case uses its own modified definition that is
NOT implemented here (source not accessible from the agent's environment; see data/reference/README.md).
"""

from __future__ import annotations

import math
import re

A4_OPEN = -0.1015
A4_CLOSED = -0.1036


def parse_naca4(code: str) -> tuple[float, float, float]:
    """'NACA2412' -> (m=0.02, p=0.4, t=0.12)."""
    m = re.fullmatch(r"(?:NACA)?(\d)(\d)(\d\d)", code.upper().replace(" ", ""))
    if not m:
        raise ValueError(f"not a NACA 4-digit code: {code!r}")
    return int(m.group(1)) / 100, int(m.group(2)) / 10, int(m.group(3)) / 100


def cosine_spacing(n: int) -> list[float]:
    """n x-stations from 0 to 1, clustered at both ends."""
    return [0.5 * (1 - math.cos(math.pi * i / (n - 1))) for i in range(n)]


def naca4_coordinates(code: str, n_points: int, closed_te: bool = False):
    """Return (upper, lower): lists of (x, y) from leading edge (0, 0) to trailing edge, chord 1.

    Both lists share the leading-edge point. With closed_te=True both end at (1, y_camber(1)) = (1, 0).
    """
    m, p, t = parse_naca4(code)
    a4 = A4_CLOSED if closed_te else A4_OPEN
    upper, lower = [], []
    for x in cosine_spacing(n_points):
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 + a4 * x**4)
        if m == 0 or p == 0:
            yc, dyc = 0.0, 0.0
        elif x < p:
            yc, dyc = m / p**2 * (2 * p * x - x**2), 2 * m / p**2 * (p - x)
        else:
            yc = m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2)
            dyc = 2 * m / (1 - p) ** 2 * (p - x)
        th = math.atan(dyc)
        upper.append((x - yt * math.sin(th), yc + yt * math.cos(th)))
        lower.append((x + yt * math.sin(th), yc - yt * math.cos(th)))
    return upper, lower


def naca5_coordinates(code: str, n_points: int, closed_te: bool = False):
    """Return (x, y) arrays for a 5-digit NACA airfoil. TODO F6."""
    raise NotImplementedError("TODO: naca5_coordinates")
