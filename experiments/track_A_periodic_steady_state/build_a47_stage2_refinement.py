"""Generate A47 stage-2's 9.0%-10.0% threshold refinement grid (0.1% steps).

The coarse 1%-10% grid (build_a47_stage2_interval3_sweep.py) already
bracketed the transition inside the original A42-convention range itself
(9%: no ZVS, min Vds=0.760V; 10%: ZVS, min Vds=-0.021V) -- unlike A45's
EPC2067 branch, which needed a much wider bracket search first. This
predeclares the finer 0.1%-step grid inside that bracket before any
finer-than-1-percentage-point result is read, mirroring
build_a42_threshold_refinement.py's / build_a45_stage2_refinement.py's
basis-point mechanism.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_a47_stage2_interval3_sweep import HERE, _base_text  # noqa: E402

OUT = HERE / "refinement_cases"
NEGATIVE_BASIS_POINTS = tuple(range(900, 1001, 10))


def build() -> list[Path]:
    source = _base_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for basis_points in NEGATIVE_BASIS_POINTS:
        pct = basis_points / 100
        fraction = basis_points / 10000
        text = source
        text = text.replace(
            "* A47 stage 2 - P24 interval 3, nonlinear GS61008T Coss(V) commutation cap",
            f"* A47 stage 2 refinement - nonlinear Coss(V) {pct:.1f}% negative-current row (P25_SUPPLEMENT/SENSITIVITY_ONLY)",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected threshold-refinement row: {pct:.1f}% of the P24 Eq.(2) phase peak (125 A).",
            1,
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.4f}", 1)
        text = text.replace(
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
            ".meas tran A47_SOURCE_CODE PARAM 2",
            1,
        )
        path = OUT / f"a47_refine_{basis_points:04d}bp_nonlinear.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
