"""Generate R04E9's unified inductor-mediated bootstrap grid.

PARENTS (synthesis, see BOUNDARY.md Section 1 for the full lineage):
  - R04E3/R04E4/R04E5 (paper_locked/02_ectc2024_main/STEP_30/STEP_31,
    experiments/track_B_zero_start_extension/
    R04E5_ramped_duty_event_gated_zero_start/): the event-driven .machine
    skeleton and the physical current-limit turn-off rule
    (I(Lk)>=I_LIMIT), reused unchanged in form.
  - R03A/R03D (paper_locked/02_ectc2024_main/STEP_07_R03_PRECHARGE_PWM_
    TAKEOVER.md): R03A shows fixed PWM with no current limit lets current
    run away (884 A); R03D shows a duty ramp gets Vout up but with no
    current limiting (phase currents to hundreds of A). R04E9 keeps R03D's
    goal (bootstrap Vout using the inductor-mediated path) but replaces its
    fixed-clock PWM with physical-event gating throughout, and adds R04E3's
    current limit.
  - R04E6/R04E7/R04E8 (experiments/track_B_zero_start_extension/): the
    voltage-ratio-gated multi-state ladder-bootstrap idea (cycle through
    phases, monitor voltages, decide when to stop) is the CONCEPTUAL
    ancestor of "rotate phases and check a handoff condition after each
    rotation" here, but R04E9 does NOT reuse their mechanism: R04E6/E7/E8
    charge C(k+1) directly from C(k) through a switch-only path with NO
    series inductance limiting di/dt (a borrowed EPE2019 mechanism), which
    produced multi-kilo-amp capacitor-to-capacitor currents. R04E9 instead
    uses P24's OWN native Interval-1 mechanism (PAPER_LOCKED_REPRODUCTION_
    BASELINE.md: "QH1 ... L1 charges through Vin, QH1, C1, and Co") for
    EVERY phase: each phase's own inductor Lk is the current-limiting,
    charge-transferring, Vout-contributing element for THAT phase's own
    charge state, never a bare switch-to-switch path.

THE MECHANISM: for phase k in rotation 1->2->3->4->1..., two states:
  - CHARGE_k: QHk on. Exit when I(Lk)>=I_LIMIT (reusing R04E3/R04E4's
    already-validated current-limit turn-off rule, adapted per phase).
  - FREE_k: QLk on. Exit at the EARLIER of I(Lk)<=0 (natural event) or
    time-in-state>=T_FREEWHEEL_MAX (a per-state elapsed-time timeout,
    reusing A48's "event OR timeout, whichever first" pattern and R04E5's
    elapsed-time timer construct, redirected from an on-time ceiling to a
    freewheel ceiling).

FIXED VALUES: Vin=48V, nP=4, full four-phase P24 connectivity (reused
unchanged from R04E3/R04E5/R04E8's SCB4P_P24_* subcircuits), GS61008T Ron/
Coss (1 HS / 2 parallel LS, same as R04E3/R04E5), LPHASE=1.4666667nH
(Eq.-4 branch, this project's Track-A mainline), CFLY=3uF for C1/C2/C3
(R04E8's own middle, first-principles-corrected value -- NOT R04E7's
cross-topology-suspect 53.8uF), COUT=4.672mF (EPE2019 Table-I cross-
topology candidate, still flagged-unconfirmed per CURRENT_ASSUMPTION_
CROSSCHECK.md's "Output capacitor value" row -- not corrected here, same
scope limit R04E8 declared for Cout).

SWEPT (free axes): I_LIMIT in {10, 30, 60} A (R04E3's own attempted 10 A
is the low point; R04E4's sweep informs the upper points) x
T_FREEWHEEL_MAX in {50, 200, 1000} ns (all well below R04E3's own
1.63 us natural-zero-crossing finding at near-zero Vout, the entire
motivation for a timeout-based freewheel exit). 9 cells.

TSTOP=3 us and TMAX=50 ps for every cell, chosen from an UNTRACKED pilot
run (scratchpad-only, per R04E7/R04E8's own precedent).

TWO BUGS WERE FOUND AND FIXED DURING PILOTING, both stated here so the
final committed numbers are not mistaken for the first pilot's own
(wrong) results:
  1. An early pilot draft omitted the timer's own storage capacitor
     (CTIMER) that R04E5's proven elapsed-time-timer pattern requires --
     without it, "V(timer)" had no defined capacitance to integrate the
     charging current into a voltage, so the FREE-state timeout branch of
     the OR-rule never behaved as a controlled elapsed-time comparison.
     Fixed by adding CTIMER timer 0 {TIMER_C} ic=0, mirroring R04E5.
  2. Even after adding CTIMER, V(timer) counted DOWNWARD instead of
     upward with a "+1p*(condition)" B-source current coefficient --
     confirmed directly (not assumed) by probing V(timer) at fixed time
     checkpoints during a diagnostic run: it went NEGATIVE and never
     crossed the (positive) T_FREEWHEEL_MAX threshold, so every FREE
     state was resolving only via the natural I(Lk)<=0 event, never the
     timeout, regardless of the commanded T_FREEWHEEL_MAX value. This
     simulator's "Bxxx n+ n- I=expr" convention sources current OUT of
     n+ for a positive expr (the opposite of the naive expectation);
     flipping the coefficient to "-1p*(condition)" fixed it, confirmed by
     the same diagnostic: T_FREEWHEEL_MAX=50 ns then fires the FREE1->
     CHARGE2 transition at t=52.27 ns, matching the commanded 50 ns to
     within the same small overshoot margin R04E3/R04E4 already
     documented for their own current-limit turn-off event. This same
     latent sign convention may be present, unnoticed, in R04E5's own
     ton_timer construct -- R04E5's own results show its ramped-ceiling
     branch of the OR-rule was NEVER the one that actually fired in any
     of its 12 cells (the current-limit branch always won), so R04E5
     never exercised the branch that would have exposed this. Not fixed
     here (out of scope, R04E5's own files are not touched by this
     experiment per the project's archiving rules); flagged for a future
     contributor.

With BOTH fixes applied, a pilot at I_LIMIT=30 A / T_FREEWHEEL_MAX=200 ns
run to 3 us and again to 20 us produced BIT-IDENTICAL measured quantities
(il1_max, il2_max=13.285 A, il3_max=0, il4_max=0, and VC1_final==VC2_final
to full printed precision, i.e. C1/C2 reach a genuine capacitive-divider
equilibrium) -- direct evidence of a real permanent stall (not slow
continuing progress), so 3 us is not an arbitrary truncation but an
already-converged window. With the fix, T_FREEWHEEL_MAX now visibly
matters (pilot spot check, I_LIMIT=30 A fixed): IL2_max=20.05 A at
T_FREEWHEEL_MAX=50 ns, 13.29 A at 200 ns, 0.47 A at 1000 ns -- a shorter
freewheel timeout leaves phase 1's inductor current less fully decayed
when phase 2's charge state begins, giving phase 2 a bigger initial kick
(monotonically), though none of the three tested values was enough to
reach I_LIMIT=30 A in this pilot cell. TMAX=50ps follows R04E8's own
resolution reasoning for this same CFLY=3uF value (RC time constant
scales down with C).
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E9_unified_inductor_mediated_bootstrap"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

I_LIMIT_LIST = (10.0, 30.0, 60.0)
T_FREEWHEEL_LIST_NS = (50.0, 200.0, 1000.0)

CFLY = 3.0e-6  # R04E8's own middle, corrected value (NOT R04E7's 53.8uF).
LPHASE = 1.466666666666667e-9  # Eq.-4 branch, unchanged project mainline.
TSTOP = 3.0e-6  # pilot-confirmed converged/stalled window (see docstring).
TMAX = 50e-12  # matches R04E8's own CFLY=3uF resolution reasoning.

VGATE = 5.0
VOUT_TARGET = 1.0
VOUT_TOL = 0.05  # matches R04E5's own [0.95,1.05] V handoff band convention.
CAP_TOL = 0.02  # matches R04E7/R04E8's own tightest (best) tested tolerance.
TARGET1, TARGET2, TARGET3 = 36.0, 24.0, 12.0

# Checkpoints as fractions of TSTOP for the required "trajectory, not just
# start/end" reporting (same convention as R04E5's 25/50/75%/final table).
FRACTIONS = (0.2, 0.4, 0.6, 0.8, 1.0)

NROT_MEAS = 8  # rotation-boundary checkpoints attempted (matches R04E7/E8's
# style of measuring several cycle boundaries even when few or none fire).


def ilimit_tag(i_limit: float) -> str:
    return f"{int(round(i_limit))}a"


def tfw_tag(t_ns: float) -> str:
    return f"{int(round(t_ns))}ns"


def case_id(i_limit: float, t_fw_ns: float) -> str:
    return f"r04e9_ilimit_{ilimit_tag(i_limit)}_tfw_{tfw_tag(t_fw_ns)}"


TEMPLATE = """\
* R04E9 - unified inductor-mediated four-phase bootstrap ({case_id})
* SENSITIVITY CASE: I_LIMIT={i_limit:g} A, T_FREEWHEEL_MAX={t_fw_ns:g} ns.
* SYNTHESIS of R03D (duty-ramp Vout bootstrap goal) + R04E3/R04E4/R04E5
* (event-driven, latched, current-limited .machine skeleton) + the
* rotate-and-monitor CONCEPT from R04E6/R04E7/R04E8 -- but using P24's OWN
* Interval-1 inductor-mediated charging path for every phase, NOT
* R04E6/E7/E8's borrowed switch-only EPE2019 mechanism. See
* build_b05_r04e9_unified_inductor_mediated_bootstrap.py module docstring
* and BOUNDARY.md for full parentage.
* Full four-phase P24 power stage, all four phases actively commanded by
* the machine (not one held statically, unlike R04E3/R04E5/R04E6-E8).
* True zero initial energy on every capacitor and inductor (ic=0, UIC).
* CFLY={cfly_uf:g} uF (R04E8's own corrected middle value). COUT=4.672 mF
* (EPE2019 cross-topology candidate, NOT corrected here -- see BOUNDARY.md).
* TSTOP={tstop_us:g} us / TMAX={tmax_ps:g} ps: pilot-confirmed converged
* window (see module docstring) -- fixed across the whole grid, not swept.
* SCOPE: bootstrap-only. Does NOT build or test handoff into the existing
* strict steady-state controller; only measures whether/when the handoff
* CONDITION is reached.

.include "{gs_lib}"
.param VIN=48 VOUT_REF=1 POUT_MODULE=250 NP=4 NM=4
.param LPHASE={lphase:.9e} CFLY={cfly:.6e}
.param COUT={{8*220u+32*47u+64*22u}} RLOAD={{VOUT_REF*VOUT_REF/POUT_MODULE}}
.param CH={{GS61008T_COTR_0_50V}} CL={{2*GS61008T_COTR_0_50V}}
.param RHS={{GS61008T_RDS_TYP_25C}} RLS={{GS61008T_RDS_TYP_25C/2}}
.param RLDAMP=1u VGATE={vgate:g}

.param I_LIMIT={i_limit:g}
.param T_FREEWHEEL_MAX={t_fw:.6e}
* Elapsed-freewheel-time timer components (NUMERICAL_IDEALIZATION, no
* physical counterpart), same TIMER_C/TIMER_RESET_RON values R04E5 used
* for its own analogous elapsed-on-time timer.
.param TIMER_C=1p TIMER_RESET_RON=5

* Handoff-condition monitor (measurement only -- this experiment does NOT
* build or exercise the actual handoff/steady-state chain, per BOUNDARY.md).
.param VOUT_LO={vout_lo:.6f} VOUT_HI={vout_hi:.6f}
.param VC1_LO={vc1_lo:.6f} VC1_HI={vc1_hi:.6f}
.param VC2_LO={vc2_lo:.6f} VC2_HI={vc2_hi:.6f}
.param VC3_LO={vc3_lo:.6f} VC3_HI={vc3_hi:.6f}

VRAIL vin 0 {{VIN}}
CCO out 0 {{COUT}} ic=0
RLOAD_MAIN out 0 {{RLOAD}}
XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E9

BVC1 vc1_mon 0 V=V(xmod:a1,xmod:x1)
BVC2 vc2_mon 0 V=V(xmod:a2,xmod:x2)
BVC3 vc3_mon 0 V=V(xmod:a3,xmod:x3)
RVC1 vc1_mon 0 1k
RVC2 vc2_mon 0 1k
RVC3 vc3_mon 0 1k

* Per-state elapsed-time freewheel timer (NUMERICAL_IDEALIZATION, no
* physical counterpart): charges (1 pA into 1 pF => V(timer) numerically
* equals elapsed time in seconds) only while the machine is in ANY
* freewheel state (FREE1/FREE2/FREE3/FREE4); reset through a low-Ron
* switch the instant it enters ANY charge state. Only one state is ever
* active at a time, so one shared timer serves all four phases -- same
* pattern as R04E5's ton_timer, with the charge/reset roles swapped
* (R04E5 timed elapsed ON-time; this experiment times elapsed FREEWHEEL
* time) and the A48 "event OR timeout, whichever first" idea applied per
* state instead of as a single global fixed delay.
CTIMER timer 0 {{TIMER_C}} ic=0
* NOTE: the B-source current coefficient is NEGATIVE (-1p), not +1p, even
* though the intent is to charge V(timer) UPWARD. Verified directly (not
* assumed): with +1p, V(timer) counted DOWNWARD (e.g. -9.42e-8 V at
* t=100 ns), because this simulator's B-source current convention for
* "Bxxx n+ n- I=expr" sources current OUT of n+ (the first node) for a
* positive expr -- the opposite of the naive expectation. With -1p,
* V(timer) counts upward exactly as intended (confirmed: T_FREEWHEEL_MAX=
* 50 ns now fires the FREE1->CHARGE2 transition at t=52.27 ns, matching
* the commanded 50 ns to within the same small overshoot margin R04E3/
* R04E4 already documented for their own current-limit turn-off event).
BTIMER_CHG timer 0 I=-1p*((V(state_mon)>0.5)&(V(state_mon)<1.5)|(V(state_mon)>2.5)&(V(state_mon)<3.5)|(V(state_mon)>4.5)&(V(state_mon)<5.5)|(V(state_mon)>6.5)&(V(state_mon)<7.5))
BRESET_GATE reset_gate 0 V=5*((V(state_mon)<0.5)|(V(state_mon)>1.5)&(V(state_mon)<2.5)|(V(state_mon)>3.5)&(V(state_mon)<4.5)|(V(state_mon)>5.5)&(V(state_mon)<6.5))
SRESET timer 0 reset_gate 0 SWRESET
.model SWRESET SW(Ron={{TIMER_RESET_RON}} Roff=1Meg Vt=2.5 Vh=0)

* Handoff-condition observer: high only while Vout and all three flying
* capacitor voltages simultaneously sit within their declared bands.
BHANDOFF handoff_flag 0 V=5*((V(out)>=VOUT_LO)&(V(out)<=VOUT_HI)&(V(vc1_mon)>=VC1_LO)&(V(vc1_mon)<=VC1_HI)&(V(vc2_mon)>=VC2_LO)&(V(vc2_mon)<=VC2_HI)&(V(vc3_mon)>=VC3_LO)&(V(vc3_mon)<=VC3_HI))
RHANDOFF handoff_flag 0 1k

* Unified event-driven, latched four-phase rotation machine. CHARGE_k
* exits at the R04E3/R04E4 current-limit rule (I(Lk)>=I_LIMIT); FREE_k
* exits at the earlier of the natural I(Lk)<=0 event or the
* T_FREEWHEEL_MAX timeout (A48-style event-OR-timeout).
.machine 1p
.state CHARGE1 0
.state FREE1 1
.state CHARGE2 2
.state FREE2 3
.state CHARGE3 4
.state FREE3 5
.state CHARGE4 6
.state FREE4 7
.rule CHARGE1 FREE1 I(XMOD:L1)>=I_LIMIT
.rule FREE1 CHARGE2 (I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE2 FREE2 I(XMOD:L2)>=I_LIMIT
.rule FREE2 CHARGE3 (I(XMOD:L2)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE3 FREE3 I(XMOD:L3)>=I_LIMIT
.rule FREE3 CHARGE4 (I(XMOD:L3)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE4 FREE4 I(XMOD:L4)>=I_LIMIT
.rule FREE4 CHARGE1 (I(XMOD:L4)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.output (gh1_cmd) VGATE*(state==CHARGE1)
.output (gl1_cmd) VGATE*(state==FREE1)
.output (gh2_cmd) VGATE*(state==CHARGE2)
.output (gl2_cmd) VGATE*(state==FREE2)
.output (gh3_cmd) VGATE*(state==CHARGE3)
.output (gl3_cmd) VGATE*(state==FREE3)
.output (gh4_cmd) VGATE*(state==CHARGE4)
.output (gl4_cmd) VGATE*(state==FREE4)
.output (state_mon) state
.output (rot_flag) VGATE*(state==FREE4)
.endmachine

RSTATE state_mon 0 1k
RROT rot_flag 0 1k
RGH1 gh1_cmd 0 1k
RGL1 gl1_cmd 0 1k
RGH2 gh2_cmd 0 1k
RGL2 gl2_cmd 0 1k
RGH3 gh3_cmd 0 1k
RGL3 gl3_cmd 0 1k
RGH4 gh4_cmd 0 1k
RGL4 gl4_cmd 0 1k

.meas tran STATE_FINAL FIND V(state_mon) AT {{TSTOP}}
.meas tran VOUT_FINAL FIND V(out) AT {{TSTOP}}
.meas tran VC1_FINAL FIND V(vc1_mon) AT {{TSTOP}}
.meas tran VC2_FINAL FIND V(vc2_mon) AT {{TSTOP}}
.meas tran VC3_FINAL FIND V(vc3_mon) AT {{TSTOP}}
.meas tran T_HANDOFF WHEN V(handoff_flag)=2.5 RISE=1
{fraction_meas}
.meas tran IL1_MAX MAX I(XMOD:L1)
.meas tran IL1_MIN MIN I(XMOD:L1)
.meas tran IL2_MAX MAX I(XMOD:L2)
.meas tran IL2_MIN MIN I(XMOD:L2)
.meas tran IL3_MAX MAX I(XMOD:L3)
.meas tran IL3_MIN MIN I(XMOD:L3)
.meas tran IL4_MAX MAX I(XMOD:L4)
.meas tran IL4_MIN MIN I(XMOD:L4)
* NOTE: ICS1-3 windowed FROM 2n, not 0, excluding a sub-2ns t=0 ideal-
* switch/capacitor initial-condition numerical startup spike -- the same
* KIND of artifact R04E6 documented and excluded (its own bit-identical
* ~1.23e6 A "ICS1_MAX" across every swept cell, present regardless of the
* swept parameters, confirming it is a t=0 numerical transient, not a
* physical result). Diagnosed directly here, not assumed: an unwindowed
* check on the I_LIMIT=60A row found a 4548 A ICS1 spike whose .meas WHEN
* crossing landed at t=8.1e-20 s (state=CHARGE1, IL1~=0 A) -- i.e.
* genuinely at t=0, not a later physical event. A FROM 1n window (R04E8's
* own cutoff) left this one row's spike partly inside the window; FROM 2n
* removes it completely and gives a smoothly I_LIMIT-ordered result
* (0.298/0.361/0.577 A at I_LIMIT=10/30/60 A) confirmed stable from 2n
* through 50n windows (bit-identical at every wider cutoff tested).
.meas tran ICS1_MAX MAX I(XMOD:CS1) FROM 2n TO {{TSTOP}}
.meas tran ICS1_MIN MIN I(XMOD:CS1) FROM 2n TO {{TSTOP}}
.meas tran ICS2_MAX MAX I(XMOD:CS2) FROM 2n TO {{TSTOP}}
.meas tran ICS2_MIN MIN I(XMOD:CS2) FROM 2n TO {{TSTOP}}
.meas tran ICS3_MAX MAX I(XMOD:CS3) FROM 2n TO {{TSTOP}}
.meas tran ICS3_MIN MIN I(XMOD:CS3) FROM 2n TO {{TSTOP}}
{rotation_meas}

.options plotwinsize=0 reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt cshunt=1e-15
.save V(vc1_mon) V(vc2_mon) V(vc3_mon) V(state_mon) V(rot_flag) V(handoff_flag) V(out) I(XMOD:L1) I(XMOD:L2) I(XMOD:L3) I(XMOD:L4) I(XMOD:CS1) I(XMOD:CS2) I(XMOD:CS3)
.tran 0 {{TSTOP}} 0 {tmax:.3e} UIC

.subckt SCB4P_P24_R04E9 vin out g gh1_in gl1_in gh2_in gl2_in gh3_in gl3_in gh4_in gl4_in
BGH1 gh1 g V=V(gh1_in,g)
BGL1 gl1 g V=V(gl1_in,g)
BGH2 gh2 g V=V(gh2_in,g)
BGL2 gl2 g V=V(gl2_in,g)
BGH3 gh3 g V=V(gh3_in,g)
BGL3 gl3 g V=V(gl3_in,g)
BGH4 gh4 g V=V(gh4_in,g)
BGL4 gl4 g V=V(gl4_in,g)

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
.ends SCB4P_P24_R04E9
.end
"""


def render(i_limit: float, t_fw_ns: float) -> str:
    tstop = TSTOP
    t_fw = t_fw_ns * 1e-9

    fraction_lines = []
    for frac in FRACTIONS:
        label = f"{int(round(frac * 100))}PCT"
        t_at = tstop * frac
        fraction_lines.append(
            f".meas tran VOUT_AT_{label} FIND V(out) AT {t_at:.6e}"
        )
        fraction_lines.append(
            f".meas tran VC1_AT_{label} FIND V(vc1_mon) AT {t_at:.6e}"
        )
        fraction_lines.append(
            f".meas tran VC2_AT_{label} FIND V(vc2_mon) AT {t_at:.6e}"
        )
        fraction_lines.append(
            f".meas tran VC3_AT_{label} FIND V(vc3_mon) AT {t_at:.6e}"
        )
        fraction_lines.append(
            f".meas tran STATE_AT_{label} FIND V(state_mon) AT {t_at:.6e}"
        )

    rotation_lines = []
    for j in range(1, NROT_MEAS + 1):
        rotation_lines.append(
            f".meas tran T_ROT{j} WHEN V(rot_flag)=2.5 FALL={j}"
        )
        rotation_lines.append(
            f".meas tran VOUT_ROT{j} FIND V(out) WHEN V(rot_flag)=2.5 FALL={j}"
        )
        rotation_lines.append(
            f".meas tran VC1_ROT{j} FIND V(vc1_mon) WHEN V(rot_flag)=2.5 FALL={j}"
        )
        rotation_lines.append(
            f".meas tran VC2_ROT{j} FIND V(vc2_mon) WHEN V(rot_flag)=2.5 FALL={j}"
        )
        rotation_lines.append(
            f".meas tran VC3_ROT{j} FIND V(vc3_mon) WHEN V(rot_flag)=2.5 FALL={j}"
        )

    return TEMPLATE.format(
        case_id=case_id(i_limit, t_fw_ns),
        i_limit=i_limit,
        t_fw_ns=t_fw_ns,
        t_fw=t_fw,
        cfly=CFLY,
        cfly_uf=CFLY * 1e6,
        lphase=LPHASE,
        tstop_us=TSTOP * 1e6,
        tmax_ps=TMAX * 1e12,
        tmax=TMAX,
        gs_lib=GS_LIB,
        vgate=VGATE,
        vout_lo=VOUT_TARGET * (1 - VOUT_TOL),
        vout_hi=VOUT_TARGET * (1 + VOUT_TOL),
        vc1_lo=TARGET1 * (1 - CAP_TOL),
        vc1_hi=TARGET1 * (1 + CAP_TOL),
        vc2_lo=TARGET2 * (1 - CAP_TOL),
        vc2_hi=TARGET2 * (1 + CAP_TOL),
        vc3_lo=TARGET3 * (1 - CAP_TOL),
        vc3_hi=TARGET3 * (1 + CAP_TOL),
        fraction_meas="\n".join(fraction_lines),
        rotation_meas="\n".join(rotation_lines),
    ).replace("{TSTOP}", f"{tstop:.6e}")


def build() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for i_limit in I_LIMIT_LIST:
        for t_fw_ns in T_FREEWHEEL_LIST_NS:
            text = render(i_limit, t_fw_ns)
            path = CASES / f"{case_id(i_limit, t_fw_ns)}.cir"
            path.write_text(text)
            generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
