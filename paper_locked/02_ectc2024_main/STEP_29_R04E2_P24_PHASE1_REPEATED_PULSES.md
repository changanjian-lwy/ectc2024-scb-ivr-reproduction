# Step 29 - R04E2 P24 phase-1 repeated-pulse screen

## Main-line scope

This remains a P24 single-module/four-phase reproduction support experiment.
Only the P24-explicit `QH1+QS2` first-interval state is repeated. The existing
power stage, formula library, device library and P24/P25 sequence branches are
unchanged. No phase rotation or complete-startup claim is made.

## Changed variable relative to R04E1

The calculated pulse width stays at `0.3055556 ns` and the positive current
increment target stays at 10 A. Only repetition period is stepped:

| Period | Sensitivity frequency | Pulses in 100 ns |
|---:|---:|---:|
| 10 ns | 100 MHz | 10 |
| 4 ns | 250 MHz | 25 |
| 2 ns | 500 MHz | 50 |
| 1 ns | 1 GHz | 100 |

The 250-MHz to 1-GHz cases are numerical sensitivity cases, not proposed
hardware operating frequencies.

## Failed controller implementation retained

The first netlist used a behavioral `mod(time,TPREP)` pulse generator. Individual
pulses 1, 2 and 10 measured about 10.03 A, but unplanned intermediate peaks of
11.31 A and 14.95 A appeared. Replacing only this plug-in implementation with
LTspice's native `PULSE` source removed those peaks. The behavioral version is
therefore rejected as a reliable sub-nanosecond timing implementation.

## Final native-PULSE results

LTspice lists stepped periods in ascending order. Reordered physically:

| Repetition period | Maximum `iL1` | Minimum `iL1` | `iL1` before pulse 10 | `VC1` at 100 ns |
|---:|---:|---:|---:|---:|
| 10 ns | 10.0655 A | -4.5994 A | approximately 0 A | 0.2877 mV |
| 4 ns | 10.0654 A | -4.5994 A | approximately 0 A | 0.7193 mV |
| 2 ns | 10.0679 A | -4.5994 A | approximately 0 A | 1.4386 mV |
| 1 ns | 10.0723 A | -4.5994 A | approximately 0 A | 2.8771 mV |

At 100 ns, `VC2` and `VC3` remain numerically zero for every case. `VC1`
approximately scales with pulse count, so repeating pulses does accumulate
charge in the first capacitor but cannot establish the full ladder.

## Boundary verdict

Status: **FAILED_SAFE_REPETITION; PASSED_CHARGE_ACCUMULATION_SCREEN**.

Positive current limiting is repeatable and every sampled pulse-10 entry current
is near zero. Nevertheless, the uncontrolled post-turn-off trajectory reaches
about `-4.60 A`, roughly 46% of the positive peak. It violates P24's 1%-2%
negative-current statement and also exceeds the separate 8% local scalar-model
operating choice. Therefore repetition frequency must not be increased further
as if the first interval were an independent charge pump.

The next replaceable controller experiment must chain the already separated P24
physical events: QH1 turn-off, low-side Coss commutation/QL1 ZVS, `iL1=0`,
controlled small negative current, QL1 turn-off, and QH1 ZVS. It must first be
tested for one complete local `t0-t3` cycle from zero energy. Repetition becomes
eligible only if that cycle returns to a declared safe release state.
