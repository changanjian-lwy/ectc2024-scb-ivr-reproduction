"""Generate R04E6's EPE2019 3-state charge-redistribution ladder-bootstrap grid.

SCOPE (see BOUNDARY.md for the complete, per-item borrowed-fact table):

This experiment borrows ONE NEW thing from Roberts/McRae/Prodic, EPE'19 ECCE
Europe ("A Multiphase Series-Capacitor Buck Converter with Reduced Flying
Capacitor Volume and Auxiliary Start-Up Circuit"): the THREE-STATE CHARGE-
REDISTRIBUTION START-UP SEQUENCE shown in that paper's own Fig. 5, drawn for
the paper's own "conventional 4-phase SC buck" comparison topology (not
their proposed CSC-buck main contribution). CFLY=53.8 uF and COUT=4.672 mF
are an ALREADY-APPROVED cross-source candidate from the same paper (used
unchanged in R02-R04E5); this experiment does not re-derive those.

TRUTH-TABLE DERIVATION (done independently here, then cross-checked against
the rendered Fig. 5 raster):
  This project's own already-validated P24 four-phase connectivity (copied
  unchanged from R04E3_P24_minimal_zero_start_event_cycle.cir's
  SCB4P_P24_EVENT subcircuit) is: a series high-side chain
  vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4, with flying capacitor CSk bridging node
  ak to xk (k=1,2,3; no C4), SLk grounding xk, and Lk from xk to the common
  "out" node.  Basic charge-conservation/loop reasoning on THIS topology
  gives:
    (a) CHARGING:            H1 ON, L1 ON,              all else OFF.
        -> vin-SH1-a1-CS1-x1-SL1-g. Only C1 is in this loop.
    (b) CHARGE REDISTRIBUTION I:  H2 ON, L1 ON, L2 ON,   all else OFF.
        -> g-SL1-x1-CS1-a1-SH2-a2-CS2-x2-SL2-g. C1<->C2 loop closed through
           the shared ground return on both ends.
    (c) CHARGE REDISTRIBUTION II: H3 ON, L2 ON, L3 ON,   all else OFF.
        -> g-SL2-x2-CS2-a2-SH3-a3-CS3-x3-SL3-g. C2<->C3 loop.
  H4 and L4 are never asserted in any of the three states (matches Fig. 5:
  the bottom, phase-4 pair of switches is black/OFF in every one of the
  three panels).

  This independently-derived table was THEN checked against a rendered
  page-5 raster (pymupdf, dpi=500) of the source PDF and MATCHES it exactly,
  switch-for-switch, in all three panels. It does NOT match this task's own
  a-priori paraphrase ("C1+C2+C3 in series, only the outermost switches"),
  which is corrected in BOUNDARY.md Section 3 -- state (a) charges C1 ALONE
  (phase-1's own H/L pair), not a 3-capacitor series stack, exactly as the
  source paper's own body text says ("the effective capacitance is C1
  itself" for Fig. 5(a), p.5).

MECHANISM: fixed hold-time, open-loop (no .machine/event detector). The
source paper gives no threshold or event to trigger a state change -- only
"repeatedly cycled through until the desired voltages ... are obtained"
(p.5) -- so a fixed per-state hold time TH, swept as a free sensitivity
axis, is the most direct source-faithful implementation, not a violation of
this project's physical-event boundary-control principle (that principle
governs the separate, already-tested P24 steady-state ZVS admission chain;
this sub-mechanism is explicitly out of that scope, see BOUNDARY.md).

Two free sensitivity axes (SENSITIVITY_ONLY, not paper values):
  TH (hold time applied equally to states a, b, c each cycle) in
    {200 ns, 1 us, 5 us, 20 us}
  NCYC (number of full a-b-c cycles) in {1, 3, 5, 10}
16 cases total.
"""

from __future__ import annotations

from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E6_epe2019_charge_redistribution_startup"
CASES = HERE / "cases"

