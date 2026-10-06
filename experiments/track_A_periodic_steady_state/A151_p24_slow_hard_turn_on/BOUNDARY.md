# A151 - a slow hard turn-on (separate turn-on drive) against the package overshoot (BOUNDARY)
Method: mixed - math (A145 single-edge harness screen) + RTL cosim (plant cfg edge.didt_on_a_ns; no RTL change)
Track A, package layer. Written and committed before any cosim run; the harness screen (a151_screen.py) ran first.
Decision it changes: whether the line-step / start-up switch overshoot is met by a driver spec (slow turn-on, fast
turn-off) instead of a < 50 pH package. After A148-A150 closed the control path (user: "solve the problem").
Cheaper check done first: the harness screen (a151_screen.json, 18 s). Budget: 21 cosim runs, ~1-1.5 h at 10 jobs.

## 1. What and why
- Mechanism B (A144 / A145 / A149): a hard turn-on of phase k-1 rings SH_k to rail_(k-1) + rail_k + f(V_on). A145
  tested only one di/dt for both edges (1 / 2 ns) and concluded "edges cannot fix it". A turn-on that is soft only
  when it is hard is standard gate-drive practice (split source / sink outputs or a turn-on resistor; active gate
  drivers, Dymond et al. 2018 onward). Under ZVS the turn-on carries no V_DS, so a slow turn-on costs only when hard.
- Screen (rails 12 V, Q 7, turn-off 72 A/ns), SH2 peak at turn-on di/dt 72 / 36 / 18 / 9 A/ns:
  - V_on 17 V (the line-step event): 50 pH 37.1 / 30.1 / 29.0 / 26.7 V; 100 pH 39.1 / 36.9 / 30.1 / 28.4 V;
    150 pH 40.6 / 37.3 / 34.0 / 28.1 V. Edge + damper energy per event stays 1.05-1.13 uJ: the loss moves from the
    loop damper into the channel.
  - rev40 (start-up): 50 pH 34.2 -> 31.0 (36); 100 pH 44.5 -> 30.8 (18), but 1.6 -> 2.7 uJ per event (start-up only).
  - Steady valley (V_on 3.8 V): +11 / +44 / +113 nJ per event (36 / 18 / 9 A/ns).
  - Damping Q 7 -> 3 at 72 A/ns: only -2.0..-2.8 V. Not pursued.
- Cosim: frozen design (A145's 72 A/ns cfgs), turn-off 72 A/ns, turn-on 36 / 18 at 50 pH, 36 / 18 / 9 at 100 pH
  (rows l_p48_1us, n0, s_p62), 18 / 9 at 150 pH (l_p48_1us, n0). Plus the bus-slew lever: 72 / 72 A/ns on +4.8 V /
  5 us at 50 / 100 pH. Reference: A145's 72 A/ns records of the same rows.
- Voltage limits: 40 V = EPC2067 continuous rating (the project's limit so far); 48 V = its transient rating (up to
  10,000 5 ms pulses at 150 C, datasheet). Both are reported; whether 48 V applies to ns rings repeated per line step
  needs EPC's reliability report (asked from the user) and Mihai's derating rule.
- Not tested: a gate model (Miller plateau, dv/dt control: the plant's edge is a linear current ramp), temperature,
  L corners, falling steps, four modules. The realisable turn-on slope comes from the driver literature, not from here.

## 2. Criteria
1. Harness transfer: on l_p48_1us the cosim's change in whole-run max V_DS from the 72 A/ns record equals the
   harness's change in SH2 (V_on 17 V, same L, same di/dt) within +-2 V, in >= 5 of the 7 (L, di/dt) pairs.
2. 50 pH: a tested turn-on di/dt gives whole-run max V_DS <= 40.0 V on l_p48_1us, n0 and s_p62 (start-up included).
3. 100 pH: a tested turn-on di/dt gives whole-run max V_DS <= 40.0 V on all three rows.
4. Controller unchanged at that di/dt: post-step peak within +5 A of the 72 A/ns record and <= 200 A, 0 NEW oracle
   events, late fires <= record + 2, Vo back within 1 % no later than record + 2 us, n0 Vo mean within 0.5 mV.
5. Cost: on n0 the channel's edge power rises by <= 0.5 W (0.2 % of 250 W) against the 72 A/ns record; the damper's
   share is taken from the harness per event (A145's method) and reported.

## 3. Predictions (not criteria; cosim = A145 record + harness change at V_on 17 V / rev40)
- 50 pH: 36 A/ns line step ~34.8 V, start-up ~34.1 V; 18 A/ns 33.7 / 31.9 V -> criterion 2 passes at 36 A/ns.
- 100 pH: line step 48.8 / 42.0 / 40.3 V at 36 / 18 / 9 A/ns; start-up 32.4 V at 36 -> criterion 3 fails narrowly or
  passes only at 9 A/ns; <= 48 V from 18 A/ns.
- 150 pH: line step ~48.1 / ~42.2 V at 18 / 9 A/ns.
- n0 edge power +0.05..+0.4 W; peaks within +-3 A; the 5 us bus slew lowers the 50 pH line-step overshoot below 40 V.
- Criterion 1 holds at 50 pH; at 100 / 150 pH the cosim event is larger than the harness's (51.0 vs 39.1 V at 72 A/ns),
  so the transfer may be off by more than 2 V.

## 4. Decision rule
- 2 + 4 + 5 pass: the package spec becomes "turn-on di/dt <= X A/ns, turn-off fast" at 50 pH (scorecard T20, Mihai
  question: P24's driver); 3 also passing extends it to 100 pH (inside published embedded loops' reach).
- 2 fails: the driver lever is not enough on its own; combine with the transient rating and the bus-slew rows.
- 1 fails: the harness is not a design tool for this; the cosim numbers stand for the tested points only.
