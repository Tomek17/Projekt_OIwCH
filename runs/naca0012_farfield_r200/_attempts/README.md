# Attempt 001: CONFOUNDED, not a far-field result

The mesh code used the far-field radius also as the distance over which the triangle size grows
(Threshold DistMax = radius). Changing the radius therefore also changed the mesh near the airfoil:
triangles 6,200 (R = 50) / 15,864 (R = 100) / 48,104 (R = 200); quads identical (21,810).
CL/CD here mix far-field and resolution effects. See Finding F4b-1 in docs/agent_log/failures.md.

| R [chords] | elements | CL | CD |
|---|---|---|---|
| 50 | 28,010 | 0.551961 | 0.011271 |
| 100 (runs/naca0012_gci4 medium) | 37,674 | 0.553987 | 0.010320 |
| 200 | 69,914 | 0.554628 | 0.010077 |

Fix: separate parameter `size_growth_distance_chords` (default 100, R = 100 meshes unchanged), then rerun.
