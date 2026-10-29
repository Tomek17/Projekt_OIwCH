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

## X-009 (2026-10-27): far-field sensitivity test was confounded by the agent's own mesh code
- What: the triangle size field used `DistMax = farfield radius`, so changing the radius also changed the
  mesh near the airfoil (triangles 6,200 / 15,864 / 48,104 for R = 50 / 100 / 200; quads identical).
  The first R = 50 / 200 runs mixed far-field and resolution effects (CD 0.01127 vs 0.01008, looked like a
  large far-field effect).
- Detected by: the agent, comparing element counts before interpreting CL/CD. No gate can catch this:
  every case passed all per-case gates.
- Fix: new mesh parameter `size_growth_distance_chords` (default 100, R = 100 meshes unchanged, D-019).
  Confounded runs kept in `runs/naca0012_farfield_r*/_attempts/001_confounded/` and rerun.
- Lesson: in a sensitivity study, check that only the intended input changed (cell counts per region).

## X-010 (2026-10-27): grid-study bookkeeping errors found in the first 4-level run
- (a) A level outside the three GCI levels (coarse) inherited the GCI PASS and was marked `valid`, although
  the GCI says nothing about it. Fix: such levels get gci NOT_RUN -> `incomplete` (D-018).
- (b) The exit code of `nacacfd run` used the per-case status before the GCI (always `incomplete`), so it
  was 1 even when everything ended `valid`. Fix: the final statuses decide the exit code.
- Detected by: the agent, reading the run log. Both fixed before reporting.

## Finding F4b-1 (2026-10-27): 4-level grid study, alpha 5 (student's choice: diagnose before changing method)
| Level | Cells | max y+ | Iterations | Wall | CL | CD |
|---|---|---|---|---|---|---|
| xfine | 150,640 | 0.55 | 1262 | 501 s | 0.556920 | 0.0095234 |
| fine | 75,328 | 0.78 | 1054 | 174 s | 0.556044 | 0.0097822 |
| medium | 37,674 | 1.10 | 1001 | 78 s | 0.553987 | 0.0103197 |
| coarse | 19,014 | 1.55 | 1001 | 38 s | 0.552012 | 0.0116206 |
- GCI on xfine/fine/medium: CL monotonic (R = 0.43), p = 2.46, GCI_fine = 0.15 %; CD monotonic (R = 0.48),
  p = 2.11, GCI_fine = 3.15 %. Gate PASS -> xfine, fine, medium `valid`; coarse `incomplete` (outside the triplet).
