# A162 - when and where the late fires happen (BOUNDARY)
Method: RTL cosim cfg only (diagnostic): a cfg-gated record field, frozen design
Track A, package layer. Written and committed before the runs, with the bridge change (cfg "late_log": every section
records the N phases' cumulative late-fire counters; off = unchanged).
Decision it changes: whether the late fires on -8 V / 10 us, which grow with the loop (0 / 6 / 16 / 28-33 at 50 / 100 /
125 / 150 pH, no consequence so far), are a transient of the falling ramp (bounded) or a steady drift that larger loops
could turn into a defect; the loop bound (150 pH) rests partly on that.
Cheaper check done first: the final counters (A156: 13 of 16 on phase 4). Budget: 2 runs, ~45 min.

## 1. What and why
- r150 = A161's s150_l_m80_10us (150 pH, 20 A/ns), r100 = A152's s100_l_m80_10us (100 pH, 18 A/ns), both with late_log 1.
- The counter is shared by three timed edges of scb_phase (high-side turn-off, predicted low-side turn-on, slot
  low-side turn-off whose target had passed); the log gives time and phase, not which edge.

## 2. Criteria
1. Identity: every other field of r150 / r100 equals the original run (A161 / A152 records), bit for bit.
2. Location: at least 80 % of each run's late fires fall in [ramp start, ramp end + 20 us] (1000-1030 us).

## 3. Predictions
Phase 4 carries most (A156: 13 / 16); the fires sit in the falling ramp and its first ~10 us, none in steady state.

## 4. Decision rule
- 1-2 pass: the late fires are a bounded ramp transient; the loop bound stays 150 pH and the mechanism note goes to
  D68 Section 11.
- 2 fails (fires spread through steady state): the late fires are a drift; the loop bound drops to the largest L
  without them in steady state, and the mechanism becomes the next experiment.
