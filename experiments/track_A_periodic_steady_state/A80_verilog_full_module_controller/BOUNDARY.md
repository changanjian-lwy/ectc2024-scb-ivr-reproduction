# A80 - the full P24 module controller in Verilog, co-simulated from zero (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any declared run, while A79
was running. The loop gain is fixed by a rule stated here (Section 4).

## 1. Question

A77 showed that the mode-P controller in Verilog reproduces the Python
event controller's steady state. A single module also needs:
- the start-up sequence: fixed timing (mode S) during the input ramp;
- the handover to mode P when the load is connected;
- the output-voltage loop.

Does the complete Verilog controller take the P24 module from the all-zero
state to its regulated periodic state, as the Python reference does? The
Python reference is A73's sequence with the A76/A78/A79 rules.

## 2. Model used, and why

**The physical model** (A79's plant, a byte-identical copy in
`cosim/plant_a79.py`), with the controller in synthesizable Verilog. The
question is whether the whole control sequence is implementable with a
clock, synchronisers and finite resolution. Only the implementation-level
description answers it (A77 Section 0).

## 3. Controller (`rtl/`, a copy of A77's RTL, extended)

**Mode S.** A71/A73 fixed timing: T0 200 ns, Ton 16.667 ns, dead time
2.15 ns.
- Timed transitions that fall in the same 4 ns window are emitted
  together, so the dead time stays 2.125 ns (17 LSB).
- Mode S uses no comparator and no restart timer.

**Handover.** `hand_req` rises when the plant reaches t_hand (88.61 us).
The next phase-1 high-side turn-on switches the mode register to P, as in
A71/A73.

**Mode P.** A77's controller:
- predictive valley turn-on;
- sign-based comparator trim;
- restart timers of 20 and 400 ns;
- fixed slots;
- no reactive ZVS;
- target -6.25 A (A78);
- `dt_pred` starting at 11.6 ns, the same start value as the Python rule;
- trim codes starting at 0.

**Voltage loop (A79's rule).**
- At each phase-1 turn-on, a 12-bit ADC sample of Vo (0.5 mV per LSB,
  behavioural) enters the loop.
- `ton_acc += ki * (vref - code)`, with 16 fractional bits.
- Ton is the rounded accumulator, clamped to [0.5, 2] x Ton.
- The loop acts in mode P only.

**Timing.** 250 MHz with a 5-bit delay line (125 ps), and a 10 ns driver
delay.

## 4. Runs

**Plant.** A73's sequence with A79's plant:
- all-zero start;
- 48 V reached over a 68.61 us ramp;
- 4 mOhm load and handover at 88.61 us;
- t_end 388.61 us.

| case | voltage loop | reference (Python) |
|---|---|---|
| f0 | off (open-loop Ton) | A78 run 5 (-6.25 A, open loop) |
| f1 | on, `ki` by the rule below | the A79 run with that `ki` |

**Rule for `ki`.** Use 0.25 ns/V (A79 run 1) if that run passes both
conditions:
- Vo within 1% of 1 V by the end;
- single-module criterion 2.

Otherwise use 1.0 ns/V (A79 run 2) if it passes both. If neither passes,
run f1 at 0.25 ns/V and report it as such.

## 5. Checks already made

- **Unit tests** (`tb/test_scb_ctrl.py`): 15 of 15 pass.
  - A77's ten tests run unchanged in mode P from reset, which is the
    backward-compatibility check.
  - The five new tests cover:
    - mode S (period and dead times);
    - chained edges in one window;
    - the handover at the phase-1 turn-on;
    - loop integration with rounding;
    - loop clamping.
- **Synthesis** (Yosys 0.69): `check -assert` passes, no latch, 22,267
  generic cells.

## 6. Reporting

Against each case's Python reference:
- the handover time;
- Vo settling (1% band) after the handover;
- final Vo, Ton and period;
- per-phase turn-on kind and voltage over the last 50 cycles;
- criterion 2;
- the trim codes, `dt_pred`, late fires;
- the dither.

## 7. Decides / does not decide

Decides:
- whether the complete controller (start-up, handover, switching rules,
  voltage loop) works as synthesizable, clocked logic on P24's module from
  zero.

Does not decide:
- load and line transients;
- analog front-end non-idealities (behavioural comparators, ADC, delay
  line and TDC);
- channel mismatch;
- timing closure on real hardware;
- nonlinear Coss;
- the mathematical-model cross-check.

## 8. Amendment (after case f0, before any further run)

**What f0 showed.** The complete controller runs the zero start: mode S
through the ramp, the handover at 88.80 us, and every phase predictive and
soft in mode P.

**A gap.** The bridge did not record peak Vds and peak current, which
criterion 2 needs (< 40 V). The bridge now keeps both. They are computed
from the per-step switch voltages it already evaluates for the diode
update, so the dynamics are unchanged.

**Added case f0r.** It is f0's configuration rerun with the peak record.
Its sections must equal f0's bit for bit. f1 is run with the same bridge.

## 9. Amendment (after f0, f0r, f1 and A79 runs 3-4; before f2)

**f1 (5% target, loop on).** It regulates Vo from zero to 1.0013 V, but
phase 4 settles in the restart state. So does A79 run 2 (5%, ki 1.0),
while A79 run 1 (5%, ki 0.25) settles in the soft state. At 5%, both
phase-4 states exist.

**A79 runs 3-4 (7.5%).** Both loop gains settle in the soft state. 7.5%
(-9.375 A) is inside P25's 5-10%.

**Added case f2.** f1 with the target at -9.375 A. The reference is A79
run 3 (7.5%, ki 0.25).
