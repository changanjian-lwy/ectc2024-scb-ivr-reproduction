"""Generate R04E7's voltage-RATIO-gated EPE2019 3-state charge-redistribution
ladder-bootstrap grid.

PARENT: R04E6 (experiments/track_B_zero_start_extension/
R04E6_epe2019_charge_redistribution_startup/). R04E6 implemented the SAME
EPE2019 Fig. 5 three-state sequence (state (a): charge C1 alone via H1+L1;
state (b): redistribute C1<->C2 via H2+L1+L2; state (c): redistribute
C2<->C3 via H3+L2+L3) -- that switch truth table is reused UNCHANGED here,
per this project's instruction (it was independently derived from this
project's own topology and cross-checked against the source figure in
R04E6/BOUNDARY.md Sections 5-6; not re-derived).

THE SINGLE CONCEPTUAL CHANGE relative to R04E6: R04E6 gated each state by a
FIXED HOLD TIME (TH, swept as a sensitivity axis) and a FIXED CYCLE COUNT
(NCYC). R04E6's own finding was that this blind repetition makes the ladder
error WORSE with more cycles (states (b)/(c) are unbiased pairwise
equalizers with no mechanism favoring the 3:2:1 target ratio). R04E7
replaces the fixed-time gating with VOLTAGE-RATIO gating implemented with
this project's own `.machine`/`.state`/`.rule` construct (matching
R04D3A/R04E3/R04E5's established convention for physical-event-gated
switching):

  - state (a) exits when V(C1) >= 36 V (the final target, gated directly --
    see BOUNDARY.md for the charge-conservation reasoning on why a single
    pass cannot reach the target and why re-entering state (a) on a later
    cycle still works).
  - state (b) exits when 2*V(C1) <= 3*V(C2), i.e. V(C1)/V(C2) has reached
    the target ratio 3/2 -- self-correcting regardless of C1's actual
    present voltage.
  - state (c) exits when V(C2) <= 2*V(C3), i.e. V(C2)/V(C3) has reached the
    target ratio 2/1.
  - the whole (a)-(b)-(c) cycle repeats, driven by measured state, until all
    three absolute voltages are simultaneously within a swept tolerance
    band of 36/24/12 V, or a safety cap on total simulated time is hit.

See BOUNDARY.md for: the charge-conservation check, the borrowed-fact
table, the tolerance-band/safety-cap definitions and their justification,
and prohibited claims.

Free sensitivity axis: TOL (tolerance band half-width, as a fraction of
each target) in {0.02, 0.05, 0.10} (+/-2%, +/-5%, +/-10%). The safety cap
TCAP_TOTAL=50 us is fixed across the grid (not swept) -- see BOUNDARY.md
for why 50 us was chosen (empirically, from an untracked diagnostic run
described there, convergence at the loosest and tightest tested tolerances
both complete inside ~15 us, so 50 us is a >3x margin, not a tuned value).
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E7_ratio_gated_charge_redistribution_startup"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

TOL_LIST = (0.02, 0.05, 0.10)
TCAP_TOTAL = 50e-6  # SENSITIVITY_ONLY safety cap, fixed across the grid.
NCYC_MEAS = 50  # number of per-cycle .meas checkpoints generated (reporting
# resolution only -- the actual stop condition is TCAP_TOTAL/convergence,
# not a cycle counter in the netlist itself; see BOUNDARY.md Section 6).

VGATE = 5.0
TARGET1, TARGET2, TARGET3 = 36.0, 24.0, 12.0


def tol_tag(tol: float) -> str:
    return f"{tol * 100:g}pct".replace(".", "p")


def case_id(tol: float) -> str:
    return f"r04e7_tol_{tol_tag(tol)}"


TEMPLATE = """\
* R04E7 - voltage-ratio-gated EPE2019 3-state charge-redistribution ladder
* bootstrap ({case_id})
* SENSITIVITY CASE: TOL=+/-{tol_pct:g}% of each target (36/24/12 V),
* TCAP_TOTAL={tcap_us:g} us safety cap (fixed across the grid).
* PARENT: R04E6_epe2019_charge_redistribution_startup (same truth table,
* same power stage, same Cfly/Cout). SINGLE CHANGE: R04E6's fixed hold-time
* PWL gate sequencer is replaced by a voltage-ratio-gated .machine, per
* BOUNDARY.md. See that file for the charge-conservation reasoning check,
* the borrowed-fact table, and the tolerance/cap justification.
* Power-stage connectivity (SH1-4/SL1-4/CS1-3/L1-4 node names) is copied
* UNCHANGED from R04E6's SCB4P_P24_R04E6 subcircuit (itself copied from
* R04E3's already-validated P24 four-phase connectivity).
* True zero initial energy on every capacitor and inductor (ic=0, UIC).
* SCOPE: ladder bootstrap ONLY -- no PWM, no P24 steady-state ZVS admission
* chain, no Vout regulation attempt, no four-phase claim (H4/L4 off).

