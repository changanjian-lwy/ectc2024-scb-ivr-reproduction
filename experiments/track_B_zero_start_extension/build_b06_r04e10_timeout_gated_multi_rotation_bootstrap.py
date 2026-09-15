"""Generate R04E10's timeout-gated multi-rotation bootstrap grid.

PARENT: R04E9 (experiments/track_B_zero_start_extension/
R04E9_unified_inductor_mediated_bootstrap/). R04E9 built a unified rotating
CHARGE_k/FREE_k machine where CHARGE_k (QHk on) exits ONLY on a physical
current-limit event (I(Lk)>=I_LIMIT) and FREE_k (QLk on) exits at the
earlier of the natural I(Lk)<=0 event or an A48-style timeout
T_FREEWHEEL_MAX. Result: peak currents stayed physically plausible (under
61 A everywhere, vs R04E6-E8's 4.2-4.6 kA), but every one of the 9 tested
cells stalled permanently in CHARGE2, because phase 2's high side connects
between C1 and C2 (not directly to Vin), so it depends on C1 already
holding charge that phase 1's own very brief (~0.93 ns) first pulse barely
supplied -- and since CHARGE_k had no timeout fallback, a phase that
cannot reach its own current limit never exits, so the rotation never
completes even once.

THE SINGLE CHANGE THIS EXPERIMENT TESTS: add a timeout fallback to CHARGE_k
too, symmetric with FREE_k's existing "event OR timeout" pattern --
CHARGE_k now exits at (I(Lk)>=I_LIMIT) OR (time-in-state>=T_CHARGE_MAX),
whichever comes first. This lets the rotation always complete even when an
early phase cannot fully reach its own current limit on a given pass, so
multiple rotations can each contribute a little more charge to the
downstream capacitors -- the same "don't demand full success in one pass,
let repetition converge" principle that made R04E7's ratio-gated ladder
mechanism work where R04E6's blind version failed. Everything else
(CHARGE/FREE structure, node topology, CFLY=3uF, COUT=4.672mF flagged
placeholder, the current-limit turn-off mechanism, the FREE_k timer
construct) is reused UNCHANGED from R04E9.

NEW CHARGE-STATE TIMER CONSTRUCT (exact mirror of R04E9's own validated
FREE-state timer, roles of "charge" and "reset" swapped):
  - CTIMER_CHG (a new 1pF capacitor, timer_chg node, ic=0) charges (counts
    up) via BTIMER_CHG2 (I=-1p*(IS_CHARGE)) only while the machine is in
    ANY CHARGE_k state (the SAME boolean condition R04E9's own
    BRESET_GATE already computed for the opposite purpose).
  - It is held reset near 0 by a low-Ron switch SRESET_CHG, gated by
    BRESET_GATE2 (V=5*(IS_FREE), the SAME boolean condition R04E9's own
    BTIMER_CHG already computed for the opposite purpose), throughout ANY
    FREE_k state.
  - The B-source current sign (-1p, not +1p) is carried over UNCHANGED
    from R04E9's own diagnosed fix (BOUNDARY.md Section 2): this
    simulator's "Bxxx n+ n- I=expr" convention sources current OUT of n+
    for positive expr, so -1p is required to charge the node upward.

PILOT FINDING -- T_CHARGE_MAX must not be too close to the machine's own
internal timescales (see BOUNDARY.md Section "Pilot verification" for the
full diagnostic trail, mirroring R04E9's own "verify before trusting"
discipline): an isolated single-phase-chain diagnostic (I_LIMIT set to an
unreachable 100 kA so only the timeout branch could possibly fire) found
that T_CHARGE_MAX=100 ps and T_CHARGE_MAX=1 ns BOTH produce a genuine
state-machine malfunction -- CHARGE2's timeout-triggered transition lands
back on FREE1's own state value (1) instead of forward to FREE2's (3),
confirmed directly by parsing the raw transient trace (V(state_mon) and
I(XMOD:L2) both show a wild, clearly non-physical excursion at the
transition, not merely a slow/late one). The SAME diagnostic at
T_CHARGE_MAX=5, 10, and 50 ns produced clean, monotonically increasing
state progression (0->1->2->3->4->...) with the commanded timeout value
matched to the same small overshoot margin R04E3/R04E4/R04E9 already
documented for their own events, and no anomalous current excursion. This
experiment's swept grid is therefore restricted to T_CHARGE_MAX values of
5 ns and above, i.e. NOT the literal "roughly ~1 ns" starting point named
in the task description -- that specific value was tried first and found
to break the construct, which is exactly the kind of pitfall the task
asked to check for before trusting the mechanism in the full machine. This
is reported as a finding, not silently worked around.

FIXED VALUES carried over UNCHANGED from R04E9: Vin=48V, nP=4, full
four-phase P24 connectivity, GS61008T Ron/Coss (1 HS / 2 parallel LS),
LPHASE=1.4666667nH (Eq.-4 branch), CFLY=3uF (R04E8's corrected value),
COUT=4.672mF (still-flagged cross-topology candidate, not corrected
here). T_FREEWHEEL_MAX is FIXED (not swept) at 50 ns -- R04E9's own
best-performing cell by every measure (RESULTS.md Section 8: I_LIMIT=60A,
T_FREEWHEEL_MAX=50ns reached IL2_max=39.966A, 67% of its own I_LIMIT, the
closest any R04E9 cell got to unsticking), per the task's explicit
instruction to fix this axis at R04E9's own best value rather than
re-sweep it.

SWEPT (free axes): I_LIMIT in {10, 30, 60} A (R04E9's own axis, reused
unchanged for direct comparability) x T_CHARGE_MAX in {5, 20, 50} ns (the
pilot-verified-stable range: 5 ns is the smallest value found clean in the
isolated diagnostic, closest to the task's suggested ~1ns starting point
that the construct can actually tolerate; 50 ns matches the fixed
T_FREEWHEEL_MAX value and the task's own suggested upper bound; 20 ns is
an intermediate point). 9 cells.

TSTOP=20 us (long enough for tens of rotations per cell given a
worst-case per-phase dwell of T_CHARGE_MAX+T_FREEWHEEL_MAX<=100 ns, i.e.
<=400 ns per rotation; pilot-confirmed, see BOUNDARY.md) / TMAX=50 ps
(unchanged from R04E9, same CFLY=3uF resolution reasoning).
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E10_timeout_gated_multi_rotation_bootstrap"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

I_LIMIT_LIST = (10.0, 30.0, 60.0)
T_CHARGE_MAX_LIST_NS = (5.0, 20.0, 50.0)
T_FREEWHEEL_MAX_NS = 50.0  # fixed: R04E9's own best-performing cell (Section 8).

CFLY = 3.0e-6  # R04E8's own corrected middle value, unchanged from R04E9.
LPHASE = 1.466666666666667e-9  # Eq.-4 branch, unchanged project mainline.
TSTOP = 20.0e-6  # pilot-justified multi-rotation window (see BOUNDARY.md).
TMAX = 50e-12  # unchanged from R04E9 (same CFLY=3uF resolution reasoning).

VGATE = 5.0
VOUT_TARGET = 1.0
VOUT_TOL = 0.05  # same convention as R04E5/R04E9.
CAP_TOL = 0.02  # same convention as R04E7/R04E8/R04E9 (tightest tested).
TARGET1, TARGET2, TARGET3 = 36.0, 24.0, 12.0

FRACTIONS = (0.2, 0.4, 0.6, 0.8, 1.0)

NROT_MEAS = 60  # rotation-boundary checkpoints attempted -- much larger than
# R04E9's own 8, because this experiment's whole point is to see whether
# MANY rotations occur and whether they show cumulative progress.


def ilimit_tag(i_limit: float) -> str:
    return f"{int(round(i_limit))}a"


def tchg_tag(t_ns: float) -> str:
    return f"{int(round(t_ns))}ns"


def case_id(i_limit: float, t_chg_ns: float) -> str:
    return f"r04e10_ilimit_{ilimit_tag(i_limit)}_tchg_{tchg_tag(t_chg_ns)}"


TEMPLATE = """\
* R04E10 - timeout-gated multi-rotation bootstrap ({case_id})
* SENSITIVITY CASE: I_LIMIT={i_limit:g} A, T_CHARGE_MAX={t_chg_ns:g} ns,
* T_FREEWHEEL_MAX={t_fw_ns:g} ns (FIXED, R04E9's own best-performing value).
* PARENT: R04E9 (unified inductor-mediated four-phase bootstrap). SINGLE
* CHANGE from R04E9: CHARGE_k now exits at (I(Lk)>=I_LIMIT) OR
* (time-in-CHARGE_k>=T_CHARGE_MAX), symmetric with FREE_k's existing
* event-OR-timeout pattern. Everything else (node topology, CFLY=3uF,
* COUT=4.672mF, current-limit mechanism, FREE_k timer) is unchanged from
* R04E9. See build_b06_r04e10_timeout_gated_multi_rotation_bootstrap.py
* module docstring and BOUNDARY.md for the pilot-verified-safe
* T_CHARGE_MAX range (values near 1ns were found to break the construct;
* this grid uses only pilot-confirmed-clean values, >=5ns).
* Full four-phase P24 power stage, all four phases actively commanded by
* the machine (unchanged from R04E9). True zero initial energy on every
* capacitor and inductor (ic=0, UIC).
* TSTOP={tstop_us:g} us / TMAX={tmax_ps:g} ps: pilot-justified multi-
* rotation window (see BOUNDARY.md) -- fixed across the whole grid.
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
.param T_CHARGE_MAX={t_chg:.6e}
* Elapsed-time timer components (NUMERICAL_IDEALIZATION, no physical
* counterpart), same TIMER_C/TIMER_RESET_RON values R04E5/R04E9 used.
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
XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd gh4_cmd gl4_cmd SCB4P_P24_R04E10

BVC1 vc1_mon 0 V=V(xmod:a1,xmod:x1)
BVC2 vc2_mon 0 V=V(xmod:a2,xmod:x2)
BVC3 vc3_mon 0 V=V(xmod:a3,xmod:x3)
RVC1 vc1_mon 0 1k
RVC2 vc2_mon 0 1k
RVC3 vc3_mon 0 1k

* Per-state elapsed FREEWHEEL-time timer (unchanged from R04E9): charges
* only while the machine is in ANY FREE_k state; held reset near 0 by a
* low-Ron switch throughout ANY CHARGE_k state.
CTIMER timer 0 {{TIMER_C}} ic=0
BTIMER_CHG timer 0 I=-1p*((V(state_mon)>0.5)&(V(state_mon)<1.5)|(V(state_mon)>2.5)&(V(state_mon)<3.5)|(V(state_mon)>4.5)&(V(state_mon)<5.5)|(V(state_mon)>6.5)&(V(state_mon)<7.5))
BRESET_GATE reset_gate 0 V=5*((V(state_mon)<0.5)|(V(state_mon)>1.5)&(V(state_mon)<2.5)|(V(state_mon)>3.5)&(V(state_mon)<4.5)|(V(state_mon)>5.5)&(V(state_mon)<6.5))
SRESET timer 0 reset_gate 0 SWRESET
.model SWRESET SW(Ron={{TIMER_RESET_RON}} Roff=1Meg Vt=2.5 Vh=0)

* NEW: per-state elapsed CHARGE-time timer -- exact mirror of the
* freewheel timer above (BOUNDARY.md Section "The mechanism"): charges
* only while the machine is in ANY CHARGE_k state; held reset near 0 by a
* low-Ron switch throughout ANY FREE_k state. Same -1p sign convention
* (verified, not assumed -- R04E9's own diagnosed B-source polarity fix,
* Section 2 of its BOUNDARY.md, applies identically here).
CTIMER_CHG timer_chg 0 {{TIMER_C}} ic=0
BTIMER_CHG2 timer_chg 0 I=-1p*((V(state_mon)<0.5)|(V(state_mon)>1.5)&(V(state_mon)<2.5)|(V(state_mon)>3.5)&(V(state_mon)<4.5)|(V(state_mon)>5.5)&(V(state_mon)<6.5))
BRESET_GATE2 reset_gate_chg 0 V=5*((V(state_mon)>0.5)&(V(state_mon)<1.5)|(V(state_mon)>2.5)&(V(state_mon)<3.5)|(V(state_mon)>4.5)&(V(state_mon)<5.5)|(V(state_mon)>6.5)&(V(state_mon)<7.5))
SRESET_CHG timer_chg 0 reset_gate_chg 0 SWRESET

* Handoff-condition observer: high only while Vout and all three flying
* capacitor voltages simultaneously sit within their declared bands.
BHANDOFF handoff_flag 0 V=5*((V(out)>=VOUT_LO)&(V(out)<=VOUT_HI)&(V(vc1_mon)>=VC1_LO)&(V(vc1_mon)<=VC1_HI)&(V(vc2_mon)>=VC2_LO)&(V(vc2_mon)<=VC2_HI)&(V(vc3_mon)>=VC3_LO)&(V(vc3_mon)<=VC3_HI))
RHANDOFF handoff_flag 0 1k

* Unified event-driven, latched four-phase rotation machine. CHARGE_k
* exits at the R04E3/R04E4 current-limit rule (I(Lk)>=I_LIMIT) OR the NEW
* T_CHARGE_MAX timeout (THIS EXPERIMENT'S single change from R04E9);
* FREE_k exits at the earlier of the natural I(Lk)<=0 event or the
* T_FREEWHEEL_MAX timeout (unchanged from R04E9).
.machine 1p
.state CHARGE1 0
.state FREE1 1
.state CHARGE2 2
.state FREE2 3
.state CHARGE3 4
.state FREE3 5
.state CHARGE4 6
.state FREE4 7
.rule CHARGE1 FREE1 (I(XMOD:L1)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)
.rule FREE1 CHARGE2 (I(XMOD:L1)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE2 FREE2 (I(XMOD:L2)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)
.rule FREE2 CHARGE3 (I(XMOD:L2)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE3 FREE3 (I(XMOD:L3)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)
.rule FREE3 CHARGE4 (I(XMOD:L3)<=0) | (V(timer)>=T_FREEWHEEL_MAX)
.rule CHARGE4 FREE4 (I(XMOD:L4)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)
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
* NOTE: ICS1-3 windowed FROM 2n, not 0, excluding the same sub-2ns t=0
* ideal-switch/capacitor initial-condition numerical startup spike R04E6/
* R04E8/R04E9 already documented and excluded.
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

.subckt SCB4P_P24_R04E10 vin out g gh1_in gl1_in gh2_in gl2_in gh3_in gl3_in gh4_in gl4_in
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
.ends SCB4P_P24_R04E10
.end
"""


def render(i_limit: float, t_chg_ns: float) -> str:
    tstop = TSTOP
    t_chg = t_chg_ns * 1e-9
    t_fw = T_FREEWHEEL_MAX_NS * 1e-9

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
        case_id=case_id(i_limit, t_chg_ns),
        i_limit=i_limit,
        t_chg_ns=t_chg_ns,
        t_fw_ns=T_FREEWHEEL_MAX_NS,
        t_chg=t_chg,
        t_fw=t_fw,
        cfly=CFLY,
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
        for t_chg_ns in T_CHARGE_MAX_LIST_NS:
            text = render(i_limit, t_chg_ns)
            path = CASES / f"{case_id(i_limit, t_chg_ns)}.cir"
            path.write_text(text)
            generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
