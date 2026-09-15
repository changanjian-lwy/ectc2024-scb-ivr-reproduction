# R04E7 - voltage-ratio-gated EPE2019 charge-redistribution ladder bootstrap (BOUNDARY)

## 1. Parent

**PARENT: R04E6** (`experiments/track_B_zero_start_extension/
R04E6_epe2019_charge_redistribution_startup/`, `BOUNDARY.md`/`RESULTS.md`).
R04E6 implemented EPE2019 Fig. 5's 3-state charge-redistribution startup
sequence for P24's flying-capacitor ladder, on the same
`SCB4P_P24_EVENT`-derived power stage this project has used since R04E3
(series high-side chain `vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4`, flying
capacitors `CSk` bridging `ak`-`xk`, low-side switches `SLk` grounding
`xk`, `CFLY=53.8 uF`, `COUT=4.672 mF`, true zero initial energy). R04E7
reuses that power stage and that switch truth table **unchanged**:

- state (a) "Charging": `H1` ON, `L1` ON, all else OFF (charges `C1` alone
  from `vin`).
- state (b) "Charge Redistribution I": `H2` ON, `L1` ON, `L2` ON, all else
  OFF (redistributes `C1`<->`C2`).
- state (c) "Charge Redistribution II": `H3` ON, `L2` ON, `L3` ON, all else
  OFF (redistributes `C2`<->`C3`).

This table was independently derived from this project's own P24 topology
in R04E6 and cross-checked switch-for-switch against a rendered raster of
the EPE2019 source figure (R04E6/BOUNDARY.md Sections 5-6). It is **reused
unchanged here, not re-derived**, per the task's explicit instruction.

## 2. The single conceptual change relative to the parent

R04E6 gated every state by a **fixed hold time** `TH` (swept in `{200 ns,
1 us, 5 us, 20 us}`, applied equally to states a/b/c) and ran a **fixed
cycle count** `NCYC` (swept in `{1, 3, 5, 10}`). R04E6's own finding
(`NOT_CONVERGING`, 9/16 cells with `NCYC>=3`): every additional cycle
beyond the first makes `LADDER_ERR` monotonically **worse** at every hold
time `>=1 us`, because states (b)/(c) are unbiased pairwise-equalizing
loops with no mechanism favoring the `3:2:1` target ratio -- more cycles
just drift all three capacitors toward a common voltage.

**R04E7 replaces R04E6's blind-timer gating with voltage-ratio gating.**
Each state's exit condition is now a measured relationship between
capacitor voltages, implemented with this project's own
`.machine`/`.state`/`.rule` construct (the same mechanism already used for
physical-event-gated switching in R04D3A/R04E3/R04E5, and required by the
task instead of a plain behavioral voltage source):

- **State A** exits when `V(C1) >= 36 V` (the final target, gated
  directly -- see Section 3 for why this is correct even though a single
  pass cannot reach the full ladder).
- **State B** exits when `2*V(C1) <= 3*V(C2)`, i.e. `V(C1)/V(C2)` has
  reached the target ratio `3/2` -- self-correcting regardless of `C1`'s
  actual present voltage on any given cycle. This is the specific
  mechanism change addressing R04E6's diagnosed root cause (unbiased
  pairwise equalization).
- **State C** exits when `V(C2) <= 2*V(C3)`, i.e. `V(C2)/V(C3)` has
  reached the target ratio `2/1`.
- The whole (a)-(b)-(c) cycle repeats -- driven by measured state, not a
  fixed count -- until all three absolute voltages are **simultaneously**
  within a tolerance band of `36/24/12 V` (Section 5), or a safety cap on
  total simulated time is hit (Section 6).

