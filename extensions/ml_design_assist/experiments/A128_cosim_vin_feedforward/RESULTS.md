# A128 - co-simulation of the Vin feed-forward (A127 hybrid) at 2.5 MHz (RESULTS)

**Boundary and RTL:** bd85b70.

**Records:**
- `cosim/run_v125_*.json`, `cosim/cfg_*.json`;
- `a128_predictions.json` (registered);
- `a128_summary.json` (`a128_analyze.py`).

## 0. Verdict

1. **For the first time, every A124 row is within 200 A.** The worst is
   188 A.

   | row | A124 (no feed-forward) | **A128** | D63 (registered) | Vo extreme, A124 → A128 |
   |---|---|---|---|---|
   | +4.8 V / 1 µs | 217.7 | **181.5** | 186 | +13.7 → −12.3 mV |
   | +4.8 V / 5 µs | 210.2 | **175.4** | 176 | −7.7 → +10.9 mV |
   | −4.8 V / 1 µs | 215.9 | **175.5** | 169 | +42.9 → +17.2 mV |
   | −4.8 V / 5 µs | 173.7 | 175.3 | 169 | +22.6 → +17.6 mV |
   | −8 V / 10 µs | 168.5 | **188.2** | 168 | −28.2 → **+38.1 mV** |
   | +62.5 A | 177.7 | 177.8 | 177 | −12.0 → −11.8 mV |
   | −62.5 A | 143.9 | 143.9 | 144 | +15.9 → +15.8 mV |

   - **The physics cap on phase 1** (cap_vin) closes the rising steps.
   - **The learned falling-step rule** (from PPO, distilled) closes the
     fast falling step (−40 A).
2. **The cost:** on the slow, large fall (−8 V / 10 µs) the falling rule
   keeps phase 1's Ton raised for the whole ramp.
   - The peak rises by 20 A, still within 200 A.
   - |Vo| rises by 10 mV.
   - Registered criterion 4 (no row's |Vo| more than 3 mV worse) misses
     there. It also misses on +4.8 V / 5 µs by 0.2 mV.
3. **Nothing else moves:**
   - steady state identical: n0 90.609%, start-up 163.4 A, HS turn-on
     voltages, Vo;
   - load steps within 0.1 A;
   - no overlap, no runaway;
   - **with vff off, bit-identical** (2458 sections, plus the full
     regression).
4. **A125's prospective test:** the registered conformal bands hold.
   - M80 covers 7 of 7, G80 6 of 7 (+4.8 V / 1 µs came in below its
     lower edge), the |Vo| band 5 of 7.
   - **D63's errors:** −3 to +4% on the fast rows, but **+12% on −8 V /
     10 µs.** That is A125's second weak domain again. M80 (146-190)
     still held it.

## 1. Criteria (BOUNDARY Section 2)

| # | criterion | result |
|---|---|---|
| 0 | identity with vff off | **pass** (full regression; 2458/2458 sections) |
| 1 | +4.8 V / 5 µs ≤ 200 A | **pass** (175.4) |
| 2 | −4.8 V / 1 µs ≤ 200 A | **pass** (175.5) |
| 3 | +4.8 V / 1 µs −10 A | **pass** (−36.2) |
| 4 | no harm | loads, overlap/runaway, n0 **pass**; **Vo miss** (−8 V / 10 µs +9.9 mV; +4.8 V / 5 µs +3.2 mV) |

**Decision (Section 4):** criterion 4 misses, so as registered the
feed-forward is **not adopted as the closure**. The bus-slew spec stays
the answer.

**Recorded:** A128 is the first configuration that meets the 200 A
constraint on every row. The open trade is the falling rule on slow,
large falls.

**Proposed next step (not run):** gate the falling term by Vin's slope.
It is a fast-fall rule, and that is where its gain is (−40 A on
−4.8 V / 1 µs).

## 2. Limits

- **One design, one load level, one Cs** (no Cs tolerance in the
  co-simulation).
- **The Vin ADC is ideal apart from quantisation:** 20 mV, one sample
  per period, no noise.
- **The falling rule's coefficients come from D63.** D63 is weakest
  exactly on the row that regressed.
