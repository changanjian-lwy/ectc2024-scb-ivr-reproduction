"""Generate A45's stage-2 (P24 interval 3, EPC2067 candidate) coarse sweep.

Parent: paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir
(the same parent A42_zero_snubber_negative_current_threshold's coarse sweep
used). Mirrors build_a42_negative_current_threshold.py's exact grid,
percentage-to-source-label mapping and NEG_FRAC substitution mechanism.

Two things differ from A42, both declared as the single changed variable
(the EPC2067 commutation-capacitance swap) and its unavoidable chained
consequence (a new interval-2 handoff state):

1. The two .include lines are swapped from GS61008T_*.lib to EPC2067_*.lib,
   with Ron frozen at the GS61008T 1-HS/2-LS literal values exactly as A45
   stage 1 did (BOUNDARY.md scope limitation: no validated EPC2067 Ron
   model).
2. VC1_T2/VX1_T2/VA1_T2 are replaced with A45 stage 1's own measured
   handoff state (read from A45_stage1_interval2_EPC2067_to_IL1_zero.log),
   not the old GS61008T-chain values R04D3A/A42 used. Reusing the old
   handoff state would be physically wrong: CL_TOTAL participates in
   interval 2's commutation too, so the state at iL1=0 is itself a function
   of which device's capacitance is in use.
"""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
HERE = TRACK / "A45_epc2067_table3_candidate_commutation"
OUT = HERE / "cases"
NEGATIVE_PERCENTAGES = tuple(range(1, 11))

# A45 stage 1's measured EPC2067-chain handoff state (A45_stage1_interval2_
# EPC2067_to_IL1_zero.log: p24_c1_at_il1_zero / p24_x1_at_il1_zero /
# p24_a1_at_il1_zero), replacing R04D3A's GS61008T-chain literals.
VC1_T2_EPC2067 = 36.0201391787
VX1_T2_EPC2067 = -7.76858225411e-05
VA1_T2_EPC2067 = 36.0200614929

HEADER_OLD = (
    "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS"
)

DEVICE_NOTE_OLD = (
    "* P25 Table III population and GS61008T CO(TR) scalar are retained from R04D2.\n"
    "* No snubber, nonlinear Coss, detector delay, gate delay or dead time is added."
)
DEVICE_NOTE_NEW = (
    "* EPC2067 Table-3 candidate commutation capacitance (NHS=2/NLS=3:\n"
    "* CH_TOTAL=3720 pF, CL_TOTAL=5580 pF), chained from A45 stage 1's own\n"
    "* measured interval-2 handoff state. Ron is frozen at the GS61008T\n"
    "* 1-HS/2-LS literal values (scope limitation, see A45 BOUNDARY.md).\n"
    "* No snubber, nonlinear Coss, detector delay, gate delay or dead time is added."
)

INCLUDE_OLD = (
    ".include ../../04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../04_component_models/GS61008T_commutation_capacitance.lib"
)
INCLUDE_NEW = (
    ".include ../../../../paper_locked/04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../../../paper_locked/04_component_models/EPC2067_typical_params.lib\n"
    ".include ../../../../paper_locked/04_component_models/EPC2067_commutation_capacitance.lib"
)

STATE_OLD = (
    ".param VC1_T2=36.0193959392 VX1_T2=-9.6476751536u VA1_T2=36.0193862915"
)
STATE_NEW = (
    f".param VC1_T2={VC1_T2_EPC2067!r} VX1_T2={VX1_T2_EPC2067!r} "
    f"VA1_T2={VA1_T2_EPC2067!r}"
)

RHS_RLS_OLD = "RHS={GS61008T_RDS_TYP_25C/NHS} RLS={GS61008T_RDS_TYP_25C/NLS}"
RHS_RLS_NEW = "RHS={GS61008T_RDS_TYP_25C/1} RLS={GS61008T_RDS_TYP_25C/2}"


def source_label(pct: float) -> str:
    if pct <= 2:
        return "P24_EXPLICIT"
    if pct <= 4:
        return "DIAGNOSTIC_BRIDGE"
    return "P25_SUPPLEMENT"


def _base_text() -> str:
    text = PARENT.read_text()
    for old in (HEADER_OLD, DEVICE_NOTE_OLD, INCLUDE_OLD, STATE_OLD, RHS_RLS_OLD):
        assert old in text, f"parent text changed, missing:\n{old}"
    text = text.replace(
        HEADER_OLD,
        "* A45 stage 2 - P24 interval 3, EPC2067 Table-3 candidate commutation cap",
        1,
    )
    text = text.replace(DEVICE_NOTE_OLD, DEVICE_NOTE_NEW, 1)
    text = text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
    text = text.replace(STATE_OLD, STATE_NEW, 1)
    text = text.replace(RHS_RLS_OLD, RHS_RLS_NEW, 1)
    return text


def build() -> list[Path]:
    source = _base_text()
    OUT.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    for pct in NEGATIVE_PERCENTAGES:
        fraction = pct / 100
        label = source_label(pct)
        text = source
        text = text.replace(
            "* A45 stage 2 - P24 interval 3, EPC2067 Table-3 candidate commutation cap",
            f"* A45 stage 2 - EPC2067 candidate {pct}% negative-current row ({label})",
            1,
        )
        text = text.replace(
            "* selected sensitivity row: {pct}% of the P24 Eq.(2) phase peak (125 A).",
            "",
            1,
        )
        text = text.replace(
            "* published lower boundary, 1% of the P24 Eq.(2) phase peak (125 A).",
            f"* selected sensitivity row: {pct}% of the P24 Eq.(2) phase peak (125 A).",
            1,
        )
        text = text.replace("NEG_FRAC=0.01", f"NEG_FRAC={fraction:.2f}", 1)
        text = text.replace(
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}",
            ".meas tran P24_NEGATIVE_TARGET PARAM {INEG}\n"
            f".meas tran A45_SOURCE_CODE PARAM "
            f"{0 if label == 'P24_EXPLICIT' else 1 if label == 'DIAGNOSTIC_BRIDGE' else 2}",
            1,
        )
        path = OUT / f"a45_{pct:02d}pct_epc2067.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
