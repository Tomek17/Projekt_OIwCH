Earlier attempts of this experiment, kept as evidence (see docs/agent_log/failures.md and decisions.md).
- 001_sa_options_negative: SU2 refused `SA_OPTIONS= NEGATIVE` without EXPERIMENTAL; solver exit 1 -> invalid (X-004)
- 002_no_yplus_short_window: run stopped at 768 iterations (< 500-iteration window after transient) -> convergence FAIL; no y+ in surface CSV (X-005, X-006)
- 003_no_yplus_in_surface_csv: min iterations fixed; y+ still missing -> incomplete (X-006)
- 004_uncommitted_code: same result as the final run, but produced from an uncommitted working tree (git_dirty=true); rerun from a clean commit
