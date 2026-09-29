# A81 - an asynchronous fast path for phase 1's turn-off and turn-on (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`; how to run:
`README.md`. Records:
- `cosim/run_g*.json`;
- `a81_summary.json`;
- `synth/stat_scb_ctrl.txt`.

**Model: the physical model** (A79's plant, identical copy) with the
controller in Verilog and a behavioural asynchronous front end. The
question concerns which edges are clocked and which are asynchronous
(BOUNDARY Section 2).

## 0. Verdict

1. **Phase 1's edge jitter came from the synchroniser.** The asynchronous
   path removes it.
   - The spread of phase 1's turn-off current falls from 3.0 A (-10.6 to
     -7.56 A) to 0.26 A (-9.61 to -9.35 A). The target is -9.375 A.
   - Phase 1's turn-on voltage now varies by 0.04 V (7.88 mean, 7.92 max),
     against 0.6 V with the synchroniser.
   - The comparator trim settles at code 30 (threshold -1.9 A). It now
     compensates only about 11.5 ns: 1 ns comparator and latch, plus the
     10 ns driver.
2. **The module's dither halves, from 4.0 to 1.9 A.** The period spread
   falls from 4.2 to 2.9 ns. It is still above the 1 A threshold of
   criterion 2 (a `PROJECT_DECISION`). The remainder is not yet
   attributed. The candidate is the Ton command alternating between 125 ps
   LSBs under the voltage loop: the Vo ripple is unchanged at 0.56-0.58 mV.
3. **Nothing else changes.**
   - every phase turns on predictively once per cycle, no restart;
   - Vo 0.9999 V, reached within 67.9 us of the handover;
   - peak Vds 25.65 V, peak current 170.5 A;
   - the handover still at 88.80 us.

## 1. Cases

The setup is A80 case f2's:
- all-zero start; 7.5% target (-9.375 A);
- voltage loop ki 0.25 ns/V;
- 250 MHz, 125 ps edges, 10 ns driver.

| | g0: async off (gate) | g1: async on (`t_async` 1 ns) |
|---|---:|---:|
| identical to A80 f2 | yes: 1707 sections, difference 0.0 | - |
| asynchronous firings | 0 | 1266 |
| phase-1 turn-off current, mean [min, max] | -9.49 [-10.60, -7.56] A | -9.48 [-9.61, -9.35] A |
| phase 1 Vds at turn-on, mean / max | 7.88 / 8.49 V | 7.88 / 7.92 V |
| phases 2-4 Vds at turn-on, mean / max | 7.81-7.94 / 8.61-8.84 V | 7.83-7.93 / 8.15-8.56 V |
| section-current dither, last 20 | 4.01 A | 1.92 A |
| period (spread) | 239.41 (4.2) ns | 238.77 (2.9) ns |
| Vo, settle to 1% after handover | 1.0002 V, 64.9 us | 0.9999 V, 67.9 us |
| Ton | 18.000 ns | 18.000 ns |
| trim code (threshold) | 55 (+4.4 A) | 30 (-1.9 A) |
| peak Vds / current | 25.40 V / 170.6 A | 25.65 V / 170.5 A |

## 2. Checks

- **Unit tests:** 18 of 18 pass. A80's 15 are unchanged with `cfg_async`
  = 0, and there are 3 async tests (BOUNDARY Section 4).
- **Synthesis** (Yosys 0.69): `check -assert` passes, no latch, 24,160
  generic cells. The asynchronous latch and delay line are front-end
  blocks outside the synthesised logic.
- **Regression gate:** g0 equals A80 f2 bit for bit.

## 3. Limits

- **Behavioural front end.** The latch, the delay line and the TDC are
  behavioural. The comparator-plus-latch delay (1 ns) is a
  `PROJECT_DECISION`, and the TDC hand-off into the clock domain is
  assumed clean: no metastability.
- **Idealised plant.** The same as A80: linear Coss, lumped R, ideal
  diodes, Cout 4.672 mF (inherited and suspect), one module, no load step.

## 4. Next

**Attribute the remaining 1.9 A.** Test the Ton-LSB hypothesis with a finer
Ton or Roberts' minimum-duty-increment method (per-phase Ton codes one
LSB apart). This is an implementation refinement. The single-module
criteria that remain open are the mathematical-model cross-check and the
phase-4 bistability at 5% (CURRENT_STATUS).

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py
cd cosim && zsh run_a81_cosim.sh g0_async_off_gate g1_async_on && cd ..
python3 a81_analyze.py
```
