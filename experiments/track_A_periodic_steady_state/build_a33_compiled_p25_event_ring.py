"""Compile the source-labelled P25 NP4 event ring into the A27 power stage."""

from pathlib import Path
import sys

TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
sys.path.insert(0, str(PROJECT))

from p25_np4_controller_emitter import emit_p25_np4_machine


SOURCE = TRACK / "A27_ideal_gan_reverse_clamp" / "A27_ideal_gan_reverse_clamp.cir"
NAME = "A33_p25_np4_compiled_event_ring_09pct"
OUT = TRACK / NAME

text = SOURCE.read_text()
start = text.index("VH1 gh1 g PULSE")
end_marker = "RST4 st4 g 1k"
end = text.index(end_marker, start) + len(end_marker)
controller = emit_p25_np4_machine(phases=4)
text = text[:start] + controller + text[end:]
text = text.replace("* A27 - A26 plus ideal GaN off-state reverse-conduction paths",
                    "* A33 - compiled P25 NP4 rotating event ring, 9% branch", 1)
text = text.replace(
    ".save V(xmod:h2_guard_state)",
    ".save V(xmod:sequence_state)",
    1,
)
# Old per-phase diagnostic state nodes no longer exist.
for token in (" V(xmod:st1)", " V(xmod:st2)", " V(xmod:st3)", " V(xmod:st4)"):
    text = text.replace(token, "")

measure_anchor = ".options plotwinsize"
measure = """* A33 event-ring observations.
.meas tran T_H1_OFF WHEN V(xmod:gh1)=2.5 FALL=1
.meas tran T_L1_ON WHEN V(xmod:gl1)=2.5 RISE=1
.meas tran T_L2_OFF WHEN V(xmod:gl2)=2.5 FALL=1
.meas tran T_H2_ON WHEN V(xmod:gh2)=2.5 RISE=1
.meas tran VDS_H2_ON FIND V(xmod:a1,xmod:a2) WHEN V(xmod:gh2)=2.5 RISE=1
"""
text = text.replace(measure_anchor, measure + measure_anchor, 1)

OUT.mkdir(exist_ok=True)
(OUT / f"{NAME}.cir").write_text(text)
(OUT / "BOUNDARY.md").write_text("""# A33 boundary

- Parent power stage and state seed: A27.
- Sequence slot only is replaced by the compiled `P25_NP4_EXTENSION` truth
  table: one 20-state rotating event machine.
- Negative-current input remains the labelled 9% P25 sensitivity value.
- No absolute phase-time transition exists inside the controller.
- Device Coss, ideal reverse clamp, topology, L, capacitors, output boundary,
  initial state and timestep are unchanged.
- Acceptance: parser/run completion, ordered H1-off/L1-on/L2-off/H2-on events,
  H2 Vds zero at admission, no same-leg commanded overlap. Failure is retained.
""")
print(OUT / f"{NAME}.cir")
