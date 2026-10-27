# Failures and near-misses

Format: ID, date, what went wrong, how it was detected (gate / test / human / agent), fix, lesson.

## X-001 (2026-10-27): duplicated `git clone` instruction
- What: the agent put the same `git clone` step in two consecutive messages; the student ran both and got
  `fatal: destination path 'Projekt_OIwCH' already exists`.
- Detected by: the student's terminal output (screenshot).
- Impact: none (the first clone was fine), a few minutes of confusion.
- Fix: the agent explained the error and gave a check command instead of a new clone.
- Lesson: when repeating a step from an earlier message, make it idempotent or say it was already done.

## X-002 (2026-10-27): first image build failed on the proxy's TLS certificate
- What: `micromamba install` inside `docker build` failed with "SSL certificate problem: self-signed certificate
  in certificate chain" (6 s into the build). The agent's environment check had verified conda-forge access
  from the host, not from inside a container build, which does not trust the proxy CA.
- Detected by: the build itself (exit code 1).
- Fix: optional `--secret id=extra_ca` in the Dockerfile (D-009). Second build succeeded.
- Lesson: "reachable from the host" is not "reachable from inside the build"; test the real path.

## X-003 (2026-10-27): Dockerfile needed BuildKit, which the student's Docker did not have
- What: the F1 Dockerfile uses `RUN --mount=type=secret` (BuildKit). Ubuntu's `docker.io` package ships without
  buildx, so `docker build` on the student's laptop used the legacy builder and stopped at step 3/10:
  "the --mount option requires BuildKit".
- Detected by: the student's first build on the target machine (screenshot), ~25 min after the PR was merged.
- Root cause: the agent tested the build only in its own cloud container, where BuildKit was available,
  and declared the Dockerfile tested without testing it on the target environment.
- Fix: `sudo apt install -y docker-buildx` (confirmed working on the laptop the same evening); requirement added to docker/README.md, runbook and CLAUDE.md.
- Lesson: "tested" must name WHERE it was tested. F1 was tested in the agent's environment, not the target one.

## X-004 (2026-10-27): agent changed a validated solver option without checking it
- What: when deriving the template from the SU2 test case, the agent dropped `EXPERIMENTAL` from
  `SA_OPTIONS= NEGATIVE, EXPERIMENTAL` ("cannot explain it, so remove it"). SU2 aborted at start-up.
- Detected by: SU2 itself; the pipeline recorded exit code 1 and status `invalid` (physics_flags FAIL,
  other gates NOT_RUN). No result was reported. Evidence: runs/naca0012_a5_su2grid/_attempts/001_*.
- Fix: standard SA without options (D-010).
- Lesson: removing half of an option set is a change too; check it like any other.

## X-005 (2026-10-27): solver stop criterion inconsistent with the QA stabilisation window
- What: SU2 stopped at 768 iterations (residual criterion), the convergence gate judged CL over the last
  500 iterations, which still contained the transient -> FAIL (1.17e-4 > 1e-4).
- Detected by: the convergence gate (attempt 002). Fix: minimum iteration count (D-011), threshold unchanged.
- Note for the report: the gate did its job; the alternative "fix" of loosening the threshold to 2e-4 would
  have been a human checkpoint.

## X-006 (2026-10-27): y+ missing from the SU2 surface output
- What: the y+ gate had nothing to check because SU2's surface CSV lacked the Y_Plus column (attempts 002, 003).
- Detected by: the y+ gate returned NOT_RUN -> case status `incomplete` (not a silent pass).
- Fix: WRT_RESTART_COMPACT= NO (D-013).

## Finding F2-1 (2026-10-27, not an agent error): the 225x65 mesh fails the y+ gate
- max y+ = 3.105 at the leading edge (mean 1.18) > fail limit 2.0 -> status `invalid`.
  On the 449x129 mesh: max y+ = 1.089 (mean 0.50) -> pass with a note (above the target 1.0).
- CL/CD differ between the two meshes (CD 0.01102 vs 0.00941, about 15%), so grid dependence is large at this
  level; this is what F4 (GCI) must quantify. No result here is validated against experiment.

