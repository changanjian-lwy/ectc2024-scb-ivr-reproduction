# A18 results - P24 Interval 2 Coss commutation

## Run performed

The unchanged A16 electrical result was used. The extraction begins at the P24
high-side turn-off time `t1=16.6666667 ns` and searches for the first instant at
which `Vds(QL1)=V(x1)` reaches zero. No dead time or component value was tuned.

## Measurements

| Quantity | At `t1` sample | At first `Vds(QL1)<=0` event |
|---|---:|---:|
| Time | 16.6677 ns | 16.8047 ns |
| `Vds(QL1)` | 11.1466 V | -0.00924 V |
| `Vds(QH1)` | 0.83475 V | 11.9904 V |
| `iL1` | 119.3279 A | 119.7492 A |

Extracted capacitive-commutation duration: **0.138019 ns**.

All three causal acceptance checks pass:

1. low-side `Vds` falls to zero;
2. high-side `Vds` rises at the same time;
3. `iL1` remains positive and therefore supplies the commutation charge.

The small increase in sampled `iL1` during the very short transition is retained
as simulated. It does not affect the sign/path acceptance check.

## What P24 and P25 actually report

- P24 Fig. 4 is labelled **theoretical**; Table I is a numerical calculation.
  P24 does not report a prototype, measured commutation time, exact Coss, added
  parallel capacitance, or dead time.
- P25 supplies hardware validation for a different operating point: 12 V to
  1 V, 0.5 MHz, 200 W total, three phases and three modules. Its Fig. 4 measures
  high/low-side gate-source waveforms and device drain-source waveforms. Fig. 5
  measures one inductor current and one module's summed current; those current
  traces were taken at 100 kHz because of current-probe frequency limitations.

Therefore the extracted `0.138 ns` is a result of the present candidate Coss
model and P24-scale current. It is **not** a reproduced experimental value from
either paper.

## Result status

**Pass: P24 Interval-2 Coss-commutation mechanism.** The current candidate has
enough positive `iL1` to move the switch-node charge and create a low-side
zero-voltage turn-on opportunity.

This does not yet prove low switching loss: the model uses scalar candidate
capacitances, contains no published P24 nanofarad parallel capacitor, and does
not model a real gate-driver delay. The next sub-step in paper order is to let
`QL1` conduct after this zero-voltage event and verify that `iL1` decreases to
its zero crossing without changing the stage-entry state.
