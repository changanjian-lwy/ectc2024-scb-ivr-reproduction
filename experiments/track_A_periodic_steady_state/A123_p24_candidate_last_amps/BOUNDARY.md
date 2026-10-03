# A123 - the candidate's last amps: Cs 4.5 µF, a 3 A floor, or a 66 kHz loop (BOUNDARY)

Track A, main line. **Written before any A123 run.**

**Base:** A118's f6 (1 MHz, 10%, timed turn-off with a 2 A floor, Cs
6 µF, 60 kHz). It misses 200 A only on:
- +4.8 V / 1 µs: 206 A;
- −4.8 V / 1 µs: 201 A;
- −8 V / 10 µs: 205 A (A119).

**Screen** (`make_cfgs.py`; 3 single changes × those rows and n0, 12
runs):

| variant | change | why |
|---|---|---|
| c45 | Cs 4.5 µF | a faster ladder, since the line-step peaks come from the rails lagging. The risk is A117's 3 µF handover oscillation (517 A), so n0 decides. |
| f3 | floor 3 A | phase 1 turns off earlier on falling steps |
| k66 | loop 66 kHz | faster Ton correction; ki register 60 808 < 65 535 |

## Registered predictions (D63, `a123_predictions.json`)

| variant | +4.8 V / 1 µs | −4.8 V / 1 µs | −8 V / 10 µs |
|---|---|---|---|
| f6 (base; co-simulated 206 / 201 / 205) | 208 | 203 | 168 |
| c45 | 206 | 202 | 164 |
| f3 | 208 | 203 | 168 |
| k66 | 207 | 199 | 165 |

**D63 sees at most 4 A from any lever.** That is below its own error
(~10%), and D63 missed the −8 V row by 37 A (A119). **So D63 does not
decide here; the co-simulation does.** The registered expectation is
only that no lever moves a peak by more than ~10 A either way.

## Criteria

- **Per variant:**
  - no overlap; no runaway (late ≤ 100, peak ≤ 400 A);
  - n0's start-up ≤ 200 A;
  - steady efficiency within 0.1 points of f6 (88.97%).
- **A variant "closes" the candidate if all three rows are ≤ 200 A.**
- **Any closing variant is then run on the full matrix** before it
  replaces f6.
