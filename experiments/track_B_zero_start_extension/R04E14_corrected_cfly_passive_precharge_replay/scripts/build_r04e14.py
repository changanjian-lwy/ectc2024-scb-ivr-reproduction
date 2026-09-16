"""Generate R04E14's corrected-Cfly replay of the R02A/R02B passive-precharge
startup module.

PARENT: R02A/R02B (paper_locked/02_ectc2024_main/spice/
R02A_ipec2018_passive_precharge_only.cir and
R02B_passive_precharge_charge_ramp_sweep.cir). This module is a
byte-level-faithful copy of R02B's own circuit body -- the four equal
input-divider capacitors, LPAR=5nH/RPAR=10mOhm source parasitics, the three
ideal precharge diodes (Ron=1m Roff=1T Vfwd=0), ground-referenced flying
capacitor lower terminals, true-zero-energy initial conditions (UIC, no IC
statements), and the exact same .meas definitions (VC1/2/3_FINAL, RATIO21,
RATIO31, LADDER_ERR, IIN_PK, ID1/2/3_PK) -- with NO PWM, switches, or load,
exactly as R02A/R02B themselves were.

THE ONLY CHANGE relative to R02B: CFLY is fixed at 3 uF (this project's own
corrected first-principles candidate, R04E8's value) instead of R02B's
53.8 uF, and CDIV's swept range is re-scaled to {10, 30, 100, 300} uF
(around R02A's own found 10:1 CDIV:CFLY ratio, i.e. 30 uF) instead of
R02B's {10, 53.8, 538, 1076} uF, which was scaled for the old 53.8 uF
target. TRAMP's swept range, {1, 10, 100} us, is unchanged from R02B.

UNLIKE R02B (which uses LTspice's own .step param mechanism to run all 12
of its cells inside one file/one LTspice invocation), this experiment
generates ONE NETLIST FILE PER GRID CELL (14 files total, matching this
project's own recent R04E8-R04E13 per-cell convention and the task's own
"14 LTspice runs" framing) -- each file is a single-cell instantiation of
the identical R02B circuit body with CDIV/TRAMP/CFLY as fixed .param
values instead of .step lists. This is a packaging/tooling difference
only: the circuit topology, values, and .meas definitions are unchanged
from, and directly comparable to, R02B's own multi-step file.

NAMING NOTE: case filenames are kept deliberately short
(e14_c<CDIV>_t<TRAMP>_f<CFLY>.cir, values in uF/us with 'p' for a decimal
point). This worktree's own absolute path is unusually long (nested under
.claude/worktrees/agent-<hash>/...), and a directly measured, reproducible
LTspice-runner failure threshold was found empirically during this
experiment's own piloting: full absolute .cir paths at or above ~250-259
characters cause the underlying wine-hosted LTspice.exe to silently fail
to open its per-run measurement database ("unable to open database file"
in the .log) and emit NO .meas results at all, while otherwise reporting
a normal, fast, error-free elapsed time -- a silent failure mode, not a
convergence or circuit problem. Paths at or below ~239 characters were
confirmed clean in the same test. Short names keep every case safely
under that threshold with margin.

Primary grid (12 cells): CFLY=3uF fixed x CDIV in {10,30,100,300} uF x
TRAMP in {1,10,100} us.

Secondary grid (2 cells): built separately by build_r04e14_secondary.py
after the primary grid's own best (CDIV, TRAMP) cell is identified by its
normalized LADDER_ERR.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

CDIV_LIST_PRIMARY = (10e-6, 30e-6, 100e-6, 300e-6)
TRAMP_LIST = (1e-6, 10e-6, 100e-6)
CFLY_PRIMARY = 3e-6

TEMPLATE = """\
* R04E14 - corrected-Cfly replay of the R02A/R02B passive-precharge
* startup module ({case_id})
* PARENT: R02B_passive_precharge_charge_ramp_sweep.cir (byte-level-faithful
* circuit body: four equal input-divider capacitors, LPAR=5nH/RPAR=10mOhm
* source parasitics (IPEC 2018 Table II), three ideal precharge diodes
* (Ron=1m Roff=1T Vfwd=0), flying-capacitor lower terminals tied to the
* module reference (R02A's own "all-low-side-on precharge state"
* approximation), true-zero-energy initial conditions (UIC, no IC
* statements), no PWM/switches/load -- unchanged from R02A/R02B.
* ONLY CHANGE from R02B: CFLY={cfly_uf:g} uF (this project's own corrected
* first-principles candidate; R02B used the cross-topology-suspect
* 53.8 uF) and this cell's own (CDIV, TRAMP) point from the re-scaled
* {{10,30,100,300}} uF x {{1,10,100}} us grid (BOUNDARY.md Section 4),
* replacing R02B's own {{10,53.8,538,1076}} uF x {{1,10,100}} us grid.
* CDIV={cdiv_uf:g} uF, TRAMP={tramp_us:g} us.
* This file uses fixed .param values (one cell per file) rather than
* R02B's own .step param lists (one file, 12 cells) -- a packaging
* difference only; the circuit body and .meas definitions are otherwise
* an unchanged, direct copy of R02B's own.

.param VIN=48 CFLY={cfly:.6e} CDIV={cdiv:.6e} TRAMP={tramp:.6e} LPAR=5n RPAR=10m RLEAK=1G

VSTEP src 0 PWL(0 0 {{TRAMP}} {{VIN}} 500u {{VIN}})
RPAR_IN src src_r {{RPAR}}
LPAR_IN src_r vin {{LPAR}}

CIN1 vin tap3 {{CDIV}}
CIN2 tap3 tap2 {{CDIV}}
CIN3 tap2 tap1 {{CDIV}}
CIN4 tap1 0 {{CDIV}}
RLEAK1 vin tap3 {{RLEAK}}
RLEAK2 tap3 tap2 {{RLEAK}}
RLEAK3 tap2 tap1 {{RLEAK}}
RLEAK4 tap1 0 {{RLEAK}}

DPC1 tap3 vc1 DPRE
DPC2 tap2 vc2 DPRE
DPC3 tap1 vc3 DPRE
CF1 vc1 0 {{CFLY}}
CF2 vc2 0 {{CFLY}}
CF3 vc3 0 {{CFLY}}
.model DPRE D(Ron=1m Roff=1T Vfwd=0)

.meas tran VC1_FINAL AVG V(vc1) FROM 490u TO 500u
.meas tran VC2_FINAL AVG V(vc2) FROM 490u TO 500u
.meas tran VC3_FINAL AVG V(vc3) FROM 490u TO 500u
.meas tran RATIO21 PARAM VC2_FINAL/VC1_FINAL
.meas tran RATIO31 PARAM VC3_FINAL/VC1_FINAL
.meas tran LADDER_ERR PARAM abs(VC1_FINAL-36)/36+abs(VC2_FINAL-24)/24+abs(VC3_FINAL-12)/12
.meas tran IIN_PK MAX -I(VSTEP) FROM 0 TO 500u
.meas tran ID1_PK MAX I(DPC1) FROM 0 TO 500u
.meas tran ID2_PK MAX I(DPC2) FROM 0 TO 500u
.meas tran ID3_PK MAX I(DPC3) FROM 0 TO 500u

.options reltol=1e-5 abstol=1e-10 chgtol=1e-16
.save V(vin) V(vc1) V(vc2) V(vc3) I(VSTEP) I(DPC1) I(DPC2) I(DPC3)
.tran 0 500u 0 10n UIC
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


def case_id(cdiv: float, tramp: float, cfly: float) -> str:
    # Kept deliberately short -- see module docstring's NAMING NOTE for the
    # empirically-measured LTspice-runner path-length failure mode this
    # avoids. Encodes CDIV (uF), TRAMP (us), CFLY (uF) in that order.
    return f"e14_c{fmt_uf(cdiv)}_t{fmt_us(tramp)}_f{fmt_uf(cfly)}"


def render(cdiv: float, tramp: float, cfly: float) -> str:
    return TEMPLATE.format(
        case_id=case_id(cdiv, tramp, cfly),
        cfly=cfly,
        cfly_uf=cfly * 1e6,
        cdiv=cdiv,
        cdiv_uf=cdiv * 1e6,
        tramp=tramp,
        tramp_us=tramp * 1e6,
    )


def build_primary() -> list[Path]:
    CASES.mkdir(parents=True, exist_ok=True)
    generated = []
    for cdiv in CDIV_LIST_PRIMARY:
        for tramp in TRAMP_LIST:
            text = render(cdiv, tramp, CFLY_PRIMARY)
            path = CASES / f"{case_id(cdiv, tramp, CFLY_PRIMARY)}.cir"
            path.write_text(text)
            generated.append(path)
    return generated


if __name__ == "__main__":
    paths = build_primary()
    print(f"# generated {len(paths)} primary-grid cases")
    for p in paths:
        print(p)
