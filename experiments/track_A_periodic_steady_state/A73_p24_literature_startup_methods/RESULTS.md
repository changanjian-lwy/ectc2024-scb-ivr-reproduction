# A73 - P24 start-up with the published ladder-control methods, and a simulator defect (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with amendments
8-10, each made before the runs it declares. Records:
- `run_*.json`;
- `a73_summary.json`;
- `regression_gate_vs_A72.json`.

## 0. Verdict

**The cause of A72's failure was a defect in the simulator, not the circuit
and not open-loop ladder balancing.**

The defect: since A69, the reverse-conduction branch was a 0.1 uOhm resistor
whose on/off state was updated only at step boundaries. Within a step it
therefore conducted in **both** directions. When a switch turned on while the
opposite device's diode was conducting (a hard turn-on), the input was shorted
through that "diode" for one 10 ps step:
- 3.4 MA was observed through SL1 at t = 200 ns in the run-1 smoke test;
- a 3 uF flying capacitor jumped by 11 V in that step.

It was found because the result was physically impossible: an 11 V change on
3 uF in one step would need ~150 A average over 200 ns, while the inductor
currents were ~15 A.

**The fix, `diode_check`.** A diode-only branch that ends a step with Vds > 0
(drain->source current) is switched off, and the step is recomputed.

With the fix:
- **The A71 sequence works on P24.** The sequence is a fixed-timing input
  ramp at Roberts' rate, then load and handover together, with the valley
  fallback and A72's controller fixes. It settles on a periodic state within
  the device rating (run 5).
- **All three sequences end in the same periodic state.** The literature
  methods reach it too: Wei-type ratio precharge plus Kim-type soft start
  (run 1), and Xia-Stauth-type closed-loop balancing during the ramp
  (runs 2-3). In this idealised model they are not needed. They were not
  harmful either.

| run | sequence | ladder deviation before the handover (Vin ≥ 12 V) | peak i | peak Vds | end state |
|---|---|---:|---:|---:|---|
| 1 | M1: precharged ladder + 86 us Ton ramp, load + handover at 106 us | 1.3% | 161 A | 24.8 V | periodic |
| 2 | M2: balancing k_b = 1 during the 68.61 us ramp | 2.0% | 161 A | 24.8 V | periodic |
| 3 | M2: k_b = 3 | 1.5% | 160 A | 24.8 V | periodic |
| 4 | ramp only (re-check of A72 run 4), no load | 3.0% (end 0.12%) | 109 A | 24.6 V | mode S, no handover |
| 5 | ramp, then load + handover (re-check of A72 run 9) | 3.0% | 161 A | 24.8 V | periodic |

**The common periodic state of runs 1, 2, 3 and 5:**
- period 222.891 ns; Vo 0.9653 V;
- ladder `VCs/Vin` = 0.7487 / 0.5034 / 0.2579 (deviation 0.8%);
- section currents 1.05 / 29.80 / 63.56 / 108.99 A;
- over the last 20 cycles, the currents vary by 11 uA and Vo by 0 V.

**Peak Vds.** SH2-SH4 normally block 2*Vin/N = 24 V while the preceding phase
is on; SH1 and the low sides block Vin/N = 12 V. The start-up peaks, 24.6-24.8 V,
are that normal value. EPC2067's 40 V leaves a 1.6x margin in this model.

## 1. What the P24 steady state reveals

- **Phases 1-3 turn on by the valley path in every cycle, at Vds ≈ 9.8 V.**
  The node rises only ~2 V of 12 V, as A67 predicted for P24's point
  (ZVS is out of reach).
- **Phase 4 turns on by the restart timer in every cycle.** All 199
  restarts after convergence were phase-4 `high_restart`.
  - The fixed shifts are 50/100/150 ns (T0/4 multiples). The current-sensed
    phase 1 stretches the period to 222.9 ns.
  - Phase 4's timed low-side turn-off therefore comes while its current is
    still positive (109 A at the section). The node is diode-clamped, and
    no resonance occurs.
  - The steady state thus depends on the restart-timer value (20 ns,
    `PROJECT_DECISION`).
  - This makes the **adaptive phase shift** (shifts that follow the
    measured period; see CURRENT_STATUS) a requirement at P24 scale, not a
    refinement.

## 2. Re-checks of earlier results with the fixed diode model

| run | earlier result | with `diode_check` | diode corrections | status of the earlier result |
|---|---|---|---:|---|
| 6 | A71: mode S under load never settles (sustained oscillation) | settles within 100 us (Vo 0.933 V; zero variation after) | 89 | **withdrawn**: artefact |
| 7 | A71 run 6: load + handover together reach D42's section | same final section (identical to 5 digits); 4 valley firings (A71: 5) | 80 | stands |
| 8 | A71 run 1: handover 100 us after the load stalls | reaches D42's section 129 us after the handover, no valley firing | 133 | **withdrawn**: artefact |
| 9 | A69: deadlock without the valley path | same deadlock: t = 7.854 us, states (LOW, UP, UP) | 40 | stands |
| 10 | A70 run 2: one valley firing (SH2 at 54 mV) recovers to D42 | identical: one firing, phase 2, 54 mV, t = 2.54 us; reaches D42 at 150 us | 0 | stands |

