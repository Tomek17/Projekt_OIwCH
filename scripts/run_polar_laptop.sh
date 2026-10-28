#!/usr/bin/env bash
# Run the polar on the student's laptop in the background and build polar.csv/polar.png at the end.
# Usage (repo root, WSL): scripts/run_polar_laptop.sh   then follow progress with: tail -f runs/polar_laptop.log
# Safe to start again after an interruption: finished angles are skipped (--resume), unfinished ones rerun.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG=runs/polar_laptop.log
[ -f "$LOG" ] && mv "$LOG" "runs/polar_laptop.$(date -u +%Y%m%dT%H%M%SZ).log"
nohup bash -c "
  date -u +'start %FT%TZ'
  scripts/run_experiment.sh experiments/naca0012_polar.yaml nacacfd --resume || echo 'run exit code' \$?
  docker run --rm --user \$(id -u):\$(id -g) -v \"\$PWD\":/work -w /work nacacfd nacacfd report runs/naca0012_polar
  date -u +'end %FT%TZ'
" > "$LOG" 2>&1 &
echo "started in the background (pid $!); progress: tail -f $LOG"
