---
name: assess-convergence
description: Decide whether an SU2 run has converged, using the convergence gate and a look at the history. Use when a run finished, stalled or looks suspicious.
---

Status: procedure written; the convergence gate is NOT implemented yet (F2/F3).

1. Run the gate: `nacacfd qa runs/<experiment>` and read the `convergence` entry in `qa_report.json`.
2. Look at `history.csv` yourself: residual drop, and CL/CD over the last window
   (window length and limits are in `config/qa_thresholds.yaml`).
3. Classify: converged / oscillating / stalled / diverged. An oscillating case is NOT converged,
   even if the mean looks reasonable; it gets flagged.
4. If you propose more iterations or other settings, write the reason in `docs/agent_log/decisions.md`.
5. Never change the thresholds to make a case pass. That is a human checkpoint.
