"""Provenance metadata for each case.

Status: implemented (F2). Git and image information come from environment variables set by
scripts/run_experiment.sh on the host, because the image has no git and cannot see its own image ID.
Missing values are recorded as "unknown", never guessed.
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone

UNKNOWN = "unknown"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def collect_metadata(case_dir, **extra) -> dict:
    """Return git commit, dirty flag, image ID, versions, host, cores, plus anything passed in `extra`."""
    try:
        import gmsh  # noqa: PLC0415

        gmsh_version = gmsh.__version__
    except Exception:  # gmsh is optional outside the image
        gmsh_version = UNKNOWN
    from nacacfd import __version__

    meta = {
        "git_commit": os.environ.get("NACACFD_GIT_COMMIT", UNKNOWN),
        "git_dirty": os.environ.get("NACACFD_GIT_DIRTY", UNKNOWN),
        "image_id": os.environ.get("NACACFD_IMAGE_ID", UNKNOWN),
        "host": os.environ.get("NACACFD_HOST", platform.node()),
        "cpu_count_visible": os.cpu_count(),
        "python": sys.version.split()[0],
        "gmsh": gmsh_version,
        "nacacfd": __version__,
        "case_dir": str(case_dir),
    }
    meta.update(extra)
    return meta
