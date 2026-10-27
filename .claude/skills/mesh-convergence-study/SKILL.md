---
name: mesh-convergence-study
description: Run a 3-level grid independence study and compute GCI with Richardson extrapolation. Use before trusting any polar on a given mesh family.
---

Status: procedure written; GCI code is NOT implemented yet (F4).

1. Generate coarse/medium/fine meshes with a constant refinement ratio (record the ratio and cell counts).
2. Run the same case on all three; all three must pass the convergence gate first.
3. Run the GCI gate; report observed order p, extrapolated value and GCI_fine for CL and CD.
4. If convergence is oscillatory or divergent across levels, report that; do not force a GCI number.
5. Pick the production mesh level and log the decision with the numbers in `docs/agent_log/decisions.md`.
