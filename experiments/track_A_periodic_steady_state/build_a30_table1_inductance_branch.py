"""Build the P24 Table-1 inductance sensitivity from A28.

Only LPHASE changes.  The inherited current/capacitor seed is deliberately not
refitted, so this case diagnoses direction and cannot claim a periodic orbit.
"""

from pathlib import Path

TRACK = Path(__file__).resolve().parent
SOURCE = TRACK / "A28_p24_phase2_event_scheduler" / "A28_p24_phase2_event_scheduler.cir"
NAME = "A30_p24_table1_2p68nH_sensitivity"
OUT = TRACK / NAME

text = SOURCE.read_text()
old = ".param LPHASE=1.466666666666667n IPEAK=125 NEG_FRAC=.02"
new = ".param LPHASE=2.68n IPEAK=125 NEG_FRAC=.02"
if text.count(old) != 1:
    raise SystemExit("A28 inductance anchor changed")
text = text.replace("* A28 - A27 plus phase-2 paper-event scheduler",
                    "* A30 - A28 with P24 Table-1 2.68 nH sensitivity", 1)
text = text.replace(old, new, 1)
OUT.mkdir(exist_ok=True)
(OUT / f"{NAME}.cir").write_text(text)
(OUT / "BOUNDARY.md").write_text("""# A30 boundary

- Parent: A28 P24 2% event-scheduler branch.
- Only changed electrical parameter: `LPHASE`, from 1.4667 nH calculated from
  the printed equation to 2.68 nH printed in P24 Table 1.
- The inherited periodic seed is not recomputed. Therefore this is a one-cycle
  direction/sufficiency sensitivity, not a periodic-state reproduction.
- No timing, Coss, clamp, threshold or timestep fitting is allowed.
""")
print(OUT / f"{NAME}.cir")
