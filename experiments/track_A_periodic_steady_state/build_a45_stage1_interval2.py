"""Generate A45's stage-1 (P24 interval 2, EPC2067 candidate) netlist.

Parent: paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir
Single changed variable: the two .include lines are swapped from the active
GS61008T device/commutation-capacitance libraries to the EPC2067 Table-3
candidate libraries (paper_locked/04_component_models/EPC2067_*.lib). Ron
values are intentionally left as the GS61008T-derived RHS/RLS expression
(see A45 BOUNDARY.md scope limitation: Table 3 does not give a validated Ron
model to swap in cleanly, so only Coss/parallel-count-for-capacitance
changes).

IL1_T1/VC1_T1/IL2_T1 are the R04D0 interval-1 handoff state. A45 stage 0
reproduced R04D0's committed IL1_MAX/VC1_END/IL2_AT_TON values exactly
(interval 1 has no commutation-capacitance element, so it cannot depend on
the GS61008T-vs-EPC2067 choice); the same literal values are therefore
carried forward unchanged, not re-derived by hand.
"""

from __future__ import annotations

from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
TRACK = Path(__file__).resolve().parent
PARENT = (
    PROJECT / "paper_locked/02_ectc2024_main/spice/"
    "R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir"
)
OUT = (
    TRACK
    / "A45_epc2067_table3_candidate_commutation"
    / "A45_stage1_interval2_EPC2067_to_IL1_zero.cir"
)

HEADER_OLD = "* R04D2A - P24 interval 2, ending at iL1=0 per P24"
HEADER_NEW = (
    "* A45 stage 1 - P24 interval 2, EPC2067 Table-3 candidate commutation cap\n"
    "* PARENT: R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir. SINGLE CHANGED\n"
    "* VARIABLE: .include swapped from GS61008T_*.lib to EPC2067_*.lib (2024\n"
    "* Table 3's nP=4/nM=4 row: 2 parallel HS + 3 parallel LS EPC2067, NOT yet\n"
    "* confirmed to be the Sec.II-B ZVS-mechanism device -- see A45 BOUNDARY.md).\n"
    "* Ron is intentionally left at the GS61008T-derived RHS/RLS value; Table 3\n"
    "* gives no validated Ron model to swap in, so only Coss/parallel-count-for-\n"
    "* capacitance changes here (declared scope limitation, not an oversight)."
)

DEVICE_NOTE_OLD = (
    "* P25 Table III population plus GS61008T datasheet typical values are used to\n"
    "* make the state executable: CH=385 pF, CL=770 pF, low-side Ron=3.5 mOhm."
)
DEVICE_NOTE_NEW = (
    "* EPC2067 datasheet typical values (2024 Table 3 population: NHS=2, NLS=3)\n"
    "* are used for the commutation capacitance only: CH_TOTAL=3720 pF,\n"
    "* CL_TOTAL=5580 pF. Ron remains the GS61008T-derived RHS/RLS expression\n"
    "* (scope limitation, see header)."
)

INCLUDE_OLD = (
    ".include ../../04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../04_component_models/GS61008T_commutation_capacitance.lib"
)
INCLUDE_NEW = (
    ".include ../../../paper_locked/04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../../paper_locked/04_component_models/EPC2067_typical_params.lib\n"
    ".include ../../../paper_locked/04_component_models/EPC2067_commutation_capacitance.lib"
)

# EPC2067_commutation_capacitance.lib defines its own NHS=2/NLS=3 (the
# Table-3 EPC2067 parallel count), which would silently change RHS/RLS too if
# the original ".param RHS={GS61008T_RDS_TYP_25C/NHS} ..." formula were kept,
# because that formula reads whichever NHS/NLS the included commutation-
# capacitance library last defined. Per BOUNDARY.md's declared scope
# limitation ("keep Ron as-is, only swap Coss/parallel-count-for-
# capacitance"), RHS/RLS are instead frozen to the exact literal GS61008T
# 1-HS/2-LS values R04D2A already used (7 mOhm / 3.5 mOhm), independent of
# whichever capacitance library's NHS/NLS is in scope.
RHS_RLS_OLD = (
    ".param RHS={GS61008T_RDS_TYP_25C/NHS} RLS={GS61008T_RDS_TYP_25C/NLS}"
)
RHS_RLS_NEW = (
    "* Ron frozen at the GS61008T 1-HS/2-LS values regardless of the EPC2067\n"
    "* capacitance library's own NHS=2/NLS=3 (declared scope limitation).\n"
    ".param RHS={GS61008T_RDS_TYP_25C/1} RLS={GS61008T_RDS_TYP_25C/2}"
)


def build() -> Path:
    text = PARENT.read_text()
    for old in (HEADER_OLD, DEVICE_NOTE_OLD, INCLUDE_OLD, RHS_RLS_OLD):
        assert old in text, f"parent text changed, missing:\n{old}"
    text = text.replace(HEADER_OLD, HEADER_NEW, 1)
    text = text.replace(DEVICE_NOTE_OLD, DEVICE_NOTE_NEW, 1)
    text = text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
    text = text.replace(RHS_RLS_OLD, RHS_RLS_NEW, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    return OUT


if __name__ == "__main__":
    print(build())
