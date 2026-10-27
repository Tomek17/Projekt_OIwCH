# CLAUDE.md: project memory for the agent

## Goal
Research question: *can an AI agent (Claude Code) autonomously run a reproducible, validated CFD workflow
in the cloud, and what architecture is needed to trust its results?*

Test case: parametric 2D RANS aerodynamics of NACA airfoils with SU2 + Gmsh in Docker, producing
cL/cD/cM polars, validated against experiment (NACA 0012, M ~ 0.15, Re ~ 6e6, Ladson data via NASA TMR).
The written report (Polish) is graded mostly on architecture and on evidence of how the agent behaved.

## Hard rules (never break these)
1. Never fabricate numbers, citations or reference data. Unknown = write "unknown".
2. Never claim something works unless you ran it and saw the output. Use the status vocabulary below.
3. Never write `"status": "valid"` by hand. Only `nacacfd.qa.status.assign_status()` may set it,
   and only when every relevant QA gate passed.
4. Never hide a failed, non-converged or unphysical case. Flag it and log the reason.
5. Do not edit `data/reference/**` or `config/qa_thresholds.yaml` without explicit human approval
   (hooks block it; do not try to work around the hooks).
6. Prefer simple and boring over clever. Everything must be explainable in the report.
7. Commit in small steps with clear messages.

## Status vocabulary (use it in commits, logs and messages)
- **written**: code/file exists, has not been run.
- **tested**: it was run and the output was seen; link the log or test.
- **to be confirmed**: a value proposed by the agent that needs the student's decision.

## Human-in-the-loop checkpoints: STOP and ask before
- changing the turbulence model (default: SA),
- adding, changing or removing validation reference data,
- relaxing any QA threshold,
- spending cloud money (starting any paid VM),
- deleting results in `runs/`.
Record each such stop in `docs/agent_log/interventions.md`.

## Quality gates
Thresholds live in ONE place: `config/qa_thresholds.yaml`. Gates are code in `src/nacacfd/qa/`;
each returns a `GateResult` (passed, value, threshold, evidence path, reason).
A result is valid only if all relevant gates pass: mesh quality, wall y+, convergence (residual drop
AND force-coefficient stabilisation), grid independence (GCI) where required, validation vs reference.

## Evidence logging (do this as you work, not at the end)
- `docs/agent_log/decisions.md`: non-trivial decisions, reasoning, alternatives.
- `docs/agent_log/interventions.md`: every time the human corrected, redirected or unblocked the agent.
- `docs/agent_log/failures.md`: every mistake or near-miss, how it was detected, the fix.
- `docs/agent_log/metrics.md`: counts and timings per phase.
A log with only successes is useless. Be honest.

## Conventions
- Code, comments, configs, file names and repo docs in English; the student talks Polish.
- Python >= 3.11, package `nacacfd` in `src/`, CLI `nacacfd`.
- One experiment = one YAML in `experiments/`. One case = one directory `runs/<experiment>/<case>/`
  with machine-readable outputs (`results.json`, `qa_report.json`, `metadata.json`).
- All heavy tools (SU2, Gmsh) run inside the Docker image from `docker/`.

## Environment notes
- Main compute: the student's laptop, WSL2 Ubuntu 24.04, 8 physical cores, Docker Engine (apt docker.io + docker-buildx).
- In the Claude Code cloud container the Docker daemon is not running by default: start it with `dockerd &`.
  NASA TMR (turbmodels.larc.nasa.gov) is blocked from that container; reference data must be supplied by the student.
