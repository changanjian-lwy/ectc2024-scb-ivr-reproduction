# A19 results - P24 Interval 2 low-side conduction to zero

## Measurements

| Physical event | Time | `iL1` | `Vds(QL1)` |
|---|---:|---:|---:|
| A18 low-side zero-voltage opportunity | 16.804686 ns | 119.749199 A | -9.245 mV |
| First subsequent `iL1<=0` sample | 160.719743 ns | -0.000792 A | -6.5 uV |

Observed current-decay duration: **143.915058 ns**. Net current reduction:
**119.749992 A**.

## Causal result

After positive phase-1 current completes the Coss commutation and brings
`Vds(QL1)` to zero, the controller admits `QL1`. The switch node remains near
the low-side conducting potential and `L1` current falls to zero while the
other three phases continue their interleaved activity. Both acceptance checks
pass: the phase current has a valid continuation path and reaches the P24
Interval-2 terminal event without parameter tuning.

## Source ambiguity preserved

P24 says both that Interval 2 ends when the current reaches zero and, in the
following paragraph, that the current "at t2" is already 1-2% negative. A19
uses the unambiguous physical zero crossing as its observed boundary. The later
negative threshold and `QL1` turn-off remain a separate Interval-3 experiment;
the two events are not collapsed into one timestamp.

## Status

**Pass: P24 Interval-2 continuation from low-side ZVS opportunity to phase-1
current zero crossing.** This is still an output-clamped periodic-state result,
not a zero-start or hardware-loss result.