## X-007 (2026-10-27): commit with failing tests
- What: the F2b commit was made with 3 failing tests (the stub list still named functions that were now
  implemented). The agent chained `pytest; git commit` with `;` instead of `&&`.
- Detected by: the agent, reading the test output right after the commit. Not pushed.
- Fix: follow-up commit updating the stub list and adding mesh tests (80 pass in the image).
- Lesson: never chain a commit after tests with `;`.

## Finding F2-2 (2026-10-27): own mesh vs SU2 TestCases mesh at alpha = 5 deg
| Mesh | Elements | max y+ | CL | CD | Status |
|---|---|---|---|---|---|
| SU2 TestCases 449x129 (C-grid) | 57,344 quads | 1.09 | 0.56221 | 0.009413 | valid (per-case gates) |
| own Gmsh, medium, design y+ 0.5 | 37,674 (21,810 quads) | 1.10 | 0.55399 | 0.010320 | valid (per-case gates) |
- Difference: CL -1.5 %, CD +9.6 %. Possible causes, NOT yet separated: different geometry definition
  (standard closed trailing edge vs the TMR-modified section the SU2 grids appear to use), far-field distance
  (100 chords vs unknown for the SU2 grid), resolution and mesh type. Both cases pass all per-case gates, which
  shows that per-case gates alone do not establish an accurate answer: GCI (F4) and validation (F5) are needed.

## X-008 (2026-10-27): F4 code commit made while the in-image tests did not run
- What: the Docker daemon had stopped; the test command was piped into `tail`, so the pipeline exit code
  was the one from `tail` (0) and the commit went ahead although pytest never ran.
- Detected by: the agent, noticing the output contained a Docker connection error instead of a pytest summary.
- Fix: restarted dockerd and ran the tests in the image afterwards (87 passed); no code change was needed.
- Lesson: same family as X-007. Use `set -o pipefail` (or no pipe) before a commit gated on tests.

## Finding F4-1 (2026-10-27): grid study on own Gmsh meshes, NACA 0012, M 0.15, Re 6e6, SA
Three levels, sizes scaled by sqrt(2) per level (effective ratios from cell counts: r21 = 1.414, r32 = 1.408).
| alpha | Level | Cells | max y+ | CL | CD | Per-case status |
|---|---|---|---|---|---|---|
| 5 | fine | 75,326 | 0.78 | 0.556044 | 0.0097822 | gates passed |
| 5 | medium | 37,674 | 1.10 | 0.553987 | 0.0103197 | gates passed |
| 5 | coarse | 19,014 | 1.55 | 0.552014 | 0.0116206 | gates passed |
| 10 | fine | 75,326 | 1.12 | 1.087710 | 0.013919 | gates passed |
| 10 | medium | 37,674 | 1.58 | 1.081225 | 0.015371 | gates passed |
| 10 | coarse | 19,014 | 2.22 | 1.072695 | 0.018507 | invalid (wall_yplus, max at the leading edge, suction side) |
- alpha 5, CD: monotonic (R = 0.41), observed order p = 2.61, GCI_fine = 4.67 % (limit 5 %) -> would pass.
- alpha 5, CL: R = e21/e32 = 1.04, i.e. the change does not shrink with refinement -> "divergent", no GCI can be
  computed -> GCI gate FAIL -> all three alpha 5 cases `invalid`. The CL change per level is small (~0.37 %),
  but the method cannot bound the error when the sequence is not converging.
- alpha 10: GCI gate NOT_RUN because the coarse case failed y+ -> fine and medium `incomplete`.
- Observation only (not validation): the extrapolated CD at alpha 5 (0.009417) is close to the CD on the
  SU2 TestCases 449x129 grid (0.009413, F2-2). This does not show either number is correct.
- Not done: the cause of the non-converging CL is unknown. Candidates (none tested): the far-field
  distance is not refined (fixed 100 chords, so a far-field error does not shrink); the hybrid mesh is not a
  geometrically similar refinement; the levels are still outside the asymptotic range.
