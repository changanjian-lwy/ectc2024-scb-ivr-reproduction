"""Generate R04E15's Grid C: Cfly robustness at the actual winning
(CDIV, TRAMP) point, per BOUNDARY.md Section 3 Grid C.

WINNING POINT, determined directly from this experiment's own Grid A/B
results.json (11 cells) combined with R04E14's own already-committed
CDIV=300uF/TRAMP=100us cell (ladder_err=0.053627, iin_pk=39.18A):
among every (CDIV,TRAMP) candidate satisfying the peak-current bar
(IIN_PK <= 150.15 A, R02B's own best), the LOWEST LADDER_ERR is
CDIV=500uF/TRAMP=100us (ladder_err=0.033461, iin_pk=61.44A) -- confirmed
by direct inspection of results.json after Grid A/B were simulated. (Grid
B's TRAMP=20us cell has a lower ladder_err (0.0454) but FAILS the current
bar at 195.90 A, so it is excluded.)

This module reuses build_r04e15.py's own render()/case_id() and naming
convention unchanged, fixing CDIV/TRAMP at the winning point and varying
CFLY across the two first-principles-range extremes
(paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md), exactly as
R04E14's own build_r04e14_secondary.py did for its own (different) winning
point.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_r04e15 import CASES, case_id, render  # noqa: E402

WINNING_CDIV = 500e-6
WINNING_TRAMP = 100e-6
CFLY_GRID_C = (0.6e-6, 8.7e-6)


def build_grid_c() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for cfly in CFLY_GRID_C:
        text = render(WINNING_CDIV, WINNING_TRAMP, cfly)
        path = CASES / f"{case_id(WINNING_CDIV, WINNING_TRAMP, cfly)}.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build_grid_c()
    print(f"# generated {len(paths)} Grid C cases")
    for p in paths:
        print(p)
