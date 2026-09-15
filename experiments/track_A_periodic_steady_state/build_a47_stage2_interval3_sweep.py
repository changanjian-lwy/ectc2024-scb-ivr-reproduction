"""Generate A47's stage-2 (P24 interval 3, nonlinear Coss(V)) coarse sweep.

Parent: paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir
(the same parent A42's and A45's own stage 2 used). Mirrors
build_a42_negative_current_threshold.py's / build_a45_stage2_interval3_sweep.py's
exact grid, percentage-to-source-label mapping and NEG_FRAC substitution
mechanism.

SINGLE CHANGED VARIABLE (plus its unavoidable chained consequence):

1. CH1/CL1 constant-Co(tr) capacitors are replaced with the same nonlinear,
   digitized-and-fitted GS61008T Coss(V) B-source/ddt() construction A47
   stage 1 used (see build_a47_stage1_interval2.py for the full mechanism
   and why: LTspice's native Q= nonlinear-capacitor device was tried first
   and pathologically failed to converge for this Coss(V) shape).
2. VC1_T2/VX1_T2/VA1_T2 are replaced with A47 stage 1's OWN measured handoff
   state (read from A47_stage1_interval2_GS61008T_nonlinear.log), not
   R04D3A/A42's linear-Co(tr)-chain values. This is the same chained-state
   consequence A45 already documented for its own device swap: CL1
   participates in interval 2's Coss discharge as iL1 falls to zero, so the
   state at iL1=0 is itself a function of which commutation-capacitance
   model is in use.

Ron (RHS/RLS) remains exactly the GS61008T 1-HS/2-LS values throughout,
unchanged from R04D3A/A42.
"""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D3A_P24_interval3_same_phase_ZVS.cir"
)
HERE = TRACK / "A47_nonlinear_coss_local_zvs"
OUT = HERE / "cases"
NEGATIVE_PERCENTAGES = tuple(range(1, 11))

# A47 stage 1's own measured nonlinear-Coss(V)-chain handoff state, read
# from A47_stage1_interval2_GS61008T_nonlinear.log
# (p24_c1_at_il1_zero / p24_x1_at_il1_zero / p24_a1_at_il1_zero), replacing
# R04D3A/A42's constant-Co(tr)-chain literals
# (VC1_T2=36.0193959392 VX1_T2=-9.6476751536u VA1_T2=36.0193862915).
VC1_T2_NL = 36.0194477751
VX1_T2_NL = -1.57071955599e-05
VA1_T2_NL = 36.0194320679

HEADER_OLD = (
    "* R04D3A - P24 interval 3, same-phase negative current to QH1 ZVS"
)

DEVICE_NOTE_OLD = (
    "* P25 Table III population and GS61008T CO(TR) scalar are retained from R04D2.\n"
    "* No snubber, nonlinear Coss, detector delay, gate delay or dead time is added."
)
DEVICE_NOTE_NEW = (
    "* P25 Table III population (1 HS/2 LS GS61008T) retained from R04D2A/A42.\n"
    "* Commutation capacitance is the digitized, fitted nonlinear Coss(V) curve\n"
    "* from GS61008T_nonlinear_coss.lib, chained from A47 stage 1's own measured\n"
    "* interval-2 handoff state. No snubber, detector delay, gate delay or dead\n"
    "* time is added."
)

INCLUDE_OLD = (
    ".include ../../04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../04_component_models/GS61008T_commutation_capacitance.lib"
)
INCLUDE_NEW = (
    ".include ../../../../paper_locked/04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../../../paper_locked/04_component_models/GS61008T_nonlinear_coss.lib"
)

STATE_OLD = (
    ".param VC1_T2=36.0193959392 VX1_T2=-9.6476751536u VA1_T2=36.0193862915"
)
STATE_NEW = (
    f".param VC1_T2={VC1_T2_NL!r} VX1_T2={VX1_T2_NL!r} VA1_T2={VA1_T2_NL!r}"
)

RHS_RLS_OLD = "RHS={GS61008T_RDS_TYP_25C/NHS} RLS={GS61008T_RDS_TYP_25C/NLS}"
RHS_RLS_NEW = "RHS={GS61008T_RDS_TYP_25C/1} RLS={GS61008T_RDS_TYP_25C/2}"

