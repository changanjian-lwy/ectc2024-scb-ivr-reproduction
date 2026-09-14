"""Build A25: all four P25-derived low-side event latches for one period."""

from pathlib import Path


TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A16_tighten_04_C3" / "A16_tighten_only_C3_from_A15.cir"
OUTDIR = TRACK / "A25_p25_four_phase_low_latches_09pct"
OUTPUT = OUTDIR / "A25_p25_four_phase_low_latches_09pct.cir"

OLD = """BL1 gl1 g V=if(time>=T0 & (V(gh4)>2.5 | (V(gh1)<2.5 & V(x1)<=0 & I(L1)>-INEG)),VG,0)
BL2 gl2 g V=if(time>=T0 & (V(gh1)>2.5 | (V(gh2)<2.5 & V(x2)<=0 & I(L2)>-INEG)),VG,0)
BL3 gl3 g V=if(time>=T0 & (V(gh2)>2.5 | (V(gh3)<2.5 & V(x3)<=0 & I(L3)>-INEG)),VG,0)
BL4 gl4 g V=if(time>=T0 & (V(gh3)>2.5 | (V(gh4)<2.5 & V(x4)<=0 & I(L4)>-INEG)),VG,0)"""

NEW = """* A25 one-period event-memory controller. At this periodic time origin,
* phase 1 begins in its own high-side interval; phases 2-4 begin with their low
* sides latched as required by P25 Mode 1. High-side timing remains the locked
* fixed P24 interleaving schedule; A25 diagnoses rather than moves those edges.

* Phase 1: admit after H1 turn-off/low-side Coss discharge, retain through the
* other high-side intervals, release after H4 support and the negative target.
.machine 1p
.state P1_WAIT_LOW_ZVS 0
.state P1_LOW_LATCHED 1
.state P1_LOW_RELEASED 2
.rule P1_WAIT_LOW_ZVS P1_LOW_LATCHED (time>TON)*(V(x1)<=0)
.rule P1_LOW_LATCHED P1_LOW_RELEASED (time>3*PHASE+TON)*(I(L1)<=-INEG)
.output (gl1) VG*(state==P1_LOW_LATCHED)
.output (st1) state
.endmachine

* Phase 2 begins latched, releases after H1 support at its negative target,
* then is re-admitted after H2 turns off and its low-side Vds reaches zero.
.machine 1p
.state P2_LOW_PRE 0
.state P2_RELEASED 1
.state P2_LOW_POST 2
.rule P2_LOW_PRE P2_RELEASED (time>TON)*(I(L2)<=-INEG)
.rule P2_RELEASED P2_LOW_POST (time>PHASE+TON)*(V(x2)<=0)
.output (gl2) VG*((state==P2_LOW_PRE)+(state==P2_LOW_POST))
.output (st2) state
.endmachine

* Phase 3 is the same rotation, one PHASE later.
.machine 1p
.state P3_LOW_PRE 0
.state P3_RELEASED 1
.state P3_LOW_POST 2
.rule P3_LOW_PRE P3_RELEASED (time>PHASE+TON)*(I(L3)<=-INEG)
.rule P3_RELEASED P3_LOW_POST (time>2*PHASE+TON)*(V(x3)<=0)
.output (gl3) VG*((state==P3_LOW_PRE)+(state==P3_LOW_POST))
.output (st3) state
.endmachine

* Phase 4 is the same rotation, two PHASE intervals later.
.machine 1p
.state P4_LOW_PRE 0
.state P4_RELEASED 1
.state P4_LOW_POST 2
.rule P4_LOW_PRE P4_RELEASED (time>2*PHASE+TON)*(I(L4)<=-INEG)
.rule P4_RELEASED P4_LOW_POST (time>3*PHASE+TON)*(V(x4)<=0)
.output (gl4) VG*((state==P4_LOW_PRE)+(state==P4_LOW_POST))
.output (st4) state
.endmachine

RGL1_MACHINE gl1 g 1k
RGL2_MACHINE gl2 g 1k
RGL3_MACHINE gl3 g 1k
RGL4_MACHINE gl4 g 1k
RST1 st1 g 1k
RST2 st2 g 1k
RST3 st3 g 1k
RST4 st4 g 1k"""

text = SOURCE.read_text()
if OLD not in text or "NEG_FRAC=.02" not in text:
    raise SystemExit("locked A16 source no longer matches A25 builder")
text = text.replace(
    "* A16 - periodic seed tightening 04: C3 only",
    "* A25 - P25-derived all-four-low-side event latches, 9% branch",
    1,
)
text = text.replace("NEG_FRAC=.02", "NEG_FRAC=.09", 1)
text = text.replace(OLD, NEW, 1)
text = text.replace(
    ".save V(out)",
    ".save V(xmod:gh1) V(xmod:gh2) V(xmod:gh3) V(xmod:gh4) "
    "V(xmod:gl1) V(xmod:gl2) V(xmod:gl3) V(xmod:gl4) "
    "V(xmod:st1) V(xmod:st2) V(xmod:st3) V(xmod:st4) "
    "V(xmod:x1) V(xmod:x2) V(xmod:x3) V(xmod:x4) V(out)",
    1,
)
OUTDIR.mkdir(exist_ok=True)
OUTPUT.write_text(text)
print(OUTPUT)
