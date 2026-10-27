"""Comparison of CFD results with reference data.

Status: STUB (not implemented). Every function raises NotImplementedError.
"""

from __future__ import annotations


def load_reference(source_dir):
    """Load a reference dataset together with its SOURCE.md metadata; refuse to load data without a source. TODO F5."""
    raise NotImplementedError("TODO: load_reference")


def deviations(polar, reference):
    """Return per-alpha differences CFD - reference at matching angles (no extrapolation). TODO F5."""
    raise NotImplementedError("TODO: deviations")