- Interpretation (agent's reading, not proven): the coarse level was outside the asymptotic range for CL;
  with it dropped the sequence converges with p close to the formal 2nd order.
- "valid" means per-case gates + GCI passed. Nothing is validated against experiment yet (F5).
- Side observation: the fine mesh had 75,328 cells here vs 75,326 in naca0012_gci with the same inputs, and
  CL differed by 2e-7. Gmsh meshing is not bit-for-bit reproducible across runs in this setup (cause unknown).

## Finding F4b-2 (2026-10-27): far-field radius, medium mesh, alpha 5 (after the X-009 fix)
| R [chords] | Elements | CL | CD |
|---|---|---|---|
| 50 | 36,502 | 0.553701 | 0.0104331 |
| 100 | 37,674 | 0.553987 | 0.0103197 |
| 200 | 39,832 | 0.554640 | 0.0102809 |
- 100 -> 200 chords: CL +0.12 %, CD -0.37 %. Smaller than the discretisation error of CD (GCI 3.15 %), of the
  same order as the CL GCI (0.15 %). The far field is not the cause of the divergent CL in F4-1 (a fixed
  far-field error is a constant offset and cancels in the level-to-level differences anyway).
- Not done: R = 400; no point-vortex far-field correction. Default stays 100 chords.

## Finding F4c-1 (2026-10-27): 4-level grid study, alpha 10
| Level | Cells | max y+ | Iterations | Wall | CL | CD | Status |
|---|---|---|---|---|---|---|---|
| xfine | 150,640 | 0.79 | 1577 | 625 s | 1.089153 | 0.0132699 | valid |
| fine | 75,326 | 1.12 | 1313 | 213 s | 1.087720 | 0.0139194 | valid |
| medium | 37,674 | 1.58 | 1077 | 84 s | 1.081218 | 0.0153705 | valid |
| coarse | 19,014 | 2.22 | 1001 | 41 s | 1.072692 | 0.0185069 | invalid (y+ > 2.0) |
- GCI on xfine/fine/medium: PASS. CL monotonic (R = 0.22), p = 4.37, GCI_fine = 0.05 %;
  CD monotonic (R = 0.45), p = 2.32, GCI_fine = 4.95 % (limit 5 %).
- Caveats the gate does not express:
  - CD passes with a margin of 0.05 percentage points. Same inputs, a slightly different mesh (the
    Gmsh non-determinism seen in F4b-1) could flip it.
  - CL: p = 4.37 is well above the formal 2nd order of the scheme. An observed order far above the formal one
    usually means the sequence is not cleanly asymptotic, so the 0.05 % is probably optimistic.
    The gate has no check on p versus the formal order (possible F3 hardening item, needs the student's decision
    because it would add a criterion).
- CD error grows with alpha: GCI 3.15 % at alpha 5 vs 4.95 % at alpha 10 on the same meshes. Higher angles
  (towards stall) will likely need the xfine level as the medium of a finer triplet, i.e. ~300k cells.
- Nothing here is validated against experiment (F5).

## Finding F4e-1 (2026-10-28): GCI gate re-applied with max_observed_order = 3.0 (set by the student)
- alpha 5 (naca0012_gci4): PASS unchanged (p 2.46 / 2.11) -> xfine, fine, medium `valid`.
- alpha 10 (naca0012_gci4_a10): FAIL, "CL: observed order p 4.37 > 3.0" -> xfine, fine, medium `invalid`.
- naca0012_gci (3 levels): unchanged (alpha 5 FAIL divergent CL, alpha 10 NOT_RUN).
- Only QA files and statuses changed; no solver result was re-run or edited. The status change came from
  `nacacfd gci`, not by hand.
- Near-miss during the edit: the student's first edit put the new key at 8 spaces of indentation, which would
  have broken loading the YAML. The agent spotted it in the screenshot before it was committed (I-004).

## Finding F4f-1 (2026-10-28): alpha 10 on xxfine/xfine/fine (student asked for a finer mesh)
| Level | Cells | max y+ | Iterations | Wall | CL | CD |
|---|---|---|---|---|---|---|
| xxfine | 300,152 | 0.56 | 1832 | 1821 s | 1.090786 | 0.0129522 |
| xfine | 150,640 | 0.79 | 1573 | 727 s | 1.089152 | 0.0132699 |
| fine | 75,328 | 1.12 | 1314 | 285 s | 1.087713 | 0.0139193 |
- CD: monotonic (R = 0.49), p = 2.05, GCI_fine = 2.98 % -> would pass.
- CL: divergent (R = 1.14): the change per level is ~0.0015 (0.14 %) and no longer shrinks -> GCI FAIL,
  all three cases `invalid`. The size of the change is small compared with the 2 % CL limit; the gate fails on
  the pattern (no error bound possible), not on the size.
- Level-to-level CL changes at alpha 10 over five levels: 0.0085, 0.0065, 0.0014, 0.0016 (coarse->xxfine).
- Agent's hypotheses (none tested): parts of the mesh do not refine with the level (boundary-layer quad block
  thickness fixed at 0.03 c, wake band fixed at 5 c, far field fixed), so a fixed error component remains;
  Gmsh unstructured triangles do not refine geometrically similarly.
- Reproducibility check: xfine and fine were re-run (different experiment directory). CL agrees with
  naca0012_gci4_a10 to within 8e-6 (fine 75,328 vs 75,326 cells, see F4b-1).
- Cost: 2851 s for the study; xxfine is ~30 min per angle on 4 vCPU.

## X-011 (2026-10-28): branch switch in the working tree while an experiment was running
- What: while naca0012_gci5_a10_bl06 was running (the container mounts the working tree and imports code
  from it), the agent checked out another branch to commit the polar tools, then switched back.
