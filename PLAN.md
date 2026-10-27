# PLAN

Approved by the student on 2026-10-27. Effort = rough estimate of working time (agent + review),
not compute time. Compute time is unknown until measured in F2.

Status legend: **written** = exists, not run; **tested** = run, output seen.

## F0. Repository skeleton and agent log (~1 session)
- [x] Directory structure, CLAUDE.md, PLAN.md, README.md
- [x] Stubs with docstrings that raise `NotImplementedError` (no fake implementations)
- [x] Subagents (`.claude/agents/`), skills (`.claude/skills/`), hooks (`.claude/settings.json`)
- [x] `docs/architecture.md` (Mermaid), `docs/runbook.md`, `docs/agent_log/*`
- [x] Test scaffold
**Acceptance:** `pytest` passes; every stub is verified by a test to raise `NotImplementedError`;
the hook that blocks manual `"status": "valid"` and edits of protected files is tested; small commits.

## F1. Docker image (2-4 h)
- [x] Dockerfile with pinned SU2 and Gmsh (SU2 8.5.0, Gmsh 4.15.2 from conda-forge; tested in the agent container)
- [x] Lock file of the full environment (`docker/environment.lock.txt`)
- [x] Build + `scripts/check_image.sh` on the student's laptop (after installing docker-buildx, X-003)
**Acceptance:** image builds from scratch; inside it `SU2_CFD` prints its version, `import gmsh` works,
`pytest` passes; image digest and build time recorded in `docs/agent_log/metrics.md`.

## F2. One case end to end: NACA 0012, alpha = 5 deg (1-2 days, biggest risk)
- [ ] NACA geometry, Gmsh boundary-layer mesh, SU2 config from template, run, cL/cD/cM, metadata.json
**Acceptance:** one command `nacacfd run experiments/naca0012_a5_smoke.yaml`; all outputs machine-readable;
preliminary convergence and y+ gates computed and stored; compared with reference data if available
(otherwise marked "not validated"); wall time of one case on N cores measured.

## F3. QA gates as code + negative tests (1-2 days)
- [ ] mesh quality, y+, convergence (residuals + coefficient stabilisation), physical flags
**Acceptance:** each gate returns `GateResult`; for each gate at least one test where deliberately broken
input is REJECTED (truncated run, too thick first cell, oscillating cL, ...).

## F4. Grid independence / GCI (~1 day + compute)
- [ ] 3 mesh levels, constant refinement ratio, procedure after Celik et al. (2008), citation to be verified
**Acceptance:** GCI for cL and cD at two angles of attack (to be confirmed); observed order p reported;
non-monotonic convergence is reported as such instead of forcing a GCI number.

## F5. Validation NACA 0012, M ~ 0.15, Re ~ 6e6 (~1 day + compute) - BLOCKED on reference data
- [ ] Polar from 0 deg to around stall vs Ladson (via NASA TMR); XFOIL cross-check at low alpha
**Acceptance:** plot + table of deviations; cases near/after stall flagged, not removed; every reference
number comes from a file in `data/reference/` with citation and sha256.

## F6. Parametric sweep, scaling, cloud VM (1-2 days)
- [ ] Parallel runner (process pool), other airfoils/Re from YAML (scope to be decided)
- [ ] `scripts/scaling_benchmark.py`: wall time vs cores (MPI within one case vs many cases in parallel)
- [ ] Runbook tested on at least one real VM - **only after the student approves the spend**
**Acceptance:** sweep from one YAML; scaling plot from real measurements; runbook tested.

## F7. Report material (continuous)
**Acceptance:** every number in the report traces to a file in `runs/`; agent logs are complete and honest.

## Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Boundary-layer mesh in Gmsh (y+ ~ 1, trailing edge quality) | high | start with a structured C-grid for one airfoil; optional comparison with a NASA TMR grid as a "golden" mesh |
| NACA 0012 definition: TMR uses a modified closed-trailing-edge variant | medium | read the definition from the TMR source before use; implement both with tests |
| SU2 RANS convergence (CFL, multigrid) | medium | conservative start settings; every settings change logged in decisions.md |
| Low Mach (0.15) in compressible solver | medium | compressible first (as the TMR case); incompressible solver as a logged alternative |
| Transition at low Re | high (low Re only) | fully turbulent by default; low-Re results flagged as outside validation range; XFOIL only as cross-check |
| Stall (steady RANS) | high (high alpha) | flag, never hide; no cL_max claims without caveats |
| No access to reference data from the cloud container | blocks F5 | the student downloads the files |
| Laptop thermal throttling during scaling runs | medium | record CPU clocks/temperatures if possible; repeat runs; final scaling on a VM |
| Agent "bends" results (e.g. relaxes a threshold) | core of the thesis | thresholds in one protected file + hook + tests; any change is a human checkpoint |
