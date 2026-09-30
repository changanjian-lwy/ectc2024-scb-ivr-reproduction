# A89 - the predicted low-side turn-on in the Verilog controller (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A88 (Python) replaced the reactive low-side turn-on (comparator + latency)
by a timed edge, t_off + dtl. A per-phase corrector learns dtl from the
node's zero crossing. With EPC2067's datasheet Coss(V) and reverse drop,
this removed the 56 W reverse-conduction loss, and D47 confirmed it in the
mathematical model.

**Can the Verilog controller do the same, and is the addition safe for
everything already verified?**

The controller is A81's RTL with the 7-bit delay line of A85 (31.25 ps
LSB). A85 met single-module criterion 2 in full at 5%.

## 2. The addition must not break the system (the gates)

The new behaviour is opt-in and every earlier result stays reproducible.

1. **RTL.** `rtl/` is a copy of A81's `rtl/`; A81's files are not touched,
   because A83 and A85 build from them.
   - The new logic sits behind `cfg_low_pred`.
   - With `cfg_low_pred = 0`, every existing path is the old code; no old
     expression changes.
2. **Unit tests.** `tb/test_scb_ctrl.py` is a copy of A81's 18 tests.
   - The only change to the old part: the start-up fixture also drives the
     new input ports to 0.
   - All 18 must pass on the new RTL (FB = 5, as before). New tests cover
     the new logic.
3. **Synthesis.** Yosys `synth; check -assert; stat` must pass with no
   latch, as for A80/A81.
4. **Co-simulation gate g0.** The new bridge and the new plant module,
   with the device realism switched off and `cfg_low_pred = 0`, must
   reproduce A85 run r7 bit-identically. That means equal section count,
   section voltages and currents (difference 0.0), and equal final dt_pred,
   trim, Ton code, late fires and asynchronous fires.
   - The bridge is a copy of A83's (A85 uses it).
   - The plant module is A88's simulator, imported read-only instead of
     A79's byte copy.

   This one run proves that the RTL copy, the bridge copy and the plant
   swap change nothing.
5. **One factor at a time.** The plant's device realism (a prerequisite,
   already accepted in A86-A88) and the new RTL rule are switched on in
   separate runs, g1 and r1, so each effect is seen on its own.

## 3. The RTL change (mode P only; mode S unchanged)

