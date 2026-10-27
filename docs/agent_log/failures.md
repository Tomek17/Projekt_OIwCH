# Failures and near-misses

Format: ID, date, what went wrong, how it was detected (gate / test / human / agent), fix, lesson.

## X-001 (2026-10-27): duplicated `git clone` instruction
- What: the agent put the same `git clone` step in two consecutive messages; the student ran both and got
  `fatal: destination path 'Projekt_OIwCH' already exists`.
- Detected by: the student's terminal output (screenshot).
- Impact: none (the first clone was fine), a few minutes of confusion.
- Fix: the agent explained the error and gave a check command instead of a new clone.
- Lesson: when repeating a step from an earlier message, make it idempotent or say it was already done.

## X-002 (2026-10-27): first image build failed on the proxy's TLS certificate
- What: `micromamba install` inside `docker build` failed with "SSL certificate problem: self-signed certificate
  in certificate chain" (6 s into the build). The agent's environment check had verified conda-forge access
  from the host, not from inside a container build, which does not trust the proxy CA.
- Detected by: the build itself (exit code 1).
- Fix: optional `--secret id=extra_ca` in the Dockerfile (D-009). Second build succeeded.
- Lesson: "reachable from the host" is not "reachable from inside the build"; test the real path.