.include "{gs_lib}"
.param VIN=48 VOUT_REF=1 POUT_MODULE=250 NP=4 NM=4
.param LPHASE=1.466666666666667n CFLY={{4*10u+2*4.7u+2*2.2u}}
.param COUT={{8*220u+32*47u+64*22u}} RLOAD={{VOUT_REF*VOUT_REF/POUT_MODULE}}
.param CH={{GS61008T_COTR_0_50V}} CL={{2*GS61008T_COTR_0_50V}}
.param RHS={{GS61008T_RDS_TYP_25C}} RLS={{GS61008T_RDS_TYP_25C/2}}
.param RLDAMP=1u

.param TOL={tol:g}
.param TARGET1={target1:g} TARGET2={target2:g} TARGET3={target3:g}
.param LO1={{TARGET1*(1-TOL)}} HI1={{TARGET1*(1+TOL)}}
.param LO2={{TARGET2*(1-TOL)}} HI2={{TARGET2*(1+TOL)}}
.param LO3={{TARGET3*(1-TOL)}} HI3={{TARGET3*(1+TOL)}}
.param TCAP_TOTAL={tcap:.6e}
.param VGATE={vgate:g}

VRAIL vin 0 {{VIN}}
CCO out 0 {{COUT}} ic=0
RLOAD_MAIN out 0 {{RLOAD}}
XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd SCB4P_P24_R04E7

BVC1 vc1_mon 0 V=V(xmod:a1,xmod:x1)
BVC2 vc2_mon 0 V=V(xmod:a2,xmod:x2)
BVC3 vc3_mon 0 V=V(xmod:a3,xmod:x3)
RVC1 vc1_mon 0 1k
RVC2 vc2_mon 0 1k
RVC3 vc3_mon 0 1k

* Voltage-ratio-gated 3-state machine (THE mechanism change vs R04E6).
* STATE_A exit: V(C1)>=TARGET1 (final target, direct comparator -- see
*   BOUNDARY.md for why a single pass cannot reach 36/24/12 and why
*   re-entering STATE_A on a later cycle still recharges C1 correctly).
* STATE_B exit: 2*V(C1)<=3*V(C2), i.e. V(C1)/V(C2) has reached 3/2.
* STATE_C exit: V(C2)<=2*V(C3), i.e. V(C2)/V(C3) has reached 2/1; branches
*   to DONE if all three absolute voltages are within the tolerance band,
*   else loops back to STATE_A for another cycle.
* Every state also has a `time>=TCAP_TOTAL` escape to CAPPED, checked with
* priority over the local exit condition (listed first) -- this is the
* single GLOBAL safety-cap fallback (see BOUNDARY.md Section 6 for why one
* global cap was used instead of three separate per-state timers).
.machine 1p
.state STATE_A 0
.state STATE_B 1
.state STATE_C 2
.state DONE 3
.state CAPPED 4
.rule STATE_A CAPPED time>=TCAP_TOTAL
.rule STATE_A STATE_B V(vc1_mon)>=TARGET1
.rule STATE_B CAPPED time>=TCAP_TOTAL
.rule STATE_B STATE_C 2*V(vc1_mon)<=3*V(vc2_mon)
.rule STATE_C CAPPED time>=TCAP_TOTAL
.rule STATE_C DONE (V(vc2_mon)<=2*V(vc3_mon)) & (V(vc1_mon)>=LO1) & (V(vc1_mon)<=HI1) & (V(vc2_mon)>=LO2) & (V(vc2_mon)<=HI2) & (V(vc3_mon)>=LO3) & (V(vc3_mon)<=HI3)
.rule STATE_C STATE_A (V(vc2_mon)<=2*V(vc3_mon)) & ((V(vc1_mon)<LO1)|(V(vc1_mon)>HI1)|(V(vc2_mon)<LO2)|(V(vc2_mon)>HI2)|(V(vc3_mon)<LO3)|(V(vc3_mon)>HI3))
.output (gh1_cmd) VGATE*(state==STATE_A)
.output (gl1_cmd) VGATE*((state==STATE_A)+(state==STATE_B))
.output (gh2_cmd) VGATE*(state==STATE_B)
.output (gl2_cmd) VGATE*((state==STATE_B)+(state==STATE_C))
.output (gh3_cmd) VGATE*(state==STATE_C)
.output (gl3_cmd) VGATE*(state==STATE_C)
.output (state_mon) state
.output (cyc_end_flag) VGATE*(state==STATE_C)
.endmachine

RSTATE state_mon 0 1k
RCYCFLAG cyc_end_flag 0 1k
RGH1 gh1_cmd 0 1k
RGL1 gl1_cmd 0 1k
RGH2 gh2_cmd 0 1k
RGL2 gl2_cmd 0 1k
RGH3 gh3_cmd 0 1k
RGL3 gl3_cmd 0 1k

