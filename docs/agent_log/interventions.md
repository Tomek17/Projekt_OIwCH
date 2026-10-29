# Interventions

Each time the human had to correct, redirect or unblock the agent.
Format: ID, date, what, why, how long (approx.), category (unblock / redirect / correct).

## I-001 (2026-10-27): reference data blocked by the network policy (OPEN)
- What: the agent cannot reach turbmodels.larc.nasa.gov from its cloud container (proxy 403).
  The student has to download the NACA 0012 reference data and add it to the repo.
- Category: unblock. Blocks F5.

## I-002 (2026-10-27): GitHub repository created by the student
- What: the cloud session cannot create repositories; the student created `Tomek17/Projekt_OIwCH`
  and granted the Claude GitHub App access.
- Category: unblock. ~10 min including instructions.

## I-003 (2026-10-27): compute location redirected to the local laptop
- What: the agent recommended a mixed setup (agent cloud container + paid VM); the student asked to compute
  locally for free. The agent then guided the WSL2 + Docker setup through copy-pasted commands and screenshots.
- Category: redirect. ~15 min. See D-004.

## I-004 (2026-10-28): student asked for a new GCI criterion (observed order check)
- The agent proposed it as an option after F4c; the student said "let's add that".
- The threshold must be written by the student into `config/qa_thresholds.yaml` (protected). Until then the
  GCI gate returns NOT_RUN. Status: OPEN until the value is set.
- 2026-10-28: CLOSED. The student set `max_observed_order: 3.0` in the GitHub web editor (commit b706b36),
  after the agent gave step-by-step instructions and caught a wrong indentation in the first attempt.

## I-005 (2026-10-28): polar run on the student's laptop, stopped and restarted by decision
- The student chose to run the polar locally (8 cores), reported the alpha 2 failure via screenshots
  (the agent has no live access to the laptop), and chose "stop now, fix, restart" on a decision card.

## I-006 (2026-10-29): polar results transferred by the student; threshold question for alpha 0
- The agent cannot reach the laptop; the student pushed results to `f5-polar-results` after help with git
  identity and GitHub login (X-014). ~30 min.
- Decision card: set `gates.convergence.cl_reference_magnitude` (agent proposes 0.1, to be confirmed) or keep
  alpha 0 invalid. Status: OPEN.
