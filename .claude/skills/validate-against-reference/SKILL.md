---
name: validate-against-reference
description: Compare a computed polar with experimental/reference data from data/reference/. Use for the NACA 0012 validation and XFOIL cross-checks.
---

Status: procedure written; validation code is NOT implemented yet (F5). Reference data: NOT available yet.

1. Check that `data/reference/<dataset>/SOURCE.md` exists with citation and sha256. If the data is missing,
   STOP and tell the student; never type reference numbers in yourself.
2. Make sure conditions match (Re, Mach, trip/transition, geometry variant); list every mismatch.
3. Run the validation gate and produce the comparison plot and the deviation table.
4. Cases near or beyond stall are shown and flagged, not removed.
5. XFOIL is a cross-check with a different physical model (panel method + boundary layer), not a reference.
