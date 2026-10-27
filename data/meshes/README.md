# External meshes

Meshes are not stored in git (too large). `scripts/fetch_meshes.sh` downloads them and checks sha256.

## su2_testcases/: NACA 0012 C-grids from the SU2 TestCases repository
- Source: https://github.com/su2code/TestCases, directory `rans/naca0012/`, commit `790c80ec5b543487b5f8ecf8bb0f0e4d2cc67f3f`
  (fetched 2026-10-27).
- Files: `n0012_225-65.su2` (14,336 quads, 14,576 points), `n0012_449-129.su2`. Markers: `airfoil`, `farfield`.
- Origin: the names and sizes match the NASA TMR NACA 0012 grid family (897x257 and its coarsenings), but the
  SU2 repository does not state the provenance in these files. Treat "TMR family" as **unverified** until checked
  against https://turbmodels.larc.nasa.gov/naca0012_grids.html.
- Role in this project: a "golden" mesh to test the solver setup separately from our own Gmsh meshing.
