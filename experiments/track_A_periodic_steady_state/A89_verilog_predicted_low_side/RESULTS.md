# A89 - the predicted low-side turn-on in the Verilog controller (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-7 were written before any run.
- Section 8 was added after runs g0, g1 and r1, before g0b, g1b and r2.

**Records:**
- `cosim/run_*.json`;
- `cosim/dbg_*_handover.json`: diagnostics with every applied edge logged
  around the handover;
- `a89_summary.json`;
- `synth/stat_scb_ctrl.txt`.

**Model: the physical model.** The Verilog controller (A81's RTL plus the
timed low side and blanking, FB = 7) closes the loop around A88's Python
plant, which has the datasheet Coss(V) and reverse drop. It runs through a
copy of A85's cocotb bridge. Mathematical counterpart of the rule: D47.

## 0. Verdict

1. **The Verilog controller realises A88's rule with the realistic device**
   (5%, run r2):
   - reverse-conduction loss 0 W;
   - every phase soft once per cycle, no restart;
   - dither 0.91 A (criterion 2 met in full);
   - Vo 0.9999 V, settled 67.5 us after the handover;
   - peak Vds 27.0 V, peak current 173 A;
   - the learned dead time is 0.97-1.22 ns.

   | | A89 r2 (Verilog) | A88 r3 (Python, 5%) |
   |---|---:|---:|
   | Ton | 17.750 ns | 17.739 ns |
   | phase 4 at its turn-off | -5.87 A | -5.75 A |
   | phase-4 turn-on voltage | 9.06 V | 9.11 V |
   | period | 231.97 ns | 231.73 ns |

2. **Without it, the realistic device costs 109 W with the RTL's reactive
   low side** (g1). The synchroniser plus the 10 ns driver delay puts the
   low-side turn-on about 19.9 ns after the high-side turn-off.
   - Ton rises to 21.0 ns.
   - The dither is 4.1 A.
   - Vo settles only after 113.6 us.

   This is worse than A87's Python 56 W, which had a 10 ns latency, as
   predicted (90-120 W).

3. **The first version (r1) exposed a latent hazard, and the addition was
   made safe before it was accepted.**
   - r1's steady state was as clean as r2's. But just after the handover,
     phase 1 shot through for 16.6 ns: SH1 turned on while SL1 conducted.
     The peak current was 773.6 A, peak Vds 38.25 V, and Cs1 was driven to
     the 48 V input.
   - **Cause.** A81's asynchronous front end arms when the RTL enters LOW.
     The timed low side enters LOW at the turn-off command, a 10 ns driver
     delay before the physical turn-off. At the handover, phase 1 starts at
     -61.8 A, so its current was still below the threshold while its high
     side conducted, and the front end fired. The reactive low side had hidden
     this by entering LOW about 20 ns late.
   - **Fix: 20 ns leading-edge blanking** of phase 1's current comparators
     after the low-side turn-on command. With cfg_blank = 0 the RTL is the old
     one (gates g0b and g1b).
   - **Result (r2).** The same diagnostic finds no turn-on against a
     conducting complement: 0, against 7 in r1's. Peak values are back to
     27.0 V and 173 A.

4. **Nothing earlier changed.**
   - All 18 A81 unit tests pass on the new RTL. With the 8 new tests, 26 of
     26 pass.
   - Synthesis is clean.
   - Three co-simulation gates are bit-identical (Section 2).

## 1. Runs (5%, FB 7; last 50 cycles)

All runs use A85 r7's settings:
- asynchronous phase-1 path, learning at restarts;
- ki 0.25 ns/V, 12-bit ADC;
- t_drv 10 ns;
- zero start to 388.61 us.

| run | device (Coss(V), reverse drop) | cfg_low_pred | cfg_blank | Ton | period | phase 4 at its turn-off | phase-4 Vds at turn-on | dither | P_rev | settle after handover | peak Vds / current | criterion 2 |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| g0 (gate) | off | 0 | - | 17.719 ns | 230.54 ns | -5.26 [-5.78, -4.84] A | 9.17 V | 0.90 A | 0 | 67.7 us | 25.50 V / 169.5 A | pass (= A85 r7) |
| g1 | on | 0 | - | 21.031 ns | 226.73 ns | -6.42 [-8.35, -4.65] A | 8.95 V | 4.10 A | **109.3 W** | 113.6 us | 26.66 V / 171.4 A | soft, no restart; dither 4.1 A |
| r1 | on | 1 | - | 17.750 ns | 232.00 ns | -5.88 [-6.41, -5.37] A | 9.06 V | 0.93 A | 0 | 76.8 us | **38.25 V / 773.6 A** | steady state passes; **shoot-through at the handover** |
| g0b (gate) | off | 0 | 0 | 17.719 ns | 230.54 ns | as g0 | 9.17 V | 0.90 A | 0 | 67.7 us | 25.50 V / 169.5 A | pass (= A85 r7) |
| g1b (gate) | on | 0 | 0 | 21.031 ns | 226.73 ns | as g1 | 8.95 V | 4.10 A | 109.3 W | 113.6 us | 26.66 V / 171.4 A | = g1 |
| **r2** | on | 1 | 20 ns | **17.750 ns** | **231.97 ns** | **-5.87 [-6.32, -5.39] A** | **9.06 V** | **0.91 A** | **0** | **67.5 us** | **27.01 V / 172.9 A** | **pass** |

**Notes.**
- **The low-side edges** of r2's last 1000 mode-P edges fall 0.97-1.22 ns
  after the high-side turn-off, at V_DS -0.49 to +0.16 V. Final dtl:
  1.22 / 1.16 / 1.16 / 0.97 ns.
