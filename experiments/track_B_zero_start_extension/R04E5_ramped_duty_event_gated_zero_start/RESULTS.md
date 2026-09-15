# R04E5 - ramped-duty, event-gated zero start (RESULTS)

## 1. Simulation completion

All 12 cells of the (`TSOFT`, `I_LIMIT`) sensitivity grid completed
normally in LTspice (batch mode, exit code 0, no time-step-too-small or
convergence failure). No case was dropped or skipped. Full logs were
parsed by `analyze_b01_r04e5_ramped_duty_event_gated_zero_start.py`;
results are in `results.csv` / `results.json`.

## 2. Parameters actually used

Fixed for every cell (see BOUNDARY.md Section 3): `Vin=48 V`,
`Vout target=1 V`, `Pmodule=250 W`, `nP=4`, `nM=4`, `fsw=5 MHz`,
`L=1.4666667 nH`, `D=1/12` (`Ton_final=16.6667 ns`), `Cfly=53.8 uF`,
`Cout=4.672 mF`, `NEG_FRAC=0.02`, GS61008T device data, true-zero-energy
initial conditions, powered-rail-first boundary with `TENABLE=10 ns`.

Swept: `TSOFT in {50, 100, 200, 500} us` x `I_LIMIT in {10, 50, 150} A`,
12 cells. Each cell ran to `TSTOP=1.2*TSOFT`.

## 3. The sensitivity grid

| TSOFT (us) | I_LIMIT (A) | `il1_max` (A) | `il1_min` (A) | `Vout` peak (V) | `Vout` final (V) | Final state | Grade |
|---:|---:|---:|---:|---:|---:|---|---|
| 50  | 10  | 14.189 | -14.171 | 1.077e-3 | 1.069e-6  | 4 (COMMUTATE_HIGH_TO_ZVS) | CONTROLLER_GUARD_PASS |
| 50  | 50  | 65.495 | -14.171 | 4.987e-3 | 4.930e-6  | 4 | CONTROLLER_GUARD_PASS |
| 50  | 150 | 155.702 | -14.171 | 1.189e-2 | 2.296e-7  | 3 (LOW_BUILD_NEGATIVE) | CONTROLLER_GUARD_PASS |
| 100 | 10  | 14.189 | -14.171 | 1.077e-3 | 9.09e-10  | 4 | CONTROLLER_GUARD_PASS |
| 100 | 50  | 65.495 | -14.171 | 4.987e-3 | 4.19e-9   | 4 | CONTROLLER_GUARD_PASS |
| 100 | 150 | 155.702 | -14.171 | 1.189e-2 | -6.05e-12 | 3 | CONTROLLER_GUARD_PASS |
| 200 | 10  | 14.189 | -14.171 | 1.077e-3 | -4.61e-13 | 4 | CONTROLLER_GUARD_PASS |
| 200 | 50  | 65.495 | -14.171 | 4.987e-3 | -3.50e-12 | 4 | CONTROLLER_GUARD_PASS |
| 200 | 150 | 155.702 | -14.171 | 1.189e-2 | -9.29e-12 | 3 | CONTROLLER_GUARD_PASS |
| 500 | 10  | 14.189 | -14.171 | 1.077e-3 | -4.62e-13 | 4 | CONTROLLER_GUARD_PASS |
| 500 | 50  | 65.495 | -14.171 | 4.987e-3 | -3.50e-12 | 4 | CONTROLLER_GUARD_PASS |
| 500 | 150 | 155.702 | -14.171 | 1.189e-2 | -9.29e-12 | 3 | CONTROLLER_GUARD_PASS |

Full numeric detail (25 fields per cell, including the 25%/50%/75%/`TSOFT`
`Vout` checkpoints and the late-window current swing used for grading) is
in `results.csv`/`results.json`.

## 4. When each key event occurred

Within every one of the 12 cells, the machine advances through states
`ENERGY(0) -> HS_OFF_COMMUTATE_LOW(1) -> LOW_FREEWHEEL_TO_ZERO(2)` and, for
`I_LIMIT in {10,50}`, also `-> LOW_BUILD_NEGATIVE(3) -> COMMUTATE_HIGH_TO_
ZVS(4)`, all within the first few nanoseconds (this matches R04E4's own
finding: the initial Coss displacement-current transient dominates the
first turn-on regardless of the commanded threshold, so the first pulse
resolves almost immediately once `I_LIMIT` is exceeded). After that, the
machine **never advances again for the rest of the run**, all the way to
each cell's own `TSTOP` (60 us up to 600 us, i.e. up to 30-370x longer
than R04E3's original 20 us test window):

- `I_LIMIT=10 A` and `I_LIMIT=50 A` (9 of 12 cells): the machine parks
  permanently in state 4, waiting for `V(vin,a1)<=0` (natural high-side
  `Vds` zero-crossing) -- this never happens in any of these 9 cells,
  regardless of `TSOFT`. This is the **exact same stuck point R04E3
  itself found** at 20 us, now shown to persist to at least 600 us.
