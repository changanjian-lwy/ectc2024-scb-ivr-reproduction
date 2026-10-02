# A110 - high-side zero-voltage turn-on by the negative current (BOUNDARY)

Track A, main line. **Written before any A110 run.**

**The design:** A105's I2 with C02's `slot_lo` (C02 `cfg_s1_n0`).

**One factor:** the negative-current target i_target. The design uses
5% of the 125 A peak (6.25 A).

## 1. Why the high side does not switch at zero voltage now, and P24's claim

- **P24 Sec. III:** a negative current of 1-2% of the peak discharges
  the high side's Coss, so it turns on at zero voltage, in every phase.
- **D57** (the extension's derivation, P24's own parameters): the
  inductor's energy ½ L i² must swing the switch node through the rail.
  The node carries the high side (2 × EPC2067), the low side (3 ×) and
  the next phase's high side. Each EPC2067 is ~2.2 nF equivalent.
  - **At this design's point** (Eq. (4)'s 1.4667 nH, rail 12.2 V), the
    free valley reaches 0 V at **i_neg = 33.4 A, 26.7%**.
  - **With P24's most favourable Table I value** (13.44 nH, only the high
    side's Coss): 5.3%.
  - So 1-2% gives a valley turn-on, not zero voltage. The co-simulation
    agrees: at 5%, 8.91-9.07 V of the 12 V rail.
- **This experiment** raises the target until the high side does switch
  at zero voltage, and measures what it costs.

## 2. Runs (`make_cfgs.py`; each C02's configuration with only i_target changed)

| run | i_target | row |
|---|---|---|
| n10, n15, n20, n25, n30 | −12.5, −18.75, −25, −31.25, −37.5 A (10-30%) | n0, 500 µs |
| n30_s_p62, n30_s_m62 | −37.5 A | load step ±62.5 A at 400 µs, 600 µs |
| n30_j30 | −37.5 A | 30 ps jitter on every edge, 500 µs |

**Reference at 5%:** C02 s1_n0 / s1_s_*62 / s1_j30.

## 3. Registered predictions and criteria (last 200 periods; before the step for step rows)

**From D57's free valley and D58's boundary-mode relations** (average
phase current I = 62.5 A, valley −i_neg, peak 2I + i_neg,
Ton = (peak − valley) L / (V_rail − Vo), T = Ton V_rail / Vo + t_x)
**and D62's middle-case loss model** on those waveforms:

| target | high-side turn-on V_DS (D57) | Ton | period | peak | D62 efficiency (middle) |
|---|---|---|---|---|---|
| 5% (C02) | 8.96 V | 18.3 ns | 234 ns | 131 A | 88.2% |
| 10% | 7.02 V | 20.0 ns | 254 ns | 138 A | 89.3% |
| 15% | 4.98 V | 21.7 ns | 274 ns | 144 A | 90.0% |
| 20% | 2.89 V | 23.3 ns | 294 ns | 150 A | 90.3% |
| 25% | 0.74 V | 25.0 ns | 314 ns | 156 A | 90.2% |
| 30% | ≤ 0 V (zero voltage) | 26.7 ns | 334 ns | 163 A | 89.9% |

**Loss terms in the prediction:**
- high-side hard turn-on: 8.9 W at 5% to 0 at 30%;
- gate drive: 7.3 → 5.1 W, with the lower frequency;
- conduction: 11.8 → 15.6 W.
- **Not in the prediction:** the reverse conduction of the high side
  between the node reaching the rail and its turn-on (GaN ~2-3 V). The
  co-simulation records it, and the measured efficiency includes it.

**Criteria:**
1. **High-side turn-on V_DS** within ±0.6 V of D57 at 10-25%. **At 30%
   ≤ +0.3 V in every phase (zero voltage).**
2. Ton and period within ±4% of the table; per-phase peak within ±5 A of
   2I + i_neg.
3. No overlap; peak ≤ 200 A (the start-up included); low-side turn-on
   V_DS ≤ 0 (n rows); Vo 1.000 V ± 1 mV.
4. **Measured efficiency** (D62 middle case on each run's measured
   waveforms, its reverse conduction included):
   - within ±0.7 points of the table;
   - the maximum at 15-25%;
   - 30% at least 1 point above 5%.
5. **At 30%:**
   - load steps within ±25% of C02's (+11.30 / −14.59 mV);
   - j30's turn-off sd within C02's s1_j30 × (1 ± 0.5);
   - the high side still ≤ +0.5 V under jitter.

**What would falsify the approach:**
- zero voltage not reached at 30%;
- the reverse conduction eating the gain, so that the efficiency at 30%
  is not above 5%'s;
- the controller losing its timing (overlap, or late turn-ons) at
  larger negative currents.

## 4. What stays assumed

- **Device and circuit:** the datasheet's typical Coss(V); 25 C; the
  D62 middle case (R_on max, MPC 500 nH-class inductor R/L, Cs ESR
  1 mΩ, QG typical for every device, t_f 0.75 ns).
- **The gate charge** at zero-voltage turn-on would be QG − QGD for the
  high sides. Not credited, so the zero-voltage rows are conservative.
- The A105/C02 assumptions.
