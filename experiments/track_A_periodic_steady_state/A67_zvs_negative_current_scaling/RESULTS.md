# A67 - how much negative current does SCB ZVS need? (RESULTS)

Track A, `SENSITIVITY_ONLY`. This is an analytical criterion with
cross-checks; there is no new solve. Records: `results.json`
(`zvs_criterion.py`).

## 0. Verdict

**ZVS at the CCM/DCM boundary with 1-2% negative current is real, but only
where the switch node's flip time is short compared with the on-time.**
The negative current needed, as a fraction of the ripple, is about
`sqrt(L*C_node) / Ton`:

| | P25, built (12 V, 0.5 MHz, GS61008T) | P24, 48 V point (5 MHz, EPC2067) |
|---|---:|---:|
| flip time `sqrt(L*C_node)` | 6.7-9.0 ns | 3.7-4.4 ns |
| on-time | 500 ns | 16.7 ns |
| **negative current needed, % of peak** | **1.5-2.0%** | **22-26%** |
| papers' rule | 1-2% (matches) | 1-2% (an order of magnitude short) |

This reconciles the papers with Track A:

- P25's measured ZVS is physically consistent. Its point sits where the
  rule holds.
- P24 states the same rule for a 48 V, 5 MHz point that was never built or
  simulated. P24's waveforms are conceptual (Fig. 4 is titled "Theoretical
  key waveforms"); the text never mentions simulation. There, 1-2% lifts the
  node only to ~2.1-2.3 V of 12 V, so the high side hard-switches at
  ~10-12 V. That is what A56-A65 find (A64: 12.0-12.4 V).

Note: the earlier Track A shorthand, "ZVS cannot be reached with a small
negative current", was too broad. The correct statement is point-specific,
as above.

## 1. The criterion

At the rising edge of phase k, the low side turns off with current `-I_n`.
The node x_k starts at 0 V, and the output (`Vo`) and flying capacitor are
stiff. Then

`v(t) = Vo (1 - cos wt) + Z0 I_n sin wt`, with `w = 1/sqrt(LC)` and
`Z0 = sqrt(L/C)`.

- **ZVS condition.** The high side switches at zero voltage if v reaches
  `Vh = Vin/nP` within the dead time.
- **Without a dead-time limit** this needs
  `I_n >= sqrt(Vh (Vh - 2 Vo)) / Z0`.
- **As a fraction of the ripple**
  `dI = (Vh - Vo) Ton / L`:
  `I_n / dI = [sqrt(Vh (Vh - 2Vo)) / (Vh - Vo)] * sqrt(LC)/Ton`.
  The bracket is 0.94-1.0 at these points.

`C` is the charge-equivalent capacitance the node moves. In the SCB, the
rise of x_k charges three devices:
- low side k, from 0 to `Vh`;
- high side k, from `Vh` to 0;
- high side k+1, from `Vh` to `2 Vh`. Its drain a_k rises while its source
  is held by the next flying capacitor.

The last phase has no k+1. This third term follows from the topology, and
leaving it out fails the check below.

## 2. Check against Track A's full-network bisections

A53 and A54 bisected the phase inductance at which all four phases first
reach ZVS at 250 W. They used ideal switches, linear C and a 2.15 ns dead
time. The criterion, with the same dead-time limit and the valley current
at 250 W, predicts:

| | C_node | predicted L_crit | bisected L_crit | error |
|---|---:|---:|---:|---:|
| A53 GS61008T, own high + low only | 1155 pF | 1.2557 nH | 1.19625 nH | +5.0% |
| A53 GS61008T, + next high side | 1540 pF | 1.2252 nH | 1.19625 nH | **+2.4%** |
| A54 EPC2067, own high + low only | 9300 pF | 0.7705 nH | 0.62741 nH | +22.8% |
| A54 EPC2067, + next high side | 13020 pF | 0.6528 nH | 0.62741 nH | **+4.0%** |

Both variants are shown. Which one to use was decided by the topology
(Section 1), not by fit. The remaining 2-4% is consistent with what the
single-node model leaves out:
- the other phases' coupling through the ladder;
- the regulated on-time;
- the exact edge placement of the centred dead-time windows.

## 3. The three operating points

- **P25** (`P25_SUPPLEMENT`; order of magnitude only, per the advisor's
  guidance on P25 numbers).
  - 1 high / 2 low GS61008T, charge-equivalent over 0-4 V and 4-8 V from
    the project's A47 datasheet fit.
  - `C_node` = 2.68 nF (phases 1-2) or 2.06 nF (phase 3).
  - L = 22 nH (Coilcraft 1212VS-22N). The reported 50 A peak implies ~30 nH
    effective, so both are shown.
  - Result: 0.74-0.99 A needed, i.e. 1.5-2.0% of 50 A. The quarter-period
    (10.6-14.1 ns) fits easily in a 0.5 MHz dead time.
- **P24** (`P24_EXPLICIT` operating point; EPC2067 `Co(tr)` = 1860 pF,
  2 high / 3 low, as in A54).
  - 27.6-32.6 A needed, i.e. 22-26% of 125 A.
  - With 1-2% (1.25-2.5 A), the node reaches only 2.1-2.3 V with any dead
    time, and 0.3-0.5 V within 2.15 ns.
- **Track A's large-ripple design** (L = 0.6274 nH) has ~84 A of negative
  current. That is above what it needs, which is why it reaches ZVS
  (A54-A65).

## 4. Cross-track note: the main-line synthetic fixture (a hypothesis, not a result)

The native P25 core's frozen synthetic fixture uses:
- 1 F per switch bank;
- L = 2 / 3 / 4 H;
- on-time 0.02 s;
- Vin 12 V;
- peak reference 20 A;
- alpha = 0.05, i.e. a -1 A negative target.

(`scripts/audit_p25_synthetic_seeds.py`, "D12 synthetic F/H/s". Values
read 2026-09-29 from the other session's uncommitted working tree; they
may change.)

On this criterion:
- The fixture's flip time `sqrt(LC)` is **122-150 times its on-time**.
  P25's built point has 1.5%.
- Its -1 A target is **29-50%** of the ~2-3.5 A needed.
- Its ripple per on-time is 0.015-0.03 A against a 20 A peak, so it is not
  at the CCM/DCM boundary at all.

A commutation that slow runs on the same time scale as the other phases'
currents. That is the failure the main line reports repeatedly (D23-D38):
another phase's current reaches zero before SH2 reaches ZVS, and only
~5-8% of the commutation charge is supplied.

Hypothesis: those failures follow from the fixture's scale ratios, not
from the event machinery. The test is to run the same machinery with P25's
own orders of magnitude:
- ~22-30 nH;
- ~0.7 nF per GS61008T;
- 12 V and a 500 ns on-time;
- a 50 A peak;
- alpha = 1-2%.

This belongs to the main-line session and is not done here.

## 5. Limits

- The model is first-order: a single node, lossless, with linear (charge-
  equivalent) capacitance and stiff flying and output capacitors.
- It is validated against Track A's ideal-switch bisections, not against
  hardware. The vendor-model SPICE (A64) agrees on the hard-switch voltage
  at P24's point.
- P25's numbers are used only for their order of magnitude. Its peak
  current and inductance are not mutually consistent (see Section 3).

## 6. Reproduction

```
python3 zvs_criterion.py
```
