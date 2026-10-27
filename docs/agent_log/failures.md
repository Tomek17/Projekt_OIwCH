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
