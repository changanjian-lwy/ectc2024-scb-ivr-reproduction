# AUX-2025 preliminary audit: earlier 2025 models

## Question being answered

Why was the earlier 2025 model described as reproduced, and how is that
different from a paper-locked supporting test?

## E-OLD-1: `apec2025_verified_3phase_module.cir`

**Changed relative to:** no earlier executable baseline; this is the old
one-module model rerun without modification.

**What it actually contains**

- Correct qualitative three-phase Fig. 1 power-stage connection.
- Published `12 V`, `1 V`, `67 W/module`, `0.5 MHz`, `22 nH`, `0.5 mOhm`
  inductor resistance and GS61008T on-resistance.
- Non-published `120 uF` flying capacitors, `470 uF` output capacitor,
  `100/200 pF` switch capacitances, `5 ns` dead time and `300 ns` low-side
  turn-off gap.
- Forced analytical initial conditions: `VCs1=8 V`, `VCs2=4 V`, `Vo=1 V`.
- Fixed gate timing rather than the paper's zero-cross/negative-current
  boundary control.

**Rerun results, 90-100 us**

| Quantity | Result | Paper comparison |
|---|---:|---|
| `Vout,avg` | 1.0233 V | close to 1 V, not sufficient proof |
| `IL1,avg/IL2,avg/IL3,avg` | 23.02/22.25/23.30 A | sum is close to 67 A/module |
| `IL1,max` | 59.79 A | misses measured about 50 A |
| `IL1,min` | -5.17 A | negative current exists |
| `VCs1/VCs2` | 8.094/4.037 V | close to initialized ladder |
| `IL1` at low-side turn-off | -5.14 A | 8.6% of simulated peak |
| high-side `VDS` immediately before next turn-on | 5.22 V | fails ZVS |

**Conclusion:** this model verifies only approximate power transfer, phase
current sharing and the expected capacitor-voltage ladder after those ladder
voltages were initialized. It does not reproduce the paper's 50 A peak or
high-side ZVS and cannot validate startup. Calling it a successful 2025
reproduction was incorrect.

## E-OLD-2: `apec2025_zvs_timing_replay_3phase_module.cir`

**Changed relative to E-OLD-1:** frequency, duty and switching instants were
manually calibrated (`0.623 MHz`, `D=0.298`) instead of retaining the paper's
nominal `0.5 MHz` operating point.

**Rerun results, 90-100 us**

| Quantity | Result | Interpretation |
|---|---:|---|
| `Vout,avg` | 0.9953 V | close to target |
| `IL1,max` | 52.40 A | close to measured 50 A |
| `IL1,min` | -6.18 A | 11.8% of peak, above the paper design's 5% case |
| `VDSH1` at high-side gate rise | -0.807 V | reverse-conduction/clamped state; low voltage overlap but not an exact zero |
| `IL1` at high-side gate rise | -6.10 A | nonzero reverse current |

**Conclusion:** this is a useful numerical timing replay, but it obtained the
match by changing frequency and duty away from the published nominal point.
It is not an independent reproduction of the 2025 prototype.

## Supporting-test acceptance boundary

The supporting test will not be declared successful from `Vout` alone. It must show,
in order, the published Mode 1-6 causality, approximately 50 A peak phase
current, the selected published negative-current case, low-side ZVZCS,
high-side `VDS` commutation before turn-on, capacitor ampere-second balance
and approximately 67 A average module output.

The paper does not publish full capacitor part numbers, snubber values, dead
time or the zero-cross detector implementation. Those remain unresolved
variables. A sensitivity run may expose their required range, but its result
will not be labelled a unique hardware reproduction.
