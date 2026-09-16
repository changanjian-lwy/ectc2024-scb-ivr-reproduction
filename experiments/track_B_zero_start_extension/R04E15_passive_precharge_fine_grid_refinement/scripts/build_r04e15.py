"""Generate R04E15's fine-grid refinement of R04E14's passive-precharge
PASS cells.

PARENT: R04E14 (`experiments/track_B_zero_start_extension/
R04E14_corrected_cfly_passive_precharge_replay/`), itself a byte-level-
faithful copy of R02B's own circuit body (`paper_locked/02_ectc2024_main/
spice/R02B_passive_precharge_charge_ramp_sweep.cir`): four equal
input-divider capacitors, LPAR=5nH/RPAR=10mOhm source parasitics (IPEC 2018
Table II), three ideal precharge diodes (Ron=1m Roff=1T Vfwd=0),
ground-referenced flying-capacitor lower terminals (R02A's own
"all-low-side-on precharge state" approximation), true-zero-energy initial
conditions (UIC, no IC statements), no PWM/switches/load, and the exact
same .meas definitions (VC1/2/3_FINAL, RATIO21, RATIO31, LADDER_ERR,
IIN_PK, ID1/2/3_PK) -- unchanged from R02A/R02B/R04E14.

NO mechanism, topology, or parameter-model change of any kind relative to
R04E14. This module (build_r04e15.py) generates Grid A (6 cells: CDIV
refinement at fixed CFLY=3uF/TRAMP=100us) and Grid B (5 cells: TRAMP
refinement at fixed CFLY=3uF/CDIV=300uF) per BOUNDARY.md Section 3. Grid C
(2 cells, CFLY sensitivity at the actual winning (CDIV,TRAMP) point) is
built separately by build_r04e15_gridc.py once Grid A/B results (plus
R04E14's own CDIV=300/TRAMP=100 cell) identify the winning point.

NAMING: case filenames follow R04E14's own short-filename convention
(e15_c<CDIV>_t<TRAMP>_f<CFLY>.cir, values in uF/us with 'p' for a decimal
point) to stay well under the ~239-character safe absolute-path length
R04E14 empirically found for this worktree's own unusually long path
(nested under .claude/worktrees/agent-<hash>/...) -- LTspice's wine-hosted
executable silently fails to open its per-run measurement database and
emits NO .meas output above roughly 250-259 characters.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

CFLY_FIXED = 3e-6

# Grid A: CDIV refinement, TRAMP=100us fixed.
GRID_A_CDIV = (150e-6, 200e-6, 250e-6, 350e-6, 400e-6, 500e-6)
GRID_A_TRAMP = 100e-6

# Grid B: TRAMP refinement, CDIV=300uF fixed.
GRID_B_CDIV = 300e-6
GRID_B_TRAMP = (20e-6, 50e-6, 75e-6, 150e-6, 200e-6)

TEMPLATE = """\
* R04E15 - fine-grid refinement of R04E14's passive-precharge PASS cells
* ({case_id})
* PARENT: R04E14 (byte-level-faithful copy of R02B's own circuit body):
* four equal input-divider capacitors, LPAR=5nH/RPAR=10mOhm source
* parasitics (IPEC 2018 Table II), three ideal precharge diodes
* (Ron=1m Roff=1T Vfwd=0), flying-capacitor lower terminals tied to the
* module reference (R02A's own "all-low-side-on precharge state"
* approximation), true-zero-energy initial conditions (UIC, no IC
* statements), no PWM/switches/load -- unchanged from R02A/R02B/R04E14.
* NO mechanism, topology, or parameter-model change relative to R04E14 --
* only this cell's own (CDIV, TRAMP, CFLY) point changes, per BOUNDARY.md
* Section 3's Grid A/B fine-grid refinement of R04E14's own coarse grid.
* CDIV={cdiv_uf:g} uF, TRAMP={tramp_us:g} us, CFLY={cfly_uf:g} uF.

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
    # Short by design -- see module docstring's NAMING section.
    return f"e15_c{fmt_uf(cdiv)}_t{fmt_us(tramp)}_f{fmt_uf(cfly)}"


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


def write_case(cdiv: float, tramp: float, cfly: float) -> Path:
    CASES.mkdir(parents=True, exist_ok=True)
    text = render(cdiv, tramp, cfly)
    path = CASES / f"{case_id(cdiv, tramp, cfly)}.cir"
    path.write_text(text)
    return path


def build_grid_a() -> list[Path]:
    return [write_case(cdiv, GRID_A_TRAMP, CFLY_FIXED) for cdiv in GRID_A_CDIV]


def build_grid_b() -> list[Path]:
    return [write_case(GRID_B_CDIV, tramp, CFLY_FIXED) for tramp in GRID_B_TRAMP]


if __name__ == "__main__":
    paths = build_grid_a() + build_grid_b()
    print(f"# generated {len(paths)} Grid A + Grid B cases")
    for p in paths:
        print(p)
