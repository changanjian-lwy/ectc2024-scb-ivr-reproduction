"""Generate the fixed A42 zero-snubber negative-current sweep."""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
OUT = TRACK / "A42_zero_snubber_negative_current_threshold" / "cases"
NEGATIVE_PERCENTAGES = tuple(range(1, 11))


def source_label(pct: int) -> str:
    if pct <= 2:
        return "P24_EXPLICIT"
    if pct <= 4:
        return "DIAGNOSTIC_BRIDGE"
    return "P25_SUPPLEMENT"


def build() -> list[Path]:
    source = PARENT.read_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for pct in NEGATIVE_PERCENTAGES:
        fraction = pct / 100
        label = source_label(pct)
        text = source
        text = text.replace(
            "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS",
            f"* A42 - zero-snubber {pct}% negative-current row ({label})",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected sensitivity row: {pct}% of the P24 Eq.(2) phase peak (125 A).",
            1,
        )
        text = text.replace(
            ".include ../../04_component_models/",
            ".include ../../../../paper_locked/04_component_models/",
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.2f}", 1)
        text = text.replace(
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
            f".meas tran A42_SOURCE_CODE PARAM "
            f"{0 if label == 'P24_EXPLICIT' else 1 if label == 'DIAGNOSTIC_BRIDGE' else 2}",
            1,
        )
        path = OUT / f"a42_{pct:02d}pct_zero_snubber.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
