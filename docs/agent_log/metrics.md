# Metrics

Wall-clock times are UTC timestamps from the conversation; effort is not measured more precisely than that.

## Phase 0 (environment check, plan, skeleton)
| Item | Value |
|---|---|
| Session start | 2026-10-27 17:21 |
| Plan proposed | 2026-10-27, before 17:33 (exact time not recorded) |
| Plan approved | 2026-10-27 17:59 |
| Skeleton PR opened | (fill in) |
| Interventions | 3 (I-001..I-003) |
| Agent failures / near-misses | 1 (X-001) |
| CFD cases run / failed / retried | 0 / 0 / 0 |

## F0 verification (2026-10-27)
| Check | Result |
|---|---|
| `pytest -q` (Python 3.13, cloud container, local venv) | 60 passed |
| Hook scripts | tested by unit tests (subprocess with hook-like JSON) |
| Hooks in a live Claude Code session | NOT verified: the session that wrote them had not loaded the repo settings (a probe command that the guard should block was not blocked) |
| Docker image | not built (F1) |

## F1 (Docker image), agent cloud container, 4 vCPU
| Item | Value |
|---|---|
| Build attempts | 3 (1 failed: X-002; 1 from the spec: 294 s; 1 from the lock: 227 s) |
| Build time includes | package download + layer export (export alone ~158 s in the first successful build) |
| Image size (uncompressed) | 5,313,091,347 bytes (~5.3 GB) |
| Image ID (lock build) | sha256:9c7ef367c0330a819178d84648e29296668b44145f2b7514ee258876726ddb9e |
| Verified inside image | SU2 v8.5.0, Gmsh 4.15.2 (CLI + Python), Open MPI 5.0.11, Python 3.11.18, pytest 60 passed |
| Not verified | an actual SU2 run |

## F1 on the student's laptop (WSL2 Ubuntu 24.04, docker.io + docker-buildx), 2026-10-27
| Item | Value |
|---|---|
| Build attempts | 2 (1 failed: X-003, no BuildKit; 1 OK after installing docker-buildx) |
| Build time | unknown: the screenshot shows a fully cached rebuild (0.9 s), the first successful build was not timed |
| `scripts/check_image.sh` | SU2 v8.5.0, Gmsh 4.15.2 (CLI + Python), Open MPI 5.0.11, Python 3.11.18, 60 passed (from the student's screenshot) |

## F2a (single case on external meshes), agent cloud container, 4 vCPU, 4 MPI ranks
| Run | Mesh | Iterations | Wall time | Status | Notes |
|---|---|---|---|---|---|
| manual check (outside pipeline) | 225x65 | 766 | 42 s (docker run incl.) | n/a | SU2 test-case options, residual -12 |
| 001 | 225x65 | 0 | 1.9 s | invalid | X-004 |
| 002 | 225x65 | 768 | 27.8 s | invalid | X-005, X-006 |
| 003 | 225x65 | 1001 | 35.1 s | incomplete | X-006 |
| 004 / final | 225x65 | 1001 | 34.8 / 35.6 s | invalid | y+ 3.1 > 2.0 |
| 001 / final | 449x129 | 2336 | 334.4 / 335.0 s | valid (per-case gates only) | y+ 1.09 |
| Reproducibility | both | | | | final reruns from a clean commit gave CL and CD identical to all printed digits |
| Cases run / failed / retried | 8 / 2 crashed or invalid by agent error / 4 reruns | | | | |

## F2b (own Gmsh mesh), agent cloud container, 4 MPI ranks
| Run | Mesh | Iterations | Wall (SU2) | Status | Notes |
|---|---|---|---|---|---|
| 001 | Gmsh medium, design y+ 1.0, 35,664 el. | 1001 | 77.0 s | invalid | max y+ 2.19 |
| final | Gmsh medium, design y+ 0.5, 37,674 el. | 1001 | 81.1 s | valid (per-case gates) | max y+ 1.10 |
| Mesh generation | | | ~1 s | | Gmsh, single thread |

## F4 (grid study), agent cloud container, 4 MPI ranks
| Case | Wall (SU2) | Status |
|---|---|---|
| alpha 5 fine / medium / coarse | 178 s / 80 s / 39 s | invalid (GCI fail, CL divergent) |
| alpha 10 fine / medium / coarse | 220 s / 88 s / 40 s | incomplete / incomplete / invalid (y+ 2.22) |
| Whole experiment (6 cases + meshing + GCI) | 653 s | one command: `scripts/run_experiment.sh experiments/naca0012_gci.yaml` |
| Agent errors in this phase | 1 (X-008) | |

## F4b (diagnosis of the CL divergence), agent cloud container, 4 MPI ranks
| Run | Wall | Status |
|---|---|---|
| far field R 50 / 200, attempt 001 (confounded, X-009) | 67 s / 144 s (whole experiment) | archived |
| far field R 50 / 200, final | 79 s / 84 s (SU2) | valid / valid |
| 4-level study, alpha 5 | 799 s whole experiment (xfine alone 501 s) | GCI PASS; 3 valid, coarse incomplete |
| Agent errors in this phase | 2 (X-009, X-010) | both detected by the agent before reporting |

## F4c (grid study alpha 10), agent cloud container, 4 MPI ranks
| Run | Wall | Status |
|---|---|---|
| 4-level study, alpha 10 | 973 s whole experiment (xfine alone 625 s) | GCI PASS; 3 valid, coarse invalid (y+ 2.22) |
| Agent errors in this phase | 0 | |

## F4f (alpha 10, xxfine/xfine/fine), agent cloud container, 4 MPI ranks
| Run | Wall | Status |
|---|---|---|
| xxfine (300,152 cells) | 1821 s, 1832 iterations | invalid (GCI FAIL, CL divergent) |
| xfine / fine (re-runs) | 727 s / 285 s | invalid (same) |
| Whole experiment | 2851 s | |
| Agent errors in this phase | 0 | the agent's runtime guess "40-60 min" was right (48 min) |