**New per-phase register `dtl`,** the low-side dead time in LSB.
- Reset value: `dtl_init` (2.15 ns, P24's dead time, as A88).
- Output for observability.

**Timed edge.** In DOWN, when `cfg_low_pred = 1`, the low side turns on at
t_off + dtl, a timed edge with its fine code, as the high side's predictive
edge.
- If t_off + dtl falls in the same clock window as the high-side turn-off,
  both edges are emitted in that clock. This is the chaining mode S already
  uses for its dead time; without it a 1 ns dead time would wait for the
  next 4 ns clock.
- The restart timer stays as a guard (t_off + 20 ns).

**Correction** from a zero-crossing measurement, delivered as a one-cycle
pulse like the high side's valley measurement: `ml_valid`, `ml_early`,
`ml_tv` (the crossing time after the high-side turn-off, in LSB).
- early: `dtl += cfg_dtl_step`, capped at `cfg_dtl_max`;
- otherwise: `dtl = ml_tv`, capped.

This is A88's rule. **Step:** 0.05 ns in A88; here 2 LSB (62.5 ps), the
nearest the 31.25 ps delay line allows. `PROJECT_DECISION`.

**Not changed:** the high side, the phase-1 path (synchronous and
asynchronous), the slots, the trim and the voltage loop.

## 4. The bridge change (a copy of A83's)

1. **Plant.**
   - `"plant": "a88"` imports A88's `a88_transient` (read-only) for Params
     and Sim.
   - Config options `nonlinear_coss` and `rev_drop` switch on the datasheet
     Coss(V) and the Fig. 8 reverse drop (A88's fit).
   - Stepping keeps A83's rules. With `rev_drop` it uses A87's: a device
     conducts in reverse only when V_DS < -Vf, it is cut when V_DS > -Vf,
     the resistive stamp, and energy accounting.
2. **Zero-crossing TDC** (only when `low_pred`, mode P).
   - For each phase, the bridge records the time its low-side V_DS first
     reaches 0 after its high-side turn-off. That comparator's own delay is
     taken as known (exact here, as in A88).
   - At the low-side turn-on edge it reports:
     - early: not yet crossed;
     - otherwise: the crossing time after the high-side turn-off, rounded to
       the LSB (the TDC resolution, as for the high-side valley).
   - All gate edges carry the same 10 ns driver delay, so the RTL's
     command-time t_off + dtl lands at the actual turn-off + dtl, as with a
     PWM-mode driver's programmable dead time (LMG1210).
3. **Records.** Per section:
   - reverse-conduction energy and time per switch;
   - each low-side edge (V_DS, early or late, the crossing time).

## 5. Runs

All at 5%, as A85 r7:
- FB 7, 250 MHz;
- asynchronous phase-1 path, learning at restarts;
- ki 0.25 ns/V, 12-bit ADC;
- t_drv 10 ns;
- zero start to 388.61 us.

| run | plant | device realism (Coss(V), reverse drop) | `cfg_low_pred` | purpose |
|---|---|---|---|---|
| g0 | A88 module | off | 0 | gate: bit-identical to A85 r7 |
| g1 | A88 module | on | 0 | the plant upgrade alone, with the RTL's reactive low side |
| r1 | A88 module | on | 1 | the new rule |

## 6. Predictions (written before the runs)

- **g0:** bit-identical to A85 r7.
- **g1:** more reverse-conduction loss than A87's 56 W.
  - The RTL's reactive low side acts 2-3 clocks after the window in which
    the comparator trips (synchroniser), plus the 10 ns driver delay:
    about 18-22 ns after the crossing, against 10 ns in A87.
  - Expected about 90-120 W, and Ton about 3-4 ns longer.
  - No confident prediction on soft switching.
- **r1:**
  - P_rev below 2 W (A88: 0 W);
  - dtl converges to about 0.9-1.25 ns;
  - Ton, the phase-4 current and turn-on voltage within the RTL
    quantisation of A88 r3 (Python, 5%): 17.74 ns, -5.75 A, 9.11 V;
  - every phase soft once per cycle, no restart; dither as A85 (about
    0.9 A).
- **Unit tests** (old and new) pass, and synthesis is clean.

## 7. Decides / does not decide

Decides:
- whether the implementation-level controller realises A88's rule and
  its result with the realistic device;
- whether the addition leaves the earlier RTL behaviour intact.

Does not decide:
- the zero-crossing comparator and TDC as circuits: their delay is taken
  as known, and their resolution as the LSB;
- gate-driver dynamics and jitter;
- other targets (only 5%);
- package and PCB parasitics.

## 8. Amendment (after runs g0, g1, r1; before g0b, g1b, r2)

**What r1 showed.**
- g0 passed its gate (bit-identical to A85 r7). g1 behaved as predicted.
- r1 reached a clean steady state: P_rev 0 W, dither 0.93 A. But peak Vds
  was 38.25 V and peak current 773.6 A, against 26.7 V and 171 A in g1.

**The diagnostic run** (`cfg_dbg_r1_handover.json`, to 89.2 us, every
applied edge logged) located the event: a shoot-through on phase 1 just
after the handover.
1. The handover turn-on of phase 1 starts at -61.8 A.
2. The RTL issues the high-side turn-off and the chained low-side turn-on
   in one clock, and phase 1 enters LOW. That arms A81's asynchronous
   current front end.
3. The plant applies both edges only after the 10 ns driver delay, so its
   high side is still on and i1 (-16.8 A) is still below the -6.25 A
   threshold. The front end fires.
4. Its SH1 turn-on (t_cmd + dt_pred + t_drv) arrives after the timed SL1
   turn-on: SH1 and SL1 conduct together for 16.6 ns. Cs1 is driven to
   the 48 V input.

**Cause.** A81's front end is armed by the RTL state LOW. It relied,
implicitly, on the reactive low side entering LOW about 20 ns after the
turn-off command, when the physical high side is off. The timed low side
enters LOW at the command, 10 ns before the physical turn-off.
- In steady state i1 is already above the threshold then, so nothing
  happens.
- In a transient (here the handover) it is not.

Python A88 has no such gap: its edges are physical, with no command
versus actual time.

**Fix: leading-edge blanking.** This is the standard enable window of a
current comparator after a switching event.
- A new RTL input `cfg_blank` enables phase 1's current comparators (the
  asynchronous arm and the synchronous `c_i`) only once
  now - t_lon >= cfg_blank, where t_lon is the low-side turn-on command.
- With `cfg_blank = 0` the condition is always true in LOW, and the RTL
  is bit-identical to before.
- r2 uses 20 ns (`PROJECT_DECISION`). It covers the driver's maximum
  propagation delay (LMG1210: 21 ns max) and restores roughly the
  front end's A81-A85 arming time (about 20 ns after the turn-off
  command).

**Added runs** (r1 is kept as the record of the hazard):

| run | device realism | `cfg_low_pred` | `cfg_blank` | purpose |
|---|---|---|---:|---|
| g0b | off | 0 | 0 | gate again with the changed RTL: bit-identical to A85 r7 |
| g1b | on | 0 | 0 | regression: bit-identical to g1 |
| r2 | on | 1 | 20 ns | the rule with blanking |

**Prediction for r2:**
- the r1 steady state (P_rev 0 W, dither below 1 A);
- peak Vds about 27 V and peak current about 175 A, with no shoot-
  through: every applied SH1 turn-on finds SL1 off.

**New unit tests:**
- the arm stays low until the blanking has elapsed;
- the synchronous current comparator cannot turn the low side off inside
  the blanking.

The old tests run with `cfg_blank = 0`.
