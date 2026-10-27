# Projekt_OIwCH: agent-driven, validated CFD workflow (NACA airfoils, SU2 + Gmsh)

Course project: *Obliczenia Inżynierskie w Chmurze* (Cloud Engineering Computations), WUT.

Research question: can an AI agent (Claude Code) autonomously run a reproducible, validated CFD
workflow in the cloud, and what architecture is needed to trust its results?

## Status
F2a done: one case runs end to end on an external mesh with QA gates. Own Gmsh meshing is **not implemented yet**: most functions raise
`NotImplementedError`. See [PLAN.md](PLAN.md).

## Layout
| Path | Purpose |
|---|---|
| `CLAUDE.md` | rules and conventions for the agent |
| `config/qa_thresholds.yaml` | all QA gate thresholds (protected file) |
| `experiments/*.yaml` | one YAML = one experiment |
| `src/nacacfd/` | Python package: `airfoil`, `runner`, `postprocess`, `qa`, `cli` |
| `docker/` | image with SU2 + Gmsh + Python stack (draft) |
| `data/reference/` | experimental/reference data, each source documented |
| `runs/<experiment>/<case>/` | outputs of each case |
| `docs/` | architecture, runbook, agent logs |
| `.claude/` | subagents, skills, hooks |
| `tests/` | unit tests |

## Quickstart (planned; does not work yet)
```bash
docker build -t nacacfd -f docker/Dockerfile .          # works (F1)
scripts/check_image.sh nacacfd                           # works (F1)
scripts/fetch_meshes.sh                                  # works (F2a)
scripts/run_experiment.sh experiments/naca0012_a5_su2grid449.yaml   # works (F2a), ~6 min on 4 cores
```

## Development (works now)
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```