GS_LIB = (
    "../../../../paper_locked/04_component_models/GS61008T_typical_params.lib"
)

TH_S = (200e-9, 1e-6, 5e-6, 20e-6)
NCYC_LIST = (1, 3, 5, 10)

VGATE = 5.0
EDGE = 100e-12  # 100 ps commanded-gate rise/fall; << smallest TH (200 ns).
TSTART = 1e-9  # small initial delay before state (a) of cycle 1, matching
# this project's own R04A/R04C convention (T0=1n) of not switching exactly
# at the t=0 operating-point solve.


def _fmt(t: float) -> str:
    return f"{t:.6e}"


def pwl_points(intervals: list[tuple[float, float]], tstop: float) -> str:
    """Build an LTspice PWL(...) point list for a signal that is HIGH
    (VGATE) during each (start, end) interval and LOW (0) elsewhere, with a
    short EDGE ramp at every transition. Intervals must be sorted and
    non-overlapping."""

    pts: list[tuple[float, float]] = [(0.0, 0.0)]
    for start, end in intervals:
        if start <= 0.0:
            # Command HIGH from t=0 directly (true zero-start case only).
            pts = [(0.0, VGATE)]
        else:
            pts.append((start - EDGE, 0.0))
            pts.append((start, VGATE))
        pts.append((end - EDGE, VGATE))
        pts.append((end, 0.0))
    if tstop - pts[-1][0] > 1e-15:
        pts.append((tstop, 0.0))
    # De-duplicate/clip non-strictly-increasing points. LTspice's PWL
    # source requires STRICTLY increasing time; floating-point jitter (or
    # EDGE pushing a breakpoint before the previous one, for pathologically
    # small TH not present in this grid) can otherwise produce two points
    # at the same instant, which LTspice rejects outright.
    cleaned: list[tuple[float, float]] = []
    last_t = -1.0
    for t, v in pts:
        if t <= last_t:
            continue
        cleaned.append((t, v))
        last_t = t
    return " ".join(f"{_fmt(t)} {v:g}" for t, v in cleaned)


def build_gate_intervals(th: float, ncyc: int) -> dict[str, list[tuple[float, float]]]:
    gh1: list[tuple[float, float]] = []
    gl1: list[tuple[float, float]] = []
    gh2: list[tuple[float, float]] = []
    gl2: list[tuple[float, float]] = []
    gh3: list[tuple[float, float]] = []
    gl3: list[tuple[float, float]] = []
    for i in range(ncyc):
        cyc0 = TSTART + i * 3 * th
        a0, a1 = cyc0, cyc0 + th
        b0, b1 = a1, a1 + th
        c0, c1 = b1, b1 + th
        gh1.append((a0, a1))
        gl1.append((a0, b1))  # L1 stays on through states a AND b
        gh2.append((b0, b1))
        gl2.append((b0, c1))  # L2 stays on through states b AND c
        gh3.append((c0, c1))
        gl3.append((c0, c1))
    return {
        "gh1": gh1,
        "gl1": gl1,
        "gh2": gh2,
        "gl2": gl2,
        "gh3": gh3,
        "gl3": gl3,
    }


