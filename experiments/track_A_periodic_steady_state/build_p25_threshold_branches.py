"""Build source-labelled P25 four-phase threshold branches from locked A16.

The builder performs two auditable text substitutions only:
1. P25's all-inactive-low Mode-1 rule is extended from three to four phases.
2. The negative-current target is selected as 5%, 8%, or 10%.
All electrical state and component text remains inherited from A16.
"""

from pathlib import Path


TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A16_tighten_04_C3" / "A16_tighten_only_C3_from_A15.cir"

BRANCHES = {
    "A21_p25_all_inactive_lows_05pct": 0.05,
    "A22_p25_all_inactive_lows_08pct": 0.08,
    "A24_p25_all_inactive_lows_09pct": 0.09,
    "A23_p25_all_inactive_lows_10pct": 0.10,
}

OLD_CONTROLS = """BL1 gl1 g V=if(time>=T0 & (V(gh4)>2.5 | (V(gh1)<2.5 & V(x1)<=0 & I(L1)>-INEG)),VG,0)
BL2 gl2 g V=if(time>=T0 & (V(gh1)>2.5 | (V(gh2)<2.5 & V(x2)<=0 & I(L2)>-INEG)),VG,0)
BL3 gl3 g V=if(time>=T0 & (V(gh2)>2.5 | (V(gh3)<2.5 & V(x3)<=0 & I(L3)>-INEG)),VG,0)
BL4 gl4 g V=if(time>=T0 & (V(gh3)>2.5 | (V(gh4)<2.5 & V(x4)<=0 & I(L4)>-INEG)),VG,0)"""

NEW_CONTROLS = """* P25 Mode-1 rule extended from nP=3 to nP=4: while QH1 is active,
* all inactive lows L2-L4 are commanded ON. Phase-1 uses explicit event memory:
* x1<=0 admits SL1 once, then SL1 stays ON through the rotated high-side support
* intervals and is released only after QH4 ends and iL1 reaches -INEG.
.machine 1p
.state P1_WAIT_LOW_ZVS 0
.state P1_LOW_LATCHED 1
.state P1_LOW_RELEASED 2
.rule P1_WAIT_LOW_ZVS P1_LOW_LATCHED (time>TON)*(V(x1)<=0)
.rule P1_LOW_LATCHED P1_LOW_RELEASED (time>3*T/NP+TON)*(I(L1)<=-INEG)
.output (gl1) VG*(state==P1_LOW_LATCHED)
.output (p1_state) state
.endmachine
RGL1_MACHINE gl1 g 1k
RSTATE_P1 p1_state g 1k
BL2 gl2 g V=if(time>=T0 & (V(gh1)>2.5 | V(gh3)>2.5 | V(gh4)>2.5 | (V(gh2)<2.5 & V(x2)<=0 & I(L2)>-INEG)),VG,0)
BL3 gl3 g V=if(time>=T0 & (V(gh1)>2.5 | V(gh2)>2.5 | V(gh4)>2.5 | (V(gh3)<2.5 & V(x3)<=0 & I(L3)>-INEG)),VG,0)
BL4 gl4 g V=if(time>=T0 & (V(gh1)>2.5 | V(gh2)>2.5 | V(gh3)>2.5 | (V(gh4)<2.5 & V(x4)<=0 & I(L4)>-INEG)),VG,0)"""


source = SOURCE.read_text()
if OLD_CONTROLS not in source:
    raise SystemExit("locked A16 controller block no longer matches builder")
if "NEG_FRAC=.02" not in source:
    raise SystemExit("locked A16 2% parameter no longer matches builder")

for directory_name, fraction in BRANCHES.items():
    directory = TRACK / directory_name
    directory.mkdir(exist_ok=True)
    case = source.replace(
        "* A16 - periodic seed tightening 04: C3 only",
        f"* {directory_name} - P25 all-inactive-low nP=4 extension",
        1,
    )
    case = case.replace("NEG_FRAC=.02", f"NEG_FRAC={fraction:.2f}", 1)
    case = case.replace(OLD_CONTROLS, NEW_CONTROLS, 1)
    case = case.replace(
        ".save V(out)",
        ".save V(xmod:gl1) V(xmod:p1_state) V(out)",
        1,
    )
    output = directory / f"{directory_name}.cir"
    output.write_text(case)
    print(output)
