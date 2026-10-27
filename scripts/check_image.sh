#!/usr/bin/env bash
# Smoke check of the Docker image: tool versions + unit tests inside the container.
# Usage (from the repo root): scripts/check_image.sh [image]   (default image: nacacfd)
# It does NOT run any CFD case.
set -euo pipefail
IMAGE="${1:-nacacfd}"
docker run --rm -v "$PWD":/work -w /work "$IMAGE" bash -c '
  set -e
  echo "== SU2";    SU2_CFD --help | head -1
  echo "== Gmsh";   gmsh --version
  echo "== Gmsh Python API"; python -c "import gmsh; print(gmsh.__version__)"
  echo "== MPI";    mpirun --version | head -1
  echo "== Python"; python --version
  echo "== nacacfd"; nacacfd --version
  echo "== pytest"; python -m pytest -q -p no:cacheprovider
'
