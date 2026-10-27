import math

import pytest

from nacacfd.airfoil.naca import naca4_coordinates, parse_naca4


def test_parse():
    assert parse_naca4("NACA2412") == (0.02, 0.4, 0.12)
    with pytest.raises(ValueError):
        parse_naca4("NACA23012")


def test_naca0012_symmetric_and_thickness():
    up, lo = naca4_coordinates("NACA0012", 401, closed_te=True)
    assert up[0] == (0.0, 0.0) and lo[0] == (0.0, 0.0)
    assert all(abs(u[1] + l[1]) < 1e-15 for u, l in zip(up, lo))
    t_max = max(u[1] - l[1] for u, l in zip(up, lo))
    assert abs(t_max - 0.12) < 2e-4  # max thickness = 12 % chord (at ~30 % chord)


def test_trailing_edge_closed_vs_open():
    up_c, lo_c = naca4_coordinates("NACA0012", 101, closed_te=True)
    up_o, lo_o = naca4_coordinates("NACA0012", 101, closed_te=False)
    assert abs(up_c[-1][1]) < 1e-12
    assert up_o[-1][1] > 1e-3  # original definition leaves a finite trailing-edge thickness


def test_cambered_airfoil_has_camber():
    up, lo = naca4_coordinates("NACA2412", 201)
    mid = [0.5 * (u[1] + l[1]) for u, l in zip(up, lo)]
    assert max(mid) == pytest.approx(0.02, abs=1e-3)
    assert all(math.isfinite(v) for v in mid)