.meas tran STATE_FINAL FIND V(state_mon) AT {{TSTOP}}
.meas tran VC1_FINAL FIND V(vc1_mon) AT {{TSTOP}}
.meas tran VC2_FINAL FIND V(vc2_mon) AT {{TSTOP}}
.meas tran VC3_FINAL FIND V(vc3_mon) AT {{TSTOP}}
.meas tran VOUT_FINAL FIND V(out) AT {{TSTOP}}
.meas tran T_TERMINAL WHEN V(state_mon)=2.5 RISE=1
.meas tran IL1_MAX MAX I(XMOD:L1)
.meas tran IL1_MIN MIN I(XMOD:L1)
.meas tran ICS1_MAX MAX I(XMOD:CS1) FROM 1n TO {{TSTOP}}
.meas tran ICS1_MIN MIN I(XMOD:CS1) FROM 1n TO {{TSTOP}}
.meas tran ICS2_MAX MAX I(XMOD:CS2) FROM 1n TO {{TSTOP}}
.meas tran ICS2_MIN MIN I(XMOD:CS2) FROM 1n TO {{TSTOP}}
.meas tran ICS3_MAX MAX I(XMOD:CS3) FROM 1n TO {{TSTOP}}
.meas tran ICS3_MIN MIN I(XMOD:CS3) FROM 1n TO {{TSTOP}}
{cycle_meas}

.options plotwinsize=0 reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt cshunt=1e-15
.save V(vc1_mon) V(vc2_mon) V(vc3_mon) V(state_mon) V(cyc_end_flag) V(out) I(XMOD:L1) I(XMOD:L2) I(XMOD:L3) I(XMOD:CS1) I(XMOD:CS2) I(XMOD:CS3)
.tran 0 {{TSTOP}} 0 1n UIC

.subckt SCB4P_P24_R04E7 vin out g gh1_in gl1_in gh2_in gl2_in gh3_in gl3_in
BGH1 gh1 g V=V(gh1_in,g)
BGL1 gl1 g V=V(gl1_in,g)
BGH2 gh2 g V=V(gh2_in,g)
BGL2 gl2 g V=V(gl2_in,g)
BGH3 gh3 g V=V(gh3_in,g)
BGL3 gl3 g V=V(gl3_in,g)
VGH4 gh4 g 0
VGL4 gl4 g 0

SH1 vin a1 gh1 g SWH
CH1 vin a1 {{CH}} ic=0
CS1 a1 x1 {{CFLY}} ic=0
CL1 x1 g {{CL}} ic=0
SL1 x1 g gl1 g SWL
L1 x1 out {{LPHASE}} Rser={{RLDAMP}} ic=0
SH2 a1 a2 gh2 g SWH
CS2 a2 x2 {{CFLY}} ic=0
SL2 x2 g gl2 g SWL
L2 x2 out {{LPHASE}} Rser={{RLDAMP}} ic=0
SH3 a2 a3 gh3 g SWH
CS3 a3 x3 {{CFLY}} ic=0
SL3 x3 g gl3 g SWL
L3 x3 out {{LPHASE}} Rser={{RLDAMP}} ic=0
SH4 a3 x4 gh4 g SWH
SL4 x4 g gl4 g SWL
L4 x4 out {{LPHASE}} Rser={{RLDAMP}} ic=0

RNUM_A1 a1 g 1Meg
RNUM_X1 x1 g 1Meg
RNUM_A2 a2 g 1Meg
RNUM_X2 x2 g 1Meg
RNUM_A3 a3 g 1Meg
RNUM_X3 x3 g 1Meg
RNUM_X4 x4 g 1Meg
.model SWH SW(Ron={{RHS}} Roff=1T Vt=2.5 Vh=0)
.model SWL SW(Ron={{RLS}} Roff=1T Vt=2.5 Vh=0)
.ends SCB4P_P24_R04E7
.end
"""


def render(tol: float) -> str:
    tstop = TCAP_TOTAL * 1.05
    cyc_lines = []
    for j in range(1, NCYC_MEAS + 1):
        cyc_lines.append(
            f".meas tran VC1_CYC{j} FIND V(vc1_mon) WHEN V(cyc_end_flag)=2.5 FALL={j}"
        )
        cyc_lines.append(
            f".meas tran VC2_CYC{j} FIND V(vc2_mon) WHEN V(cyc_end_flag)=2.5 FALL={j}"
        )
        cyc_lines.append(
            f".meas tran VC3_CYC{j} FIND V(vc3_mon) WHEN V(cyc_end_flag)=2.5 FALL={j}"
        )
        cyc_lines.append(
            f".meas tran T_CYC{j} WHEN V(cyc_end_flag)=2.5 FALL={j}"
        )
    return TEMPLATE.format(
        case_id=case_id(tol),
        tol=tol,
        tol_pct=tol * 100,
        tcap_us=TCAP_TOTAL * 1e6,
        tcap=TCAP_TOTAL,
        gs_lib=GS_LIB,
        target1=TARGET1,
        target2=TARGET2,
        target3=TARGET3,
        vgate=VGATE,
        cycle_meas="\n".join(cyc_lines),
    ).replace("{TSTOP}", f"{tstop:.6e}")


def build() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for tol in TOL_LIST:
        text = render(tol)
        path = CASES / f"{case_id(tol)}.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
