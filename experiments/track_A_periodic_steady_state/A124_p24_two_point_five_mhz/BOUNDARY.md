# A124 - the 2.5 MHz design point (BOUNDARY)

Track A, main line. **Written before any A124 run.**

## 1. Why

**D64** (the inductor from first principles) finds that at P24's
in-package scale (≤ 2 cm² per phase) the best frequency is 2-5 MHz,
never 1 MHz. Its likely sweet spot is 2-3 MHz with a 10-15% target.

**At 2.5 MHz** (Eq. (4): L 2.933 nH) D57's threshold is 23.6 A (18.9%).
So a 12.5% target (15.6 A) keeps a 7.9 A margin, 3× A118's 1 MHz
design.

**Design** (`make_cfgs.py`):
- C02's s1_n0 time-scaled ×2 from 5 MHz, as A115 was to 1 MHz;
- Cs 6 µF (Q/Cs as 3 µF at 5 MHz);
- D59 loop at 100 kHz, designed at 12.5%: kp 355.39 ns/V, ki 22.519 ns/V
  per sample (register 23 613), phase margin 70°;
- the 2 A floor (A118).

**Rows (11):**
- n0 at 10, 12.5 and 15%;
- at 12.5%: ±62.5 A; ±4.8 V over 1 and 5 µs; −8 V over 10 µs;
- a control without the floor (−62.5 A).

## 2. Registered predictions (`a124_predictions.json`)

**Steady state** (orbit, D57, D62 middle with L 2.933 nH):

| target | high-side turn-on, phase 1 / 4 | Ton | period | ripple | efficiency middle / ideal inductor |
|---|---|---|---|---|---|
| 10% | 5.33 / 4.54 V | 37.81 ns | 486.5 ns | 153.8 A | 90.31 / 92.19% |
| 12.5% | 3.86 / 2.94 V | 38.60 ns | 504.2 ns | 159.9 A | **90.43 / 92.36%** |
| 15% | 2.37 / 1.30 V | 39.40 ns | 522.2 ns | 166.0 A | 90.45 / 92.43% |

**For comparison (measured):** 5 MHz 20% 90.17%; 1 MHz 10% 88.97%.

**Transients (D63 at 2.933 nH, the floor):**

| row | D63 peak | Vo, back | phase 1 crossing |
|---|---|---|---|
| −62.5 A | 144 A | +16.8 mV, 8.0 µs | 0 |
| +62.5 A | 177 A | −10.1 mV, 2.4 µs | 0 |
| +4.8 V / 1 µs | 212 A (rising: D63 weak) | +13.0 mV | 0 |
| −4.8 V / 1 µs | 202 A | +53.3 mV, 19.3 µs | 2.1 A × 8 |
| +4.8 V / 5 µs | 187 A (rising: weak) | +7.1 mV | 0 |
| −4.8 V / 5 µs | 168 A | +33.3 mV, 10.0 µs | 1.7 A × 11 |
| −8 V / 10 µs | 164 A | +34.3 mV, 26.9 µs | 2.1 A × 17 |
| control, no floor, −62.5 A | 144 A | +10.0 mV | **8.9 A × 30**, below the refitted 12 A rule: predicted to recover |

## 3. Criteria

1. **n rows:**
   - high side within ±0.6 V of D57 (phases 1-3), ±1.0 V (phase 4);
   - period ±2%, Ton ±5%, peaks ±5 A;
   - efficiency ±0.7 points;
   - start-up ≤ 200 A; Vo ±1 mV; the low side at zero voltage;
   - no overlap; late fires ≤ 5.
2. **Floor step rows** (all but the 1 µs rows):
   - the floor holds (phase 1 ≥ −18.6 A);
   - peak ≤ 200 A; back ≤ 100 µs;
   - no runaway; peak ±10% of D63 (the rising 5 µs row flagged).
3. **1 µs rows:** no overlap, no runaway; the peak reported against
   200 A.
4. **The control recovers** (no runaway, back ≤ 100 µs). This is D63's
   refitted crossing rule, tested prospectively: 8.9 A × 30 periods.

**Decision:** if 1 and 2 hold, 2.5 MHz / 12.5% / floor becomes the
recommended design. It is more efficient than both the 5 MHz and the
1 MHz candidates in the middle case, and has 3× the 1 MHz margin.
