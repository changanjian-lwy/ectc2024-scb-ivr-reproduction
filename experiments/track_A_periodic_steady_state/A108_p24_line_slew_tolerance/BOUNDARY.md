# A108 - how fast may the input change? Line-slew tolerance of the adopted design (BOUNDARY)

Track A, main line. **Written before any A108 run.**

- **The design:** A105's I2 with C02's `slot_lo` (C02 `cfg_s1_n0`).
- **One factor:** the slew of a ±4.8 V (10%) input step.
- **Source:** A106's open item (the fast rising step peaks at 207 A),
  re-read in `../../track_C_multi_module/LITERATURE.md` Section 7 and
  traced here.

## 1. What A106's records show (before this experiment)

**Phase by phase, in the 15 µs after A106's steps:**

| A106 run | phase 1 valleys | phases 2-4 valleys | peak | high-side turn-on V_DS max |
|---|---|---|---|---|
| +4.8 V / 1 µs | −8.7 to **+55.2 A** | −29.0 to −5.8 A | 202 A (phase 1) | **18.8 V** (phase 1) |
| −4.8 V / 1 µs | **−88.5** to +0.4 A | phase 4 to **+55.9 A** | 191 A (phase 4) | 14.6 V (phase 4) |
| +4.8 V / 10 µs | −11.1 to +1.2 A | −32.5 to −5.8 A | 166 A | 13.0 V (phase 1) |

**Mechanism:**
- **After learning, no low-side turn-off is current-decided.** Phase 1's
  is timed by the learned on-low interval dlo (A99/A100). Phases 2-4's
  are slots (A93/A97).
- **A rail change mis-times them.** The fall from the peak to the
  target takes (V_rail,k − Vo) Ton / Vo, about 17.75 ns per volt of
  rail. A fixed turn-off time therefore leaves Ton / L ≈ 12 A per volt
  in the inductor, cycle after cycle, until the adaptation catches up
  (dlo's adaptive step, at most 32 LSB = 1 ns per cycle).
- **Phase 1 in the rising step:** its rail takes the step first
  (12.2 → 15.9 V, the series capacitors lag). Its valley climbs about
  10 A per cycle to +55 A. The boundary mode becomes CCM for ~2 µs, and
  the high side turns on hard.
- **In the falling step** the same happens with opposite signs, and the
  ladder's re-division moves it to phase 4.

## 2. Remedies considered, and why this experiment is the slew

Each was checked against the ladder (D60) and the driver path before
any code:

| remedy | effect | verdict |
|---|---|---|
| (a) module Vin feed-forward to Ton (one input ADC) | ΔI common to all phases cut by (V_rail0 − Vo)/(Vin/4 − Vo) | does not touch the per-phase mis-timing that makes the valleys climb. Partial |
| (b) per-phase Ton ∝ ((V_rail0 − Vo)/(V_rail,k − Vo))^α | per-phase volt-seconds held | **removes the ladder's restoring force.** D60's charge per on-time Q_k = Ton_k(−i_neg + (V_rail,k − Vo) Ton_k/(2L)) gives dQ_k/dV_rail,k ≈ Ton²/(2L)(1 − 1.9α): zero at α ≈ 0.53, reversed (ladder unstable) above. Rejected |
| (b') per-phase turn-off timing from the rail: dlo and the slots shifted by (ΔV_rail,k) Ton / Vo | each phase's turn-off stays at its zero crossing; Ton untouched, so the ladder keeps D60's relaxation | the targeted fix. It needs the rail of every phase (Vin and the three Cs voltages) and RTL changes. Candidate for A109 if A108 shows the slew must be tolerated |
| (c) cycle-by-cycle peak current limit | the comparator → driver path is ~11 ns (t_async + t_drv); at a 15.9 V rail the current rises 112 A in that time | ineffective at this driver delay. Rejected |
| (d) a slew specification for the 48 V bus | no change to the module | **measured here:** the slowest slew the module rides without loss of zero-voltage turn-on and within 200 A |

A 48 V rack bus carries bulk capacitance, so whether a 10% step in 1 µs
is a real requirement is a question for evaluation (Mihai). A108 gives
the numbers for that decision.

## 3. Runs (`make_cfgs.py`)

- 10 runs: +4.8 V and −4.8 V over 1, 2, 3, 5, 10 µs at 400 µs, to
  600 µs.
- **Physical model:** Verilog RTL; A88's plant (kernel2); A105's I2 with
  `slot_lo`; 5%, 25 C.
- **References:** A106 (the same rows without `slot_lo`) and C03's
  four-module line rows.

## 4. Registered predictions and criteria (the 30 µs after the step start, per phase)

1. **No overlap** in any run.
2. **Peak current falls monotonically with slew.**
   - 1 µs rising: 200-215 A.
   - **≤ 200 A from 2 µs.**
   - Falling steps ≤ 200 A at every slew (A106 193 A at 1 µs).
3. **The valley excursion falls monotonically with slew:** the most
   positive valley of any phase, and the most negative.
   - Predicted most positive valley: rising 1 µs +45 to +65 A; 5 µs
     ≤ +10 A.
4. **Zero-voltage high-side turn-on** (every valley < 0 and high-side
   turn-on V_DS ≤ 9.5 V, against 8.9-9.1 V in steady state):
   - lost at every rising slew up to 10 µs (A106: 13.0 V at 10 µs);
   - lost for falling steps up to 5 µs.
   - The slew at which it is kept, if any within 10 µs, is the result.
5. **Vo extreme falls monotonically with slew:** 1 µs as A106
   (+11.8 / −18.5 mV ± 15%); 10 µs as A106 (+4.2 / −3.9 mV ± 15%).
6. **Late fires** are allowed: C03 / tmp diagnostics show 1-2 phase-1
   late fires with `slot_lo` in line steps. They are reported with the
   results.

## 5. What stays assumed

- An ideal input source stepping linearly: no bus impedance, no input
  filter.
- 25 C.
- The other A105/C02 assumptions.