- `I_LIMIT=150 A` (3 of 12 cells): the machine parks one stage earlier,
  in state 3, waiting for `I(L1)<=-I_NEG` (the negative-current target,
  4.5 A for this row) -- this also never happens in any of these 3 cells.
  This is a stall point one step earlier than R04E3's own, not documented
  by either parent directly.

No case ever returns to state 0 a second time. Consequently the ramped
on-time ceiling (`TSOFT`, item 1 of the synthesis) never gets a second
opportunity to act as a constraint in any tested cell -- only the very
first pulse's current-limit condition (item 2) is ever exercised.

## 5. Key voltages and currents

- `il1_max`/`il1_min` are **bit-identical across all four TSOFT values**
  at a fixed `I_LIMIT` (e.g. 14.189245224 A / -14.1705741882 A for every
  one of the four `I_LIMIT=10` rows, to full printed precision). This is
  not noise or coincidence: since the machine never returns to `ENERGY`
  a second time, the entire observed trajectory in every cell is fixed by
  the single first pulse, which is controlled only by `I_LIMIT`, not by
  `TSOFT`.
- The realized peak current exceeds the commanded `I_LIMIT` in every
  cell, by a shrinking relative (but roughly flat, few-amp absolute)
  margin: `+4.19 A` (+42%) at `I_LIMIT=10`, `+15.50 A` (+31%) at
  `I_LIMIT=50`, `+5.70 A` (+3.8%) at `I_LIMIT=150`. This matches the same
  post-limit commutation overshoot R04E3/R04E4 already documented (their
  10-A commanded limit reached 43.68 A over a longer commutation window;
  here the overshoot is smaller in the same direction but the mechanism
  -- current keeps moving briefly after the commanded turn-off event --
  is the same).
- Every cell's current stays comfortably inside the `+/-250 A` safety
  bound defined in BOUNDARY.md Section 6 (worst case 155.702 A /
  -14.171 A, both well under 250 A). Relative to R03D's own uncontrolled
  extrema (`L1`: -225.75 A to 382.55 A; `L4`: -268.49 A to 390.96 A), the
  current-limit half of the synthesis does successfully bound the
  excursion -- but only because a single pulse, not a sustained
  multi-cycle trajectory, is what gets bounded.
- `Vout` rises to a small millivolt-scale peak on the first pulse (from
  1.08 mV at `I_LIMIT=10` up to 11.9 mV at `I_LIMIT=150` -- larger
  `I_LIMIT` gives a larger first-pulse charge injection and hence a
  higher peak) and then **decays monotonically toward zero** for the
  remainder of every run, consistent with `Cout` discharging through
  `RLOAD` with no further recharging pulse (`RLOAD*Cout` =
  `4e-3*4.672e-3` = 18.7 us, matching the observed decay rate: e.g. the
  `I_LIMIT=10` row's `Vout` falls from its 1.08 mV peak to 1.07e-9 V by
  100 us, roughly 5.3 time constants, consistent with pure RC decay).
  `Vout` never approaches anywhere near the 1 V target in any of the 12
  cells; the closest approach to the 5% band (`[0.95, 1.05] V`) is not
  close at all -- the largest `Vout` observed anywhere in the whole grid
  is the 11.9 mV peak (`I_LIMIT=150`, before its own decay).

## 6. Acceptance condition

Not met in any of the 12 cells. `LOCAL_PASS` requires both the current
bound (met in all 12) and `Vout` within 5% of 1 V at the end of the run
(met in 0 of 12).

## 7. First failure boundary

In every cell, the first (and only) failure boundary is the same one
R04E3 already identified: the machine cannot complete a second full
cycle back to `ENERGY`, because it never observes the physical event its
own rules require (`V(vin,a1)<=0` for 9 cells, or `I(L1)<=-I_NEG` for the
other 3) within a window at least 30x-370x longer than R04E3's original
20 us test. This is upstream of, and blocks, any chance to observe
`TSOFT`'s intended effect.

## 8. Grade

All 12 cells: **`CONTROLLER_GUARD_PASS`** (the machine safely parks in a
single latched state for the remainder of each run -- no chatter, no
divergence, no boundary-condition violation -- but it also never
completes a second cycle, so it cannot be called a bootstrap success).
Overall grid label: **`SENSITIVITY_ONLY`** (both axes are swept,
non-paper values; see BOUNDARY.md Section 8 for what cannot be claimed).

### Plain-word statement of both swept axes' effects

- **`TSOFT` (the ramp duration): has no observed effect on anything in
  this grid.** Peak current, trough current, and which state the machine
  gets permanently stuck in are all identical across all four tested
  `TSOFT` values at a fixed `I_LIMIT`. This is not because a longer or
  shorter ramp is "better" or "worse" -- it is because the machine never
  returns to `ENERGY` a second time in any tested cell, so the ramped
  ceiling this axis controls never gets a chance to bind. A longer ramp
  neither helps nor hurts here; it is simply never exercised.
