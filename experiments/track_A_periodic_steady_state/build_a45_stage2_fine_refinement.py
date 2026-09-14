"""Generate A45 stage-2's predeclared 22.00%-22.10% final local refinement grid.

Mirrors build_a42_threshold_fine_refinement.py's 1-basis-point mechanism,
inside the bracket build_a45_stage2_refinement.py's 0.1%-step grid found
(22.00%: no ZVS, min Vds=24.6 mV; 22.10%: ZVS, min Vds=-7.6 mV).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Robust to both direct script invocation and package-style import (see
# build_a45_stage2_refinement.py for the same pattern and rationale).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_a45_stage2_interval3_sweep import HERE, _base_text  # noqa: E402

OUT = HERE / "fine_cases"
NEGATIVE_BASIS_POINTS = tuple(range(2200, 2211))
TRAN_END_NS = 200.0


def build() -> list[Path]:
    source = _base_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for basis_points in NEGATIVE_BASIS_POINTS:
        pct = basis_points / 100
        fraction = basis_points / 10000
        text = source
        text = text.replace(
            "* A45 stage 2 - P24 interval 3, EPC2067 Table-3 candidate commutation cap",
            f"* A45 stage 2 fine refinement - EPC2067 candidate {pct:.2f}% negative-current row (P25_SUPPLEMENT/SENSITIVITY_ONLY)",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected final local refinement row: {pct:.2f}% of the P24 Eq.(2) phase peak (125 A).\n"
            f"* .tran window widened to {TRAN_END_NS:g} ns, same rationale as the wide-bracket search.",
            1,
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.4f}", 1)
        text = text.replace(
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
            ".meas tran A45_SOURCE_CODE PARAM 2",
            1,
        )
        text = text.replace("FROM=2n TO=50n", f"FROM=2n TO={TRAN_END_NS:g}n", 1)
        text = text.replace(
            "FIND V(vin,a1) AT=50n", f"FIND V(vin,a1) AT={TRAN_END_NS:g}n", 1
        )
        text = text.replace(
            ".tran 0 50n 0 0.5p UIC", f".tran 0 {TRAN_END_NS:g}n 0 0.5p UIC", 1
        )
        path = OUT / f"a45_fine_{basis_points:04d}bp_epc2067.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