TEMPLATE = """\
* R04E6 - EPE2019 Fig.5 3-state charge-redistribution ladder bootstrap ({case_id})
* SENSITIVITY CASE: TH={th_ns:g} ns per state, NCYC={ncyc:d} cycles.
* CROSS_PAPER_EXTENSION (startup mechanism only): Roberts/McRae/Prodic,
* EPE'19 ECCE Europe, Fig. 5 (p.5), "conventional 4-phase SC buck" states
* (a) Charging / (b) Charge Redistribution I / (c) Charge Redistribution II.
* See BOUNDARY.md for the full per-item borrowed-fact table and the
* independent truth-table derivation/cross-check against the rendered figure.
* Power-stage connectivity (SH1-4/SL1-4/CS1-3/L1-4 node names) is copied
* UNCHANGED from paper_locked/02_ectc2024_main/spice/
* R04E3_P24_minimal_zero_start_event_cycle.cir's SCB4P_P24_EVENT subcircuit
* (already-validated P24 four-phase connectivity; reused, not reinvented).
* CFLY=53.8uF, COUT=4.672mF: already-approved EPE2019 cross-source
* candidates, unchanged from R02-R04E5 (not re-derived here).
* True zero initial energy on every capacitor and inductor (ic=0, UIC),
* same starting point as R04E3/R04E5. SCOPE: ladder bootstrap ONLY -- no
* PWM, no P24 steady-state ZVS admission chain, no Vout regulation attempt.
* Open-loop FIXED hold time per state (the source paper gives no event or
* threshold to detect; TH and NCYC are free SENSITIVITY_ONLY axes).

.include "{gs_lib}"
.param VIN=48 VOUT_REF=1 POUT_MODULE=250 NP=4 NM=4
.param LPHASE=1.466666666666667n CFLY={{4*10u+2*4.7u+2*2.2u}}
.param COUT={{8*220u+32*47u+64*22u}} RLOAD={{VOUT_REF*VOUT_REF/POUT_MODULE}}
.param CH={{GS61008T_COTR_0_50V}} CL={{2*GS61008T_COTR_0_50V}}
.param RHS={{GS61008T_RDS_TYP_25C}} RLS={{GS61008T_RDS_TYP_25C/2}}
.param RLDAMP=1u

VRAIL vin 0 {{VIN}}
CCO out 0 {{COUT}} ic=0
RLOAD_MAIN out 0 {{RLOAD}}
XMOD vin out 0 gh1_cmd gl1_cmd gh2_cmd gl2_cmd gh3_cmd gl3_cmd SCB4P_P24_R04E6

VGH1 gh1_cmd 0 PWL({gh1_pwl})
VGL1 gl1_cmd 0 PWL({gl1_pwl})
VGH2 gh2_cmd 0 PWL({gh2_pwl})
VGL2 gl2_cmd 0 PWL({gl2_pwl})
VGH3 gh3_cmd 0 PWL({gh3_pwl})
VGL3 gl3_cmd 0 PWL({gl3_pwl})

.meas tran VOUT_FINAL FIND V(out) AT {tstop:.6e}
.meas tran IL1_MAX MAX I(XMOD:L1) FROM 0 TO {tstop:.6e}
.meas tran IL1_MIN MIN I(XMOD:L1) FROM 0 TO {tstop:.6e}
.meas tran IL2_MAX MAX I(XMOD:L2) FROM 0 TO {tstop:.6e}
.meas tran IL2_MIN MIN I(XMOD:L2) FROM 0 TO {tstop:.6e}
.meas tran IL3_MAX MAX I(XMOD:L3) FROM 0 TO {tstop:.6e}
.meas tran IL3_MIN MIN I(XMOD:L3) FROM 0 TO {tstop:.6e}
.meas tran ICS1_MAX MAX I(XMOD:CS1) FROM 0 TO {tstop:.6e}
.meas tran ICS1_MIN MIN I(XMOD:CS1) FROM 0 TO {tstop:.6e}
.meas tran ICS2_MAX MAX I(XMOD:CS2) FROM 0 TO {tstop:.6e}
.meas tran ICS2_MIN MIN I(XMOD:CS2) FROM 0 TO {tstop:.6e}
.meas tran ICS3_MAX MAX I(XMOD:CS3) FROM 0 TO {tstop:.6e}
.meas tran ICS3_MIN MIN I(XMOD:CS3) FROM 0 TO {tstop:.6e}
.meas tran ICS1_INRUSH_CYC1 MAX I(XMOD:CS1) FROM {a0:.6e} TO {a1:.6e}
.meas tran ICS1_STATEB_CYC1_MAX MAX I(XMOD:CS1) FROM {a1:.6e} TO {b1:.6e}
.meas tran ICS1_STATEB_CYC1_MIN MIN I(XMOD:CS1) FROM {a1:.6e} TO {b1:.6e}
.meas tran ICS2_STATEB_CYC1_MAX MAX I(XMOD:CS2) FROM {a1:.6e} TO {b1:.6e}
.meas tran ICS2_STATEB_CYC1_MIN MIN I(XMOD:CS2) FROM {a1:.6e} TO {b1:.6e}
.meas tran ICS2_STATEC_CYC1_MAX MAX I(XMOD:CS2) FROM {b1:.6e} TO {c1:.6e}
.meas tran ICS2_STATEC_CYC1_MIN MIN I(XMOD:CS2) FROM {b1:.6e} TO {c1:.6e}
.meas tran ICS3_STATEC_CYC1_MAX MAX I(XMOD:CS3) FROM {b1:.6e} TO {c1:.6e}
.meas tran ICS3_STATEC_CYC1_MIN MIN I(XMOD:CS3) FROM {b1:.6e} TO {c1:.6e}
{cycle_meas}
.options plotwinsize=0 reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt cshunt=1e-15
.save V(out) V(xmod:a1,xmod:x1) V(xmod:a2,xmod:x2) V(xmod:a3,xmod:x3) I(XMOD:L1) I(XMOD:L2) I(XMOD:L3) I(XMOD:CS1) I(XMOD:CS2) I(XMOD:CS3) V(gh1_cmd) V(gl1_cmd) V(gh2_cmd) V(gl2_cmd) V(gh3_cmd) V(gl3_cmd)
.tran 0 {tstop:.6e} 0 1n UIC

.subckt SCB4P_P24_R04E6 vin out g gh1_in gl1_in gh2_in gl2_in gh3_in gl3_in
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
.ends SCB4P_P24_R04E6
.end
"""


