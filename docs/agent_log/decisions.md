# Decisions

Format: ID, date, decision, reasoning, alternatives considered, who decided.

## D-001 (2026-10-27): SU2 from conda-forge, build from source as fallback
- Decision: install SU2 8.5.0 and Gmsh 4.15.2 from conda-forge in the Docker image.
- Reasoning: both packages exist there (checked in conda-forge `current_repodata.json`); SU2 is not in Ubuntu apt.
  Pinned binary packages are faster and simpler than compiling.
- Alternatives: compile SU2 from tag `v8.5.0` (reachable via git), more control over MPI, slower; Ubuntu apt
  gmsh 4.12.1 (older).
- Status: written; not yet built (F1).
- Decided by: agent, plan approved by the student.

## D-002 (2026-10-27): "valid" status is assigned by code, hooks are a second layer
- Decision: only `nacacfd.qa.status.assign_status()` may set `status: valid`; a Claude Code hook additionally
  blocks the agent from writing it by hand.
- Reasoning: hooks only act inside Claude Code and the agent has Bash, so hooks alone are a soft guarantee.
  The rule must also hold when the pipeline runs without the agent.
- Alternatives: hooks only (weaker); human approval of each case (does not scale).
- Decided by: agent, approved by the student with the plan.

## D-003 (2026-10-27): Spalart-Allmaras as the default turbulence model
- Decision: SA by default, SST later as a comparison. Changing the model is a human checkpoint.
- Reasoning: the NASA TMR NACA 0012 validation case is centred on SA.
- Decided by: the student (answer to question 4).

## D-004 (2026-10-27): Compute on the student's laptop, short cloud VM at the end
- Decision: campaigns run locally (WSL2 Ubuntu 24.04, Ryzen 7 8745HX, 8 physical cores / 16 threads,
  30 GiB RAM for WSL, Docker Engine from apt); one short cloud VM run at the end proves the runbook and
  gives scaling data, only after the student approves the cost.
- Reasoning: zero cost; the laptop is stronger than the agent's cloud container (4 vCPU, 15 GiB);
  the course topic still needs cloud evidence.
- Alternatives: the agent's cloud container (ephemeral, 4 vCPU, not under the student's control);
  paid VM from the start (cost before we know the time per case).
- Agent's original recommendation: mixed (cloud container for F0-F3, VM for F4-F6). The student chose local.
- Decided by: the student.

## D-005 (2026-10-27): Python 3.11 in the image, one package `nacacfd` in `src/`
- Reasoning: conda-forge SU2 8.5.0 builds seen for py310/py311 (not 3.12+, as of the check).
  One installable package gives one CLI entry point and clean imports in tests.
- Note: only `current_repodata.json` was checked, which may not list all builds. To verify in F1.

## D-006 (2026-10-27): QA thresholds accepted as starting defaults
- Decision: thresholds proposed in the plan go into `config/qa_thresholds.yaml` as starting values.
  Validation tolerance and aspect-ratio limit stay undefined until data is seen (after F2/F5).
- Decided by: the student (answer to question 5), to be revisited after F2.

## D-007 (2026-10-27): Image built from an explicit lock file, base image pinned by digest
- Decision: `environment.yml` is the human-readable spec; the image installs `environment.lock.txt`
  (exact URLs + md5 of 322 packages); `FROM mambaorg/micromamba:2.3.0@sha256:d008b261...`.
- Reasoning: reproducibility is part of the thesis; a version spec alone can resolve differently later.
- Check: rebuilding from the lock and re-exporting gives the same 322 packages (order differs). Tested.
- Alternatives: version spec only (simpler, not reproducible); conda-lock tool (one more tool to explain).

## D-008 (2026-10-27): Mounted repository code takes precedence in the container (PYTHONPATH=/work/src)
- Reasoning: during development the repo is mounted at /work; the git hash recorded for a run must match the
  code that actually ran, not a copy baked into the image at build time.
- Trade-off: a stale image + new repo code can mix if Python dependencies change; `metadata.json` will record
  both the git hash and the image ID (F2).

## D-009 (2026-10-27): Proxy CA passed as a BuildKit secret, never baked into the image
- Reasoning: the agent's cloud container intercepts TLS; the student's laptop and a cloud VM do not.
  A build secret works in both cases and leaves no trace in the image.

