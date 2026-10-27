---
name: run-single-case
description: Run one airfoil case (one angle of attack) end to end and report the result with its QA status. Use for smoke tests and for re-running a single case.
---

Status: procedure written; the `nacacfd run` command is NOT implemented yet (F2).

1. Check the experiment file: `nacacfd validate-config experiments/<name>.yaml`.
2. Make sure the Docker image exists (`docker image inspect nacacfd`); if not, build it (F1) and log the build time.
3. Run inside the image:
   `docker run --rm -v "$PWD":/work -w /work nacacfd nacacfd run experiments/<name>.yaml`
4. Open `runs/<name>/<case>/results.json` and `qa_report.json`. Report CL, CD, CM **with** the status
   and every failed or not-run gate. Never report the coefficients without the status.
5. Delegate an independent check to the qa-agent.
6. If the run failed because of the agent (wrong setting, wrong path), add an entry to `docs/agent_log/failures.md`.
7. Update `docs/agent_log/metrics.md` (cases run/failed, wall time).
