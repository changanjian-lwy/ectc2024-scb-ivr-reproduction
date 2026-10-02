# C04 - module-to-module component spread (BOUNDARY)

Track C. **Written before any C04 run.** It is the last experiment of
the multi-module level.

**The design:** C03's, four modules of A105's I2 with `slot_lo`.

**The question:** besides the inductors (C01, C03), modules differ in
their series capacitors and their series resistance. Does the system
keep its sharing, interleave and soft switching under that spread, alone
and combined with ±5% inductors?

## 1. Runs (`make_cfgs.py`; module 1 takes the spread, module 3 the opposite, modules 0 and 2 nominal)

| run | spread (module 1 / module 3) | row |
|---|---|---|
| cs20_n0 | Cs +20% / −20% (ceramic tolerance and DC bias) | n0, 500 µs |
| r30_n0 | R (0.54 mΩ series per phase) +30% / −30% | n0, 500 µs |
| all_n0 | L +5%, Cs −20%, R +30% / the opposite | n0, 500 µs |
| all_s_p62 | the same | system load step +250 A at 400 µs, 600 µs |

**Reference:** C03's n0 and s_p62.

## 2. Not spread, and why

- **Coss.** With `nonlinear_coss` the plant replaces the linear switch
  capacitances (c_high, c_low) by n × the EPC2067 datasheet Coss(V)
  (`circuit.py`, the charge correction). Changing c_high / c_low
  therefore has no effect. Spreading Coss needs a scale factor on the
  datasheet curve, a plant change. Listed as not done.
- **Driver delay per module.** The bridge gives every module the same
  driver mismatch m (only the jitter seed differs). A per-module driver
  needs a bridge key. Listed as not done.

## 3. Registered predictions and criteria (last 200 master periods; before the step for all_s_p62)

1. **Every run:** no overlap; locked periods (0.1 ns); the 16 gaps
   within T/16 ± 0.1 ns; join ≤ 0.1 mV; Vo 1.000 V ± 1 mV.
2. **cs20_n0:** Cs does not enter the steady state (D58; A107).
   - Currents within ±1% of 250 A.
   - Valleys within ±0.3 A of C03 n0's.
   - Run peak (the start-up) ≤ 185 A. A107: Cs scales the start-up
     peak, 215 A at 8.7 µF.
3. **r30_n0:** ±30% of R moves a phase's drive by ±10 mV of 11 V.
   - Currents within ±0.5%.
   - Valleys within ±0.3 A.
4. **all_n0:** the inductors dominate, as C03.
   - Module 1 (+5% L) −4.5% ± 1.5%; module 3 (−5% L) +4.7% ± 1.5%.
   - Every valley ≤ −2.5 A and low-side turn-on V_DS ≤ 0 (zero voltage
     kept).
5. **all_s_p62:** the step's extreme within ±10% of C03 s_p62
   (−14.74 mV); no overlap; peak ≤ 200 A.

## 4. What stays assumed

As C03:
- identical controllers;
- one output node;
- an ideal shared input;
- 25 C.
