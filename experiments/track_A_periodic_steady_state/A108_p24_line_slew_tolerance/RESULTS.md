# A108 - line-slew tolerance of the adopted design (RESULTS)

Track A, main line. One factor: the slew of a ±4.8 V (10%) input step.

**Boundary:** `BOUNDARY.md`, committed (e194f4a) before any run. The 20
and 50 µs slews were added after the first ten runs (fa536e6, before
their runs), when no slew up to 10 µs had kept the valleys negative.

**Records:**
- `cosim/run_*.json`, `cfg_*.json` (`make_cfgs.py`);
- `a108_summary.json` (`a108_analyze.py`).

**Models:**
- **Physical:**
  - Verilog RTL;
  - A88's plant (kernel2);
  - A105's I2 with C02's `slot_lo`;
  - 5%, 25 C, one module, 4 mΩ load.
- **Mathematical:** D60's ladder relaxation (11.1 / 3.2 / 1.9 µs at
  3 µF) and the per-cycle valley error Ton / L ≈ 12 A per volt of rail
  (BOUNDARY Section 1).
- **References:** A106 at 1 and 10 µs (without `slot_lo`). They agree
  within 1 A and 0.5 mV.

## 0. Verdict

1. **The 200 A limit holds from 2 µs per 4.8 V (2.4 V/µs) rising, and at
   every falling slew.**
   - Only the 1 µs rising step exceeds it: 207.6 A, as A106.
2. **Zero-voltage turn-on (every valley negative) needs a much slower
   input:**
   - **rising: ≤ 0.24 V/µs** (4.8 V over 20 µs).
   - **falling: not even at 0.096 V/µs** (50 µs). Phases 3-4 keep
     valleys of +9.6 / +12.1 A.
3. **Two mechanisms, both quantitative:**
   - **Phase 1, the timed turn-off.**
     - Its on-low interval adapts by at most 1 ns per cycle. That
       follows a rail moving at most 1 ns × Vo / Ton per cycle,
       0.24 V/µs.
     - Rising steps faster than that leave its valley positive. The
       boundary is exactly where the runs put it: +1.4 A at 0.48 V/µs,
       −4.1 A at 0.24 V/µs.
   - **Phases 2-4, the slots.** Their turn-offs follow phase 1's period,
     with no correction from their own current.
     - When the input moves, the ladder lags it by about the ramp rate
       × D60's slow time constant (11 µs). That leaves the lower phases'
       rails off Vin/4 by ~1 V at 0.096 V/µs.
     - That gives ~12 A of valley error (Ton/L per volt), against the
       +12.1 A measured.
     - **The sign:** falling inputs shorten phase 1's period and turn
       the high-rail phases (3-4) off early, so their valleys go
       positive. Rising inputs make theirs deeper, which is harmless.
4. **What it means for the design.**
   - The peak-current constraint is met for any bus slower than
     ~2.4 V/µs.
   - Soft switching through input changes needs a per-phase correction
     of the slot timing from each phase's own current, the residual
     current at its turn-off.
   - Without it, even slow input drifts (≥ 0.1 V/µs falling) cost phases
     3-4 their zero-voltage turn-on while the ladder re-divides.
   - **This is the same missing piece C01 found for D61's scheme B**
     (slaves have no valley target), so one feature, a per-phase valley
     trim of the slot, serves both. It is the candidate for A109.

## 1. Results (30 µs from the step start, or slew + 20 µs; per phase 1/2/3/4)

| run | V/µs | peak after the step | most positive valley | most negative valley | high-side turn-on max | Vo extreme | late fires |
|---|---|---|---|---|---|---|---|
| p48_1us | 4.80 | **203 A** (run 207.6) | **+56.7** / −6.7 / −7.0 / −5.9 | −8.4 / −15.3 / −26.4 / −28.4 | 18.8 V | +11.98 mV | 0 |
| p48_2us | 2.40 | 185 A | +37.0 / −6.6 / −7.0 / −5.9 | −9.0 / −17.0 / −24.9 / −28.2 | 18.5 V | +8.85 | 0 |
| p48_3us | 1.60 | 173 A | +24.3 / ... | −29.5 (phase 4) | 18.3 V | +6.29 | 0 |
| p48_5us | 0.96 | 164 A | +12.0 / ... | −32.5 | 15.2 V | +3.51 | 0 |
| p48_10us | 0.48 | 166 A | +1.4 / ... | −33.0 | 13.0 V | +4.07 | 0 |
| p48_20us | 0.24 | 154 A | **−4.1** / −6.1 / −6.9 / −5.9 | −24.5 | 11.2 V | +3.44 | 0 |
| p48_50us | 0.096 | 143 A | −5.3 / −6.3 / −6.7 / −5.8 | −14.1 | 10.6 V | +1.78 | 0 |
| m48_1us | 4.80 | 190 A | −1.0 / −4.4 / +28.7 / **+55.7** | **−86.9** (phase 1) | 14.6 V | −18.03 | 1 |
| m48_2us | 2.40 | 181 A | −2.0 / −3.1 / +26.8 / +49.6 | −69.9 | 14.6 V | −15.21 | 4 |
| m48_3us | 1.60 | 164 A | −2.7 / −1.0 / +21.0 / +36.9 | −44.1 | 14.5 V | −11.27 | 1 |
| m48_5us | 0.96 | 146 A | −4.6 / +7.8 / +18.1 / +23.8 | −21.7 | 14.3 V | −7.24 | 2 |
| m48_10us | 0.48 | 138 A | −4.6 / +17.1 / +26.3 / +29.2 | −11.2 | 14.1 V | −3.78 | 2 |
| m48_20us | 0.24 | 138 A | −4.8 / +11.8 / +20.2 / +23.6 | −8.0 | 11.0 V | −2.61 | 0 |
| m48_50us | 0.096 | 139 A | −5.0 / −1.3 / **+9.6 / +12.1** | −7.2 | 10.5 V | −1.80 | 1 |

