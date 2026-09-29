# A78 - P24 single module: the negative-current target (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Records:
- `run_*.json`;
- `a78_summary.json`;
- `gate_pairs.json`: the regression gate.

**Model: the physical model** (A76's simulator plus the `i^2 dt` record).
The target is a quantitative operating-point question in P24's four-phase
circuit (BOUNDARY Section 2).

## 0. Verdict

1. **P24's stated negative current (1-2% of the 125 A peak) is not enough
   for every phase to switch softly in this model.**
   - At 1% (-1.25 A), phases 2, 3 and 4 are restart-driven.
   - At 2-4% (-2.5 to -5.0 A), phase 4 is restart-driven. At its timed
     turn-off it carries +6.83, +2.18 and +0.42 A.
   - Phase 4's threshold lies between 4% and 5%.
2. **5% (-6.25 A), the lower end of P25's 5-10%, is the smallest tested
   target that meets single-module criterion 2.**
   - Every phase turns on predictively once per cycle, with no restart.
   - Phase 4 carries -4.94 A at its turn-off and turns on at 9.4 V;
     phases 1-3 at 8.9 V.
   - Peak Vds is 25.4 V, and the dither 0.94 A.

   BOUNDARY Section 3 of A79 fixed the rule before these results were
   read: this target is the one carried forward.
3. **Larger targets (7.5% and 10%) keep every phase soft**, with lower turn-
   on voltages (8.0 and 7.0 V). Their predictive dither, 1.15 and 1.42 A,
   exceeds the 1 A threshold of criterion 2. That threshold is a
   `PROJECT_DECISION`, so this is a margin statement, not a hard failure.
4. **The price of a larger target is small in conduction loss and large in
   turn-on voltage.**
   - Normalised to the output power, the conduction loss rises only from
     4.8% (1-2%) to 5.2% (10%).
   - The turn-on proxy falls from 5.3% to 2.3%.
   - Vo is open loop and falls with the target (0.965 to 0.910 V), so the
     absolute numbers are not at equal output. A79 regulates Vo.

## 1. Runs (last 50 cycles)

The controller is A76's adopted one in every run: predictive, trim 0.5,
no reactive ZVS, 10 ns latency, fixed shifts, restart 20 / 400 ns. Run 0
also has reactive ZVS on (= A76 run 1).

| run | target (% of 125 A) | phase-4 current at turn-off | phase 4 | phases 1-3 Vds at turn-on | phase-4 Vds | period | Vo | Irms (phases 1-4) | P_cond | P_on proxy | P_out | (P_cond + P_on)/P_out | criterion 2 |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| 0 (gate) | -2.5 A (2%) | +6.83 A | restart | 9.85 V | 10.82 V | 221.41 ns | 0.9628 V | 71.4 / 71.3 / 71.3 / 74.2 A | 11.22 W | 10.86 W | 231.7 W | 9.5% | fail |
| 1 | -1.25 A (1%) | +7.94 A | restart (phases 2-3 too) | 10.33 / 10.84 / 10.84 V | 11.51 V | 224.63 ns | 0.9651 V | 73.2 / 69.9 / 69.9 / 76.6 A | 11.34 W | 12.46 W | 232.9 W | 10.2% | fail |
| 2 | -2.5 A (2%) | +6.83 A | restart | 9.85 V | 10.82 V | 221.41 ns | 0.9628 V | 71.4 / 71.3 / 71.3 / 74.2 A | 11.22 W | 10.96 W | 231.7 W | 9.6% | fail |
| 3 | -3.75 A (3%) | +2.18 A | restart | 9.72 V | 10.98 V | 226.06 ns | 0.9594 V | 72.4 / 72.2 / 72.2 / 71.9 A | 11.26 W | 10.55 W | 230.1 W | 9.5% | fail |
| 4 | -5.0 A (4%) | +0.42 A | restart | 9.40 V | 11.62 V | 229.24 ns | 0.9523 V | 72.4 / 72.2 / 72.1 / 71.2 A | 11.19 W | 10.17 W | 226.7 W | 9.4% | fail |
| **5** | **-6.25 A (5%)** | **-4.94 A** | **predictive** | **8.90 V** | **9.36 V** | 229.84 ns | 0.9472 V | 71.4 / 71.1 / 71.2 / 73.3 A | 11.12 W | 8.39 W | 224.3 W | 8.7% | **pass** (dither 0.94 A) |
| 6 | -9.375 A (7.5%) | -8.24 A | predictive | 7.95 V | 8.15 V | 238.63 ns | 0.9290 V | 71.0 / 70.7 / 70.7 / 72.7 A | 10.97 W | 6.44 W | 215.8 W | 8.1% | soft; dither 1.15 A |
| 7 | -12.5 A (10%) | -11.5 A | predictive | 6.96 V | 6.91 V | 248.40 ns | 0.9095 V | 70.5 / 70.3 / 70.3 / 72.1 A | 10.83 W | 4.69 W | 206.8 W | 7.5% | soft; dither 1.42 A |

**Definitions.**
- `P_cond`: R = 0.54 mOhm times each phase's `integral of i^2 dt` over a
  cycle, divided by the period.
- `P_on`: the turn-on proxy, `1/2 * C_node * Vds_on^2 * f`, with `C_node`
  = 13.02 nF for phases 1-3 and 9.30 nF for phase 4.
- `P_out`: `Vo^2 / 4 mOhm`.
- **Peak Vds** is 24.6-25.8 V in every run (EPC2067: 40 V). Peak current
  is 170-177 A.

## 2. Checks

**Regression gate.** Run 0 replays A76 run 1 over its full length bit-
identically: 1809 sections, difference 0.0, equal end state. The `i^2 dt`
record does not change the dynamics.

## 3. Interpretation

- **This connects A67 and A74.**
  - A67 found that at P24's 1-2%, ZVS is out of reach, and the high sides
    can only use the valley.
  - A74 found phase 4 carrying a positive current at its timed turn-off.
  - A78 shows the size of the phase-1 target moves the whole orbit.
    Between 4% and 5%, phase 4's turn-off current changes sign (+0.42 to
    -4.94 A), and the node rings.
- **A P24 module built as specified (1-2%) would, in this model, hard-
  switch phase 4 every cycle.** At 2% the turn-on voltage is 10.8 V, and
  the timing depends on a restart timer.
- **P25's 5-10% range is the operating range at which the four-phase
  module works as intended.**

## 4. Limits

- **The circuit.** A76's idealised P24 module: linear Coss, lumped R,
  ideal unidirectional diodes, open-loop Ton, Cout 4.672 mF (inherited and
  suspect), one module.
- **The threshold is not a universal constant.** The 4-5% threshold
  belongs to this operating point and open loop. Closed-loop Vo (A79),
  nonlinear Coss and parasitics can move it.
- **The loss figures are not an efficiency.** Reverse-conduction drop,
  gate charge, magnetics and switching overlap are absent, and `P_on` is
  a proxy.
- **The dither threshold (1 A) is a `PROJECT_DECISION`.**

## 5. Next

1. **A79.** The output-voltage loop at the selected -6.25 A: does
   criterion 2 hold at Vo = 1 V?
2. **A80.** The full Verilog module controller (mode S start-up, handover,
   mode P, voltage loop) co-simulated from zero at the same settings.
3. **For the advisor.** Evidence that P24's 1-2% may be insufficient, and
   P25's 5% is the working value. This is a candidate question once A79
   confirms it under regulation.

## 5a. Reproduction

```
zsh run_a78.sh
python3 a78_analyze.py
```

The datasheet and paper PDFs are not in this repository.