CH_CL_OLD = (
    "SH1 vin a1 gh1 0 SWH\n"
    "CH1 vin a1 {CH_TOTAL} IC={VIN-VA1_T2}\n"
    "CF1 a1 x1 53.8u IC={VC1_T2}\n"
    "CL1 x1 0 {CL_TOTAL} IC={VX1_T2}\n"
    "SL1 x1 0 gl1 0 SWL"
)
CH_CL_NEW = (
    "SH1 vin a1 gh1 0 SWH\n"
    "* Split floor/nonlinear-correction construction, see A47 stage 1\n"
    "* (build_a47_stage1_interval2.py) and BOUNDARY.md 'LTspice\n"
    "* implementation note' for why (native Q=cap and a single full-Q(V)\n"
    "* B-source both failed to converge in this stiff capacitor-loop\n"
    "* topology; this split plus method=gear below converges normally).\n"
    "CH1LIN vin a1 {NHS_NL*GS61008T_NL_CFLOOR} IC={VIN-VA1_T2}\n"
    "BCH1 vin a1 I=ddt(NHS_NL*GS61008T_NL_A*GS61008T_NL_VKNEE"
    "*atan(V(vin,a1)/GS61008T_NL_VKNEE))\n"
    "CF1 a1 x1 53.8u IC={VC1_T2}\n"
    "CL1LIN x1 0 {NLS_NL*GS61008T_NL_CFLOOR} IC={VX1_T2}\n"
    "BCL1 x1 0 I=ddt(NLS_NL*GS61008T_NL_A*GS61008T_NL_VKNEE"
    "*atan(V(x1)/GS61008T_NL_VKNEE))\n"
    "SL1 x1 0 gl1 0 SWL"
)

OPTIONS_OLD = ".options reltol=1e-7 abstol=1e-10 chgtol=1e-16"
# method=gear: same reason as stage 1 (see build_a47_stage1_interval2.py and
# BOUNDARY.md). This is the base/tier-1 solver-tolerance tier; a small
# minority of rows do not converge promptly under it and are escalated to a
# looser tier by run_a47_sweep.py's adaptive retry (see that script and
# BOUNDARY.md "Solver tolerance" for exactly which rows needed escalation
# and the direct tier-vs-tier comparison confirming the physics answer does
# not change). This is a disclosed solver-efficiency choice, not a physics
# change: the standalone ddt() validation (validate_nlcap_charging.py)
# already showed <0.0001% error even at much tighter tolerances than any
# tier used here, all of which remain far tighter than the several-percent
# digitization/fit uncertainty that dominates this experiment's overall
# accuracy.
OPTIONS_NEW = ".options reltol=1e-5 abstol=1e-9 method=gear"


def source_label(pct: float) -> str:
    if pct <= 2:
        return "P24_EXPLICIT"
    if pct <= 4:
        return "DIAGNOSTIC_BRIDGE"
    return "P25_SUPPLEMENT"


def _base_text() -> str:
    text = PARENT.read_text()
    for old in (HEADER_OLD, DEVICE_NOTE_OLD, INCLUDE_OLD, STATE_OLD, RHS_RLS_OLD, CH_CL_OLD, OPTIONS_OLD):
        assert old in text, f"parent text changed, missing:\n{old}"
    text = text.replace(
        HEADER_OLD,
        "* A47 stage 2 - P24 interval 3, nonlinear GS61008T Coss(V) commutation cap",
        1,
    )
    text = text.replace(DEVICE_NOTE_OLD, DEVICE_NOTE_NEW, 1)
    text = text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
    text = text.replace(STATE_OLD, STATE_NEW, 1)
    text = text.replace(RHS_RLS_OLD, RHS_RLS_NEW, 1)
    text = text.replace(CH_CL_OLD, CH_CL_NEW, 1)
    text = text.replace(OPTIONS_OLD, OPTIONS_NEW, 1)
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
            "* A47 stage 2 - P24 interval 3, nonlinear GS61008T Coss(V) commutation cap",
            f"* A47 stage 2 - nonlinear Coss(V) {pct}% negative-current row ({label})",
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
            f".meas tran A47_SOURCE_CODE PARAM "
            f"{0 if label == 'P24_EXPLICIT' else 1 if label == 'DIAGNOSTIC_BRIDGE' else 2}",
            1,
        )
        path = OUT / f"a47_{pct:02d}pct_nonlinear.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in build():
        print(generated_path)
