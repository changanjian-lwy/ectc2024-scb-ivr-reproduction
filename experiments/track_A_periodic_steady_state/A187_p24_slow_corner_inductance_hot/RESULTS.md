# A187 - the slow corner's inductance at 125 C after +4.8 V / 1 us, six step positions (RESULTS)
Boundary: 1402a46 (stage-2 cfgs d6bd283). Records: release records-a187 (3 trim start-ups, 12 runs, logs). Analysis:
a187_analyze.py -> a187_summary.json. Code cfe581f, plant V5, t_il 1.0 ns, A186's start-up (handover at Vo 1.03 V).

## 0. Verdict
- **Neither board holds 200 A at 125 C** (decision rule: S80 fails too, so the limit is above 0.8 L0; it is named,
  and 0.85 was not run).
  - S75 (L x 0.75): post-step 194.9-207.2 A; above 200 A at 2 of 6 positions (phase 0.63 204.5 A, 0.96 207.2 A).
  - S80 (L x 0.8): post-step 190.8-217.1 A; above 200 A at 2 of 6 (phase 0.75 217.1 A, 0.08 201.5 A).
  - The worst peak is not monotone in L (S80 worse than S75), as with nominal devices (A178: L0 182.5, 1.3 L0
    188.7 A).
- **Start-up and safety pass everywhere.** Start-up 134-138 A, handover 186.5-187.5 A, V_DS <= 33.7 V, 0
  shoot-throughs, Vo <= 1.033 V. The start-up is no longer what limits this corner.
- **Mechanism (mode P, every run).** After the step, phases 3-4 lose their valley for ~25 us: 28-65 late fires in
  the first 30 us, valleys at -80..-90 A, turn-ons with the body diodes conducting. The lost charge pulls Vo down to
  0.980-0.987 V at +20-28 us, and the loop raises Ton by ~20 % (S80 p3: 37.0 -> 45.4 ns). The post-step peak is
  that Ton meeting a phase whose valley is recovering (S80 p3: phase 4's valley -67 -> -28 A, then 217.1 A at
  +27.7 us). Whether it crosses 200 A depends on where the step lands in the period, not on the late-fire count
  (S80 p3 has the fewest, 28).
- This is the slow corner's valley-timing limit (A163: the RTL cannot schedule a predictive turn-on before t_lo
  + ~1 clock, and the slow gates' delay eats the valley). At L0 the same events stay <= 183.5 A (A181, three
  positions); at 0.75-0.8 L0 the faster current slopes leave no margin. A fix belongs to the controller (an earlier
  or valley-aware predictive turn-on, A176's candidate) or to the gate drive at the slow corner, not to the
  start-up.
- S80's trim 35.545 ns (prediction ~35.5) and its interpolated seed gave a clean start-up (134.3 / 186.5 A).

## 1. Criteria
| board | positions (step phase) | c1 start / hand | c2 post-step | c3 | c7 |
|---|---|---|---|---|---|
| S75 | 0.13 / 0.30 / 0.46 / 0.63 / 0.79 / 0.96 | 137.5 / 187.5 | 197.2 / 194.9 / 196.9 / **204.5** / 197.7 / **207.2** | <= 33.7 V | 1.033 |
| S80 | 0.26 / 0.42 / 0.59 / 0.75 / 0.92 / 0.08 | 134.3 / 186.5 | 193.0 / 191.6 / 190.8 / **217.1** / 191.1 / **201.5** | <= 32.9 V | 1.032 |

## 2. Predictions
- S75: "192-208 A, > 200 A at phases ~0.75-0.95 (1-2 of 6)". The range was right and 2 of 6 failed, but at
  phases 0.63 and 0.96, not in a single band.
- S80: "worst 193-201 A". Wrong: 217.1 A.

## 3. Limits
- One row, 125 C only (S75 at 25 C stayed <= 198.7 A at phases 0.12-0.88, A181 / A184). L between 0.8 and 1.0 not run.
- Six positions per board. With a peak this sensitive to position, more positions could find higher values.

## 4. Decision (BOUNDARY Section 4)
S80 fails too, so for slow devices at 125 C the +4.8 V / 1 us limit lies above 0.8 L0 (L0 holds, A181). FINAL_SPEC
states the inductance tolerance per device corner and temperature: nominal 0.75 L0 (A178, 25 C), slow 0.75 L0 at
25 C only. The slow-corner valley-timing limit is the open controller item behind it.
