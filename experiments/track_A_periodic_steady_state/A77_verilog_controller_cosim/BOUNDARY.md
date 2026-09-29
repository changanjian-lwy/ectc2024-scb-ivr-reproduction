# A77 - the P24 module controller in Verilog, co-simulated with the plant (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any declared run. The design
is in `DESIGN.md`.

## 1. Questions

1. **Does the synthesizable controller reproduce the Python event
   controller's steady state?** The controller is:
   - clocked, with comparators seen through a 2-FF synchroniser;
   - using a counter plus delay-line DPWM with 125 ps edges;
   - using a sign-based comparator trim;
   - using a predictive valley turn-on corrected from measurements.

   It closes the loop around the same A76 P24 plant, with a 10 ns
   gate-driver delay. The reference is A76 run 1: predictive, trimmed,
   10 ns latency, -2.5 A target.
2. **Does a counter-only DPWM at 125 MHz (8 ns resolution) work at P24?**
   This is the setting of Roberts' SCB FPGA controller.

## 2. Model used, and why

**The physical model (the A76 plant, an unmodified copy) with the
controller replaced by Verilog.** The question is whether the control rules
survive implementation: clocking, synchronisation, finite edge resolution
and sign-only measurements. Only an implementation-level description can
show that. The mathematical model has neither delays nor clocks.

## 3. Setup

**Controller.** `rtl/scb_ctrl.v` (N = 4, TW = 32, FB = 5, CW = 8), run by
Icarus Verilog 14.0.

**Bridge.** `cosim/test_cosim.py` (cocotb 2.1.0) steps the plant one clock
window at a time:
- gate edges are applied at `(window + fine) * LSB + t_drv`;
- the comparators are sampled at each window end;
- measurements return as one-cycle pulses.

**Plant.** `cosim/plant_a76.py`, a byte-identical copy of A76's
`a76_transient.py`:
- P24 values: 48 V held, 4 mOhm load on;
- `diode_check`, h = 10 ps.

**Initial state.** A76 run 1's last section (phase 1 just turned on, phases
2-4 LOW), with the controller's reset state matching it:
- `dt_pred` from A76 run 1's end;
- the trim code from its threshold: +4.07 A gives code 26 at 0.25 A per
  LSB.

**Controller settings:**
- Ton 16.667 ns, i.e. 133 LSB;
- slots 50 / 100 / 150 ns;
- restart 20 ns (high) and 400 ns (low);
- predictive step 0.25 ns (2 LSB; A75 used 0.2 ns), predictive cap
  34.8 ns;
- trim LSB 0.25 A (`PROJECT_DECISION`);
- valley hysteresis 0.05 V (unused in predictive mode).

**Latency now has three parts:**
- the comparator itself (0 here);
- 1-2 synchroniser clocks (4-8 ns at 250 MHz);
- the driver's 10 ns.

With the trim, A76 found the steady state independent of the latency.

## 4. Checks already made

- **Unit tests** (`tb/test_scb_ctrl.py`): 10 of 10 pass. They cover:
  - edge windows and fine codes;
  - synchroniser latency (2-3 clocks);
  - the current-decided turn-off and its flag;
  - predictive timing;
  - the slots;
  - predictive correction (early, late, flat, cap);
  - the trim (step, saturation, and no trim on a timer-decided turn-off);
  - the counter-only mode;
  - the restart.
- **Synthesis** (Yosys 0.69, `synth/`): `check -assert` passes, no latch,
  13,284 generic cells.
- **Smoke test.** 2 us of c1, not a declared run, record deleted. The bridge
  runs at about 2 s wall per simulated us. Edges land at slot + t_drv, and
  the trim moves the phase-1 edge current toward target (-9.0 to -7.5 A
  over 8 cycles).

  It also showed a start-up artefact: the plant starts with phase 1's high
  side already on, while its first turn-off command passes through the
  10 ns driver delay, so the first on-time is 10 ns long. The runs are
  therefore long enough (100 us, ~450 cycles) for that transient and the
  trim convergence (~1 LSB per cycle) to die out.

## 5. Runs

| case | clock | edge resolution | `i_target` | t_end | purpose |
|---|---|---|---:|---:|---|
| c1 | 250 MHz | 125 ps (5-bit delay line) | -2.5 A | 100 us | question 1 |
| c2 | 125 MHz | 8 ns (counter only) | -2.5 A | 100 us | question 2 |

After A78 has settled the target, a case at the chosen target will be
declared in an amendment before it is run.

## 6. Reporting

Over the last 50 phase-1 cycles, compared with A76 run 1 (period
221.41 ns, Vo 0.9628 V, phases 1-3 at 9.85 V, phase 4 restart-like at
10.82 V):
- period and Vo;
- per phase: turn-on kind (predictive, or restart-equivalent) and Vds at
  the edge;
- phase 1's edge current against -2.5 A, and the trim code;
- the late-fire counts;
- `dt_pred`;
- periodicity or dither (the last 20 sections).

## 7. Decides / does not decide

Decides:
- whether the adopted rules survive a clocked, synchronised, finite-
  resolution implementation at P24;
- whether a counter-only 125 MHz DPWM is adequate.

Does not decide:
- comparator offsets and noise, channel mismatch;
- the analog front-end circuits: the comparators, the delay line and the
  TDC are behavioural;
- start-up (mode S and the handover are not in the RTL yet);
- closed-loop Vo;
- timing closure on a real FPGA or process.
