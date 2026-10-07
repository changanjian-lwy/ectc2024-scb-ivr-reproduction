# A162 - when and where the late fires happen (RESULTS)
Boundary: 4af997e. Records: release records-a162 (2 runs). Output: a162_summary.json (a162_analyze.py).

## 0. Verdict
- **PASS 2/2. The late fires on -8 V / 10 us are a bounded transient right after the falling ramp, not a drift.**
- **Identity:** with cfg late_log 1 every other record field equals the original runs (A161 s150_l_m80_10us, A152
  s100_l_m80_10us) bit for bit.
- **Where:** all 28 (150 pH, 20 A/ns) and all 6 (100 pH, 18 A/ns) fall between 1011.9 and 1027.0 us: 2-17 us after the
  ramp ends (100 pH: 2-4 us) (1000-1010 us), none during the ramp, none in steady state. 150 pH: phase 4 23, phase 2 5; 100 pH: phase 2 5,
  phase 3 1.
- So the count grows with the loop because the post-ramp settling of the slotted phases (2-4) takes more periods with a
  larger loop, while each late fire is one edge fired at once in the next clock window (a delay of < 4 ns). With no
  peak, voltage or Vo consequence (A156, A159, A161), the loop bound (150 pH) stands.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | identity with the original runs | PASS (no field differs) |
| 2 | >= 80 % of late fires in 1000-1030 us | PASS (100 % in 1011.9-1027.0 us) |

## 2. Limits
- The shared counter does not say which of the three timed edges fired late; the mechanism inside the slotted phases'
  settling is not traced further.
