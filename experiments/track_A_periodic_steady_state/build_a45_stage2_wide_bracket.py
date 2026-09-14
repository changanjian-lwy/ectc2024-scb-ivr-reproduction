"""Generate A45 stage-2 wide-bracket search cases.

The 1%-10% coarse grid (build_a45_stage2_interval3_sweep.py) matched A42's
required convention/labelling but did not reach ZVS anywhere in that range
(unlike A42's GS61008T-based 7.76%-7.77% bracket): at 10% the high-side Vds
minimum after release is still 5.93 V, far from 0. The EPC2067 candidate's
~9.7x/7.2x larger CH_TOTAL/CL_TOTAL means more commutation charge is needed,
so a wider bracket is expected and searched here, per A45's BOUNDARY.md
("if the 1%-10% coarse sweep needs a wider bracket, that is an expected,
fine outcome"). All rows here are P25_SUPPLEMENT-or-further sensitivity
rows; none are P24_EXPLICIT/DIAGNOSTIC_BRIDGE.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Robust to both direct script invocation and package-style import (see
# build_a45_stage2_refinement.py for the same pattern and rationale).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_a45_stage2_interval3_sweep import HERE, _base_text  # noqa: E402

OUT = HERE / "wide_bracket_cases"


def build(percentages: tuple[float, ...], tran_end_ns: float = 150.0) -> list[Path]:
    """Build wide-bracket cases with an EXTENDED .tran observation window.

    The parent R04D3A/A42 50 ns window was sized for GS61008T's 1%-10% rows,
    where the pre-release negative-current ramp only costs 1.8-18.7 ns. At
    the EPC2067 candidate's larger negative-current percentages, the
    pre-release ramp itself grows (~1.9-2.0 ns per percentage point, measured
    directly from the 1%-10% and initial wide-bracket runs) and can consume
    most or all of a fixed 50 ns window, truncating the post-release
    commutation event before it is observed -- a fixed-time boundary
    silently substituting for the physical Vds=0 event, which
    EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md Section VI forbids. The window
    is therefore widened (never shortened) so every declared physical event
    (release, ZVS or its absence) is actually observed, not truncated. This
    changes only the simulation stop time, not the control-latch mechanism,
    the device model or any measurement point.
    """
    source = _base_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for pct in percentages:
        fraction = pct / 100
        text = source
        text = text.replace(
            "* A45 stage 2 - P24 interval 3, EPC2067 Table-3 candidate commutation cap",
            f"* A45 stage 2 wide bracket - EPC2067 candidate {pct:g}% negative-current row (P25_SUPPLEMENT/SENSITIVITY_ONLY)",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected wide-bracket sensitivity row: {pct:g}% of the P24 Eq.(2) phase peak (125 A).\n"
            f"* .tran window widened to {tran_end_ns:g} ns (see build_a45_stage2_wide_bracket.py)"
            " so the pre-release ramp cannot truncate the post-release event.",
            1,
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.4f}", 1)
        text = text.replace(
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
            ".meas tran A45_SOURCE_CODE PARAM 2",
            1,
        )
        text = text.replace(
            "FROM=2n TO=50n", f"FROM=2n TO={tran_end_ns:g}n", 1
        )
        text = text.replace(
            "FIND V(vin,a1) AT=50n", f"FIND V(vin,a1) AT={tran_end_ns:g}n", 1
        )
        text = text.replace(
            ".tran 0 50n 0 0.5p UIC", f".tran 0 {tran_end_ns:g}n 0 0.5p UIC", 1
        )
        tag = f"{pct:g}".replace(".", "p")
        path = OUT / f"a45_wide_{tag}pct_epc2067.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    import sys

    args = [float(x) for x in sys.argv[1:]]
    tran_end = 150.0
    if args and args[0] > 1000:
        tran_end = args[0]
        args = args[1:]
    for generated_path in build(tuple(args), tran_end_ns=tran_end):
        print(generated_path)