- **In g1**, the low side turns on 19.8-19.9 ns after the turn-off, with the
  node at -2.33 V throughout.
- **Late edges.** A timed edge due before the current window is placed at
  the window start. Over the whole run: g0 12, g1 30, r1 67, r2 15. None in
  r2's last 1000 low-side edges.

## 2. Checks: the addition breaks nothing

| check | result |
|---|---|
| A81's 18 unit tests on the new RTL (new inputs at 0) | 18 / 18 pass |
| new unit tests (timed edge, chaining, comparator ignored, correction, reports ignored when off, mode S unaffected, blanking of the asynchronous arm and of the synchronous comparator) | 8 / 8 pass |
| Yosys `synth; check -assert` | 0 problems, 0 latch cells; 30,721 cells (A81: 24,160) |
| g0: A89 RTL, bridge and plant module, all additions off, against A85 r7 | bit-identical: 1755 sections, difference 0.0; equal dt_pred, trim, Ton code, late and asynchronous fires, step count, peak Vds and current |
| g0b: the same with the blanking RTL (cfg_blank 0) | bit-identical to A85 r7 |
| g1b: the blanking RTL (cfg_blank 0) against g1 | bit-identical: 1780 sections |
| RTL diff against A81 | additions, plus four existing lines changed: two port-list commas (scb_phase, scb_ctrl), and the asynchronous arm and synchronous `c_i` conditions, each now ANDed with the blanking term, which is always true at cfg_blank = 0. `sync2.v` is identical |
| bridge diff against A85 | only the plant import, the step call, two diode thresholds, the Params line and two record dictionaries changed; the rest is additions |

**The overlap checker is validated.** Applied to r1's diagnostic it finds 7
turn-ons against a conducting complement, the first at 88.8386 us (the one
found by hand); on r2's it finds 0.

## 3. Predictions (BOUNDARY Sections 6 and 8) against the results

| | predicted | result |
|---|---|---|
| g0 | bit-identical | bit-identical |
| g1 P_rev | 90-120 W | 109.3 W |
| g1 Ton | +3-4 ns | +3.3 ns (21.03 ns) |
| r1/r2 P_rev | below 2 W | 0 W |
| r1/r2 dtl | 0.9-1.25 ns | 0.97-1.22 ns |
| r1/r2 against A88 r3 | within quantisation | Ton +0.011 ns, phase-4 current -0.12 A, Vds -0.05 V |
| r1 transient | (not predicted) | shoot-through at the handover; found by the peak check |
| r2 (after the amendment) | peak about 27 V and 175 A, no overlap | 27.01 V, 172.9 A, 0 overlaps at the handover |

## 4. Consequences

- **The implementation-level controller now carries the whole adopted
  rule set with the realistic device.** That is:
  - predictive valley high side, learning at restarts;
  - asynchronous phase-1 path;
  - timed low side with blanking;
  - voltage loop.

  At 5% it meets criterion 2 in full with no reverse-conduction loss.
- **A lesson for later additions.** The RTL's state leads the physical
  switches by the driver delay. Any comparator that acts on physical
  quantities must be enabled from physical, not command, time.
  - The reactive low side had masked this.
  - The peak-current and peak-Vds records exposed it, together with the
    requirement that no addition may break the system.
- **The single-module device-realism chain so far:**

  | step | model | addition | result |
  |---|---|---|---|
  | A86 | Python | Coss(V) | 2% works |
  | A87 | Python | reverse drop | 56 W with the reactive low side |
  | A88 | Python | timed low side | 0 W |
  | A89 | Verilog | the same rule | 0 W, after the blanking fix |

## 5. Limits

- **One target** (5%) and **one gate-driver model**: a fixed 10 ns delay,
  with no jitter, ramp or high/low mismatch (LMG1210: 3.4 ns). The timing
  window after the crossing is 0.16-0.22 ns (A88/D47); a real driver's
  jitter must stay inside it.
- **The zero-crossing comparator and TDC are ideal:** a known delay and LSB
  resolution.
- **Blanking** of 20 ns is a `PROJECT_DECISION`, checked at the handover
  transient only. Load and line steps are not tested.
- **The circuit.** A88's idealised module otherwise: lumped R, no package or
  PCB parasitics (next level), Cout 4.672 mF (inherited, suspect).

## 5a. Reproduction

```
export PATH="$HOME/tools/oss-cad-suite/bin:$PATH"
python3 tb/run_unit.py                                   # 26 unit tests
yosys -p "read_verilog rtl/sync2.v rtl/scb_phase.v rtl/scb_ctrl.v; synth -top scb_ctrl; check -assert; stat"
zsh cosim/run_a89_cosim.sh g0_gate_a85r7 g1_device_reactive_low r1_device_low_pred
zsh cosim/run_a89_cosim.sh g0b_gate_a85r7 g1b_regression_g1 r2_device_low_pred_blank
python3 cosim/run_cosim.py cfg_dbg_r1_handover.json      # and cfg_dbg_r2_handover.json (from cosim/)
python3 a89_analyze.py
```

**Code history.** r1, g0 and g1 were produced before the `cfg_blank` input
and the diagnostic edge log existed.
- With `cfg_blank = 0` and no debug window, the current code is equivalent
  for low_pred = 0: g0b and g1b are bit-identical to g0 (A85 r7) and g1.
- For r1 the equivalence follows from the same argument: with cfg_blank = 0
  the blanking condition is always true in LOW. r1 was not rerun.
