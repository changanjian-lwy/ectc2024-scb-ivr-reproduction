"""Generate R04E14's secondary grid: 2 cells at the primary grid's own
best-performing (CDIV, TRAMP) point (by normalized LADDER_ERR, R02B's own
metric), re-run at CFLY=0.6uF and CFLY=8.7uF -- the two extremes of this
project's own first-principles Cfly candidate range
(paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md), per
BOUNDARY.md Section 4.

The primary grid's own best cell by LADDER_ERR (confirmed directly from
results.json after all 12 primary-grid LTspice runs completed): CDIV=300uF,
TRAMP=10us, LADDER_ERR=0.035116 (the single lowest of all 12 primary
cells). This module reuses build_r04e14.py's own render()/TEMPLATE and
naming convention (case_id) unchanged, just fixing CDIV/TRAMP at that point
and varying CFLY.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_r04e14 import CASES, case_id, render  # noqa: E402

BEST_CDIV = 300e-6
BEST_TRAMP = 10e-6
CFLY_SECONDARY = (0.6e-6, 8.7e-6)


def build_secondary() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for cfly in CFLY_SECONDARY:
        text = render(BEST_CDIV, BEST_TRAMP, cfly)
        path = CASES / f"{case_id(BEST_CDIV, BEST_TRAMP, cfly)}.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build_secondary()
    print(f"# generated {len(paths)} secondary-grid cases")
    for p in paths:
        print(p)
