"""Build the recommended fixed-TON/event-ZVS/phase-slot controller."""

from pathlib import Path
import sys

TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
sys.path.insert(0, str(PROJECT))

from scb_ivr.p25_np4_controller_emitter import emit_p25_np4_machine

SOURCE = TRACK / "A27_ideal_gan_reverse_clamp" / "A27_ideal_gan_reverse_clamp.cir"
NAME = "A35_hybrid_fixed_ton_event_zvs_slot_guard_09pct"
OUT = TRACK / NAME

text = SOURCE.read_text()
start = text.index("VH1 gh1 g PULSE")
end_marker = "RST4 st4 g 1k"
end = text.index(end_marker, start) + len(end_marker)
text = text[:start] + emit_p25_np4_machine(phases=4, hybrid_timing=True) + text[end:]
text = text.replace("* A27 - A26 plus ideal GaN off-state reverse-conduction paths",
                    "* A35 - hybrid fixed-TON, event-ZVS, phase-slot guard, P25 9%", 1)
text = text.replace(".save V(xmod:h2_guard_state)", ".save V(xmod:sequence_state)", 1)
for token in (" V(xmod:st1)", " V(xmod:st2)", " V(xmod:st3)", " V(xmod:st4)"):
    text = text.replace(token, "")

measure = """* A35 fixed-TON and slot-readiness measurements.
.meas tran T_H1_OFF WHEN V(xmod:gh1)=2.5 FALL=1
.meas tran IL1_H1_OFF FIND I(XMOD:L1) WHEN V(xmod:gh1)=2.5 FALL=1
.meas tran PEAK_ERROR_H1 PARAM IL1_H1_OFF-IPEAK
.meas tran T_H2_ON WHEN V(xmod:gh2)=2.5 RISE=1
.meas tran VDS_H2_SLOT FIND V(xmod:a1,xmod:a2) AT {T0+PHASE}
.meas tran VDS_H2_ON FIND V(xmod:a1,xmod:a2) WHEN V(xmod:gh2)=2.5 RISE=1
"""
text = text.replace(".options plotwinsize", measure + ".options plotwinsize", 1)
OUT.mkdir(exist_ok=True)
(OUT / f"{NAME}.cir").write_text(text)
(OUT / "BOUNDARY.md").write_text("""# A35 hybrid-controller boundary

- Parent power stage/state/device model: A27; 9% remains the labelled P25
  commutation-margin branch.
- Control-only change: every high side turns off after relative `TON`; peak
  current is measured at that edge. Other transitions remain physical events.
- Next high-side admission requires its nominal `T/nP` slot and `Vds=0`.
- If the early ZVS window has disappeared at the slot, the controller remains
  blocked. It must not hard-switch or retune a component.
- This first run tests H1-to-H2 and accepts a documented missed-slot failure.
""")
print(OUT / f"{NAME}.cir")
