"""Build paired phase-2 tests from A27 without fitting paper values.

A28 changes only the SH2 scheduler: paper events, not the fixed T/4 request,
control the local turn-on/turn-off sequence.
A29 adds a labelled non-paper sensitivity plug-in on top of A28.
"""

from pathlib import Path


TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A27_ideal_gan_reverse_clamp" / "A27_ideal_gan_reverse_clamp.cir"


OLD_MACHINE = """* A26 phase-2 ZVS readiness plug-in. The nominal phase-2 origin arms
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
.endmachine"""

EVENT_MACHINE = """* A28 phase-2 paper-event scheduler.
* P2 low-side release (negative-current event) arms commutation.  The first
* high-side Vds-zero event turns SH2 on.  The phase-current peak ends Mode 1.
.machine 1p
.state H2_WAIT_LOW_RELEASE 0
.state H2_WAIT_VDS_ZERO 1
.state H2_ON 2
.state H2_OFF_AFTER_PEAK 3
.rule H2_WAIT_LOW_RELEASE H2_WAIT_VDS_ZERO V(st2)>=0.5
.rule H2_WAIT_VDS_ZERO H2_ON V(a1,a2)<=0
.rule H2_ON H2_OFF_AFTER_PEAK I(L2)>=IPEAK
.output (gh2) VG*(state==H2_ON)
.output (h2_guard_state) state
.endmachine"""


def base_text() -> str:
    text = SOURCE.read_text()
    if OLD_MACHINE not in text:
        raise SystemExit("A27 phase-2 machine no longer matches builder")
    text = text.replace(OLD_MACHINE, EVENT_MACHINE, 1)
    text = text.replace("* A27 - A26 plus ideal GaN off-state reverse-conduction paths",
                        "* A28 - A27 plus phase-2 paper-event scheduler", 1)
    measures = """
* A28/A29 local phase-2 event measurements.
.meas tran T_SL2_RELEASE WHEN V(xmod:st2)=0.5 RISE=1
.meas tran T_SH2_ON WHEN V(xmod:gh2)=2.5 RISE=1
.meas tran T_SH2_OFF WHEN V(xmod:gh2)=2.5 FALL=1
.meas tran VDS_H2_AT_ON FIND V(xmod:a1,xmod:a2) WHEN V(xmod:gh2)=2.5 RISE=1
.meas tran IL2_AT_ON FIND I(XMOD:L2) WHEN V(xmod:gh2)=2.5 RISE=1
.meas tran LOCAL_COMM_DELAY PARAM T_SH2_ON-T_SL2_RELEASE
"""
    return text.replace(".options plotwinsize", measures + "\n.options plotwinsize", 1)


def write_case(name: str, text: str, boundary: str) -> None:
    out = TRACK / name
    out.mkdir(exist_ok=True)
    (out / f"{name}.cir").write_text(text)
    (out / "BOUNDARY.md").write_text(boundary)


a28_name = "A28_p24_phase2_event_scheduler"
a28 = base_text().replace("NEG_FRAC=.09", "NEG_FRAC=.02", 1)
write_case(a28_name, a28, """# A28 boundary

- Parent: A27.
- P24 main branch: negative-current target restored from 9% to the published
  upper boundary of 2%.
- Only control change: phase-2 SH2 follows the paper event order: SL2 release,
  first Vds zero, SH2 on, current peak, SH2 off.
- No component, Coss, clamp, initial-state or timestep fitting is permitted.
- The 50 ns phase origin is observed; it is not used as a substitute for the
  physical ZVS event.
""")

a29_name = "A29_p24_nonideal_timing_sensitivity"
a29 = a28.replace("* A28 - A27 plus phase-2 paper-event scheduler",
                  "* A29 - A28 plus declared non-paper timing/parasitic sensitivity", 1)
a29 = a29.replace(".param VIN=48", ".param T_SENSE=500p LPKG_SENSE=500p RPKG_SENSE=5m\n.param VIN=48", 1)
# A controlled transport delay is inserted only in the SH2 command path.
a29 = a29.replace(".output (gh2) VG*(state==H2_ON)",
                  ".output (gh2_event) VG*(state==H2_ON)", 1)
a29 = a29.replace("RGH2_MACHINE gh2 g 1k",
                  "B_GH2_DELAY gh2 g V=delay(V(gh2_event),T_SENSE)\nRGH2_EVENT gh2_event g 1k\nRGH2_MACHINE gh2 g 1k", 1)
# Shared rail parasitic is inserted without altering the internal converter.
a29 = a29.replace("VRAIL vin 0 {VIN}\nXMOD vin out 0", 
                  "VRAIL vin_src 0 {VIN}\nRPKG vin_src vin_r {RPKG_SENSE}\nLPKG vin_r vin {LPKG_SENSE}\nXMOD vin out 0", 1)
write_case(a29_name, a29, """# A29 boundary

- Parent: A28; the event scheduler and P24 2% target are unchanged.
- Added sensitivity inputs only: 0.5 ns SH2 command-path delay and a shared
  0.5 nH + 5 mOhm input/package path.
- These values are deliberately labelled NON-PAPER SENSITIVITY VALUES. They
  are not P24/P25 extracted parameters and cannot support a hardware claim.
- Purpose: determine direction and identify which missing data matter after
  the ideal event sequence is tested.
""")

print(TRACK / a28_name / f"{a28_name}.cir")
print(TRACK / a29_name / f"{a29_name}.cir")

# Direct control comparison: same A28 topology/event scheduler, only the
# separately labelled P25-extension negative-current target changes to 9%.
a28b_name = "A28B_p25_extension_09pct_event_scheduler"
a28b = a28.replace("* A28 - A27 plus phase-2 paper-event scheduler",
                   "* A28B - A28 event scheduler with labelled P25 9% extension", 1)
a28b = a28b.replace("NEG_FRAC=.02", "NEG_FRAC=.09", 1)
write_case(a28b_name, a28b, """# A28B boundary

- Direct comparison parent: A28.
- Only change: `NEG_FRAC` changes from the P24 upper boundary 2% to the
  separately labelled P25-extension sensitivity value 9%.
- Topology, four-phase mapping, initial state, Coss, ideal reverse clamp,
  event scheduler and timestep are unchanged.
- This is not a claim that P24 specifies 9%.
""")
print(TRACK / a28b_name / f"{a28b_name}.cir")