- **No overlap in any run.** The run peak at slow slews is the
  start-up's 170.2 A.
- **The high-side turn-on V_DS** is reported, not graded. It scales
  with the rail: the steady state after a rising step is ~9.9 V at the
  10% higher rail. So BOUNDARY 4.4's fixed 9.5 V limit was ill-posed,
  and the valley sign is the soft-switching criterion.

## 2. Registered criteria (BOUNDARY Section 4)

| criterion | result |
|---|---|
| 1. no overlap | pass |
| 2. peak ≤ 200 A from 2 µs (rising); all falling; 1 µs rising 200-215 A | pass (207.6 A at 1 µs) |
| 2. peak monotone in slew | **miss as written.** Rising 5 µs 164 A, 10 µs 166 A after the step. The run peaks tie at the start-up's 170.2 A |
| 3. most positive valley monotone; 1 µs +45 to +65 A; 5 µs ≤ +10 A | rising: monotone, +56.7 A pass. **5 µs +12.0 A, miss.** Falling: **not monotone** (5 µs +23.8, 10 µs +29.2 A): the slot mechanism (0.3) grows with the duration of the ladder's lag |
| 3. most negative valley monotone | falling: pass. Rising: **not monotone**: phases 3-4 deepen at slower slews, the harmless side of the same mechanism |
| 4. zero-voltage turn-on lost up to 10 µs rising and 5 µs falling | as predicted, and beyond: falling slews lose it up to 50 µs |
| 5. Vo extreme monotone; 1 µs and 10 µs as A106 ±15% | 1 µs and 10 µs pass. Rising **not monotone** between 5 and 10 µs (3.51 / 4.07 mV) |
| 6. late fires | 0-4 per run, phase 1 in falling steps. As C03 |

## 3. For evaluation (Mihai), and next

**The decision this rests on: the 48 V bus slew the module must ride.**

| bus slew (10% step) | peak ≤ 200 A | soft switching kept |
|---|---|---|
| ≥ 2.4 V/µs (4.8 V in ≤ 2 µs) | no at 4.8 V/µs | no |
| 0.24-2.4 V/µs | yes | no |
| ≤ 0.24 V/µs rising | yes | yes |
| ≤ 0.096 V/µs falling | yes | **no** (phases 3-4 +9.6 / +12.1 A) |

- A rack bus with bulk capacitance likely moves slower than 0.1 V/µs.
  So the hard constraint is safe, but a falling drift still costs phases
  3-4 their zero-voltage turn-on for ~20 µs.
- The size of that loss in watts is D62's hard-turn-on term, for those
  phases, over that time.

**A109 (candidate):** a per-phase valley trim of the slot timing.
- Each slotted phase moves its turn-off by a small step per cycle, from
  the sign of its residual current at turn-off (the existing r_below
  report).
- It is opt-in, with a bit-identical default.
- At 1 ns per cycle it follows rails moving up to ~0.24 V/µs. The
  falling 50 µs case needs ~0.1 V/µs, so the valleys of phases 3-4
  should stay negative.
- **The same feature gives each slave module a valley target**, which
  D61's scheme B needs (C01 Section 3).

## Erratum (2026-10-02, found in A109)

The second mechanism in Section 0.3 is wrong in its cause.

- **Not the cause:** the slotted phases are not "turned off early".
- **The cause:** while the ladder re-divides, the phases whose rails sit
  above Vin/4 carry more current. At 0.096 V/µs falling, phase 4 carries
  73.5 A against 65 A, with its rail 0.26 V above Vin/4. At a common
  period and Ton, that extra current lifts their waveform, and the valley
  goes positive.
- A109 confirmed it: a slot-timing correction has no authority over
  these valleys.
- **What stands:** the measured tolerances and their scaling with the
  ramp rate.
- **Still open:** the size of the extra current. It is larger than
  tracking the ramp alone needs (A109 RESULTS Section 1).