- Impact check: the modules the running process imports lazily (runner.case, airfoil.mesh_gmsh, qa.*) were
  identical on both branches (`git diff --stat` touched only cli.py, postprocess/*, tests); cli.py was already
  loaded. metadata.json records the commit at the start. So no result was affected, but only by luck.
- Detected by: the agent, right after the switch.
- Lesson: use a separate `git worktree` for code work while a run uses the main working tree.

## X-012 (2026-10-28): multi-line command continued after its first line failed
- What: a shell block started with `git checkout -b f4g-results origin/main && ... && plot`, followed by
  separate lines (append logs, git add, git commit). The first line failed (`origin/main` not a known ref),
  but the next lines still ran: the log entries and the commit landed on the already-merged branch
  f4g-bl-thickness, and the figure the log refers to had not been made.
- Detected by: the agent, from the error output and `git branch --show-current`. Nothing was pushed.
- Fix: new branch at that commit, figure rendered, commit amended before the first push.
- Lesson: same family as X-007/X-008. Start multi-step blocks with `set -euo pipefail`.

## Finding F5-1 (2026-10-28): alpha 5 re-checked on the polar mesh family (0.06 c BL block)
| Level | Cells | max y+ | Iterations | Wall | CL | CD |
|---|---|---|---|---|---|---|
| xxfine | 319,382 | 0.39 | 1423 | 1501 s | 0.557438 | 0.0095196 |
| xfine | 160,482 | 0.55 | 1269 | 602 s | 0.556747 | 0.0096396 |
| fine | 80,744 | 0.78 | 1061 | 214 s | 0.555554 | 0.0098227 |
- GCI PASS: CL monotonic (R 0.58), p = 1.60, GCI_fine = 0.21 %; CD monotonic (R 0.66), p = 1.24,
  GCI_fine = 2.97 %. All three `valid`.
- Observed orders are below the formal 2nd order here (no lower bound on p in the gate, see D-020). With
  p < 2 the GCI is larger than with p = 2, so it errs on the safe side; noted, not acted on.
- Cross-check between mesh families: Richardson-extrapolated CD 0.009293 (0.06 c block) vs 0.009283
  (0.03 c block, F4b-1), CL 0.55838 vs 0.55757. The extrapolated values agree within 0.1-0.15 %, although
  the individual meshes differ by up to 1.2 % in CD. Consistent, but not a validation against experiment.

## X-013 (2026-10-28): X-012 repeated within the hour, despite the written lesson
- What: the next block started with `set -euo pipefail`, but its first line was an `&&` list; bash does not
  exit on a failure inside an `&&` list (only on its last command), so after `git checkout -b f5-polar
  origin/f5-polar-tools` failed the later lines ran and committed the new experiment onto the PR #12 branch.
- Root cause of both: the clone had no `remote.origin.fetch` refspec, so `origin/<branch>` refs did not exist.
- Detected by: the agent, from the error output. Not pushed. Fix: refspec added, commit moved to f5-polar,
  f4g-results reset to its pushed head.
- Lesson (corrected): `set -e` alone is not enough; run one command per line under `set -e`, no `&&` lists.

## Finding F5-2 (2026-10-28): polar attempt 1 on the laptop stopped; low angles fail the stabilisation window
- Seen by the student on the laptop (screenshots in the thread): alpha 2 on xxfine `invalid` with residual
  drop 6.6 orders (rms[Rho] -5.5 -> -12.1) at 1001 iterations, but CL relative range 3.1e-4 > 1e-4 and CD
  1.5e-3 > 1e-3 over the last 500 iterations. At low alpha the residual reaches the 1e-12 stop before the
  1000-iteration minimum, so the window still covers the force transient (same pattern as X-005).
- The gate worked as designed: the point would otherwise have entered the polar with an unverified CL.
- Decision (student, card): stop, fix, restart. First attempt moved aside by the student to
  `runs/naca0012_polar_attempt1` on the laptop (not deleted).
- Fix (solver setting, not a threshold): `min_iterations: 2000` in the polar experiment. Checked in the cloud
  on the medium mesh at alpha 0 and 2: both `valid`, CL relative range 1.1e-8 and 0 (2001 iterations, 187 s).
- Also added: `nacacfd run --resume` (skips cases with results.json, never overwrites) and an optional
  `gates.convergence.cl_reference_magnitude` (denominator max(|mean CL|, ref) for CL near 0). The optional key
  is NOT set: the medium-mesh check showed alpha 0 passes without it. The agent's worry about alpha 0 was
  not confirmed.

## Finding F5-3 (2026-10-29): polar on the laptop, 9 of 12 angles valid
- Run on the student's laptop (8 MPI ranks, commit 7dd653f, clean tree), 2026-10-28 16:16 to 2026-10-29 08:18 UTC
  (16.0 h elapsed, ~8.3 h computing; alpha 16 shows an 8 h gap, most likely the laptop was suspended). Results pushed by the student to branch `f5-polar-results` (small files only, no vtu/mesh/restart).
- valid: alpha 2, 4, 6, 8, 10, 12, 14, 15, 16. invalid: alpha 0, 17, 18 (all convergence gate). y+ max <= 0.75.
- alpha 0: CL = -4.51e-5, last-500 range 8e-9 (absolute), residual drop 7.8 orders. Fails only because the
  relative range divides by |mean CL| ~ 0 (1.78e-4 > 1e-4). The agent had predicted this risk, then dismissed it
  after alpha 0 passed on the medium mesh (F5-2): one coarser-mesh check was not evidence for xxfine.
  Proposed fix: set `cl_reference_magnitude` (threshold file, student's decision, see I-006).
- alpha 17 / 18: residual reached 1e-12 at 2775 / 3792 iterations, but CL rose monotonically through the whole
  window (499 of 499 steps up), range 3.0e-4 / 4.4e-4; alpha 18 also CD 1.19e-3. A slow drift that the residual
  stop does not see. The gate rejected them correctly. Rerun with min_iterations 6000 in the cloud
  (`experiments/naca0012_polar_stall.yaml`), thresholds unchanged.
- alpha 14: residual plateaued at 10^-11.45 and never reached the 1e-12 stop, so SU2 ran to the 20,000-iteration
  cap (12,406 s = 3.4 h of ~8.3 h computing). CL was constant to ~1e-8 from about iteration 2000. Result valid, time wasted.
  Possible fix (not done): a force-based stop (SU2 Cauchy criterion) next to the residual stop.
- Reproducibility across machines: alpha 10 laptop (8 ranks, own image build) vs cloud (4 ranks, F4g):
  CL 1.093860 vs 1.093862, CD 0.01313631 vs 0.01313632. Same mesh statistics (319,382 elements), but the
  mesh.su2 SHA-256 differs; cause unknown (the laptop mesh file is not in the repo to compare).

## X-014 (2026-10-29): agent's push instructions assumed git was configured on the laptop
- The agent gave `git commit` + `git push` commands; the laptop had no git identity and no GitHub credentials
  (password auth is not supported). The student pasted all commands at once into the `gh auth login` prompt.
- Detected from the student's screenshots. Fixed with `git config user.*`, `gh auth login` (device code), `gh auth setup-git`.
- Lesson: check prerequisites (identity, auth) before giving push commands; ask for one command at a time.

## X-015 (2026-10-29): long rerun started with plain `nohup` died with the cloud container
- The alpha 17/18 rerun (both angles, ~3.5 h) was launched with `nohup ... &`, untracked by the session harness.
  Within ~10 min the container was restarted (dockerd and SU2 gone, 234 iterations written, no exit line in the log).
  Detected by the agent when `docker ps` failed while checking progress, before reporting anything.
- No result was lost or reported; the partial run is archived in `runs/_attempts/naca0012_polar_stall_001_killed/`.
- Fix: one angle per experiment (`naca0012_polar_a17_long.yaml`, `..._a18_long.yaml`), each run as a tracked
  background job (2 h limit), which keeps the session alive and reports the exit.
- Lesson: in the cloud session, long jobs must be tracked by the harness; `nohup` is not enough.
