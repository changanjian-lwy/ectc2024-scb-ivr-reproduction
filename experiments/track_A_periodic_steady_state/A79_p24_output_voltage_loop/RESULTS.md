# A79 - P24 single module: output-voltage loop (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`.
- Section 3 fixed the target rule before A78's results were read.
- Section 7 records the selection (-6.25 A).
- Section 8 adds runs 3-4, after runs 0-2 and before 3-4.

Records:
- `run_*.json`;
- `a79_summary.json`;
- `gate_pairs.json`.

**Model: the physical model** (A78's simulator plus the voltage loop). The
loop acts through the full switching dynamics (BOUNDARY Section 2).

## CORRECTION (2026-09-30, D43 and A82): the 5% bistability is a corrector lock-up

- **Two orbits exist.** D43's exact event map confirms that the soft and restart states at 5% are two
  stable orbits.
- **But the restart state is not a circuit property.** It persists only because the corrector does
  not sample at restart turn-ons, and phase 4's valley lies before the restart.
- **With the fix.** With a corrector that also samples there (A82), the ki = 1.0 case of run 2 settles
  soft, and so do 3% and 4%.

The text below is kept unchanged as the record.

## 0. Verdict

1. **A per-cycle integral loop on the common Ton regulates the P24 module
   to 1 V.**
   - Every run reaches Vo = 1.0000 V.
   - Vo enters the 1% band 60-79 us after the handover and stays in it.
   - Ton settles at 17.7-18.0 ns, against the open-loop 16.667 ns.
   - Peak Vds stays at 25.4-25.6 V.
   - Conduction loss at 250 W out is 12.4-12.7 W (4.9-5.1%).
2. **At the 5% target (-6.25 A), phase 4 has two steady states at the
   regulated point.** The transient decides which one it reaches.
   - ki = 0.25 ns/V: every phase soft. Phase 4 carries -5.09 A at its
     turn-off and turns on at 9.2 V.
   - ki = 1.0 ns/V: phase 4 restart-driven. It carries -0.63 A at its
     turn-off and turns on at 12.0 V.
   - The operating points nearly coincide: Ton 17.70 against 17.74 ns.

   This is the clearest evidence so far for A74's candidate 2: a self-
   reinforcing restart state that coexists with the soft state. A80's
   Verilog co-simulation at 5% also lands in the restart state.
3. **At 7.5% (-9.375 A, still inside P25's 5-10%), both gains settle in the
   soft state.**
   - Phase 4 carries -8.4 A at its turn-off and turns on at 8.0 V; phases
     1-3 at 7.9 V.
   - Conduction loss is 12.65 W, against 12.36 W at 5%: +2%.

   7.5% is the robust choice at this operating point.
4. **Criterion 2 is met except for the dither threshold.** The predictive
   rule's dither under the loop is 1.03-1.25 A. The 1 A threshold is a
   `PROJECT_DECISION`, so this is a margin statement: every phase is soft
   once per cycle, and no restart fires in runs 1, 3 and 4.

## 1. Runs (last 50 cycles)

| run | target | ki (ns/V) | Vo | settle to 1% after handover | Ton | period | phases 1-3 Vds at turn-on | phase 4 (current at turn-off; Vds) | dither | peak Vds / i | P_cond (P_out 250 W) |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|---|---:|
| 0 (gate = A78 r5) | -6.25 A | 0 | 0.9472 V | - | 16.667 ns | 229.84 ns | 8.90-8.92 V | predictive (-4.94 A; 9.36 V) | 0.94 A | 25.4 V / 172 A | 11.12 W (P_out 224 W) |
| 1 | -6.25 A | 0.25 | 1.0000 V | 69.0 us | 17.695 ns | 230.11 ns | 8.85-8.86 V | **predictive** (-5.09 A; 9.24 V) | 1.03 A | 25.4 V / 171 A | 12.36 W |
| 2 | -6.25 A | 1.0 | 1.0000 V | 79.4 us | 17.739 ns | 232.67 ns | 8.96-8.98 V | **restart** (-0.63 A; 11.97 V) | 0.53 A | 25.4 V / 169 A | 12.42 W |
| 3 | -9.375 A | 0.25 | 1.0000 V | 69.9 us | 18.034 ns | 238.28 ns | 7.87-7.91 V | predictive (-8.43 A; 7.99 V) | 1.18 A | 25.6 V / 170 A | 12.65 W |
| 4 | -9.375 A | 1.0 | 1.0000 V | 60.2 us | 18.037 ns | 238.21 ns | 7.89-7.90 V | predictive (-8.40 A; 8.00 V) | 1.25 A | 25.6 V / 170 A | 12.65 W |

- **Common settings.** Every run uses the adopted controller: predictive,
  trim 0.5, no reactive ZVS, 10 ns latency, fixed shifts, restart 20 /
  400 ns.
- **Timing.** The loop runs from the handover at 88.8 us to 388.61 us.
- **Vo ripple** at the section samples is below 0.03 mV.

## 2. Checks

**Regression gate.** Run 0 (loop off) replays A78 run 5 over its full length
bit-identically: 1763 sections, difference 0.0, equal end state.

## 3. Limits

- **The circuit.** A78's idealised P24 module: linear Coss, lumped R,
  ideal unidirectional diodes, Cout 4.672 mF (inherited and suspect), one
  module.
- **The measurement.** Vo is sampled exactly at each phase-1 turn-on, with
  no ADC quantisation or delay (the RTL version, A80, has a 12-bit ADC).
- **The loop.** An integral-only compensator. It was not optimised, and no
  load or line step was applied.
- **The bistability evidence** comes from two transients per target. It is
  not a map of the basins of attraction.
- **The dither threshold (1 A) is a `PROJECT_DECISION`.**

## 4. Next

1. **A80** at 7.5%: the full Verilog controller from zero (case f2).
2. **The phase-4 bistability, structurally.** Whether two periodic orbits
   coexist at 5%, and where the restart orbit disappears between 5% and
   7.5%, is a question for the mathematical model: the section map and
   its fixed points. It is also a design statement: P24's 1-2% is not
   enough (A78), and P25's lower 5% is marginal.

## 5a. Reproduction

```
zsh run_a79.sh      # runs 0-2
zsh run_a79b.sh     # runs 3-4 (amendment 8)
python3 a79_analyze.py
```

The datasheet and paper PDFs are not in this repository.
