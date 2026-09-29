# A80 - the full P24 module controller in Verilog, co-simulated from zero (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with amendments 8
(f0r) and 9 (f2). How to run: `README.md`. Records:
- `cosim/run_f*.json`;
- `a80_summary.json`;
- `synth/stat_scb_ctrl.txt`.

**Model: the physical model** (A79's plant, a byte-identical copy), with
the controller in synthesizable Verilog (Icarus Verilog 14.0, cocotb
2.1.0).

## 0. Verdict

1. **The complete Verilog controller takes P24's module from the all-zero
   state to a regulated 1 V with every phase switching softly (case f2,
   7.5% target).** The controller covers:
   - mode S during the 68.61 us input ramp;
   - the handover to mode P at the first phase-1 turn-on after the load is
     connected (88.80 us, the same instant as the Python reference);
   - predictive turn-on with the comparator trim;
   - the 12-bit ADC integral voltage loop.

   Result:
   - Vo enters the 1% band 64.9 us after the handover and ends at 1.0002 V;
   - Ton settles at 18.000 ns;
   - every phase turns on predictively once per cycle at 7.8-7.9 V (mean;
     Python reference 7.87-7.99 V), with no restart;
   - peak Vds 25.4 V, peak current 170.6 A.
2. **The implementation reproduces the Python model's behaviour, including
   A79's phase-4 bistability.** At the 5% target with the loop (f1), phase 4
   settles in the restart state, as A79 run 2 does; A79 run 1 settles in
   the soft state. At 7.5% (f2) it is soft, as in both A79 runs.
3. **The shortfall is the dither.** The cycle-to-cycle variation of the
   section currents is 2.3 A (f0, open loop) and 4.0 A (f2), against 0.9-
   1.2 A in the Python model. It has two sources:
   - phase 1's comparator-decided turn-off, quantised to the 4 ns clock by
     the synchroniser (A77);
   - the Ton command, which alternates between neighbouring 125 ps LSBs
     under the loop. One LSB is about 6.7 mV of Vo; the Vo ripple at the
     section samples is 0.56 mV.

   Criterion 2's 1 A dither threshold (a `PROJECT_DECISION`) is therefore
   not met by the Verilog version. The rest of criterion 2 is: soft once
   per cycle, no restart, Vds < 40 V.

## 1. Cases

**Common settings:**
- all-zero start; 48 V reached over a 68.61 us ramp;
- 4 mOhm load and handover request at 88.61 us; 388.61 us of plant time;
- 250 MHz, 125 ps edges, 10 ns driver delay;
- predictive turn-on with the sign-based trim, restart 20 / 400 ns,
  `dt_pred` starting at 11.6 ns;
- mode S with T0 200 ns, Ton 16.667 ns, dead time 2.15 ns.

| case | target | voltage loop | reference (Python) | mode P from | settle to 1% | Vo | Ton | period (spread) | phases 1-3 Vds at turn-on | phase 4 | dither | peak Vds / i | `VCs/Vin` |
|---|---:|---|---|---:|---:|---:|---:|---|---|---|---:|---|---|
| f0 | -6.25 A | off | A78 r5 | 88.80 us | - | 0.9437 V (ref 0.9472) | 16.625 ns | 230.40 ns (4.0) | 8.84-8.86 V (ref 8.90-8.92) | predictive, 9.27 V (ref 9.36) | 2.31 A | not recorded | 0.7467 / 0.4994 / 0.2517 |
| f0r | = f0, with the peak record | off | A78 r5 | 88.80 us | - | 0.9437 V | 16.625 ns | 230.40 ns (4.0) | 8.84-8.86 V | predictive, 9.27 V | 2.31 A | 25.19 V / 173.7 A | 0.7467 / 0.4994 / 0.2517 |
| f1 | -6.25 A | ki 0.25 | A79 r1 | 88.80 us | 65.1 us | 1.0013 V | 17.750 ns | 232.00 ns (0.5) | 9.05 V | **restart, 11.90 V** | 1.47 A | 25.2 V / 173.7 A | 0.7437 / 0.4936 / 0.2433 |
| **f2** | **-9.375 A** | **ki 0.25** | **A79 r3** | **88.80 us** | **64.9 us** | **1.0002 V** | **18.000 ns** | 239.41 ns (4.2) | **7.81-7.88 V** (ref 7.87-7.91) | **predictive, 7.94 V** (ref 7.99) | 4.01 A | 25.4 V / 170.6 A | 0.7456 / 0.4982 / 0.2504 |

**Start-up in mode S (f0).** The ladder follows the ramp:

| time | Vin | `VCs/Vin` |
|---|---:|---|
| 20 us | 14 V | 0.723 / 0.473 / 0.234 |
| 68 us | 47.6 V | 0.737 / 0.488 / 0.244 |
| 88 us (just before the handover) | 48 V | 0.749 / 0.500 / 0.251 |

This matches A73's mode-S behaviour.

**Late timed edges** are 1 on phase 2 and 10-12 on phase 4, all during the
transients.

## 2. Checks

- **Unit tests** (`tb/test_scb_ctrl.py`): 15 of 15 pass.
  - A77's ten tests, unchanged in mode P;
  - five new tests: mode S timing, chained edges in one window, the
    handover, loop integration with rounding, loop clamping.
- **Synthesis** (Yosys 0.69): `check -assert` passes, no latch, 22,267
  generic cells.
- **The peak record is dynamics-neutral.** f0r's 1755 sections equal f0's
  bit for bit (BOUNDARY Section 8).
- **Plant identity.** `cosim/plant_a79.py` is byte-identical to A79's
  `a79_transient.py` (checked with `cmp`).

## 3. Limits

- **Behavioural analog blocks.** The comparators, the delay line, the TDC,
  the residual-sign sampler and the ADC are behavioural Python: ideal
  thresholds and linear codes.
- **One driver delay** (10 ns) for every gate; no channel mismatch.
- **Idealised plant.** Linear Coss, lumped R, ideal diodes, Cout
  4.672 mF (inherited and suspect), one module.
- **Scenarios.** No load or line step.
- **Synthesis is generic.** Gate counts only; no timing closure.

## 4. Next

1. **Remove the quantisation dither: A81.** Give phase 1's comparator-
   decided turn-off, and the predictive turn-on that follows it, an
   asynchronous path in the mixed-signal front end: comparator -> latch
   -> gate, then a programmable delay line -> gate. The clocked logic arms
   it and sets the trim and delay codes, and a TDC reports the edge times.
   - Chiang and Chen 2009's controller is built this way: comparators, a
     latch and delay compensation, no clock.
   - Schaef et al. 2019's ZCD is an on-chip comparator path.
2. **Ton resolution.** Roberts' minimum-duty-increment method: per-phase
   Ton codes differing by one LSB, which raises the effective resolution
   N-fold.
3. **The mathematical model.** The four-phase extension, and the phase-4
   bistability at 5% (A79).

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py
cd cosim && zsh run_a80_cosim.sh f0_zero_start_loop_off f1_zero_start_loop_ki0p25 f2_zero_start_loop_ki0p25_itgt9p375 && cd ..
python3 a80_analyze.py
```

The toolchain is outside this repository (`~/tools/oss-cad-suite`). The
datasheet and paper PDFs are not in this repository.