def case_id(th: float, ncyc: int) -> str:
    th_ns = th * 1e9
    th_tag = f"{th_ns:g}".replace(".", "p")
    return f"r04e6_th_{th_tag}ns_ncyc_{ncyc:d}"


def render(th: float, ncyc: int) -> str:
    tstop = TSTART + ncyc * 3 * th
    gates = build_gate_intervals(th, ncyc)
    cycle_meas_lines = []
    for i in range(ncyc):
        cyc_end = TSTART + (i + 1) * 3 * th
        j = i + 1
        cycle_meas_lines.append(
            f".meas tran VC1_CYC{j} FIND V(xmod:a1,xmod:x1) AT {cyc_end:.6e}"
        )
        cycle_meas_lines.append(
            f".meas tran VC2_CYC{j} FIND V(xmod:a2,xmod:x2) AT {cyc_end:.6e}"
        )
        cycle_meas_lines.append(
            f".meas tran VC3_CYC{j} FIND V(xmod:a3,xmod:x3) AT {cyc_end:.6e}"
        )
    a0 = TSTART
    a1 = TSTART + th
    b1 = TSTART + 2 * th
    c1 = TSTART + 3 * th
    return TEMPLATE.format(
        case_id=case_id(th, ncyc),
        th_ns=th * 1e9,
        ncyc=ncyc,
        gs_lib=GS_LIB,
        tstop=tstop,
        gh1_pwl=pwl_points(gates["gh1"], tstop),
        gl1_pwl=pwl_points(gates["gl1"], tstop),
        gh2_pwl=pwl_points(gates["gh2"], tstop),
        gl2_pwl=pwl_points(gates["gl2"], tstop),
        gh3_pwl=pwl_points(gates["gh3"], tstop),
        gl3_pwl=pwl_points(gates["gl3"], tstop),
        a0=a0,
        a1=a1,
        b1=b1,
        c1=c1,
        cycle_meas="\n".join(cycle_meas_lines),
    )


def build() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for th in TH_S:
        for ncyc in NCYC_LIST:
            text = render(th, ncyc)
            path = CASES / f"{case_id(th, ncyc)}.cir"
            path.write_text(text)
            generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
