"""Gate: grid independence, GCI with Richardson extrapolation (Celik et al. 2008; citation to verify).

Status: STUB (not implemented). Every function raises NotImplementedError.
"""

from __future__ import annotations


def compute_gci(h: list, phi: list, safety_factor: float):
    """Return observed order, extrapolated value and GCI_fine; report non-monotonic convergence instead of forcing a number. TODO F4."""
    raise NotImplementedError("TODO: compute_gci")


def check_gci(study_dir, thresholds: dict):
    """Return GateResult for a 3-level mesh study. TODO F4."""
    raise NotImplementedError("TODO: check_gci")

