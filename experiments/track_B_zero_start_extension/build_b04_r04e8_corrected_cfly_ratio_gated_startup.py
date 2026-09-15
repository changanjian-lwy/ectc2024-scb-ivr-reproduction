"""Generate R04E8's corrected-Cfly voltage-ratio-gated EPE2019 3-state
charge-redistribution ladder-bootstrap grid.

PARENT: R04E7 (experiments/track_B_zero_start_extension/
R04E7_ratio_gated_charge_redistribution_startup/). R04E7 validated the
voltage-ratio-gated mechanism (state (a) exits at V(C1)>=36V, state (b) at
2*V(C1)<=3*V(C2), state (c) at V(C2)<=2*V(C3), cycle repeats until all
three voltages sit within TOL of 36/24/12 V or a safety cap is hit) using
Cfly=53.8 uF, the EPE2019 Table I component sum. That table is EPE2019's
own CSC-buck prototype parts list, a different, topologically modified
converter from the conventional SC buck P24 actually is (see
paper_locked/00_boundaries/CURRENT_ASSUMPTION_CROSSCHECK.md's "Flying
capacitor" row and paper_locked/00_boundaries/CFLY_FIRST_PRINCIPLES_ESTIMATE.md).
A first-principles re-derivation from P24's own operating point gives a
candidate range of ~0.6-8.7 uF, well below 53.8 uF.

THE SINGLE CHANGED VARIABLE relative to R04E7: CFLY, swept in
{1 uF, 3 uF, 8.7 uF} (representative low/mid/high points spanning the
derived 0.6-8.7 uF range; 8.7 uF is C3's own 1%-ripple figure, the most
conservative/largest end of the range). TOL is held FIXED at 2%
(R04E7's own best-performing tolerance in its grid, chosen here for the
fairest one-parameter comparison -- TOL is not swept in this experiment).
Everything else -- Vin=48V, nP=4, power-stage topology, the truth table,
the GS61008T Ron/device data, the .machine/.state/.rule ratio-gating
construct, Cout=4.672 mF (unchanged, NOT also "fixed" here -- that is
explicitly a separate, still-unresolved gap per
CFLY_FIRST_PRINCIPLES_ESTIMATE.md's own "Cout is not estimated here"
section) -- is reused unchanged from R04E7.

TWO NUMERICAL-RESOLUTION SETTINGS also change, both justified by the pilot
run (see BOUNDARY.md Section 6), NOT physical parameters and NOT swept:
  - TMAX (the .tran maximum internal timestep) is reduced from R04E7's 1 ns
    to 50 ps, because the RC time constant governing each state's dynamics
    scales down with Cfly (same series Ron, smaller C); 1 ns would under-
    resolve the much faster transients at 1-8.7 uF. 50 ps was validated
    directly in the pilot run (Cfly=3 uF): it reproduced R04E7's own
    per-cycle VC1 trajectory almost exactly (21.59 V vs R04E7's 21.60 V at
    cycle 1, etc.), confirming adequate resolution.
  - TCAP_TOTAL (the safety cap) is reduced from R04E7's 50 us to 10 us --
    see BOUNDARY.md Section 6 for the post-pilot derivation.
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E8_corrected_cfly_ratio_gated_startup"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

CFLY_LIST = (1e-6, 3e-6, 8.7e-6)
TOL = 0.02  # FIXED (not swept) -- R04E7's own best-performing tolerance.
TCAP_TOTAL = 10e-6  # SENSITIVITY_ONLY safety cap, fixed across the grid,
# picked from the pilot run (BOUNDARY.md Section 6): observed Cfly=3uF
# convergence was 256.7 ns, giving a ~39x margin at 10 us; the naive
# RC-scaling extrapolation for the slowest cell (8.7 uF, ~744 ns expected)
# still gives a ~13x margin, comparable to R04E7's own ~12x margin at 50 us.
TMAX = 50e-12  # 50 ps, fixed across the grid -- see module docstring and
# BOUNDARY.md Section 6 for why this replaces R04E7's 1 ns.
NCYC_MEAS = 50

VGATE = 5.0
TARGET1, TARGET2, TARGET3 = 36.0, 24.0, 12.0


def cfly_tag(cfly: float) -> str:
    uf = cfly * 1e6
    if abs(uf - round(uf)) < 1e-9:
        return f"{round(uf)}uF"
    return f"{uf:g}uF".replace(".", "p")


def case_id(cfly: float) -> str:
    return f"r04e8_cfly_{cfly_tag(cfly)}"


TEMPLATE = """\
* R04E8 - corrected-Cfly voltage-ratio-gated EPE2019 3-state
* charge-redistribution ladder bootstrap ({case_id})
* SENSITIVITY CASE: CFLY={cfly_uf:g} uF (vs R04E7's 53.8 uF EPE2019
* Table-I cross-topology value), TOL=+/-2% FIXED (not swept -- R04E7's own
* best-performing tolerance), TCAP_TOTAL={tcap_us:g} us safety cap
* (fixed across the grid, post-pilot -- see BOUNDARY.md Section 6).
* PARENT: R04E7_ratio_gated_charge_redistribution_startup (same truth
* table, same power stage, same ratio-gating .machine construct, same
* Cout). SINGLE CHANGE: CFLY's numeric value. Also changed (numerical
* resolution only, not physical, not swept): TMAX reduced from R04E7's
* 1ns to {tmax_ps:g}ps to resolve the faster RC dynamics at this smaller
* capacitance (BOUNDARY.md Section 6, validated against the pilot run).
* Power-stage connectivity (SH1-4/SL1-4/CS1-3/L1-4 node names) is copied
* UNCHANGED from R04E7's SCB4P_P24_R04E7 subcircuit.
* True zero initial energy on every capacitor and inductor (ic=0, UIC).
* SCOPE: ladder bootstrap ONLY -- no PWM, no P24 steady-state ZVS admission
* chain, no Vout regulation attempt, no four-phase claim (H4/L4 off).

.include "{gs_lib}"
.param VIN=48 VOUT_REF=1 POUT_MODULE=250 NP=4 NM=4
.param LPHASE=1.466666666666667n CFLY={cfly:.6e}
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
XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd SCB4P_P24_R04E8

BVC1 vc1_mon 0 V=V(xmod:a1,xmod:x1)
BVC2 vc2_mon 0 V=V(xmod:a2,xmod:x2)
BVC3 vc3_mon 0 V=V(xmod:a3,xmod:x3)
RVC1 vc1_mon 0 1k
RVC2 vc2_mon 0 1k
RVC3 vc3_mon 0 1k

* Voltage-ratio-gated 3-state machine (UNCHANGED from R04E7 -- see that
* experiment's BOUNDARY.md for the full charge-conservation reasoning).
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
.tran 0 {{TSTOP}} 0 {tmax:.3e} UIC

.subckt SCB4P_P24_R04E8 vin out g gh1_in gl1_in gh2_in gl2_in gh3_in gl3_in
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
.ends SCB4P_P24_R04E8
.end
"""


def render(cfly: float) -> str:
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
        case_id=case_id(cfly),
        cfly=cfly,
        cfly_uf=cfly * 1e6,
        tol=TOL,
        tcap_us=TCAP_TOTAL * 1e6,
        tcap=TCAP_TOTAL,
        tmax=TMAX,
        tmax_ps=TMAX * 1e12,
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
    for cfly in CFLY_LIST:
        text = render(cfly)
        path = CASES / f"{case_id(cfly)}.cir"
        path.write_text(text)
        generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
