"""Generate R04E5's ramped-duty, event-gated, zero-start sensitivity grid.

R04E5 synthesizes two prior, independently-unresolved Track-B zero-start
attempts instead of perturbing either one alone:

  * PARENT 1 -- R03D (paper_locked/02_ectc2024_main/STEP_08_...md,
    spice/R03D_epe2019_duty_ramp_takeover.cir): a commanded on-time ramped
    LINEARLY from 0 to the locked P24 value over a declared-sensitivity
    TSOFT window. R03D's own result: this correctly bootstraps Vout to
    0.994-1.007 V, but with NO current limiting at all phase currents swing
    to hundreds of amps (L1: -225.75..382.55 A, L4: -268.49..390.96 A) --
    "PARTIAL_SUCCESS_OUTPUT / FAILED_CURRENT_BOUNDARY".

  * PARENT 2 -- R04E3 (paper_locked/02_ectc2024_main/STEP_30_...md,
    spice/R04E3_P24_minimal_zero_start_event_cycle.cir): an event-driven,
    latched .machine/.state/.rule controller starting from true zero
    energy, turning the high side off at a per-phase current limit and
    waiting for physical zero-current/negative-current events (not fixed
    times). R04E3's own result: it correctly detects that a full P24 cycle
    cannot yet close (iL1=0 takes 1.63 us, not ~200 ns) and safely refuses
    to proceed rather than chattering or diverging -- but during the long
    wait, current keeps rising past the commanded limit (10 A commanded,
    43.68 A actually reached) -- "LOGIC_PASS;
    P24_ZERO_START_LOCAL_CYCLE_FAILS_BEFORE_T3".

R04E5's synthesis: R04E3's event-driven latched machine is kept exactly as
its state/rule skeleton (ENERGY -> HS_OFF_COMMUTATE_LOW ->
LOW_FREEWHEEL_TO_ZERO -> LOW_BUILD_NEGATIVE -> COMMUTATE_HIGH_TO_ZVS), but
two changes are made relative to R04E3:

  1. The ENERGY->HS_OFF transition now fires at the EARLIER of (a) the
     per-phase current limit I_LIMIT (R04E3's own mechanism, unchanged) or
     (b) an elapsed-on-time ceiling that ramps linearly from 0 to the
     locked P24 Ton = D*T = 16.6667 ns over TSOFT (R03D's own mechanism,
     re-expressed as an event-machine rule instead of R03D's fixed-clock
     PWM expression). Elapsed on-time is measured by a small
     NUMERICAL_IDEALIZATION integrator (a capacitor charged at a constant
     rate while state==ENERGY, reset every time the state leaves ENERGY)
     -- see BOUNDARY.md.
  2. COMMUTATE_HIGH_TO_ZVS's exit rule now returns to ENERGY instead of
     entering R04E3's deliberate BLOCK state, so the machine repeats --
     necessary because a single pulse cannot show whether the ramp
     bootstraps Vout; many repeated cycles are needed to see the ramp's
     effect play out.

See BOUNDARY.md for the full provenance, the L=1.4666667nH resolution
(R04E3's Eq.-4 value is used, not R03D's own Lphase=2.68nH Table-I value),
and the prohibited claims.

Two free sensitivity axes are swept (SENSITIVITY_ONLY, not paper values):
TSOFT in {50, 100, 200, 500} us and I_LIMIT in {10, 50, 150} A.
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E5_ramped_duty_event_gated_zero_start"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

TSOFT_US = (50, 100, 200, 500)
I_LIMIT_A = (10, 50, 150)

# Post-ramp settling margin: run each case to 1.2x its own TSOFT so the
# post-ramp (fixed-ceiling) behavior is visible, not just the ramp itself.
GUARD_FACTOR = 1.2

TEMPLATE = """\
* R04E5 - ramped-duty, event-gated zero start ({case_id})
* SENSITIVITY CASE: TSOFT={tsoft_us:g} us, I_LIMIT={i_limit:g} A.
* Two-parent synthesis -- see BOUNDARY.md. PARENT 1: R03D duty ramp
* (paper_locked/02_ectc2024_main/spice/R03D_epe2019_duty_ramp_takeover.cir).
* PARENT 2: R04E3 event-driven latched current-limited controller
* (paper_locked/02_ectc2024_main/spice/R04E3_P24_minimal_zero_start_event_cycle.cir).
* Single active phase (phase 1) on the full one-module/four-phase P24
* power stage, exactly as R04E3/R04E4 already do -- this experiment does
* NOT claim four-phase interleaving, only the phase-1 startup transient.
* All capacitor/inductor initial conditions are true zero energy.

