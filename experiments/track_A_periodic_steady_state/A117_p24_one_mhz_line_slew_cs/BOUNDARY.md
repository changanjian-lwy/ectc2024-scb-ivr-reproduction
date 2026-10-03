# A117 - D63's design map at 1 MHz put to the co-simulation: input slew and Cs (BOUNDARY)

Track A, main line. **Written before any A117 run.**

**Purpose:** test D63's predictions where they decide the design.
- D63 is the valley map that closes the trade-off map's open link.
- No RTL change: D63's floor proposal needs one, and comes after this
  test.

**Design:** A115/A116's 1 MHz 10% (7.333 nH, D59 loop at 60 kHz).

**Factors** (`make_cfgs.py`; 14 rows):
- the input slew: ±4.8 V over 5-50 µs at 2000 µs (A116 ran 1 µs);
- Cs: 15 µF (A115) or 3 µF (the ladder 5× faster, D60);
- phase 1's turn-off: comparator (A116 c60) or timed (A115 n10).

## 1. Registered predictions (`a117_predict.py` → `a117_predictions.json`)

**D63's outcome rule:**
- **runaway:** the map diverges;
- **slow or runaway:** phase 1 crosses its threshold by > 8 A for
  > 5 µs;
- **peak:** otherwise, peak > 200 A;
- **ok:** otherwise.

| row | D63 outcome | D63 peak | phase 1 crossing |
|---|---|---|---|
| c3_cmp_l_p48_5us | **runaway** (map diverges) | - | - |
| c3_cmp_l_m48_1us | **runaway** (map diverges) | - | - |
| c15_tim_l_m48_20us | **slow or runaway** | 166 A | 32.1 A × 29 |
| c3_tim_l_m48_10us | **slow or runaway** | 154 A | 23.5 A × 12 |
| c15_tim_l_m48_50us | **slow or runaway** (marginal) | 145 A | 9.5 A × 50 |
| c15_cmp_l_p48_20us | peak | 286 A | - |
| c15_cmp_l_p48_50us | peak (marginal) | 208 A | - |
| c15_cmp_l_m48_5us | ok | 194 A | 2.7 A |
| c15_tim_l_p48_10us | ok, **D63 unreliable** (timed, 60 kHz, rising) | 196 A | - |
| c3_tim_l_p48_1us | peak (marginal), **D63 unreliable** | 202 A | - |
| c3_cmp_l_p48_20us | ok | 175 A | - |
| c3_cmp_s_m62 | ok: +28.9 mV, back 16.5 µs (as at 15 µF: Cs does not enter) | 140 A | - |

**Steady state with Cs 3 µF (c3_tim_n0, c3_cmp_n0):**
- not in D63 (no in-cycle ripple);
- from A107 (0.6 µF at 5 MHz, the same Q/Cs): the high-side turn-on
  +0.5 to +1.5 V against A115 n10 / A116 c60_n0, and the turn-off sd
  up;
- no overlap, peak ≤ 200 A, Vo ±1 mV.

## 2. Criteria

**The co-simulation's outcome:**
- **runaway:** late fires > 100 or peak > 400 A;
- **slow:** otherwise, back within 1% after more than 60 µs (or never);
- **peak:** otherwise, peak > 200 A;
- **ok:** otherwise.

**Checks:**
1. **The outcome as D63 predicts.** "Slow or runaway" passes on either.
2. **The peak within ±10% of D63** where D63 predicts ok or peak.
3. **c3_cmp_s_m62:** extreme within ±10% of +28.9 mV, back within
   ±5 µs.
4. **n0 rows:** as above.
5. **No overlap in any run.**

**What would falsify D63:**
- outcomes against the rule in more than 2 of the 10 reliable step rows;
- peaks off by more than 10% in more than 2 of the bounded rows.
- The two flagged rows test where the map is known to be weak. They do
  not count against it either way.

**What it decides for the design:**
- **Whether a 3 µF ladder rescues the 1 MHz line steps** with either
  turn-off rule, and from which slew.
- **Whether the comparator's rising-step failure is slew-limited**
  (D63: not before 50 µs).
- **Whether D63 is trusted enough** to design the floor turn-off (A118)
  with it.
