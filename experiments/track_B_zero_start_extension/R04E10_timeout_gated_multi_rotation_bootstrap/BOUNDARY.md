# R04E10 - timeout-gated multi-rotation bootstrap (BOUNDARY)

## 1. Parent

**R04E9** (`experiments/track_B_zero_start_extension/
R04E9_unified_inductor_mediated_bootstrap/`). R04E9 built a unified
rotating `CHARGE_k`/`FREE_k` machine driving all four phases, using P24's
own native Interval-1 inductor-mediated charging path for every phase (NOT
EPE2019's switch-only mechanism borrowed by R04E6/E7/E8). `CHARGE_k`
(`QHk` on) exited ONLY on the physical current-limit event
`I(Lk)>=I_LIMIT`; `FREE_k` (`QLk` on) exited at the earlier of the natural
`I(Lk)<=0` event or an A48-style timeout `T_FREEWHEEL_MAX`. Result: peak
currents stayed physically plausible (under `61 A` everywhere, vs.
R04E6-E8's `4.2-4.6 kA`), confirming inductor-mediated charging is the
right direction -- but every one of the 9 tested cells stalled permanently
in `CHARGE2`: phase 2's high side (`SH2`) connects between `C1` and `C2`,
not to `Vin` directly, so it depends on `C1` already holding charge that
phase 1's own very brief (`~0.93 ns`) first pulse barely supplied. Because
`CHARGE_k` had no timeout fallback, a phase that cannot reach its own
current limit never exits, so the rotation never completed even once in
any of R04E9's 9 cells.

## 2. What changed relative to the parent, exactly

**Single conceptual change**: `CHARGE_k` now exits at
`(I(Lk)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)`, symmetric with `FREE_k`'s
existing `(I(Lk)<=0) | (V(timer)>=T_FREEWHEEL_MAX)` event-OR-timeout
pattern. This is implemented by adding a SECOND per-state elapsed-time
timer (`CTIMER_CHG`/`timer_chg`/`BTIMER_CHG2`/`BRESET_GATE2`/
`SRESET_CHG`), an EXACT mirror of R04E9's own already-validated FREE-state
timer construct with the charge/reset roles swapped:

- `CTIMER_CHG` (`timer_chg` node, `1p` capacitor, `ic=0`) charges via
  `BTIMER_CHG2` (`I=-1p*(IS_CHARGE)`) only while the machine is in ANY
  `CHARGE_k` state -- the SAME boolean condition R04E9's own
  `BRESET_GATE` already computed, reused here for the opposite role.
- It is held reset near 0 by a low-`Ron` switch `SRESET_CHG`, gated by
  `BRESET_GATE2` (`V=5*(IS_FREE)`) -- the SAME boolean condition R04E9's
  own `BTIMER_CHG` already computed, reused here for the opposite role.
- The B-source current sign (`-1p`, not `+1p`) is carried over UNCHANGED
  from R04E9's own diagnosed fix (its `BOUNDARY.md` Section 2): this
  simulator's `Bxxx n+ n- I=expr` convention sources current OUT of `n+`
  for a positive `expr`, so `-1p` is required to charge the node upward.
  Verified directly here too (Section 5 below), not assumed.

No other mechanism, node, topology, or parameter changes. `FREE_k`'s own
exit rule, the current-limit turn-off mechanism, and the full four-phase
`SCB4P_P24_*` power-stage connectivity are copied unchanged from R04E9
(subcircuit renamed `SCB4P_P24_R04E10` only to avoid a same-name-different-
netlist collision if both experiments' `.lib`/`.cir` files are ever
`.include`d together; electrically identical to R04E9's `SCB4P_P24_R04E9`).

## 3. What did not change

- Full four-phase P24 power-stage connectivity (`a1-a3`/`x1-x4`/`CS1-3`
  flying caps, series `Lk` charging path per phase) -- copied unchanged
  from R04E9.
- `CHARGE_k`'s current-limit exit condition (`I(Lk)>=I_LIMIT`) -- the
  R04E3/R04E4-validated rule form, reused unchanged.
- `FREE_k`'s exit condition and its own elapsed-freewheel-time timer
  construct (`CTIMER`/`BTIMER_CHG`/`BRESET_GATE`/`SRESET`) -- copied
  byte-for-byte from R04E9's already-validated, bug-fixed construct.
- `LPHASE=1.4666667 nH` (Eq.-4 branch, unchanged since R03/R04's whole
  lineage).
- `CFLY=3 uF` (R04E8's own corrected middle value, NOT R04E7's
  cross-topology-suspect `53.8 uF`).
- `COUT=4.672 mF` (still-flagged cross-topology candidate, NOT corrected
  here -- same deliberate scope limit R04E8/R04E9 both declared).
- The handoff-condition monitor definition (`Vout` within `5%` of `1 V`
  AND `VC1-3` within `2%` of `36/24/12 V`) -- identical to R04E9's.
- True-zero-energy initial condition (`ic=0` throughout every capacitor
  and inductor, `UIC`).
- GS61008T device data (1 HS / 2 parallel LS), `TMAX=50 ps`.

## 4. Inactive-phase switch state -- stated explicitly per this task's
   ground rules

Identical to R04E9's own construct and its own explicit documentation
(R04E9 `BOUNDARY.md` Section 2, added 2026-09-15): because each phase's
high/low gate output is driven by exactly one `(state==...)` comparison
(`.output (ghK_cmd) VGATE*(state==CHARGEK)`, `.output (glK_cmd)
VGATE*(state==FREEK)`) and never by an OR of multiple states, **at any
instant only the single phase currently in `CHARGE_k` or `FREE_k` has a
switch commanded on -- every other phase's high AND low side are both
off.** This experiment makes NO change to that convention; it is carried
over identically from R04E9.

This choice **matches R04E9's own** (every inactive phase fully off, both
`H` and `L`) -- it does not differ. It remains, as R04E9 stated, a
deliberate, defensible default for the zero-start bootstrap phase
specifically: there is no steady-state amp-second/charge-balance
freewheeling relationship to maintain yet at true zero energy for the
phases not currently being driven.

**This choice explicitly does NOT take any position on the separate
P24-vs-P25 steady-state inactive-low-side question** (whether inactive
low-sides should all be held on/freewheeling per P25's convention, or
left per P24's undrawn connection) -- exactly as R04E9 stated for itself.
That question only becomes meaningful once multiple phases are genuinely
interacting in periodic operation. Even though THIS experiment (unlike
R04E9) DOES reach multiple completed rotations in every cell (Section
"Outcome" in `RESULTS.md`), it remains a **bootstrap-only** transient
study, not periodic steady-state operation -- the handoff into the
existing strict steady-state controller is explicitly not built or
exercised (Section 8 below), so the periodic P24-vs-P25 inactive-low-side
question still does not arise here. Any future experiment that builds and
exercises the actual handoff must revisit this choice explicitly rather
than carrying it forward silently.

## 5. Pilot verification of the new timeout branch (done before committing
   to any grid cell, per this task's explicit instruction)

An isolated diagnostic (`pilot_timeout_isolation.cir` family, run from the
scratchpad, not committed -- same convention R04E7/R04E8/R04E9 used for
their own untracked pilots) set `I_LIMIT=100000 A` (unreachable within any
plausible run) so that ONLY the new `T_CHARGE_MAX` timeout branch could
possibly fire, isolating it from the current-limit branch entirely --
mirroring R04E9's own discipline of confirming its `T_FREEWHEEL_MAX` timer
construct in isolation before trusting it in the full 4-phase machine.

**Finding 1 (construct works as intended, at moderate T_CHARGE_MAX):** At
`T_CHARGE_MAX=5, 10, 50 ns`, `CHARGE1` cleanly exits via the timeout branch
(confirmed: `IL1` at the transition is far below the unreachable `I_LIMIT`,
e.g. `IL1=32.65 A` at `T_CHARGE_MAX=1 ns`, `IL1=162 A` at `5 ns`, growing
with `T_CHARGE_MAX` as expected since the inductor has more time to charge
before the timeout fires), landing at the commanded time to the same small
overshoot margin R04E3/R04E4/R04E9 already documented for their own
events (e.g. `T_CHARGE_MAX=5 ns` fires at `t=5.035 ns`; `10 ns` at
`t=10.078 ns`). The full 8-state machine then advances CLEANLY and
monotonically through every subsequent state (`state_mon` visits `0, 1, 2,
3, 4, ...` in strictly increasing order across several rotations, verified
directly by scanning `RISE=1..4` crossings for every state value) with no
anomalous transitions, at `T_CHARGE_MAX=5, 10,` and `50 ns`.

**Finding 2 (a genuine construct pitfall, found and NOT worked around --
reported as this experiment's own discovered limitation, per this task's
explicit request to check for "the same construct pitfalls R04E9's own
BOUNDARY.md documents finding and fixing"):** At `T_CHARGE_MAX=100 ps` and
`T_CHARGE_MAX=1 ns` (i.e. values at or near the ~0.93 ns order of
magnitude the task description itself suggested as a starting point), the
SAME diagnostic shows a real malfunction: `CHARGE2`'s timeout-triggered
transition does not land on `FREE2`'s state value (`3`) as the rule table
requires, but instead lands on `FREE1`'s value (`1`). This was confirmed
directly, not inferred, by parsing the raw binary transient trace
(`V(state_mon)` and `I(XMOD:L2)`) at fine time resolution: in the
`T_CHARGE_MAX=1 ns` case, between `t=53.35052 ns` (`state=1.5001`,
mid-transition) and `t=53.3652 ns` (`state=1.0000`, settled), `I(L2)`
swings wildly from `-7.66 A` to `+2.84 A` within four picoseconds -- a
non-physical excursion, not a slow or merely-late transition. The
`state_rise_N` crossing log for this case shows state values `1` and `2`
repeatedly re-visited in a tight ~52 ns period for four cycles before the
machine eventually breaks through to state `3` at `t=681.5 ns` (an order
of magnitude later than the ~53 ns a correctly-firing `1 ns` timeout would
imply). The most likely cause is that `T_CHARGE_MAX` values at or below
roughly `1-2 ns` sit too close to the machine's own internal timescales
(the `.machine 1p` resolution parameter and the timer reset switch's
`Ron*C~=5 ps` time constant) for the solver to resolve the transition
cleanly -- but the exact solver-internal mechanism was not further
diagnosed, since the practical resolution (avoid that range) was already
clear and directly confirmed.

**Consequence for the swept grid:** `T_CHARGE_MAX` values of `100 ps` and
`1 ns` are **excluded** from the committed grid because of this directly-
confirmed malfunction. The grid uses only the three pilot-confirmed-clean
values `{5, 20, 50} ns` (Section 7). This means the grid does **not**
literally start at the task description's suggested "~1 ns" anchor point
-- that specific value was tried first, per the task's own instruction to
pilot before trusting the mechanism, and found to break the construct.
This is reported as a genuine finding about this experiment's own
construct, not silently worked around by picking different numbers
without comment.

## 5b. A second, distinct construct fragility found in the FULL grid (not
    just the isolated pilot) -- reported honestly, not worked around

The Section 5 pilot isolated the timeout branch alone (`I_LIMIT` set
unreachably high) and found `T_CHARGE_MAX>=5 ns` clean. However, once the
first real grid cell (`I_LIMIT=30 A`, `T_CHARGE_MAX=20 ns`,
`T_FREEWHEEL_MAX=50 ns` -- a combination where BOTH the current-limit
branch and the timeout branch are simultaneously live, unlike the
isolated pilot) was run to its full `TSTOP=20 us`, direct inspection of
the raw transient trace (same technique as Section 5) revealed a SECOND,
distinct fragility:

- The machine does not simply cycle CHARGE1->FREE1->CHARGE2->...->FREE4
  once cleanly. Instead, on early attempts it repeatedly makes PARTIAL
  forward progress (observed reaching as far as `CHARGE3`(`4`) or even
  `CHARGE4`(`6`)) and then reverses -- state values flicker back down
  through the intermediate values to `FREE1`(`1`) with near-zero dwell at
  each intermediate value, where the machine then re-dwells the full
  `T_FREEWHEEL_MAX=50 ns` before trying forward again. This retry pattern
  repeats with a period of roughly `143 ns` for many cycles.
- As a direct consequence, the FIRST full rotation in this cell took
  `18.86 us` to complete -- roughly `70x` longer than the ~260 ns a naive
  sum of each state's own commanded duration would predict. Once the
  machine does escape this retry pattern, SUBSEQUENT rotations (2nd, 3rd,
  4th in this same cell) complete cleanly and quickly, at
  `273-347 ns` each, closely matching the naive per-phase estimate --
  confirming the retry behavior, not a general slowness, is the specific
  cause of the first rotation's outlier duration.
- A single-instant, extremely large (`~233 kA`) excursion in `ICS2`/`ICS3`
  was found at `t=19.275 us` (between the 2nd and 3rd completed
  rotations). Direct inspection (multiple consecutive raw-trace rows
  sharing the IDENTICAL timestamp to 15+ significant figures, with
  `VC1`/`VC2`/`VC3`/`IL1-4` unchanged across them while `ICS2`/`ICS3`
  balloon and then partially decay across the repeated rows, and
  `V(state_mon)=3.217` -- a non-integer, "stuck mid-transition" value, not
  a clean state) confirms this is a **solver-convergence retry artifact
  at a difficult state transition, not a physical current** -- the same
  general class of numerical spike R04E6/R04E8/R04E9 already documented
  finding (at `t=0` for their cases) and excluded from their own reported
  peak currents, but occurring later in the run here and roughly `50x`
  larger in magnitude than those experiments' own `t=0` artifacts.
  `analyze_b06_...py` flags (does not silently exclude) any
  `ICSk_MAX`/`ICSk_MIN` magnitude above `1000 A` as a suspected artifact
  of this kind, since R04E9's own inductor-mediated mechanism never
  exceeded `~35 A` anywhere in its own 9-cell grid and even R04E6/E7/E8's
  structurally different switch-only mechanism never exceeded `~4.6 kA`.

**This is reported as a genuine, additional finding about this
experiment's own construct**, distinct from the Section 5
`T_CHARGE_MAX~1 ns` timing malfunction: even at pilot-verified-safe
`T_CHARGE_MAX` values, embedding BOTH the current-limit and timeout
branches together in the full, circuit-coupled four-phase machine
produces real retry/chatter behavior that (a) makes per-rotation timing
highly non-uniform (dominated by a slow, uncertain-duration first
rotation, followed by fast, regular later ones), and (b) is implicated in
at least one large non-physical current excursion. This was not
"fixed" (no further mechanism change was made, consistent with the task's
single-conceptual-change mandate) -- it is reported plainly as a
limitation of the timeout-gated approach as tested, per Ground Rule 7 and
this project's Section I rule 7 ("simulation failure is an acceptable
outcome; a boundary must never be changed merely to produce an attractive
number"). See `RESULTS.md` for whether/how this pattern recurs across the
full 9-cell grid.

## 6. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `T_CHARGE_MAX` exit-rule form (`I(Lk)>=I_LIMIT \| V(timer_chg)>=T_CHARGE_MAX`) | This experiment's single new mechanism, an explicit, symmetric extension of R04E9's own `FREE_k` event-OR-timeout pattern (itself an A48-style idea) | `CROSS_PAPER_EXTENSION`-adjacent engineering construct, `NUMERICAL_IDEALIZATION` (the timer has no physical counterpart) |
| `CTIMER_CHG`/`BTIMER_CHG2`/`BRESET_GATE2`/`SRESET_CHG` construct, `-1p` B-source sign | Exact mirror of R04E9's own validated `FREE_k` timer construct (R04E9 `BOUNDARY.md` Section 2), charge/reset roles swapped | `NUMERICAL_IDEALIZATION`, inherited pattern |
| `T_CHARGE_MAX` swept values `{5, 20, 50} ns` | Pilot-verified-safe range (Section 5): `5 ns` is the smallest value found clean (closest practical value to the task's suggested `~1 ns` starting point that this construct can actually tolerate); `50 ns` matches the fixed `T_FREEWHEEL_MAX` and the task's own suggested upper bound; `20 ns` is an intermediate point | `SENSITIVITY_ONLY`, pilot-justified |
| `I_LIMIT` swept values `{10, 30, 60} A` | Reused verbatim from R04E9 for direct comparability, per the task's explicit instruction | `SENSITIVITY_ONLY` (inherited from R04E9) |
| `T_FREEWHEEL_MAX` fixed at `50 ns` | R04E9's own best-performing cell by every measure (R04E9 `RESULTS.md` Section 8: `I_LIMIT=60 A`, `T_FREEWHEEL_MAX=50 ns` reached `IL2_max=39.966 A`, `67%` of its own `I_LIMIT`, the closest any R04E9 cell got to unsticking) -- fixed rather than re-swept, per the task's explicit instruction | inherited value, not re-derived |
| `TSTOP=20 us` | Pilot-justified multi-rotation window (Section 8/RESULTS.md): a worst-case per-phase dwell of `T_CHARGE_MAX+T_FREEWHEEL_MAX<=100 ns` implies `<=400 ns` per rotation, so `20 us` provides room for many tens of rotations per cell within a tractable LTspice run time | numerical-resolution choice, not physical, not swept |
| `TMAX=50 ps` | Unchanged from R04E9 (same `CFLY=3 uF` resolution reasoning) | numerical-resolution choice, not physical, not swept |
| Every value carried over from R04E9 (`Vin`, `nP`, `nM`, topology, `LPHASE`, `CFLY`, `COUT`, GS61008T data, handoff tolerance bands) | See R04E9 `BOUNDARY.md` Section 4 for the original provenance of each | unchanged from R04E9 |

## 7. Swept grid and its justification

`I_LIMIT` in `{10, 30, 60} A` (R04E9's own axis, unchanged) x
`T_CHARGE_MAX` in `{5, 20, 50} ns` (pilot-verified-safe range, Section 5),
9 cells, `T_FREEWHEEL_MAX` fixed at `50 ns` (Section 6), all run to a
common `TSTOP=20 us` / `TMAX=50 ps`.

## 8. What question this experiment is meant to answer

Does adding a timeout fallback to `CHARGE_k` (so a phase that cannot reach
its own current limit is forced to hand off anyway) let the four-phase
rotation complete at least once, and if so, do repeated rotations make
visible cumulative progress toward the handoff condition (rising
`Vout`/`VC1`/`VC2`/`VC3` trending toward `1 V`/`36/24/12 V` over
successive rotations), or does the machine merely repeat the same
single-pass stall pattern on a loop without net progress?

## 9. Success condition

For a given `(I_LIMIT, T_CHARGE_MAX)` cell: at least one full four-phase
rotation completes (a strictly stronger bar than R04E9, which completed
zero in every cell), AND no phase current exceeds the same `+/-250 A`
safety bound R04E5/R04E9 adopted. A cell additionally reaching
`T_HANDOFF` within `TSTOP` is graded `LOCAL_PASS`; a cell that completes
rotations but never reaches handoff is graded `CONTROLLER_GUARD_PASS` if
currents stay bounded and the machine does not diverge.

## 10. Failure conditions

- `CONTROLLER_GUARD_PASS`: rotations proceed (or the machine parks
  permanently in one state) without chattering, diverging, or exceeding
  the current safety bound, but the handoff condition is never reached --
  a safe, honestly-reported non-success.
- `PHYSICAL_BOUNDARY_FAIL`: any phase current exceeds `+/-250 A`.
- `NOT_PERIODIC` / no-progress: rotations complete but `Vout`/`VC1-3` show
  no net cumulative increase across them (plateau or bounded oscillation)
  -- a legitimate, explicitly reported negative finding about the
  timeout-fallback mechanism itself, not a numerical failure.
- Solver non-convergence before `TSTOP` is its own outcome, reported as
  such, not retried with loosened tolerances.

## 11. What this experiment cannot prove

- It does **not** build or test the actual handoff into the existing
  strict event-gated steady-state controller (R04E3/R04E5 lineage) --
  explicitly out of scope per the task; it only measures whether/when the
  handoff CONDITION is reached.
- It does **not** establish that any tested `I_LIMIT` or `T_CHARGE_MAX`
  value is "correct" -- both are declared sensitivity axes, not paper
  values or engineering recommendations. In particular, the exclusion of
  `T_CHARGE_MAX` values near `1 ns` (Section 5) is a report of a
  discovered construct limitation, not a claim that no design could ever
  use a value in that range with a different (more careful) timer
  implementation.
- It does **not** validate hardware switch stress at the observed peak
  currents -- no numeric current threshold exists in any source (same
  caveat R04E6/R04E7/R04E8/R04E9 already stated for their own peak
  currents).
- It does **not** correct or validate `Cout=4.672 mF` -- inherited
  unchanged from the whole R03A-R04E9 lineage, still flagged unconfirmed.
- A result here (positive or negative) is a single, specific
  `(I_LIMIT, T_CHARGE_MAX, T_FREEWHEEL_MAX=50ns, CFLY=3uF, COUT=4.672mF)`
  grid; it must never be read as a general statement about timeout-gated
  multi-rotation bootstrap independent of these fixed values.
- Even where multiple rotations complete, this remains a **bootstrap-only**
  transient study, not a demonstration of P24's normal four-phase
  INTERLEAVED steady-state operation -- see Section 4 above for why the
  P24-vs-P25 inactive-low-side steady-state question remains untouched.
- The `T_CHARGE_MAX~1 ns` malfunction (Section 5) is reported as a finding
  about THIS experiment's own new timer construct; it is not a claim that
  R04E9's own (structurally different, single-timer) construct has the
  same issue -- R04E9's own `FREE_k` timer was exercised down to values as
  small as its own tested range and found clean in its own grid.