.include "{gs_lib}"
.param VIN=48 VOUT_REF=1 POUT_MODULE=250 NP=4 NM=4
.param LPHASE=1.466666666666667n CFLY={{4*10u+2*4.7u+2*2.2u}}
.param COUT={{8*220u+32*47u+64*22u}} RLOAD={{VOUT_REF*VOUT_REF/POUT_MODULE}}
* P24_EXPLICIT Ton relation (same as R03D): D=NP*Vo/Vin, T=1/fsw, Ton=D*T.
.param FSW=5Meg T={{1/FSW}} D={{NP*VOUT_REF/VIN}} TON_FINAL={{D*T}}
* R04E3-inherited: 2% of the commanded gate-off limit is the P24
* source-native negative-current target used to admit high-side ZVS.
.param I_LIMIT={i_limit:g} NEG_FRAC=.02 I_NEG={{NEG_FRAC*I_LIMIT}}
.param CH={{GS61008T_COTR_0_50V}} CL={{2*GS61008T_COTR_0_50V}}
.param RHS={{GS61008T_RDS_TYP_25C}} RLS={{GS61008T_RDS_TYP_25C/2}}
* R04E4-inherited correction: rail present at the DC solution (VRAIL flat
* at VIN from t=0) with controller enable delayed to TENABLE, so a Coss
* displacement transient cannot trigger the comparator before a commanded
* power pulse (R04E4's own documented boundary correction).
.param TENABLE=10n VGATE=5 RLDAMP=1u
* SENSITIVITY AXIS 1 (R03D's mechanism): linear on-time ramp duration.
.param TSOFT={tsoft_us:g}u
* Elapsed-on-time timer (NUMERICAL_IDEALIZATION, not a physical part):
* dV/dt=1 V/s while state==ENERGY (1 pA into 1 pF), reset through a 5-ohm
* switch (RC~5 ps) the instant the machine leaves ENERGY. V(ton_timer)
* therefore numerically equals THIS pulse's own elapsed on-time in
* seconds, independent of prior cycles.
.param TIMER_C=1p TIMER_RESET_RON=5

VRAIL vin 0 {{VIN}}
CCO out 0 {{COUT}} ic=0
RLOAD_MAIN out 0 {{RLOAD}}
XMOD vin out 0 gh1_cmd gl1_cmd SCB4P_P24_R04E5

CTIMER ton_timer 0 {{TIMER_C}} ic=0
BTIMER_CHG ton_timer 0 I=1p*(V(state_mon)<0.5)*(time>=TENABLE)
BRESET_GATE reset_gate 0 V=5*(V(state_mon)>0.5)
SRESET ton_timer 0 reset_gate 0 SWRESET
.model SWRESET SW(Ron={{TIMER_RESET_RON}} Roff=1Meg Vt=2.5 Vh=0)

* Event-driven, latched machine (R04E3's skeleton). CHANGED relative to
* R04E3: rule 0 now fires at the earlier of the current limit or the
* ramped on-time ceiling (R03D mechanism); rule 4 loops back to state 0
* instead of entering R04E3's deliberate BLOCK_P24_HANDOFF_UNKNOWN state,
* so the cycle repeats and the ramp's effect can be observed.
.machine 1p
.state ENERGY 0
.state HS_OFF_COMMUTATE_LOW 1
.state LOW_FREEWHEEL_TO_ZERO 2
.state LOW_BUILD_NEGATIVE 3
.state COMMUTATE_HIGH_TO_ZVS 4
.rule ENERGY HS_OFF_COMMUTATE_LOW (time>=TENABLE) & ((I(XMOD:L1)>=I_LIMIT) | (V(ton_timer)>=(TON_FINAL*limit((time-TENABLE)/TSOFT,0,1))))
.rule HS_OFF_COMMUTATE_LOW LOW_FREEWHEEL_TO_ZERO V(xmod:x1)<=0
.rule LOW_FREEWHEEL_TO_ZERO LOW_BUILD_NEGATIVE I(XMOD:L1)<=0
.rule LOW_BUILD_NEGATIVE COMMUTATE_HIGH_TO_ZVS I(XMOD:L1)<=-I_NEG
.rule COMMUTATE_HIGH_TO_ZVS ENERGY V(vin,xmod:a1)<=0
.output (state_mon) state
.output (gh1_cmd) VGATE*(state==ENERGY)*(time>=TENABLE)
.output (gl1_cmd) VGATE*((state==LOW_FREEWHEEL_TO_ZERO)+(state==LOW_BUILD_NEGATIVE))
.endmachine

RSTATE state_mon 0 1k
RGH gh1_cmd 0 1k
RGL gl1_cmd 0 1k

.meas tran STATE_FINAL FIND V(state_mon) AT {tstop:g}u
.meas tran VOUT_FINAL FIND V(out) AT {tstop:g}u
.meas tran VOUT_AT_25PCT FIND V(out) AT {t25:g}u
.meas tran VOUT_AT_50PCT FIND V(out) AT {t50:g}u
.meas tran VOUT_AT_75PCT FIND V(out) AT {t75:g}u
.meas tran VOUT_AT_TSOFT FIND V(out) AT {tsoft_us:g}u
.meas tran VOUT_PEAK MAX V(out) FROM 0 TO {tstop:g}u
.meas tran IL1_MAX MAX I(XMOD:L1) FROM 0 TO {tstop:g}u
.meas tran IL1_MIN MIN I(XMOD:L1) FROM 0 TO {tstop:g}u
.meas tran IL1_MAX_LATE MAX I(XMOD:L1) FROM {tlate:g}u TO {tstop:g}u
.meas tran IL1_MIN_LATE MIN I(XMOD:L1) FROM {tlate:g}u TO {tstop:g}u
.meas tran VC1_FINAL FIND V(xmod:a1,xmod:x1) AT {tstop:g}u

.options plotwinsize=0 reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt cshunt=1e-15
.save V(state_mon) V(out) V(ton_timer) V(vin,xmod:a1) V(xmod:x1) V(xmod:a1,xmod:x1) I(XMOD:L1) V(gh1_cmd) V(gl1_cmd)
.tran 0 {tstop:g}u 0 1n UIC

.subckt SCB4P_P24_R04E5 vin out g gh1_in gl1_in
BGH1 gh1 g V=V(gh1_in,g)
BGL1 gl1 g V=V(gl1_in,g)
VGL2 gl2 g {{VGATE}}
VGH2 gh2 g 0
VGH3 gh3 g 0
VGH4 gh4 g 0
VGL3 gl3 g 0
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
.ends SCB4P_P24_R04E5
.end
"""


def case_id(tsoft_us: float, i_limit: float) -> str:
    tsoft_tag = f"{tsoft_us:g}".replace(".", "p")
    ilim_tag = f"{i_limit:g}".replace(".", "p")
    return f"r04e5_tsoft_{tsoft_tag}us_ilimit_{ilim_tag}a"


def render(tsoft_us: float, i_limit: float) -> str:
    tstop = tsoft_us * GUARD_FACTOR
    return TEMPLATE.format(
        case_id=case_id(tsoft_us, i_limit),
        tsoft_us=tsoft_us,
        i_limit=i_limit,
        gs_lib=GS_LIB,
        tstop=tstop,
        t25=tsoft_us * 0.25,
        t50=tsoft_us * 0.50,
        t75=tsoft_us * 0.75,
        tlate=tstop * 0.8,
    )


def build() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for tsoft_us in TSOFT_US:
        for i_limit in I_LIMIT_A:
            text = render(tsoft_us, i_limit)
            path = CASES / f"{case_id(tsoft_us, i_limit)}.cir"
            path.write_text(text)
            generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
