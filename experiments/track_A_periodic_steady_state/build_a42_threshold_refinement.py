"""Generate A42's predeclared 7.0%-8.0% threshold refinement grid."""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
OUT = TRACK / "A42_zero_snubber_negative_current_threshold" / "refinement_cases"
NEGATIVE_BASIS_POINTS = tuple(range(700, 801, 10))


def build() -> list[Path]:
    source = PARENT.read_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for basis_points in NEGATIVE_BASIS_POINTS:
        pct = basis_points / 100
        fraction = basis_points / 10000
        text = source
        text = text.replace(
            "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS",
            f"* A42 refinement - zero-snubber {pct:.1f}% P25-supplement row",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected threshold-refinement row: {pct:.1f}% of 125 A.",
            1,
        )
        text = text.replace(
            ".include ../../04_component_models/",
            ".include ../../../../paper_locked/04_component_models/",
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.4f}", 1)
        path = OUT / f"a42_refine_{basis_points:03d}bp_zero_snubber.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
