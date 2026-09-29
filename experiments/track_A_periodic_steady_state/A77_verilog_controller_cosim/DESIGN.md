# A77 - the P24 module controller in Verilog, co-simulated with the plant (DESIGN, draft)

**Status: final for the first A77 runs.** The draft was written while A76
ran. A76's decisions are now applied:
- **Kept:** the predictive valley turn-on and the comparator self-trim.
- **Dropped:** the reactive ZVS path. `cfg_zvs_react` stays in the RTL,
  off.
- **Removed:** the per-phase current condition. A76 rejected it, so the RTL
  does not implement it.

`BOUNDARY.md` declares the runs.

## 1. Why this layer

A69-A76 describe the controller as event rules inside the Python plant. In
that description, time is continuous and the controller has no clock. A75
showed that this hides a real P24 problem: a 10 ns comparator-to-gate
latency removes the reactive valley turn-on.

A synthesizable Verilog description forces the implementation facts into
the open:
- the clock and the edge resolution;
- synchroniser latency;
- counter widths;
- what every state does when its expected signal never comes;
- reset values.

It is also the form in which such controllers are built:
- Roberts' SCB controllers run on an FPGA;
- Xia and Stauth's CSS logic runs on an FPGA;
- Schaef et al.'s self-trimmed ZCD loop is on-chip digital logic.

## 2. Partition

| block | where | description |
|---|---|---|
| power stage, nodes, currents | Python plant (A76 `Sim`) | unchanged from A76, including `diode_check` |
| comparators (analog) | Python, next to the plant | produce 1-bit outputs from the plant state; the thresholds come from the Verilog trim codes through a DAC transfer |
| gate driver | Python | a propagation delay `t_drv` (LMG1210: 10 ns typical, 18 ns maximum) |
| controller (digital) | **Verilog, synthesizable** | clocked; sees the comparators only through 2-flip-flop synchronisers; outputs the gate requests with a fine-delay code |
| fine edge placement | behavioural, in the bridge | a delay line places each edge at `count * T_clk + code * LSB` |
| bridge | cocotb (Python) | advances the plant one clock period at a time; applies the gate edges at their fine times plus `t_drv`; writes the comparator bits |

The same split of digital logic in Verilog and comparators as analog
behavioural models is used in prithvideyannavar123/async-ams-multiphase-
buck-converter (GitHub; Verilog with Verilog-AMS comparators). That
repository has no licence, so only the idea is taken; none of its code is
used.

## 3. Timing resolution (`PROJECT_DECISION`, a parameter)

- **Base case.** `f_clk` = 250 MHz (4 ns), with a 5-bit delay line, so the
  edge LSB is 125 ps.
  - This is the counter-plus-delay-line hybrid DPWM of Roberts' thesis,
    Chapter 2: `T◇sw = 2^l * f_ctrl / f_sw`.
  - For P24 at 5 MHz, `T◇sw` = 32 * 50 = 1600 counts. Roberts' formula then
    gives an output-voltage resolution `Vin/(N * T◇sw)` of about 7.5 mV.
- **Contrast case.** Roberts' own FPGA setting: 125 MHz, counter only.
  - There `T◇sw` = 25, Ton ≈ 2 counts, and the resolution is about 0.48 V.
  - This case is expected to fail. It shows why P24 needs sub-clock edge
    placement.
- **Synchroniser latency.** A comparator bit reaches the logic 1-2 clock
  cycles after it changes: 4-8 ns at 250 MHz. It adds to the comparator and
  driver delays.

  This is why the rules keep the latency-critical instants (the valley,
  and ZVS if A76 confirms) on timers corrected by per-cycle measurements,
  instead of reacting to comparators.

## 4. Controller structure

**Per-phase state machine.** The states are A69-A76's HIGH, DOWN, LOW and
UP. Every state has a timeout exit, and reset puts all phases in LOW.

| from | to | condition |
|---|---|---|
| HIGH | DOWN | Ton counter expires |
| DOWN | LOW | low-side ZVS comparator (synchronised), or restart counter |
| LOW | UP | phase 1: current comparator, or restart counter. Phases 2..N: slot counter `k*T0/N` from phase 1's turn-on (A76 rejected an added current condition) |
| UP | HIGH | predictive timer `dt_pred[k]` (coarse count + fine code), or restart counter. The reactive ZVS path is off (`cfg_zvs_react` = 0, as A76 decided) |

**Predictive correction.** At each predictive edge, a slope comparator
sampled at the edge gives early or late.
- **Early:** the fine code is incremented.
- **Late:** a time-to-digital counter that timestamped the slope-sign
  change gives the valley time, and `dt_pred` is set to it.

This is A75's rule in a form hardware can measure.

**Comparator trim** (adopted in A76). Each current comparator has a
threshold code. After each comparator-decided turn-off, the sign of the
residual current is sampled at the switching node, and the code moves one
LSB. This is Schaef's sign-based loop.

A76 uses a proportional trim with the exact edge current. The co-
simulation will show whether the sign-based version converges to the same
edge current.

**Shared blocks.**
- the phase-1 period counter, giving `t_ref` and `T_meas`;
- the slot counters;
- configuration registers: Ton code, slot codes, restart counts, trim DAC
  base and LSB, and the correction step.

## 5. Verification plan

1. **Unit tests of the Verilog alone** (cocotb + Icarus):
   - state-machine transitions;
   - timeout exits;
   - reset;
   - counter overflow;
   - fine-code arithmetic.
2. **Open-loop equivalence.** Drive the Verilog with comparator traces
   recorded from an A76 run, and compare its gate edges with that run's
   edges. They should agree within the resolution plus the synchroniser
   latency.
3. **Closed-loop co-simulation.** Replace the Python event controller with
   the Verilog controller, and rerun A76's chosen configuration. Compare
   the end state and every phase's turn-on voltage.
4. **Synthesis check** (Yosys):
   - the design synthesises;
   - cell and flip-flop count;
   - no latches.

## 6. Tools

These are installed outside the repository, in `~/tools/oss-cad-suite`
(OSS CAD Suite 2026-09-29):
- Icarus Verilog 14.0;
- Verilator 5.053;
- Yosys 0.69;
- cocotb 2.1.0, installed in the system Python 3.14.

Every Verilog file carries `` `timescale 1ns/1ps``.
