#!/usr/bin/env bash
# One command to run an experiment inside the Docker image, with provenance passed in from the host.
# Usage (repo root): scripts/run_experiment.sh experiments/<name>.yaml [image]
set -euo pipefail
EXP="$1"; IMAGE="${2:-nacacfd}"
cd "$(dirname "$0")/.."
COMMIT=$(git rev-parse HEAD 2>/dev/null || echo unknown)
if [ "$COMMIT" = unknown ]; then DIRTY=unknown
elif [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]; then DIRTY=true; else DIRTY=false; fi
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work -w /work \
  -e NACACFD_GIT_COMMIT="$COMMIT" -e NACACFD_GIT_DIRTY="$DIRTY" \
  -e NACACFD_IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$IMAGE")" \
  -e NACACFD_HOST="$(hostname)" \
  "$IMAGE" nacacfd run "$EXP"
