# A76 - P24 single module: settle the control rules before the Verilog controller (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Questions

A75 left three control rules open. They must be settled before the
controller is written in Verilog, because each one changes the controller's
structure.

1. **The latency confound.** In A75, the latency also delayed phase 1's
   current-comparator edge. The effective negative current became -5.8 to
   -13.5 A instead of -2.5 A. With the comparator trip point compensated,
   does the predictive valley turn-on still keep every phase soft at
   10-18 ns?
2. **Phase 4 (A74).** At its timed low-side turn-off, phase 4 carries
   +7.08 A, so it cannot ring. If phases 2..N may turn their low sides off
   only once their own current is below the target, does phase 4 turn on
   softly, and does the dependence on the restart timer disappear?
3. **The ZVS path at 18 ns.** In A75 run 7, the delayed reactive ZVS
   decision was the weak point. Does leaving ZVS to the predictive timing
   remove it?

## 2. Model used, and why

**The physical model** (A75's simulator, copied). These are controller-rule
questions about P24's four-phase circuit. A rule change in the simulator is
the cheapest discriminating test; the Verilog implementation follows once
the rules are fixed. The mathematical model has neither four phases nor
delays.

## 3. Sources (all read; none in this repository)

- **Comparator self-trim: Schaef et al., ISSCC 2019**, DOI
  10.1109/ISSCC.2019.8662294. This is P25's reference [22] for its zero-
  cross detection. The ZCD comparator's trip point is digitally trimmed
  (a 5-bit capacitive-DAC offset) by a loop that detects the residual
  current after the low-side turn-off. This corrects the comparator offset
  and the circuit delays.
- **Per-phase current condition:**
  - **P25, Sec. II:** the low side is turned off "once [the current]
    reaches the required negative value (5-10% of the peak current)".
  - **TI UCC28063A datasheet:** in its interleaved transition-mode control,
    both channels are masters, each with its own ZCD input. A minimum-
    period timer bounds the frequency.

  The rule tested here combines the two: the timed slot of the D41 rule
  acts as the lower bound, as the minimum period does in UCC28063A, and
  the phase's own current condition must also hold.
- **Predictive turn-on for ZVS:** Chiang and Chen (TPEL 2009) derive the
  predictive turn-on for the ZVS instant itself. Leaving ZVS to the timed
  prediction follows that.

## 4. Rules as implemented (`a76_transient.py`, a copy of A75's)

All new options are off by default. Mode S is unchanged.

**`trim_gain` g: comparator self-trim.**
- Each phase's current comparator trips at its own threshold `theta_k`,
  which starts at `i_target` = -2.5 A.
- At each low-side turn-off edge that a current comparator decided, the
  threshold is corrected: `theta_k += g * (i_target - i_edge)`.
- `theta_k` is clamped to `[i_target - 10, i_target + 30]` A.
- g = 0.5 per cycle (`PROJECT_DECISION`; Schaef's loop gain is not
  published).

**`qualify_current`: per-phase current condition.**
- For phases 2..N in mode P, the low-side turn-off needs both conditions:
  `t >= t_ref + shift_k` and `i_k <= theta_k`.
- **The binding condition decides.** If the current condition is met
  last, the decision is a comparator decision: it gets the latency t_d and
  feeds the trim. If the timer is met last, the edge is a timed edge: no
  latency, no trim.

**`zvs_reactive = False`: ZVS left to prediction.**
- In predictive mode, the high side has no reactive ZVS decision.
- The predictive timer handles ZVS too. At a node clamped at ZVS, the
  late branch sets `dt_pred` to the time the minimum was reached.
- The restart timers stay.

**Regression gate (run 0).** With every new option off, run 0 replays A75
run 6 (predictive, t_d = 10 ns) over its full length bit-identically.

## 5. Runs

All runs use A75's P24 settings: fixed shifts `k*T0/N`, `t_restart_high`
20 ns, `t_restart_low` 400 ns, `level_events`, `diode_check`, a 30x ramp,
load and handover at 88.61 us, and t_end 388.61 us.

| run | valley mode | t_d | trim | qualify | reactive ZVS | question |
|---|---|---:|---|---|---|---|
| 0 | predictive | 10 ns | - | - | yes | gate (A75 run 6) |
| 1 | predictive | 10 ns | 0.5 | - | yes | 1 |
| 2 | predictive | 18 ns | 0.5 | - | yes | 1 |
| 3 | predictive | 18 ns | 0.5 | - | no | 3 |
| 4 | reactive | 0 | - | yes | yes | 2 |
| 5 | predictive | 0 | - | yes | yes | 2 |
| 6 | predictive | 10 ns | 0.5 | yes | no | all three rules together |
| 7 | predictive | 18 ns | 0.5 | yes | no | all three rules together |

## 6. Reporting

As in A75 Section 6, plus:
- the final `theta_k`;
- which condition bound each phase's turn-off (current or timer);
- the phase-1 edge current against the -2.5 A target;
- whether each run passes the single-module criterion "every phase soft,
  no restart in the last 50 cycles".

## 7. Decides / does not decide

Decides:
- whether A75's predictive gain survives with the confound removed;
- whether the per-phase current condition fixes phase 4;
- whether ZVS can be left to prediction;
- hence which rules the Verilog controller implements.

Does not decide:
- clock and DPWM resolution, channel mismatch, comparator noise and
  offset (the Verilog step);
- closed-loop Vo;
- nonlinear Coss;
- the trim gain's optimum;
- the mathematical model.