## D-010 (2026-10-27): Standard SA model, no SA_OPTIONS
- Decision: `KIND_TURB_MODEL= SA` without options (the SU2 test case uses `NEGATIVE, EXPERIMENTAL`).
- Reasoning: SU2 refuses `NEGATIVE` alone as "a non-standard version of SA-neg" (attempt 001, X-004); the agent
  cannot explain what EXPERIMENTAL changes, so it uses the plain standard model it can explain.
- Alternative: copy the test-case options verbatim; revisit if robustness problems appear at high alpha.

## D-011 (2026-10-27): CONV_STARTITER = 1000 as a minimum iteration count
- Problem: SU2 stopped at 768 iterations when rms[Rho] reached -12, so the last 500 iterations still contained
  part of the start-up transient and the convergence gate failed on CL drift (1.17e-4 > 1e-4).
- Decision: let SU2 run at least 1000 iterations (convergence is not tested before CONV_STARTITER).
  The QA threshold was NOT changed; the solver setting was.
- Result: CL relative range in the window 5.8e-6; residual drop 9.2 orders.

## D-012 (2026-10-27): Validate the solver setup on an external "golden" mesh before our own meshing
- Decision: experiments can use `mesh.source: file` (sha256-pinned). First runs use the SU2 TestCases NACA 0012
  C-grids (225x65, 449x129), so solver-setup errors are separated from meshing errors (risk table in PLAN.md).

## D-013 (2026-10-27): WRT_RESTART_COMPACT= NO to get y+ into surface_flow.csv
- Finding: with the default (YES), SU2 v8.5.0 writes only conservative variables to the surface CSV even with
  VOLUME_OUTPUT including PRIMITIVE; tested in a 2-iteration restart run, then in the pipeline.
- Cost: larger restart files (git-ignored).

## D-014 (2026-10-27): Near-stall detection is an experiment-level check
- The per-case physics_flags gate checks solver exit code, finite coefficients and negative drag only.
  Near-stall needs the whole polar and will be implemented with the polar (F5).

## D-015 (2026-10-27): Own mesh = Gmsh hybrid (quad boundary layer + triangles), not a structured C-grid
- Reasoning: the Gmsh BoundaryLayer field handles the sharp trailing edge with a fan and keeps the code short
  and explainable; SU2 handles hybrid meshes.
- Consequence for F4 (GCI): refinement is done by scaling all sizes (levels coarse/medium/fine = factor 2/1/0.5
  on surface spacing), not by an exact structured refinement ratio. The effective ratio must be computed from
  cell counts, and the report must say so.
- Alternatives: structured C-grid with transfinite blocks (exact refinement ratio, more code, trailing-edge
  block topology is error-prone); external meshes only (no parametric airfoils).
- Parameters (defaults in mesh_gmsh.MESH_DEFAULTS): far field 100 chords, 200 points per side at medium,
  boundary layer 0.03 chord thick with growth 1.15. These are the agent's choices, not taken from a reference.

## D-016 (2026-10-27): design first cell for y+ = 0.5
- The flat-plate estimate for y+ = 1 gave max y+ 2.19 (near the leading edge, suction side) -> y+ gate FAIL.
- Design value lowered to 0.5 in the experiment (a meshing parameter, not a QA threshold). Result: max y+ 1.10.

## D-017 (2026-10-27): GCI per Celik et al. (2008) as an experiment-level gate
- Implemented in `qa/gci.py`; runs only when all three levels passed their per-case gates (otherwise NOT_RUN).
- A non-monotonic sequence (oscillatory or divergent) is a FAIL, not a pass with a warning, because no error
  bound exists then. The agent did NOT relax this after the alpha 5 CL failure; that is the student's decision.
- Effective refinement ratio uses h = (1/N)^(1/2) from cell counts, as required for unstructured meshes (D-015).

## D-018 (2026-10-27): GCI uses the three finest levels of a study
- A study may list more than three levels; the GCI gate uses the three finest (Celik et al. is a 3-grid
  procedure). Other levels get gci NOT_RUN (status `incomplete`) so they never inherit a PASS (X-010).
- Student's decision (card, 2026-10-27): diagnose with a far-field test + a 4th level before changing the
  mesh method or the criteria. No threshold was changed.

## D-019 (2026-10-27): mesh size growth distance separate from the far-field radius
- New parameter `size_growth_distance_chords` (default 100) so a far-field test changes only the outer
  region (X-009). With the default, all earlier 100-chord meshes are unchanged.
