# R04E11 - root-cause of the CHARGE/FREE reversal and ICS artifact (BOUNDARY)

## 1. Parent

**R04E10** (`experiments/track_B_zero_start_extension/
R04E10_timeout_gated_multi_rotation_bootstrap/`). R04E10 added a
timeout-fallback exit to `CHARGE_k` (mirroring `FREE_k`'s own existing
event-OR-timeout pattern) and found this DOES let multi-rotation operation
happen (6/9 cells, `Vout` rises monotonically), but reported two problems
it explicitly did NOT root-cause, per its own `RESULTS.md` Section 14:

1. A retry/chatter dynamic: the machine repeatedly makes partial forward
   progress (observed reaching as far as `CHARGE3`/`CHARGE4`) and then
   reverses to `FREE1`, retrying with a ~143 ns period, for many cycles,
   before eventually escaping. This inflates the first rotation's duration
   by up to 70x and is the reason `T_CHARGE_MAX=5 ns` never escapes at all
   (permanent stall, reproducing R04E9's own failure mode) despite passing
   clean in isolated (single-branch) pilot testing.
2. A pervasive `ICS1-3` (flying-capacitor branch current) `.meas` artifact,
   up to ~500 kA, coincident with identical-timestamp raw-trace rows and a
   non-integer `V(state_mon)` -- the classic solver-retry fingerprint --
   found in every one of R04E10's 9 cells.

R04E10 diagnosed the SYMPTOM of both (raw-trace inspection showing the
reversal and the artifact happen together) but explicitly stopped short of
tracing either to a root cause inside the `.machine`/B-source construct,
since doing so was outside its own single-conceptual-change scope.

## 2. What this experiment is for

**Diagnostic-first, fix-if-warranted.** This experiment's primary
deliverable is identifying WHICH specific signal(s) inside the
`.machine`/`.rule`/`.output`/B-source construct cause the CHARGE-state
machine to reverse to `FREE1` instead of continuing forward, using direct
instrumentation of every internal node (reset-gate booleans, both timer
voltages, the raw `.machine` state variable) at the fine time resolution
around a reversal event -- not just the four state variables (`IL1-4`,
`VC1-3`, `Vout`, `state_mon`) R04E9/R04E10 examined.

If, and only if, a clean, minimal, single-conceptual fix is identified by
that diagnosis (e.g. a debounce/hysteresis on a specific comparator, or a
specific race between two B-source gate signals), it may be applied as ONE
targeted change and the same `T_CHARGE_MAX in {5, 20, 50} ns` x `I_LIMIT in
{10, 30, 60} A` grid re-run to measure whether it: (a) lets `T_CHARGE_MAX=5
ns` escape its total stall, (b) shortens/removes the retry period in the
cells that already complete rotations, (c) reduces or removes the `ICS1-3`
artifact magnitude. If no such clean fix is identified, the root cause is
reported plainly as a limitation of this construct family, per Ground Rule
7 ("simulation failure is an acceptable outcome; a boundary must never be
changed merely to produce an attractive number") -- this experiment must
NOT force a fix that only masks the symptom (e.g. blanket timestep
clamping, or silently discarding the `ICS1-3` measurement) without
identifying what actually causes it.

## 3. Diagnostic testbed

Reuse R04E10's own `I_LIMIT=30 A`, `T_CHARGE_MAX=20 ns` cell
(`T_FREEWHEEL_MAX=50 ns` fixed, as in all of R04E10) as the primary
diagnostic target -- R04E10 `BOUNDARY.md` Section 5b already localized one
concrete reversal event in this exact cell (`t=19.275 us`, `ICS2`/`ICS3`
excursion, `V(state_mon)=3.217`) and a ~143 ns retry period during the
first rotation, giving a known window to instrument rather than searching
blind. The `T_CHARGE_MAX=5 ns` total-stall cells (any `I_LIMIT`) are the
secondary target, since they represent the reversal dynamic in its most
extreme (never-escaping) form.

## 4. What must not change

- Full four-phase P24 power-stage connectivity, `CHARGE_k`/`FREE_k` state
  definitions, the current-limit exit rule (`I(Lk)>=I_LIMIT`), and
  `FREE_k`'s own timer construct -- copied byte-for-byte from R04E10/R04E9,
  unless the root-cause diagnosis itself identifies one of these specific
  elements as the fault, in which case the change and its justification
  must be documented explicitly, not silently folded in.
- `LPHASE=1.4666667 nH`, `CFLY=3 uF` (R04E8's corrected value), `COUT=4.672
  mF` (still-flagged candidate, not corrected here), GS61008T device data,
  true-zero-energy initial conditions -- unchanged.
- The inactive-phase all-off switch convention (R04E9 Section 2 / R04E10
  Section 4) -- unchanged; this experiment remains a bootstrap-only
  transient study, not periodic steady-state, so the P24-vs-P25
  inactive-low-side question still does not arise here.

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| Diagnostic instrumentation itself (probing reset-gate/timer nodes) | New for this experiment; adds observation only, no new circuit element | Not a physical value -- measurement-only |
| Any single-conceptual fix identified and applied (undetermined until diagnosis completes) | To be derived from this experiment's own root-cause finding | `NUMERICAL_IDEALIZATION` (a construct/timing fix, no physical counterpart), must be logged in `RESULTS.md` with its own justification, same as R04E9/R04E10's own construct fixes |
| `T_CHARGE_MAX in {5, 20, 50} ns`, `I_LIMIT in {10, 30, 60} A`, `T_FREEWHEEL_MAX=50 ns` (re-run grid, only if a fix is applied) | Unchanged from R04E10, for direct before/after comparability | `SENSITIVITY_ONLY`, inherited |
| Everything else | See R04E10 `BOUNDARY.md` Section 6 for original provenance | unchanged |

**No new paper-sourced, cross-paper, or external-device data is introduced
by this experiment.** Its entire content is diagnostic instrumentation of
an already-`SENSITIVITY_ONLY`-graded engineering construct (R04E10
`RESULTS.md` Section 13); nothing here should be read as bearing on any
P24_EXPLICIT or P25_SUPPLEMENT boundary.

## 6. Success condition

A `LOCAL_PASS`-style diagnostic success: the specific node(s)/signal(s)
responsible for the reversal are identified and demonstrated (not just
theorized) to be the cause, by showing the reversal disappears or changes
in a predicted way when that signal is probed/altered in a controlled
isolation test. A `CONTROLLER_GUARD_PASS`-style partial success: the
reversal mechanism is narrowed to a specific construct element (e.g. "one
of these three reset gates") without full isolation to a single signal.

If a fix is applied and re-run: the same acceptance bar as R04E10 Section 9
(rotation completion, current bounded under +/-250 A) applies to the
re-run grid, plus the specific before/after comparison this experiment
exists to produce (reversal frequency/duration, `ICS1-3` magnitude,
`T_CHARGE_MAX=5 ns` escape or not).

## 7. Failure conditions

- No signal is conclusively identified as responsible (diagnosis
  inconclusive) -- reported plainly, same as any other experiment's
  negative result; this is an acceptable, informative outcome, not a
  reason to force a claim the evidence does not support.
- A fix is attempted but does not resolve the reversal, or resolves it
  while introducing a new problem (e.g. a different chatter mode, or a
  physically implausible current) -- reported plainly, not silently
  discarded or re-tried with loosened tolerances.
- Solver non-convergence -- reported as its own outcome.

## 8. What this experiment cannot prove

- It does not, by itself, close the ~95-99% handoff gap R04E10 Section 8
  documented even if the reversal/artifact problems are fully resolved --
  R04E10 Section 10's own finding (this mechanism converges much more
  slowly per-cycle than R04E7/E8's switch-only ladder mechanism) is
  independent of the reversal dynamic and is not addressed here.
- It does not validate `Cout=4.672 mF`, still an unconfirmed inherited
  value.
- It does not build or exercise the handoff into the existing strict
  steady-state controller -- out of scope, same as R04E9/R04E10.
- A fix identified here, if any, is scoped to this specific
  `.machine`/B-source timer-pair construct; it must not be read as a
  general statement about LTspice XSPICE state-machine reliability beyond
  this project's own usage pattern.
