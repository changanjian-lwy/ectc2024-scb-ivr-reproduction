"""Generate A41 from the locked P24 local Interval-3 parent."""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT
    / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
OUT = TRACK / "A41_p24_snubber_local_sensitivity" / "cases"

CAPS_PF = (0, 50, 100, 250, 500, 1000, 2000)
NEGATIVE_FRACTIONS = (0.01, 0.02)
BRANCHES = {
    "high_only": ("{CH_TOTAL+CSNUB}", "{CL_TOTAL}"),
    "symmetric": ("{CH_TOTAL+CSNUB}", "{CL_TOTAL+CSNUB}"),
}


def build() -> list[Path]:
    source = PARENT.read_text()
    generated: list[Path] = []
    OUT.mkdir(parents=True, exist_ok=True)

    for fraction in NEGATIVE_FRACTIONS:
        pct = int(round(fraction * 100))
        for branch, (ch_expr, cl_expr) in BRANCHES.items():
            for cap_pf in CAPS_PF:
                name = f"a41_{pct}pct_{branch}_{cap_pf}pf"
                text = source
                text = text.replace(
                    "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS",
                    f"* A41 - P24 {pct}% {branch} added snubber {cap_pf} pF",
                    1,
                )
                text = text.replace(
                    "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
                    f"* selected P24 boundary, {pct}% of the P24 Eq.(2) phase peak (125 A).",
                    1,
                )
                text = text.replace(
                    "* No snubber, nonlinear Coss, detector delay, gate delay or dead time is added.",
                    f"* Added snubber is {cap_pf} pF in the {branch} branch; nonlinear Coss, "
                    "detector delay, gate delay and dead time remain absent.",
                    1,
                )
                text = text.replace(
                    ".include ../../04_component_models/",
                    ".include ../../../../paper_locked/04_component_models/",
                )
                text = text.replace(
                    ".param VIN=48 NP=4 NM=1 VO=1 FSW=5Meg",
                    ".param VIN=48 NP=4 NM=1 VO=1 FSW=5Meg\n"
                    f".param CSNUB={cap_pf}p",
                    1,
                )
                text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction}", 1)
                text = text.replace("CH1 vin a1 {CH_TOTAL}", f"CH1 vin a1 {ch_expr}", 1)
                text = text.replace("CL1 x1 0 {CL_TOTAL}", f"CL1 x1 0 {cl_expr}", 1)
                text = text.replace(
                    ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
                    ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
                    ".meas tran A41_CSNUB_F PARAM {CSNUB}\n"
                    f".meas tran A41_BRANCH_CODE PARAM {0 if branch == 'high_only' else 1}",
                    1,
                )
                path = OUT / f"{name}.cir"
                path.write_text(text)
                generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
