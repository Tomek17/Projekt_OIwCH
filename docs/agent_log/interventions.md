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
