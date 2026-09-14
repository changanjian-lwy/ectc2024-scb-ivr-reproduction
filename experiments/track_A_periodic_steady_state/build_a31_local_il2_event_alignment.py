"""Align only the local P24 phase-2 threshold event; not a periodic solve."""

from pathlib import Path

TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A28_p24_phase2_event_scheduler" / "A28_p24_phase2_event_scheduler.cir"
NAME = "A31_p24_local_il2_2pct_event_alignment"
OUT = TRACK / NAME

# A28 measured iL2(TON)=-6.540536 A from iL2(0)=4.755554 A.  Under the
# unchanged first interval, translate the initial state by the measured error
# so the allowed release event lands at -2.5 A.
old_initial = 4.75555393314
measured_at_boundary = -6.540536404
target = -2.5
derived_initial = old_initial + (target - measured_at_boundary)

text = SOURCE.read_text()
old = f"IL2_INIT={old_initial}"
new = f"IL2_INIT={derived_initial:.12g}"
if text.count(old) != 1:
    raise SystemExit("A28 IL2 initial-state anchor changed")
text = text.replace("* A28 - A27 plus phase-2 paper-event scheduler",
                    "* A31 - A28 with derived local iL2 event-alignment seed", 1)
text = text.replace(old, new, 1)
OUT.mkdir(exist_ok=True)
(OUT / f"{NAME}.cir").write_text(text)
(OUT / "BOUNDARY.md").write_text(f"""# A31 boundary

- Parent: A28 P24 2% event-scheduler branch.
- Only changed state: `IL2_INIT`, from {old_initial:.9f} A to
  {derived_initial:.9f} A.
- Derivation: add the measured A28 boundary error
  `(-2.5)-(-6.540536404)=+4.040536404 A` to the inherited seed.
- Purpose: force no switch or component value; test whether an exactly captured
  local 2% event can complete Coss commutation.
- This is not an eight-state periodic solution and cannot establish 50 ns
  interleaving or capacitor balance.
""")
print(OUT / f"{NAME}.cir")
