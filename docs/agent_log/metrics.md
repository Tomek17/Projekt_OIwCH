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
