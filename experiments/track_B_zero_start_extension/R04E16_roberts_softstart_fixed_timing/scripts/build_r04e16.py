"""Generate R04E16's 6-cell grid: Roberts' PhD dissertation Sec. 3.5
soft-start mechanism (slow Vin ramp through an eFuse, ordinary fixed-
timing PWM running unchanged during the ramp) applied to P24's own
four-phase power stage.

PARENT: R03A (`paper_locked/02_ectc2024_main/spice/
R03A_passive_precharge_to_fixed_pwm_takeover.cir`) -- gate-generation
B-source formulas (BH1..BH4/BL1..BL4, fixed T/4-shifted, D=1/12,
TON=D*T) and four-phase power-stage connectivity (SH1-4/CF1-3/SL1-4/
L1-4, out node, CCO/RLOAD_MAIN) copied unchanged, per BOUNDARY.md
Section 4/5.

CHANGED relative to R03A (BOUNDARY.md Section 4):
- TSTART=0 (PWM active from t=0, not delayed to 150us after Vin has
  already settled to 48V) -- the single most important change.
- TRAMP is now the swept variable under test (was a fixed R02B-derived
  100us).
- LPHASE=1.4666667n (Eq.-4 branch, this project's Track-A mainline)
  REPLACES R03A's own 2.68n.
- CFLY swept across the 0.6-8.7uF first-principles range REPLACES
  R03A's own 53.8uF.
- The R02B passive-divider precharge network (CIN1-4/RLEAK1-4/DPC1-3/
  CDIV, plus the DPRE diode model) is REMOVED ENTIRELY -- true
  zero-energy start with no separate precharge circuit. a1/a2/a3 keep
  exactly their R03A power-stage roles (SH/CF/SL attachments only);
  removing the diodes leaves no dangling node since those nodes never
  depended on the diode network for anything but the (now-removed)
  precharge path.

UNCHANGED (BOUNDARY.md Section 5): four-phase power-stage connectivity,
gate-generation B-source formulas themselves (only TSTART's numeric
value changes), COUT=4.672m, RLOAD=Vout^2/Pout, ideal SWI switch model,
RLDAMP=1u inductor damping, true-zero-energy IC (UIC, no IC= anywhere),
TMAX=50p. RPAR_IN/LPAR_IN (IPEC2018 Table II source parasitics) are
also kept unchanged -- they are source-impedance elements, not part of
the passive divider network BOUNDARY.md Section 4 calls out for
removal.

GRID (BOUNDARY.md Section 6):
- Grid 1 (30x margin): (Cfly=0.6uF,Tramp=30.68us),
  (Cfly=3uF,Tramp=68.61us), (Cfly=8.7uF,Tramp=116.84us).
- Grid 2 (margin sensitivity at Cfly=3uF): Tramp=22.87us (10x),
  Tramp=228.71us (100x).
- Control (near-instantaneous ramp counterfactual): Cfly=3uF,
  Tramp=1us.
TSTOP = TRAMP + 300us per cell (BOUNDARY.md Section 6).

NAMING: case filenames follow R04E14/R04E15's own short-filename
convention (e16_<tag>_f<CFLY>_t<TRAMP>, values in uF/us, 'p' for a
decimal point) to stay well under the ~239-character safe absolute-path
length this worktree's own unusually long path (nested under
.claude/worktrees/agent-<hash>/...) requires -- confirmed <=234 bytes
(<=~230 characters) for the longest case name here.

SOLVER OPTIONS -- diagnosed and added after an initial R03A-verbatim
attempt (`.options reltol=1e-5 abstol=1e-9 chgtol=1e-16`, R03A's own
default "Normal" solver) failed catastrophically on EVERY ONE of the 6
cells: raw-trace forensic inspection (exact record indices/timestamps
reproduced in RESULTS.md) showed a classic near-duplicate-timestamp
solver-retry-chatter episode immediately followed by the INDEPENDENT
PWL source V(vin) itself reading physically impossible values (e.g.
-5171 V, then ~1e24 V) while all real circuit state was still benign
(IL1 10-20A) -- unambiguous proof of Newton-iteration/solver corruption,
not a physical result, occurring early (within the first 18-28
switching periods) and well before any cell's Vin ramp had even
completed. This is fixed by restoring the EXACT solver-stabilization
convention every other Track-B experiment using this project's own
TMAX=50ps resolution already uses (`solver=alt cshunt=1e-15
plotwinsize=0`, verbatim from build_b01/b02/b03/b04/b05/b06 -- i.e.
R04E5 through R04E10, with ZERO exceptions in this track) -- the same
convention BOUNDARY.md Section 5 itself cites as the source of the
TMAX=50ps choice ("matching R04E9-R04E15's own numerical-resolution
convention for this class of circuit"). `cshunt=1e-15` adds a tiny
(femtofarad-scale, physically negligible) shunt capacitance to every
node, a standard SPICE convergence aid for circuits with many ideal
zero-hysteresis switches; `solver=alt` selects LTspice's alternate
matrix solver; `plotwinsize=0` disables output-compression so every
accepted step is retained in the .raw file, unchanged from R03A's own
implicit default. TMAX itself remains exactly 50ps, unchanged -- this
is a numerical-stabilization-technique choice, not a physical/mechanism/
timestep-coarsening change, and is reported transparently in
RESULTS.md rather than silently substituted.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

# (tag, cfly_uF, tramp_us)
GRID1 = [
    ("g1", 0.6e-6, 30.68e-6),
    ("g1", 3.0e-6, 68.61e-6),
    ("g1", 8.7e-6, 116.84e-6),
]
GRID2 = [
    ("g2", 3.0e-6, 22.87e-6),
    ("g2", 3.0e-6, 228.71e-6),
]
CONTROL = [
    ("ctrl", 3.0e-6, 1.0e-6),
]

ALL_CELLS = GRID1 + GRID2 + CONTROL

TEMPLATE = """\
* R04E16 - Roberts' soft-start mechanism on fixed-timing 4-phase PWM
* ({case_id})
* PARENT: R03A (paper_locked/02_ectc2024_main/spice/
* R03A_passive_precharge_to_fixed_pwm_takeover.cir) -- gate-generation
* B-source formulas and 4-phase power-stage connectivity copied
* unchanged. CHANGED: TSTART=0 (PWM active from t=0, implementing
* Roberts' PhD dissertation Sec 3.5's "ordinary switching pattern runs
* during the Vin ramp"), TRAMP swept (see BOUNDARY.md Section 6),
* LPHASE=1.4666667n (Eq.-4 branch, replaces R03A's own 2.68n), CFLY
* swept (replaces R03A's own 53.8uF), R02B passive-divider precharge
* network REMOVED ENTIRELY (no CIN/RLEAK/DPC/CDIV/DPRE -- true
* zero-energy start, no auxiliary precharge circuit of any kind).
* UNCHANGED: power-stage topology, COUT, RLOAD formula, ideal SWI
* switch, RLDAMP, true-zero-energy IC (UIC), TMAX=50p, IPEC2018 Table
* II source parasitics LPAR/RPAR.
* SOLVER OPTIONS: solver=alt/cshunt=1e-15/plotwinsize=0 added (not in
* R03A) -- diagnosed as REQUIRED after R03A's own default "Normal"
* solver corrupted every cell (see RESULTS.md); this restores the exact
* stabilization convention R04E5-R04E10 already use at this same
* TMAX=50p. TMAX itself is unchanged.
* Cfly={cfly_uf:g} uF, Tramp={tramp_us:g} us, Tstop=Tramp+300us.

.param VIN=48 VOUT=1 POUT=250 NP=4 FSW=5Meg T={{1/FSW}}
.param D={{NP*VOUT/VIN}} TON={{D*T}} LPHASE=1.4666667n
.param CFLY={cfly:.6e} COUT=4.672m RLOAD={{VOUT*VOUT/POUT}}
.param TRAMP={tramp:.6e} TSTART=0 TSTOP={{TRAMP+300u}}
.param LPAR=5n RPAR=10m RON=1u ROFF=1T VGATE=5 RLDAMP=1u

VSTEP src 0 PWL(0 0 {{TRAMP}} {{VIN}} {{TSTOP}} {{VIN}})
RPAR_IN src src_r {{RPAR}}
LPAR_IN src_r vin {{LPAR}}

* R02B's passive divider/precharge-diode network (CIN1-4/RLEAK1-4/
* DPC1-3/CDIV/DPRE) is REMOVED ENTIRELY per BOUNDARY.md Section 4 --
* true zero-energy start via the Vin ramp alone, no auxiliary precharge
* circuit. a1/a2/a3 keep exactly their R03A power-stage roles below
* (SH/CF/SL attachments only); no node here is left floating since none
* of a1/a2/a3/x1-x4 depended on the diode network for anything but the
* now-removed precharge path.

* Gate-generation formulas copied unchanged from R03A except TSTART=0
* (PWM active for all time>=0, not delayed to 150us after Vin settles).
BH1 gh1 0 V=if(time>=TSTART & mod(time-TSTART+T,T)<TON,VGATE,0)
BL1 gl1 0 V=if(time<TSTART | mod(time-TSTART+T,T)>=TON,VGATE,0)
BH2 gh2 0 V=if(time>=TSTART & mod(time-TSTART+T-T/4,T)<TON,VGATE,0)
BL2 gl2 0 V=if(time<TSTART | mod(time-TSTART+T-T/4,T)>=TON,VGATE,0)
BH3 gh3 0 V=if(time>=TSTART & mod(time-TSTART+T-T/2,T)<TON,VGATE,0)
BL3 gl3 0 V=if(time<TSTART | mod(time-TSTART+T-T/2,T)>=TON,VGATE,0)
BH4 gh4 0 V=if(time>=TSTART & mod(time-TSTART+T-3*T/4,T)<TON,VGATE,0)
BL4 gl4 0 V=if(time<TSTART | mod(time-TSTART+T-3*T/4,T)>=TON,VGATE,0)

SH1 vin a1 gh1 0 SWI
CF1 a1 x1 {{CFLY}}
SL1 x1 0 gl1 0 SWI
L1 x1 out {{LPHASE}} Rser={{RLDAMP}}
SH2 a1 a2 gh2 0 SWI
CF2 a2 x2 {{CFLY}}
SL2 x2 0 gl2 0 SWI
L2 x2 out {{LPHASE}} Rser={{RLDAMP}}
SH3 a2 a3 gh3 0 SWI
CF3 a3 x3 {{CFLY}}
SL3 x3 0 gl3 0 SWI
L3 x3 out {{LPHASE}} Rser={{RLDAMP}}
SH4 a3 x4 gh4 0 SWI
SL4 x4 0 gl4 0 SWI
L4 x4 out {{LPHASE}} Rser={{RLDAMP}}

CCO out 0 {{COUT}}
RLOAD_MAIN out 0 {{RLOAD}}
.model SWI SW(Ron={{RON}} Roff={{ROFF}} Vt=2.5 Vh=0)

.meas tran VC1_INIT FIND V(a1,x1) AT 1n
.meas tran VC2_INIT FIND V(a2,x2) AT 1n
.meas tran VC3_INIT FIND V(a3,x3) AT 1n
.meas tran VC1_AT_TRAMP FIND V(a1,x1) AT {{TRAMP}}
.meas tran VC2_AT_TRAMP FIND V(a2,x2) AT {{TRAMP}}
.meas tran VC3_AT_TRAMP FIND V(a3,x3) AT {{TRAMP}}
.meas tran VOUT_AT_TRAMP FIND V(out) AT {{TRAMP}}
.meas tran VC1_FINAL FIND V(a1,x1) AT {{TSTOP-1n}}
.meas tran VC2_FINAL FIND V(a2,x2) AT {{TSTOP-1n}}
.meas tran VC3_FINAL FIND V(a3,x3) AT {{TSTOP-1n}}
.meas tran VOUT_FINAL FIND V(out) AT {{TSTOP-1n}}
.meas tran VOUT_PK MAX V(out) FROM 0 TO {{TSTOP}}
.meas tran VOUT_MIN MIN V(out) FROM 0 TO {{TSTOP}}
.meas tran VOUT_OVERSHOOT PARAM (VOUT_PK-VOUT)/VOUT
.meas tran IIN_PK MAX -I(VSTEP) FROM 0 TO {{TSTOP}}
.meas tran IL1_MIN MIN I(L1) FROM 0 TO {{TSTOP}}
.meas tran IL1_MAX MAX I(L1) FROM 0 TO {{TSTOP}}
.meas tran IL2_MIN MIN I(L2) FROM 0 TO {{TSTOP}}
.meas tran IL2_MAX MAX I(L2) FROM 0 TO {{TSTOP}}
.meas tran IL3_MIN MIN I(L3) FROM 0 TO {{TSTOP}}
.meas tran IL3_MAX MAX I(L3) FROM 0 TO {{TSTOP}}
.meas tran IL4_MIN MIN I(L4) FROM 0 TO {{TSTOP}}
.meas tran IL4_MAX MAX I(L4) FROM 0 TO {{TSTOP}}
.meas tran VOUT_ERR PARAM abs(VOUT_FINAL-1)/1
.meas tran VC1_ERR PARAM abs(VC1_FINAL-36)/36
.meas tran VC2_ERR PARAM abs(VC2_FINAL-24)/24
.meas tran VC3_ERR PARAM abs(VC3_FINAL-12)/12
.meas tran LADDER_ERR PARAM VC1_ERR+VC2_ERR+VC3_ERR

.options plotwinsize=0 reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt cshunt=1e-15
.save V(vin) V(out) V(a1,x1) V(a2,x2) V(a3,x3) I(VSTEP) I(L1) I(L2) I(L3) I(L4)
.tran 0 {{TSTOP}} 0 50p UIC
.end
"""


def fmt_uf(x: float) -> str:
    uf = x * 1e6
    if abs(uf - round(uf)) < 1e-6:
        return f"{round(uf)}"
    return f"{uf:g}".replace(".", "p")


def fmt_us(x: float) -> str:
    us = x * 1e6
    if abs(us - round(us)) < 1e-6:
        return f"{round(us)}"
    return f"{us:g}".replace(".", "p")


def case_id(tag: str, cfly: float, tramp: float) -> str:
    return f"e16_{tag}_f{fmt_uf(cfly)}_t{fmt_us(tramp)}"


def render(tag: str, cfly: float, tramp: float) -> str:
    return TEMPLATE.format(
        case_id=case_id(tag, cfly, tramp),
        cfly=cfly,
        cfly_uf=cfly * 1e6,
        tramp=tramp,
        tramp_us=tramp * 1e6,
    )


def write_case(tag: str, cfly: float, tramp: float) -> Path:
    CASES.mkdir(parents=True, exist_ok=True)
    text = render(tag, cfly, tramp)
    path = CASES / f"{case_id(tag, cfly, tramp)}.cir"
    path.write_text(text)
    return path


def build_all() -> list[Path]:
    return [write_case(tag, cfly, tramp) for tag, cfly, tramp in ALL_CELLS]


if __name__ == "__main__":
    paths = build_all()
    print(f"# generated {len(paths)} cases")
    for p in paths:
        print(p)