- **`I_LIMIT` (the current limit): a larger `I_LIMIT` produces a larger
  single first-pulse peak current (bigger commanded ceiling -> a bigger
  Coss-and-commutation-driven excursion, monotonically: 14.2 A -> 65.5 A
  -> 155.7 A as `I_LIMIT` rises from 10 to 50 to 150 A) and a larger
  first-pulse `Vout` peak (1.08 mV -> 4.99 mV -> 11.9 mV, same
  direction), but it also determines whether the machine stalls one
  stage earlier: at `I_LIMIT=150 A` the machine never even reaches the
  negative-current target (stuck at state 3), one step before where the
  two lower `I_LIMIT` values stall (state 4). A bigger current limit
  therefore produces a bigger single pulse but not a working, repeating
  cycle -- all three `I_LIMIT` values still decay to a `Vout` near zero
  by the end of their own run, so a bigger current limit does not help
  bootstrap `Vout` toward the 1 V target.** In every case the excursion
  stays inside the
  `+/-250 A` safety bound, so within this tested range a larger
  `I_LIMIT` does not create an unsafe excursion -- but it also does not
  produce a bounded, sane, `Vout`-approaching-1-V trajectory either.
- **No (`TSOFT`, `I_LIMIT`) combination in this grid reaches a bounded,
  sane startup trajectory.** All 12 combinations fail to produce a
  second switching cycle and all 12 leave `Vout` decaying toward zero.

## 9. Top-level verdict

**This synthesis does not get further than either parent, on the
question each parent's own failure was about.** It does not exhibit a
genuinely new numerical failure mode (no chatter, no divergence, no
current-bound violation) -- but it also does not resolve, or even newly
probe, R04E3's own bottleneck; it reproduces R04E3's exact stuck-at-
state-4 finding in 9 of 12 cells, now confirmed to persist to at least
600 us (not just R04E3's originally-tested 20 us), and finds a one-stage-
earlier stuck-at-state-3 point in the remaining 3 cells at the highest
tested `I_LIMIT`.

Crucially, and this is the central, honest finding of this experiment:
**the synthesis does not recover R03D's `Vout`-bootstrap success either.**
This has a clear causal explanation, not just an empirical one. R03D's
`Vout` success depended on a fixed-clock PWM schedule that kept issuing
new pulses every `200 ns` on the nominal 5-MHz clock regardless of
whether the physical off-interval current had actually returned to zero
-- exactly the kind of fixed-time-substituting-for-a-physical-event
practice this project's own boundary-control principle (`EXPERIMENT_
PROTOCOL_AND_ARCHIVE_RULES.md` Section VI) prohibits, and exactly what
produced R03D's uncontrolled 225-390 A current swings. R04E5 (like R04E3
before it) correctly refuses to do this: every transition is gated by an
actual physical event, so if that event never occurs, no further pulse
is ever issued. The ramped on-time ceiling this experiment adds is a
strictly *tighter* cap on top of that already-event-gated machine, so it
cannot re-open a door R04E3's own event gating had already closed. Once
physical-event gating is correctly enforced, R03D's apparent Vout success
and R04E3's safe refusal are not simultaneously achievable by adding a
ramp on top -- they were never actually in tension over the same
mechanism; R03D's success was purchased specifically by the
boundary-violation this project prohibits.

**This is a legitimate, useful, reportable negative result**, not a
withheld or softened one: it shows that the (`TSOFT`, `I_LIMIT`)
sensitivity axes explored here are the wrong axes to resolve the zero-
start problem, because neither one touches the actual constraint (the
shallow `-Vout/L` return slope at near-zero `Vout`, identified by R04E3
and confirmed here to persist far longer than previously shown). The
bottleneck is upstream of both swept parameters.

## 10. What module should be adjusted next

Per R04E3's own "resulting next gate" and confirmed here: the next
experiment must address the shallow near-zero-`Vout` return-slope
bottleneck directly (e.g. a genuinely different starting condition, such
as a precharge-assisted approach from the R02 family that raises `Vout`
or the flying-capacitor ladder before event-gated switching begins), not
sweep `TSOFT` or `I_LIMIT` further -- this grid shows neither axis has
any leverage over the actual constraint.

## 11. What must never be changed because of this failure

- `L=1.4666667 nH` (locked Eq.-4 value; do not swap back to R03D's
  `2.68 nH` to try to change this outcome -- see BOUNDARY.md Section 4
  for why this value is used).
- The true-zero-energy starting condition (`ic=0` throughout). Do not
  mask this failure by presetting capacitor voltages or inductor
  currents, per `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section XI
  rule 5 -- that would be testing the separate, already-covered R02
  precharge question, not the zero-energy case this experiment targets.
- Physical-event-only gating (`V(vin,a1)<=0`, `I(L1)<=0`,
  `I(L1)<=-I_NEG`, all instantaneous-event triggers with post-transition
  latching). Do not substitute a fixed time for any of these events to
  force a nicer `Vout` number -- doing so would just be re-deriving
  R03D's already-rejected boundary violation under a new name.
