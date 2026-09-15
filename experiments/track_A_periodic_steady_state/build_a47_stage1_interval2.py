"""Generate A47's stage-1 (P24 interval 2, nonlinear Coss(V)) netlist.

Parent: paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir
(the same parent A42/A45's own stage 1 used).

SINGLE CHANGED VARIABLE: the constant-capacitance CH1/CL1 devices
(`CH1 vin a1 {CH_TOTAL} IC=...`, `CL1 x1 0 {CL_TOTAL} IC=...`, both plain
value-only LTspice capacitors reading a single fixed Co(tr) value from
GS61008T_commutation_capacitance.lib) are replaced with nonlinear
charge-controlled capacitors implementing the digitized, fitted GS61008T
Coss(V) curve from GS61008T_nonlinear_coss.lib:

    Coss(V) = GS61008T_NL_CFLOOR + GS61008T_NL_A/(1+(V/GS61008T_NL_VKNEE)^2)

LTspice's native `Cxxx n1 n2 Q=<expr>` nonlinear-capacitor device was tried
first and found to pathologically collapse its own timestep to ~1e-17s for
this Coss(V) shape (confirmed both for this atan-based Q(V) and for an
alternative power-law Q(V), with a floating-node-safety leak resistor
present and with looser solver tolerances -- see A47 BOUNDARY.md
"LTspice implementation note"). The numerically robust, LTspice-documented
alternative used instead is a behavioral current source implementing the
same physics via the ddt() time-derivative operator:

    B<name> n1 n2 I=ddt(Q(V(n1,n2)))

which is electrically identical to a capacitor of charge Q(V) between n1
and n2, and was validated in a standalone test circuit (see
validate_nlcap_charging.py) against direct numerical integration of the
same Coss(V), matching to <0.0001%, before being wired into this chain.

Wiring a single such B-source carrying the FULL Q(V) (floor + nonlinear
term) directly into CH1/CL1's place still failed to converge here, even
though the isolated single-node test worked: CH1/CL1 sit in a loop made
only of capacitors and an ideal voltage source
(`CH1||SH1 + CF1 + CL1||SL1`, VIN_SRC ideal), a classically stiff SPICE
topology that native capacitors handle via a dedicated companion-
conductance model but which a generic ddt()-based B-source apparently
cannot when it must represent the entire capacitance including a large
constant floor. The construction actually used splits each Coss(V) into
its constant floor (a real, native linear capacitor -- which both restores
a proper companion conductance to the stiff loop AND is what LTspice's UIC
transient start actually honors for a node's initial voltage; a bare
top-level `.ic V(node)=...` directive was tried first and found NOT to be
honored at t=0 in this circuit) plus the remaining bounded nonlinear
correction term (a ddt() B-source, now only carrying
`A_COSS*V_KNEE*atan(V/V_KNEE)`, which saturates rather than diverging).
This is mathematically identical to the single-source form. Convergence
still required switching the integrator from the default trapezoidal
method to Gear's method (`.options ... method=gear`) -- a solver-selection
change, not a circuit or physics change. See A47 BOUNDARY.md "LTspice
implementation note" for the full diagnostic trail (both failed
intermediate attempts included).

Ron (RHS/RLS) is intentionally left completely unchanged from R04D2A/A42's
own GS61008T values (7 mOhm / 1 high-side, 3.5 mOhm / 2 parallel low-side);
this experiment tests only the Coss(V) shape, not any Ron or population
change. RHS/RLS are hardcoded to the literal 1-HS/2-LS divisors (not read
from any commutation-capacitance library's NHS/NLS) so that removing the
old GS61008T_commutation_capacitance.lib include cannot silently change Ron
-- the same defensive pattern A45 already used for its own, different,
reason (there, guarding against EPC2067's NHS/NLS; here, guarding against
simply having no such library in scope at all after its removal).

IL1_T1/VC1_T1/IL2_T1 are the R04D0 interval-1 handoff state, carried
forward unchanged (interval 1 has no commutation-capacitance element at
all, so it cannot depend on the constant-vs-nonlinear Coss(V) choice --
confirmed again by A47 stage 0 exactly reproducing R04D0's committed
values).
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
    / "A47_nonlinear_coss_local_zvs"
    / "A47_stage1_interval2_GS61008T_nonlinear.cir"
)

HEADER_OLD = "* R04D2A - P24 interval 2, ending at iL1=0 per P24"
HEADER_NEW = (
    "* A47 stage 1 - P24 interval 2, nonlinear GS61008T Coss(V) commutation cap\n"
    "* PARENT: R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir. SINGLE CHANGED\n"
    "* VARIABLE: CH1/CL1 constant-Co(tr) capacitors replaced with a nonlinear,\n"
    "* digitized-and-fitted Coss(V) charge source (see A47 BOUNDARY.md). Ron\n"
    "* (RHS/RLS) is unchanged from the GS61008T 1-HS/2-LS values."
)

DEVICE_NOTE_OLD = (
    "* DEVICE PLUG-IN, NOT P24 DEVICE EVIDENCE\n"
    "* P25 Table III population plus GS61008T datasheet typical values are used to\n"
    "* make the state executable: CH=385 pF, CL=770 pF, low-side Ron=3.5 mOhm.\n"
    "* No external snubber, nonlinear Coss, detector delay or dead time is included."
)
DEVICE_NOTE_NEW = (
    "* DEVICE PLUG-IN, NOT P24 DEVICE EVIDENCE\n"
    "* P25 Table III population (1 high-side, 2 parallel low-side GS61008T),\n"
    "* Ron=3.5 mOhm low-side / 7 mOhm high-side, unchanged from R04D2A/A42.\n"
    "* Commutation capacitance is now the digitized, fitted nonlinear Coss(V)\n"
    "* curve from GS61008T_nonlinear_coss.lib, not a constant Co(tr) scalar.\n"
    "* No external snubber, detector delay or dead time is included."
)

INCLUDE_OLD = (
    ".include ../../04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../04_component_models/GS61008T_commutation_capacitance.lib"
)
INCLUDE_NEW = (
    ".include ../../../paper_locked/04_component_models/GS61008T_typical_params.lib\n"
    ".include ../../../paper_locked/04_component_models/GS61008T_nonlinear_coss.lib"
)

RHS_RLS_OLD = (
    ".param RHS={GS61008T_RDS_TYP_25C/NHS} RLS={GS61008T_RDS_TYP_25C/NLS}"
)
RHS_RLS_NEW = (
    "* Ron frozen at the GS61008T 1-HS/2-LS literal divisors, independent of\n"
    "* whichever library happens to define NHS/NLS (defensive, see header).\n"
    ".param RHS={GS61008T_RDS_TYP_25C/1} RLS={GS61008T_RDS_TYP_25C/2}"
)

CH_CL_OLD = (
    "SH1 vin a1 gh1 0 SWH\n"
    "CH1 vin a1 {CH_TOTAL} IC=0\n"
    "CF1 a1 x1 {CFLY} IC={VC1_T1}\n"
    "CL1 x1 0 {CL_TOTAL} IC={VX1_T1}\n"
    "SL1 x1 0 gl1 0 SWL"
)
CH_CL_NEW = (
    "SH1 vin a1 gh1 0 SWH\n"
    "* Split into a real linear floor capacitor (carries IC=, which is what\n"
    "* LTspice's UIC transient start actually honors for a node's initial\n"
    "* voltage -- a bare top-level .ic directive on a B-source-only node was\n"
    "* NOT honored at t=0, confirmed empirically) plus a ddt() B-source\n"
    "* carrying only the bounded nonlinear correction term. Mathematically\n"
    "* identical to a single Q=CFLOOR*V+A*VKNEE*atan(V/VKNEE) source; see\n"
    "* A47 BOUNDARY.md 'LTspice implementation note' for why this split (and\n"
    "* method=gear below) was needed for convergence.\n"
    "CH1LIN vin a1 {NHS_NL*GS61008T_NL_CFLOOR} IC=0\n"
    "BCH1 vin a1 I=ddt(NHS_NL*GS61008T_NL_A*GS61008T_NL_VKNEE"
    "*atan(V(vin,a1)/GS61008T_NL_VKNEE))\n"
    "CF1 a1 x1 {CFLY} IC={VC1_T1}\n"
    "CL1LIN x1 0 {NLS_NL*GS61008T_NL_CFLOOR} IC={VX1_T1}\n"
    "BCL1 x1 0 I=ddt(NLS_NL*GS61008T_NL_A*GS61008T_NL_VKNEE"
    "*atan(V(x1)/GS61008T_NL_VKNEE))\n"
    "SL1 x1 0 gl1 0 SWL"
)

OPTIONS_OLD = ".options reltol=1e-7 abstol=1e-10 chgtol=1e-16"
OPTIONS_NEW = (
    "* method=gear: the default trapezoidal integrator failed to converge\n"
    "* (timestep collapsed to ~1e-17s) on this nonlinear-Coss(V) stiff\n"
    "* capacitor-loop circuit; Gear's method converges normally. This is a\n"
    "* solver-selection change only, not a circuit/physics change -- see\n"
    "* A47 BOUNDARY.md 'LTspice implementation note'.\n"
    ".options reltol=1e-7 abstol=1e-10 chgtol=1e-16 method=gear"
)

MEAS_OLD = (
    ".meas tran CH_USED PARAM {CH_TOTAL}\n"
    ".meas tran CL_USED PARAM {CL_TOTAL}"
)
MEAS_NEW = (
    ".meas tran COSS_CFLOOR_USED PARAM {GS61008T_NL_CFLOOR}\n"
    ".meas tran COSS_A_USED PARAM {GS61008T_NL_A}\n"
    ".meas tran COSS_VKNEE_USED PARAM {GS61008T_NL_VKNEE}"
)


def _base_text() -> str:
    text = PARENT.read_text()
    for old in (HEADER_OLD, DEVICE_NOTE_OLD, INCLUDE_OLD, RHS_RLS_OLD, CH_CL_OLD, OPTIONS_OLD, MEAS_OLD):
        assert old in text, f"parent text changed, missing:\n{old}"
    text = text.replace(HEADER_OLD, HEADER_NEW, 1)
    text = text.replace(DEVICE_NOTE_OLD, DEVICE_NOTE_NEW, 1)
    text = text.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
    text = text.replace(RHS_RLS_OLD, RHS_RLS_NEW, 1)
    text = text.replace(CH_CL_OLD, CH_CL_NEW, 1)
    text = text.replace(OPTIONS_OLD, OPTIONS_NEW, 1)
    text = text.replace(MEAS_OLD, MEAS_NEW, 1)
    return text


def build() -> Path:
    text = _base_text()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    return OUT


if __name__ == "__main__":
    print(build())
