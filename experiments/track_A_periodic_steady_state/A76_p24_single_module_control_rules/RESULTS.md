# A76 - P24 single module: settle the control rules before the Verilog controller (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`. Records:
- `run_*.json`;
- `a76_summary.json`;
- `gate_pairs.json`: the regression gate.

**Model: the physical model** (A75's simulator, copied). These are control-
rule questions about P24's four-phase circuit (BOUNDARY Section 2).

## 0. Verdict

| rule | decision | evidence |
|---|---|---|
| comparator self-trim (Schaef et al. 2019) | **adopt** | With it, the latency is fully absorbed. At 10 and 18 ns the trimmed threshold settles at +4.07 / +9.34 A, the edge current is -2.50 A, and the steady state equals the zero-latency predictive state (A75 run 4) to 0.001 ns in period and 0.1 mV in Vo |
| reactive high-side ZVS decision | **drop** | With the trim it never fires. Removing it changes nothing (run 3 against run 2) |
| per-phase current condition on the timed turn-offs | **reject** | Phase 4 then turns on only every other cycle (25 of 50). The ladder drifts to 0.80 / 0.60 / 0.40 of Vin, the peak current reaches 217-406 A, and with latency Vds reaches 40.3-43.8 V, at or above EPC2067's 40 V |

**The phase-4 problem is not solved by any of the three rules.** With the
trim, phase 4 is again restart-driven (+6.83 A at its timed turn-off).
A75's improvement of phase 4 came from the confound, not from prediction.

**The confound points to the cause.**
- **The gate run passes.** Run 0 replays A75 run 6 (predictive,
  untrimmed, 10 ns). There, phase 1's effective turn-off current was
  -8.84 A, and that run passes the single-module criterion (every phase
  soft, no restart; Section 1).
- **The trimmed runs fail.** At -2.50 A they do not pass.
- **So the size of phase 1's negative current decides whether phase 4
  rings.**
  - P24 specifies 1-2% of the peak current: -1.25 to -2.5 A of 125 A.
  - P25 specifies 5-10%: -6.25 to -12.5 A at P24's peak.
  - The passing run's -8.84 A (7%) lies in P25's range.

This is the next test (Section 4).

## 1. Single-module criterion 2 (made precise here)

In the last 50 cycles, every phase must meet all of the following:
- it turns on once per cycle;
- every turn-on is soft (ZVS, valley or predictive), and no restart fires;
- peak Vds stays below EPC2067's 40 V;
- the last 20 sections vary by < 1 A (a periodic state, or the predictive
  rule's small dither).

**A correction to the first analysis.** The first version of the check
counted only the *kind* of turn-on. It passed runs 4-7, in which phase 4
skips cycles. The version in `a76_analyze.py` counts turn-ons per phase,
and it is the one reported.

## 2. Runs (last 50 cycles)

| run | valley | t_d | trim | qualify | reactive ZVS | phase-1 edge current | `theta_1` | phases 1-3 Vds at turn-on | phase 4 | turn-ons per phase | period | Vo | peak Vds / i | criterion 2 |
|---|---|---:|---|---|---|---:|---:|---|---|---|---:|---:|---|---|
| 0 (gate = A75 r6) | pred | 10 ns | - | - | yes | -8.84 A | -2.5 | 8.12 V | pred, 8.35 V (-7.70 A at turn-off) | 50/51/51/51 | 237.1 ns | 0.932 V | 24.6 V / 174 A | **pass** (dither 0.43 A) |
| 1 | pred | 10 ns | 0.5 | - | yes | -2.50 A | +4.07 | 9.85 V | restart, 10.82 V (+6.83 A) | 50/51/50/50 | 221.41 ns | 0.9628 V | 24.6 V / 174 A | fail |
| 2 | pred | 18 ns | 0.5 | - | yes | -2.50 A | +9.34 | 9.85 V | restart, 10.82 V (+6.83 A) | 50/51/51/50 | 221.41 ns | 0.9628 V | 24.7 V / 184 A | fail |
| 3 | pred | 18 ns | 0.5 | - | no | -2.50 A | +9.34 | 9.85 V | restart, 10.82 V (+6.83 A) | 50/51/51/51 | 221.41 ns | 0.9628 V | 25.2 V / 170 A | fail |
| 4 | reactive | 0 | - | yes | yes | -2.50 A | -2.5 | 7.6 V | valley, 9.70 V (-22.8 A), **25 of 50 cycles** | 50/51/51/25 | 190.4 ns | 0.933 V | 29.0 V / 217 A | fail |
| 5 | pred | 0 | - | yes | yes | -2.50 A | -2.5 | 7.6 V | pred, 9.96 V (-21.9 A), **25 of 50** | 50/51/51/25 | 188.6 ns | 0.929 V | 29.0 V / 217 A | fail |
| 6 | pred | 10 ns | 0.5 | yes | no | -2.48 A | +0.60 | 1.3-3.0 V | pred, **5 of 50** | 50/51/37/5 | 146.7 ns | 0.446 V | **43.8 V / 406 A** | fail |
| 7 | pred | 18 ns | 0.5 | yes | no | -2.50 A | +7.78 | 5.8-6.4 V | pred, **17 of 50** | 50/51/45/17 | 175.8 ns | 0.834 V | **40.3 V / 350 A** | fail |

`VCs/Vin` for each run:

| runs | `VCs/Vin` |
|---|---|
| 0-3 | 0.747-0.748 / 0.499-0.502 / 0.252-0.255 |
| 4-5 | 0.797 / 0.598 / 0.396 |
| 6 | 0.926 / 0.859 / 0.751 |
| 7 | 0.832 / 0.670 / 0.505 |

## 3. Checks

**Regression gate.** With every new option off, run 0 replays A75 run 6
over its full length bit-identically: 1721 sections, difference 0.0, equal
end state.

**Smoke test.** A 10 us smoke test before the runs, from the lossless D41
section with the P25 preset and all options on, exercised the new code
paths. The trimmed edge current converged to -2.51 A. It is not a declared
run, and its record was deleted.

**Implementation bug caught by the smoke test.** The threshold list was
first named `theta`. That name was already the event-interpolation fraction
in the step loop, and the smoke run crashed. The list was renamed `thr`
before any declared run.

## 4. Next

1. **The negative-current target (physical model, A78).** Sweep
   `i_target` with the adopted rules (predictive, trim, no reactive ZVS,
   10 ns latency) over P24's 1% and 2% and P25's 5%, 7.5% and 10% of the
   125 A peak.
   - Account the price: conduction loss from the phase rms currents,
     against the gain in turn-on voltage.
   - The question is whether P24's stated 1-2% is enough for every phase to
     switch softly at P24's operating point in this model.
2. **The Verilog controller (A77).** It implements the adopted rules:
   predictive valley turn-on, the sign-based comparator trim (Schaef),
   restart timers, and no reactive ZVS. It is written in parallel. The
   target is only a register value, so A78 does not change its structure.

## 5. Limits

- **The circuit.** A75's idealised P24 module: linear Coss, lumped R,
  ideal unidirectional diodes, open-loop Ton, Cout 4.672 mF (inherited and
  suspect), one module.
- **Latency.** Lumped, with no mismatch or noise.
- **The trim.** It is proportional, with the exact edge current (gain
  0.5, `PROJECT_DECISION`). Schaef's loop is sign-based; the Verilog
  version is sign-based.
- **Scope.** One trim gain and one correction step are tested.

## 5a. Reproduction

```
zsh run_a76.sh
python3 a76_analyze.py
```

The datasheet and paper PDFs are not in this repository.
