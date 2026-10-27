#!/usr/bin/env bash
# Download external meshes into data/meshes/ and verify their sha256. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=790c80ec5b543487b5f8ecf8bb0f0e4d2cc67f3f
BASE="https://raw.githubusercontent.com/su2code/TestCases/${COMMIT}/rans/naca0012"
DEST=data/meshes/su2_testcases
mkdir -p "$DEST"
while read -r sha name; do
  if [ ! -f "$DEST/$name" ]; then
    echo "downloading $name"
    curl -fsSL "$BASE/$name" -o "$DEST/$name.part" && mv "$DEST/$name.part" "$DEST/$name"
  fi
  echo "$sha  $DEST/$name" | sha256sum -c -
done <<'LIST'
20dfc96875b1d1a8377c2e64248b6ee42a1ecf525c50d822fb5f539d06d68d15 n0012_225-65.su2
2e7d2feeb9832d3d16ed6867a3dc16d9e1ec045cf3d4a89ebfb506bcac9571d2 n0012_449-129.su2
LIST
