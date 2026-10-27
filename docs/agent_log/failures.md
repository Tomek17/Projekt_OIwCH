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

## X-003 (2026-10-27): Dockerfile needed BuildKit, which the student's Docker did not have
- What: the F1 Dockerfile uses `RUN --mount=type=secret` (BuildKit). Ubuntu's `docker.io` package ships without
  buildx, so `docker build` on the student's laptop used the legacy builder and stopped at step 3/10:
  "the --mount option requires BuildKit".
- Detected by: the student's first build on the target machine (screenshot), ~25 min after the PR was merged.
- Root cause: the agent tested the build only in its own cloud container, where BuildKit was available,
  and declared the Dockerfile tested without testing it on the target environment.
- Fix: `sudo apt install -y docker-buildx`; requirement added to docker/README.md, runbook and CLAUDE.md.
- Lesson: "tested" must name WHERE it was tested. F1 was tested in the agent's environment, not the target one.
