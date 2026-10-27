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