Nothing else about the mechanism, truth table, power stage, or component
values changed. `TH` and `NCYC` (R04E6's free axes) no longer exist as
parameters; the new free axis is the tolerance-band half-width `TOL`
(Section 7).

## 3. Charge-conservation reasoning check (done before designing anything, per the task's instruction)

**Claim to check**: with `C1=C2=C3=Cfly` and this exact 3-state topology
(state (a) is the only state that draws fresh charge from `Vin`; states
(b)/(c) only move charge between capacitors already in the system), a
*single* pass through (a)-(b)-(c) cannot reach `VC1=36V, VC2=24V,
VC3=12V` exactly from zero energy.

**Check, done independently**: Model each state as an ideal (lossless,
charge-conserving) capacitor-to-capacitor transfer, since all three
capacitors are equal (`C1=C2=C3=C`):

- State (a): `C1` charges from `0` toward `Vin=48 V` via `H1`+`L1`. If held
  long enough it can reach any value up to `48 V`; call its value at the
  end of state (a) `V1a`.
- State (b): `C1` (at `V1a`) and `C2` (at `0`, on cycle 1) are connected in
  parallel through `H2`+`L1`+`L2`. Because the two capacitances are equal,
  an ideal (lossless) parallel connection would drive both to the
  **charge-conserving average** `(V1a+0)/2 = V1a/2`. The ratio-gated
  version does not have to wait for full equalization -- it can stop
  early, at any point where `V(C1)/V(C2)=3/2` -- but it is still bounded by
  the same conservation law: `C*V1a = C*VC1_after_b + C*VC2_after_b`, i.e.
  `VC1_after_b + VC2_after_b = V1a` (equal capacitances, no charge enters
  or leaves this loop). With the target ratio `VC1_after_b/VC2_after_b
  = 3/2`, this gives `VC1_after_b = (3/5)*V1a`, `VC2_after_b =
  (2/5)*V1a`.
- For `VC1_after_b` to equal the final target `36 V` (so that state (a)
  need never recharge `C1` again), `V1a` would have to equal `36*(5/3) =
  60 V`. **`60 V > Vin = 48 V`**, so state (a) cannot supply this in one
  pass -- confirming the claim's premise.
- Symmetrically, state (c) splits `VC2_after_b` between `C2` and `C3` in
  the target ratio `2/1`, giving `VC2_after_c = (2/3)*VC2_after_b`,
  `VC3_after_c = (1/3)*VC2_after_b`. Even if `VC2_after_b` were pushed to
  its own maximum plausible value, `VC3_after_c` is bounded well below
  `12 V` unless `V1a` already exceeds `48 V`.

**Conclusion: the claim holds.** A single (a)-(b)-(c) pass with equal
capacitors and `Vin=48 V` cannot reach `36/24/12 V` simultaneously,
because doing so would require state (a) to charge `C1` to `60 V` (exceeds
`Vin`). This is a hard algebraic consequence of charge conservation with
equal capacitances, not a tuning limitation. **Practical consequence**:
reaching the target requires *multiple* cycles even in this corrected
design -- confirmed directly by the actual runs (Section 8): the fastest
convergence (`TOL=10%`) still took 5 full cycles, none converged in 1.
This matches the task's own prediction and is not a symptom of a design
flaw.

(Note: state A's *own* re-entry on a later cycle is not bound by this
single-pass argument -- once `C2`/`C3` already hold some charge from a
prior cycle, `C1` recharging to `36 V` again and redistributing further
moves the whole ladder closer, cycle over cycle, exactly as observed.)

## 4. Borrowed-fact table (per-item, same standard as R04E6 Section 4)

| # | Borrowed fact | Source citation | Status |
|---|---|---|---|
| 1 | The 3-state switching TOPOLOGY and truth table (state a = `H1+L1`; state b = `H2+L1+L2`; state c = `H3+L2+L3`) | Roberts/McRae/Prodic, EPE'19 ECCE Europe, Fig. 5 (p.5); re-derived independently from this project's own P24 topology in R04E6 and cross-checked pixel-for-pixel against the rendered figure there | **CONFIRMED TRANSFERABLE**, inherited unchanged from R04E6 (already-approved, not re-derived here per the task's instruction). |
| 2 | The `36/24/12 V` target ratio (`3Vin/4, Vin/2, Vin/4`) | EPE2019 body text, p.5; already confirmed transferable in R04E6 Section 4 item 2 | **CONFIRMED TRANSFERABLE as a target number.** Reused unchanged as the comparator targets `TARGET1/TARGET2/TARGET3`. |
| 3 | The qualitative claim that the sequence "can be repeatedly cycled through until the desired voltages ... are obtained" | EPE2019 p.5, body text (quoted in full in R04E6/BOUNDARY.md Section 4 item 3) | **ASSUMPTION ONLY beyond the qualitative claim** (unchanged verdict from R04E6): the source gives no numeric hold time, cycle count, tolerance, or stopping rule. R04E7's entire voltage-ratio-gating design is this project's own `CROSS_PAPER_EXTENSION`-layered engineering response to that silence, not a value taken from the source. |
| 4 | The interpretation that the source's "bounce back-and-forth ... until the voltages ... become high enough" (EPE2019 p.4, describing the related CSC-buck mechanism) implies a *monitored*, voltage-feedback-gated stopping condition | R04E6/RESULTS.md's own closing causal discussion (not a fresh citation -- an inherited interpretive conclusion from the parent experiment) | **ASSUMPTION, inherited from R04E6, now tested directly.** R04E6 could only argue this from the *failure* of the blind version; R04E7 is the first experiment in this project to actually build and test a monitored/gated version, so this row's status graduates from "argued" to "empirically consistent with a working mechanism" (Section 8) -- but it remains this project's own engineering interpretation of the source's informal wording, not a numeric parameter EPE2019 specifies. |
| 5 | Any numeric inrush-current limit | Not present anywhere in EPE2019 (unchanged from R04E6 Section 4 item 4) | **ABSENT FROM SOURCE, explicitly not invented here.** No pass/fail current threshold is adopted; peak currents (Section 9) are reported and qualitatively flagged only, exactly as R04E6 did. |
| 6 | `Cfly=53.8 uF`, `Cout=4.672 mF` | EPE2019 Table 1 | Already an approved cross-source candidate, used unchanged since R02. **Not re-derived or re-justified here.** |
| 7 | The tolerance-band values (`+/-2%, +/-5%, +/-10%`) and the `50 us` safety cap | **This project's own working choice for this experiment, not from any source** | **NUMERICAL_IDEALIZATION / SENSITIVITY_ONLY, invented here and labelled as such.** See Sections 5-6 for the justification. Must never be read as an EPE2019 or P24 value. |

## 5. Tolerance-band definition and justification

A capacitor voltage `VCk` is considered "on target" when it lies within
`+/-TOL` of its target `TARGET_k` (`36/24/12 V`):
`TARGET_k*(1-TOL) <= VCk <= TARGET_k*(1+TOL)`. All three must hold
simultaneously for the run to be graded converged (`DONE`).

Three values of `TOL` were tried: `2%`, `5%`, `10%`, per the task's
instruction ("try at least 2-3 values"). These are **working definitions
chosen by this experiment, not paper-given numbers** (Section 4 item 7)
-- P24/EPE2019 state no numeric startup-settling tolerance. `2%`/`5%`/`10%`
were chosen because they bracket a plausible practical range (tight enough
that `10%` is still a meaningfully constrained target, loose enough that
`2%` is still reachable without an excessive cycle count) and because they
are round, easily-interpreted numbers matching the style of tolerance
bands already used elsewhere in this project (e.g. A48's dead-time
windows, R04E5's `+/-5% of 1 V` convention). No claim is made that any one
of these three is the "correct" or hardware-required tolerance.

## 6. Safety-cap definition and justification

**Choice made: a single GLOBAL cap on total simulated time,
`TCAP_TOTAL=50 us`, applied identically in all three active states (A, B,
C) via `.rule <STATE> CAPPED time>=TCAP_TOTAL`, listed with priority ahead
of each state's own local exit rule.** If time reaches `50 us` while the
machine is still cycling (not yet in `DONE`), it transitions to a
terminal `CAPPED` state (all gates forced off, safe idle) and the run is
graded `SAFETY_CAP_HIT_NOT_CONVERGED` for that cell.

This satisfies the task's requirement for "a maximum hold-time fallback in
case the comparator never trips, to avoid an infinite/hung simulation,"
including for state (a) specifically, but as a **global** rather than a
**per-state** cap. Reasoning for this choice, stated explicitly:

1. State (a)'s own physical dynamics cannot hang indefinitely by
   construction: `C1` charges toward `Vin=48 V` through switch `Ron`
   (`RHS+RLS` on the order of `10 mOhm`) and `CFLY=53.8 uF`, an `RC` time
   constant on the order of `0.5-1 us`; reaching `36 V` (`75%` of the
   `48 V` asymptote) requires about `1.4` time constants, i.e. well under
   `2 us` -- confirmed directly in the actual runs (state (a) of cycle 1
   completes in well under `1.6 us` in every case, Section 8). There is no
   physically plausible way for this specific comparator to "never trip"
   on this topology; a per-state timer would be a defensive measure
   against a failure mode that does not arise here, not a response to an
   observed risk.
2. A global cap still guarantees the simulation cannot hang: it bounds
   *every* state (A, B, and C individually, via the three separate `.rule
   ... CAPPED time>=TCAP_TOTAL` lines), not just the sum. The only
   difference from three independent per-state timers is that a state
   which somehow never exited would consume the *entire* remaining
   `TCAP_TOTAL` budget in one visit rather than being force-exited after
   its own smaller allotment and letting the cycle continue -- a
   conservative (safe, not silently permissive) behavior in the failure
   case, and irrelevant in the observed (working) case.
3. R04E6 already found and had to discard one numerical artifact from
   over-instrumenting this same circuit (the bit-identical `1.23e6 A`
   `ICS1_MAX` spike, R04E6/RESULTS.md). Three additional per-state
   RC-timer/reset-switch sub-circuits (following R04E5's own
   `CTIMER`/`BTIMER_CHG`/`SRESET` pattern) would triple the numerical
   surface area for a new artifact of that kind, for a documented-above
   negligible risk reduction. A single global cap was judged the better
   trade-off and is reported honestly as a design choice, not a
   forced necessity.

`50 us` itself (magnitude, not the cap-vs-per-state choice) was set
**empirically**, from an untracked (not committed -- purely diagnostic,
run in `/private/tmp/.../scratchpad/r04e7_pilot/`, not part of this
experiment's committed record) preliminary run of the same `.machine`
design at `TOL=5%` with `TCAP_TOTAL=20 us`: that diagnostic converged
(`DONE`) at `t~=4.07 us`, after 6 cycles, with `LADDER_ERR` decreasing
monotonically every single cycle (`1.6 -> 0.96 -> 0.576 -> 0.346 ->
0.207 -> 0.124`). All three of this experiment's own committed runs (`TOL
in {2%, 5%, 10%}`) converged between `t=3.90 us` and `t=4.24 us` (5-8
cycles) -- comfortably inside `50 us`, giving roughly a `12x` margin over
the slowest observed convergence, without being so large that a
non-converging cell (had one occurred) would take an impractical amount
of wall-clock time to simulate (each committed run took `117-135` real
seconds; at the observed step-cost rate, `50 us` of simulated time is the
largest cap this experiment judged practical to run for all three
tolerance cells within a normal session, not a value tuned to guarantee
convergence). No cell in this experiment's own committed grid hit the
cap (Section 8) -- had one occurred, this would be reported as a
legitimate, useful `SAFETY_CAP_HIT_NOT_CONVERGED` outcome, not hidden or
extended.

A cycle-COUNT cap (the task's other suggested option, "50 cycles") was not
used as the enforced stop condition, because the `.machine` construct has
no native counter variable; building one would require the same kind of
extra RC-based counter circuitry flagged as an added-artifact risk in
point 3 above. The generated netlists still report up to 50 per-cycle
`.meas` checkpoints (`VC1_CYC1` .. `VC1_CYC50`) for observability, so an
actual cycle count is always recoverable from the log even though it is
not the netlist's own enforced stopping mechanism.

## 7. Free sensitivity axis

`TOL` (tolerance-band half-width) in `{2%, 5%, 10%}`, per Section 5.
`TCAP_TOTAL=50 us` is fixed (not swept) across the grid, per Section 6.

## 8. Chatter check (per the task's explicit instruction to try before reporting a dead end)

The task specifically asked that a ratio-comparator formulation be
checked for numerical fragility/chatter (echoing R03B's old algebraic-ZCD
failure mode, STEP_08's documented lesson: "a detector needs state memory,
delay/blanking/hysteresis, or a different physically continuous
surrogate"). Reasoning and direct evidence, both reported:

- **Reasoning**: R03B's chatter was on an *instantaneous current
  zero-crossing* comparator, where the controlled quantity (current
  through a switch whose own state the comparator controls) can change
  discontinuously with the switch action, creating a self-referential
  loop prone to rapid re-triggering. This experiment's comparators are on
  *capacitor voltages* (`V(C1)`, `V(C1)/V(C2)`, `V(C2)/V(C3)`), which
  cannot jump discontinuously (an instantaneous voltage jump on a
  capacitor requires infinite current) -- the crossing is smooth and
  single-valued by construction, structurally less chatter-prone than a
  current-based detector.
- **Direct evidence**: all three committed runs (Section 9) show a single,
  clean, monotonically-progressing sequence of cycle-end voltages with no
  repeated or out-of-order `.meas` timestamps, each run completed in
  `117-135` real seconds (not a runaway/hung solve), and `state_mon`'s
  reported final state is a clean integer (`3.0`, i.e. exactly `DONE`) in
  all three cells. No hysteresis band or state-memory workaround was
  needed for this experiment's own grid.
- **Caveat, stated honestly**: this checks the three tested `(TOL)` cells
  only, at fixed component values. It does not prove chatter is
  impossible in this construction generally (e.g. under different
  `CFLY`/`Ron`/`TOL` combinations); it reports the direct evidence that no
  chatter occurred here, not a general proof.

## 9. Success condition

For a given `TOL`, the run reaches the `DONE` state (`STATE_FINAL==3`)
before `TCAP_TOTAL`, and `LADDER_ERR` at the end of every completed cycle
is monotonically non-increasing from the previous cycle (the opposite of
R04E6's own finding). Reported per-`TOL`: cycle count at convergence,
final `VC1/VC2/VC3`, and final `LADDER_ERR`.

## 10. Failure conditions

- `TCAP_TOTAL` is reached while still in `STATE_A`/`STATE_B`/`STATE_C`
  (`STATE_FINAL==4`, `CAPPED`) -- graded `SAFETY_CAP_HIT_NOT_CONVERGED`,
  reported honestly, not hidden or silently re-run with a larger cap.
- `LADDER_ERR` does not monotonically improve cycle-over-cycle at some
  `TOL` (would indicate the ratio-gating fix does not actually address
  R04E6's diagnosed root cause) -- would be reported as such, not forced
  into a pass.
- Solver non-convergence before the run's own `.tran` stop time.

## 11. What this experiment cannot prove

- It does **not** attempt, and says nothing about, handing off into P24
  steady-state ZVS admission or `Vout` regulation -- explicitly out of
  scope (inherited unchanged from R04E6's own stated scope limit).
- It cannot claim hardware switch-stress validation. Peak currents
  (Section 9 below in RESULTS.md) are reported and qualitatively flagged
  only, exactly as R04E6 did; no numeric current threshold is adopted
  (Section 4 item 5).
- It cannot claim four-phase interleaving; `H4`/`L4` are never driven,
  unchanged from R04E6.
- It cannot claim this specific `TOL`/`TCAP_TOTAL` choice is "correct"
  rather than a sensitivity/engineering choice (Sections 5-6); a
  different, unqueried tolerance or cap value might behave differently.
- It cannot claim the zero-dead-time state handoffs (inherited unchanged
  from R04E6's own Section 11 idealization: no interlock gap between one
  high-side switch's turn-off and the next's turn-on) are a validated
  hardware timing; this remains a known idealization, reported not
  hidden, exactly as in R04E6.
- It cannot claim general immunity to comparator chatter across all
  possible component values or tolerance settings -- only that no chatter
  occurred in this experiment's own tested grid (Section 8).
- A pass in these three `TOL` cells does not imply an untested `TOL`
  value would also pass, though the clean monotonic multi-cycle trend
  (Section 9 of RESULTS.md) makes this more plausible than it was for any
  single R04E6 cell.

## 12. Honesty about mechanism provenance (`CROSS_PAPER_EXTENSION`)

Unchanged from R04E6: the 3-state charge-redistribution sequence itself is
a `CROSS_PAPER_EXTENSION` from EPE2019's "conventional 4-phase SC buck"
comparison topology, grafted onto P24's four-phase connectivity because
the two are switch-for-switch identical for this purpose (R04E6 Sections
5-6). **The voltage-ratio-gating mechanism that replaces R04E6's blind
timer is this project's own engineering design, not sourced from EPE2019
or P24** -- EPE2019 gives only the qualitative "repeatedly cycled through
until the desired voltages ... are obtained" (Section 4 item 3), with no
comparator, ratio, or tolerance specified. This must never be reported as
an EPE2019-specified control law.
