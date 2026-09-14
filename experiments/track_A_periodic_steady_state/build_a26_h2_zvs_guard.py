"""Build A26 by inserting a paper-defined Vds=0 guard before SH2."""

from pathlib import Path


TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A25_p25_four_phase_low_latches_09pct" / "A25_p25_four_phase_low_latches_09pct.cir"
OUTDIR = TRACK / "A26_h2_zvs_readiness_guard"
OUTPUT = OUTDIR / "A26_h2_zvs_readiness_guard.cir"

OLD = "VH2 gh2 g PULSE(0 {VG} {T0+PHASE} 1p 1p {TON} {T})"
NEW = """* A26 phase-2 ZVS readiness plug-in. The nominal phase-2 origin arms
* the request; SH2 is not physically commanded until its own Vds reaches zero.
.machine 1p
.state H2_BEFORE_REQUEST 0
.state H2_WAIT_VDS_ZERO 1
.state H2_ON 2
.state H2_REQUEST_EXPIRED 3
.rule H2_BEFORE_REQUEST H2_WAIT_VDS_ZERO time>=T0+PHASE
.rule H2_WAIT_VDS_ZERO H2_ON V(a1,a2)<=0
.rule H2_WAIT_VDS_ZERO H2_REQUEST_EXPIRED time>=T0+PHASE+TON
.rule H2_ON H2_REQUEST_EXPIRED time>=T0+PHASE+TON
.output (gh2) VG*(state==H2_ON)
.output (h2_guard_state) state
.endmachine
RGH2_MACHINE gh2 g 1k
RH2_GUARD_STATE h2_guard_state g 1k"""

text = SOURCE.read_text()
if OLD not in text:
    raise SystemExit("A25 SH2 source line no longer matches A26 builder")
text = text.replace(
    "* A25 - P25-derived all-four-low-side event latches, 9% branch",
    "* A26 - A25 plus phase-2 Vds-zero readiness guard",
    1,
)
text = text.replace(OLD, NEW, 1)
text = text.replace(
    ".save V(xmod:gh1)",
    ".save V(xmod:h2_guard_state) V(xmod:gh1)",
    1,
)
OUTDIR.mkdir(exist_ok=True)
OUTPUT.write_text(text)
print(OUTPUT)
