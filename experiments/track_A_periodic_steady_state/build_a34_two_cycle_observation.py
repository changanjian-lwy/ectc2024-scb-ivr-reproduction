"""Extend A33 observation horizon only; no electrical/control change."""

from pathlib import Path

TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A33_p25_np4_compiled_event_ring_09pct" / "A33_p25_np4_compiled_event_ring_09pct.cir"
NAME = "A34_p25_np4_event_ring_two_cycle_observation"
OUT = TRACK / NAME

text = SOURCE.read_text()
text = text.replace("* A33 - compiled P25 NP4 rotating event ring, 9% branch",
                    "* A34 - A33 unchanged, two-cycle observation horizon", 1)
old = ".tran 0 {T0+T+5n} 0 5p UIC"
new = ".tran 0 {T0+2*T+5n} 0 5p UIC"
if text.count(old) != 1:
    raise SystemExit("A33 transient horizon anchor changed")
text = text.replace(old, new, 1)
OUT.mkdir(exist_ok=True)
(OUT / f"{NAME}.cir").write_text(text)
(OUT / "BOUNDARY.md").write_text("""# A34 boundary

- Parent: A33 compiled 9% P25-NP4 event ring.
- Only change: transient observation horizon from `T+5 ns` to `2T+5 ns`.
- No topology, controller, threshold, device, initial state, capacitance,
  inductance, output boundary or timestep change.
- Purpose: determine whether the ring returns to H1 and whether later high-side
  spacing approaches the nominal 50 ns without retuning.
""")
print(OUT / f"{NAME}.cir")