Consequences:
- A71's recommendation that the handover must coincide with the load
  connection loses its basis. The handover can also follow a settled
  fixed-timing interval under load.
- A72's verdict is withdrawn. See the correction added to its RESULTS.
- The A69 orbit cross-checks, A70, and A71's converged state are unaffected.

## 3. Checks

- **Regression gate.** With the new options off, the simulator reproduces
  A72 run 4's first 20 us bit-identically: 101 sections, 0.0 difference.
- **After the `diode_check` code change.** The gate was re-verified
  bit-identical.
- **The fix does not change fault-free runs.** A70 run 2's re-check needed
  zero corrections and is bit-level equivalent in outcome.

## 4. Limits

- The circuit is idealised:
  - linear Coss (1860 pF per device);
  - 0.54 mOhm lumped per-phase resistance;
  - 0.1 uOhm switches;
  - an ideal diode, now unidirectional, with no reverse recovery;
  - an ideal input ramp;
  - open-loop Ton;
  - Cout 4.672 mF, inherited and suspect.
- The literature methods' real value is robustness with non-ideal devices,
  faster ramps and line transients. None of that is tested here: all
  methods reach the same state in this model.
- `k_b`, the restart times, the soft-start time and the handover rule are
  `PROJECT_DECISION`s.
- **Track B discrepancy (unexplained).** Track B's LTspice ramp-only run
  (R04E16: no diodes, no dead time, 4 mOhm load throughout, 10 mOhm / 5 nH
  input) ended with the ladder in the right 3:2:1 shape but at ~55% of its
  level, with Vo 0.56 V. This model's ramp-only run tracks. That LTspice
  netlist has no diode branches, so the defect found here does not explain
  its result.

## 5. Next

1. **Adaptive phase shift (both models).**
   - In this simulator: shifts at k*T_measured/N instead of k*T0/N. Check
     that phase 4 then reaches the valley or ZVS without the restart timer.
   - In the mathematical model: the D41 policy extension already listed
     in CURRENT_STATUS.
2. **Explain the Track B R04E16 discrepancy.** That needs its netlist
   replayed in this simulator (complementary gates, input parasitics, load
   throughout).
3. **Lesson for the simulator.** The diode sign check now enforces what
   should always have been an invariant. Every model-derived result
   before A73 that involved hard turn-ons against a conducting diode is to
   be treated as unverified until re-run.

## 5a. Reproduction

```
F="--stall-periods 20 --level-events --t-restart-high 20 --t-restart-low 400 --diode-check"   # use ${=F} in zsh
python3 a73_transient.py r1_m1_precharge_softstart --t-ramp 0 --t-load 106 --t-hand 106 --t-end 406 --init-ladder 36,24,12 --t-ss 86 $F
python3 a73_transient.py r2_m2_balance_kb1 --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61 --k-b 1 $F
python3 a73_transient.py r3_m2_balance_kb3 --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61 --k-b 3 $F
python3 a73_transient.py r4_recheck_a72r4_ramp_only --t-ramp 68.61 --t-load 1e6 --t-hand 1e6 --t-end 88.61 --stall-periods 20 --diode-check
python3 a73_transient.py r5_recheck_a72r9 --t-ramp 68.61 --t-load 88.61 --t-hand 88.61 --t-end 388.61 $F
python3 a73_transient.py r6_recheck_a71r4_p25_s_loaded --preset p25 --t-ramp 46 --t-load 96 --t-hand 1e6 --t-end 496 --diode-check
python3 a73_transient.py r7_recheck_a71r6_p25_handover --preset p25 --t-ramp 46 --t-load 96 --t-hand 96 --t-end 696 --diode-check
python3 a73_transient.py r8_recheck_a71r1_p25_late_handover --preset p25 --t-ramp 457 --t-load 507 --t-hand 607 --t-end 1207 --diode-check
python3 a73_transient.py r9_recheck_a69_deadlock_no_valley --preset p25 --t-ramp 0 --t-load 0 --t-hand 0 --t-end 541 --init-z-json ref_D41_lossless.json --no-valley --diode-check
python3 a73_transient.py r10_recheck_a70r2_valley --preset p25 --t-ramp 0 --t-load 0 --t-hand 0 --t-end 541 --init-z-json ref_D41_lossless.json --diode-check
```

The datasheet and paper PDFs are not in this repository.
