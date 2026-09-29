# A77 - the P24 module controller in Verilog, co-simulated with the plant (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`; design:
`DESIGN.md`; how to run: `README.md`. Records:
- `cosim/run_c*.json`;
- `a77_summary.json`;
- `synth/stat_scb_ctrl.txt`.

**Model: the physical model** (A76's plant, a byte-identical copy), with the
controller replaced by synthesizable Verilog (Icarus Verilog 14.0, cocotb
2.1.0). The question is whether the adopted control rules survive a
clocked, synchronised, finite-resolution implementation. The event-level
models have no clock (BOUNDARY Section 2).

## 0. Verdict

1. **The Verilog controller reproduces the Python event controller's
   steady state within its quantisation.** Base case: 250 MHz, a 5-bit
   delay line with 125 ps edges, 10 ns driver delay. Against A76 run 1:
   - period 221.45 ns (reference 221.41 ns);
   - Vo 0.9599 V (0.9628 V);
   - phases 1-3 turn on predictively at a mean of 9.82-9.87 V (9.85 V);
   - phase 4 turns on at its restart time, 10.77 V (10.82 V).

   The rules adopted in A76 are implementable:
   - the predictive turn-on corrected from sign-and-time measurements;
   - Schaef's sign-based comparator trim;
   - fixed slots;
   - restart timers.
2. **The synchroniser quantises the comparator-decided edge.** Phase 1's
   low-side turn-off is decided by its current comparator. That decision
   reaches the logic only at a clock edge, so the turn-off lands on the
   4 ns grid.
   - Its edge current jitters between -4.5 and -1.9 A (mean -2.75 A;
     target -2.5 A). The span, ~2.6 A, is `Vo/L * 4 ns` ≈ 0.66 A/ns *
     4 ns.
   - The period spreads by 4 ns, and the section currents vary by 3.65 A
     over the last 20 cycles.
   - The trim settles at code 50 (threshold +10.0 A). It compensates about
     19 ns of total latency: 1-2 synchroniser clocks, the window alignment,
     and the 10 ns driver.

   The event model could not show this effect; the implementation-level
   description exposes it.
3. **A counter-only 125 MHz DPWM (Roberts' FPGA setting, 8 ns) is not
   adequate at P24.** It runs, but:
   - Vo is 0.924 V, 39 mV low, because Ton is quantised to the 8 ns grid;
   - the period spreads by 16 ns and the section currents vary by 8.5 A;
   - turn-ons reach 11.5 V;
   - 21 timed edges fire late.

   More fundamentally, one Ton step of 8 ns moves Vo by about 0.43 V (the
   plant's `dVo/dTon` ≈ 54 mV/ns). That is Roberts' resolution argument:
   his formula gives 0.48 V. P24's 5 MHz needs sub-clock edge placement.
4. **Phase 4** remains restart-driven at -2.5 A, as in A76. The target is
   A78's question.

## 1. Runs (last 50 phase-1 cycles)

| | A76 run 1 (reference) | c1: 250 MHz + 125 ps | c2: 125 MHz, counter only |
|---|---:|---:|---:|
| period | 221.411 ns | 221.450 ns (spread 4.0) | 221.200 ns (spread 16.0) |
| Vo | 0.9628 V | 0.9599 V | 0.9238 V |
| phases 1 / 2 / 3, Vds at turn-on, mean (max) | 9.85 / 9.85 / 9.85 V | 9.87 (10.06) / 9.82 (10.21) / 9.84 (10.22) V | 10.10 (11.51) / 10.01 (11.52) / 10.00 (11.54) V |
| phase 4 | restart, 10.82 V | restart-equivalent, 10.77 (10.95) V | restart-equivalent, 10.81 (12.22) V |
| phase-1 edge current, mean [min, max] | -2.50 A | -2.75 [-4.50, -1.86] A | -3.19 [-6.36, -0.02] A |
| phases 2 / 3 edge current, mean | -3.19 / -3.19 A | -3.38 / -3.34 A | -3.64 / -3.66 A |
| section-current variation, last 20 | 0.77 A (predictive dither) | 3.65 A | 8.51 A |
| late timed edges, per phase | - | 0 / 0 / 5 / 0 | 13 / 3 / 5 / 0 |
| trim code (threshold) | proportional, +4.07 A | 50 (+10.0 A) | 74 (+16.0 A) |
| `dt_pred`, phases 1-4 | 10.78 / 10.03 / 9.81 / 20.01 ns | 9.38 / 9.12 / 9.12 / 20.25 ns | 10.75 / 10.00 / 10.00 / 20.25 ns |

**Notes on the table.**
- **"Restart-equivalent".** Phase 4's `dt_pred` walks up to the 20 ns
  restart time (A75 Section 1). Both then quantise to 160 LSB, and the
  predictive branch fires first, so the edge is labelled predictive but is
  the restart edge.
- **Late edges.** They occur in the start-up transient, when a slot passes
  while a phase is still in an earlier state.
- **Simulated length.** 100 us, ~450 cycles, from A76 run 1's last section.
  The first on-time is ~10 ns long because the plant starts with phase 1's
  high side on, while its first turn-off command passes the driver delay
  (BOUNDARY Section 4). The statistics use the last 50 cycles.

## 2. Checks

- **Unit tests.** `tb/test_scb_ctrl.py`: 10 of 10 pass (listed in
  BOUNDARY Section 4).
- **Synthesis.** Yosys 0.69:
  - `check -assert` passes;
  - no latch (`select -assert-none t:*DLATCH*`);
  - 13,284 generic cells in total: two `scb_phase` variants of 3,086 and
    3,352 cells, the top level 642, the synchroniser 32.
  - The 32-bit time arithmetic dominates. The widths can be narrowed.
- **Plant identity.** `cosim/plant_a76.py` is byte-identical to A76's
  `a76_transient.py` (checked with `cmp` when copied).

## 3. Limits

- **Behavioural analog blocks.** The comparators, the delay line, the TDC
  and the residual-sign sampler are behavioural Python: ideal thresholds,
  no offset or noise.
- **No mismatch.** There is no channel-to-channel delay mismatch; one
  driver delay (10 ns) is used for every gate.
- **Mode P only.** Start-up (mode S and the handover) is not in the RTL.
- **Open-loop Ton.** Cout 4.672 mF (inherited, suspect), and one module.
- **Synthesis is generic.** Gate counts only; no FPGA or standard-cell
  mapping and no timing closure.

## 4. Next

1. **The target from A78.** Declare a c3 case at the target A78 selects
   (an amendment before the run).
2. **Remove the 4 ns jitter of phase 1's turn-off.** Time that turn-off by
   prediction too, from the previous cycles' comparator timestamps (a
   TDC), instead of reacting through the synchroniser. This is the same
   principle as the predictive turn-on.
3. **Closed-loop Vo.** Physical model first (A79); then in the RTL. The
   Ton register then needs the 125 ps resolution: about 6.7 mV of Vo per
   LSB.
4. **Start-up in the RTL.** Mode S with fixed timing, and the handover.

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py
cd cosim && zsh run_a77_cosim.sh c1_base_250mhz_itgt2p5 c2_counter_125mhz_itgt2p5 && cd ..
python3 a77_analyze.py
```

The toolchain is outside this repository (`~/tools/oss-cad-suite`, OSS CAD
Suite 2026-09-29). The datasheet and paper PDFs are not in this repository.
