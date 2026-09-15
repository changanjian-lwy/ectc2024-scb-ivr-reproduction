# R04E10 result - timeout-gated multi-rotation bootstrap

## Outcome, stated first

All 9 cells of the `(I_LIMIT, T_CHARGE_MAX)` grid ran to completion in
LTspice (batch mode, exit code 0, non-empty `.log`/`.raw` for every case,
verified directly: logs `13.2-15.4 KB`, raw files `47.8-65.3 MB`). **The
single-conceptual-change fix DOES let the rotation complete** -- unlike
R04E9, where 0 of 9 cells ever completed even one full four-phase
rotation, **6 of these 9 cells complete multiple rotations** (4 to 17),
and `Vout` rises **monotonically** across every completed rotation in
every one of those 6 cells. **No cell reaches the handoff condition**, and
the best cell's state vector is still one to two orders of magnitude short
of the handoff targets. A pervasive, previously-undocumented numerical
artifact (Section 5) contaminates the flying-capacitor branch current
(`ICS1-3`) reporting in every single cell of the grid, and the
newly-added `T_CHARGE_MAX=5 ns` value -- verified clean in isolation
(`BOUNDARY.md` Section 5) -- turns out to be uniformly the WORST value in
the full grid, completing **zero** rotations in all three `I_LIMIT` cells
that use it. This is reported plainly as a genuine, mixed finding: real
progress on the original R04E9 stall, alongside two new problems.

## 1. Simulation completion

All 9 cases ran to completion (LTspice exit code 0). Verified directly:
every case has a non-empty `.log` (`13.2-15.4 KB`) and non-empty `.raw`
(`47.8-65.3 MB`), confirming a completed `TSTOP=20 us` transient run, not
a truncated one.

## 2. Parameters actually used

Fixed for every cell (`BOUNDARY.md` Sections 3-6): `Vin=48 V`, `nP=4`,
`nM=4`, full four-phase P24 connectivity (unchanged from R04E9),
`LPHASE=1.4666667 nH`, `CFLY=3 uF`, `COUT=4.672 mF`, GS61008T device data
(1 HS / 2 parallel LS), true-zero-energy initial conditions (`ic=0`
throughout, `UIC`), `T_FREEWHEEL_MAX=50 ns` (fixed, R04E9's own
best-performing value).

Swept: `I_LIMIT` in `{10, 30, 60} A` x `T_CHARGE_MAX` in `{5, 20, 50} ns`
(the pilot-verified-safe range, `BOUNDARY.md` Section 5), 9 cells. Every
cell run to a common `TSTOP=20 us` / `TMAX=50 ps`.

## 3. The sensitivity grid

| `I_LIMIT` (A) | `T_CHG_MAX` (ns) | Final state | Rotations | `Vout` final (V) | `VC1` final (V) | `VC2` final (V) | `VC3` final (V) | `IL1_max` (A) | Handoff? |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 10 | 5  | FREE3   | 0  | 2.08e-4 | 0.0407 | -0.0101 | -0.0113 | 10.16 | NO |
| 10 | 20 | FREE1   | 17 | 2.60e-3 | 0.3971 | 0.0898  | -0.0051 | 10.18 | NO |
| 10 | 50 | FREE3   | 13 | 2.64e-3 | 0.4353 | 0.1752  | 0.0071  | 10.18 | NO |
| 30 | 5  | FREE3   | 0  | 6.07e-4 | 0.0912 | -0.0341 | -0.0341 | 30.16 | NO |
| 30 | 20 | FREE3   | 4  | 2.37e-3 | 0.5397 | -0.4301 | 0.1791  | 30.16 | NO |
| 30 | 50 | CHARGE4 | 12 | 6.89e-3 | 1.1470 | 0.1707  | -0.0186 | 30.17 | NO |
| 60 | 5  | CHARGE2 | 0  | 1.21e-3 | 0.1741 | -0.0695 | -0.0678 | 60.17 | NO |
| 60 | 20 | FREE1   | 11 | 9.41e-3 | 1.1231 | 0.0821  | -0.1497 | 60.17 | NO |
| 60 | 50 | CHARGE3 | 12 | 1.41e-2 | 1.9825 | 0.6185  | 0.0872  | 60.17 | NO |

Targets for reference: `Vout=1 V`, `VC1=36 V`, `VC2=24 V`, `VC3=12 V`.
Full numeric detail (min currents, all five trajectory checkpoints, every
per-rotation measurement up to 60, trend statistics) is in
`results.csv`/`results.json`.

## 4. Does the charge-timeout fix let rotations complete? Yes, for
   `T_CHARGE_MAX in {20, 50} ns`; no, for `T_CHARGE_MAX=5 ns`

This is the central, unambiguous, grid-wide pattern, and it did not match
this experiment's own pilot expectation:

- **`T_CHARGE_MAX=5 ns` (all three `I_LIMIT` values): ZERO rotations
  complete in every one of the 3 cells**, within the full `20 us` window
  -- the SAME `CONTROLLER_GUARD_PASS`-style total stall R04E9 found in
  ALL 9 of its own cells, even though this exact `T_CHARGE_MAX` value was
  directly verified clean in the Section-5 isolated pilot (current-limit
  branch disabled). This is a genuinely new methodological finding: a
  timer construct verified clean with only ONE of its two OR-branches
  live does not guarantee clean behavior once BOTH branches are live and
  circuit-coupled through the full four-phase machine (`BOUNDARY.md`
  Section 5b).
- **`T_CHARGE_MAX=20 ns`: 17, 4, and 11 rotations complete** at
  `I_LIMIT=10, 30, 60 A` respectively -- a real, but highly irregular,
  rotation count that does not track `I_LIMIT` monotonically.
- **`T_CHARGE_MAX=50 ns`: 13, 12, and 12 rotations complete** at
  `I_LIMIT=10, 30, 60 A` respectively -- more consistent across `I_LIMIT`
  than the `20 ns` column, though still not perfectly flat.

Direct raw-trace inspection of a representative cell (`I_LIMIT=30 A`,
`T_CHARGE_MAX=20 ns`, `BOUNDARY.md` Section 5b) explains the irregularity:
rotations do not complete via one clean pass through all 8 states.
Instead the machine repeatedly makes PARTIAL forward progress (observed
reaching as far as `CHARGE3` or `CHARGE4`) and then reverses back to
`FREE1`, retrying with a ~143 ns period, for many cycles, before finally
escaping and completing a rotation. In that specific cell the FIRST
rotation took `18.86 us` -- `70x` longer than the ~260 ns a naive
per-state-duration sum predicts -- while the 2nd-4th rotations, once the
retry pattern was escaped, completed cleanly in `273-347 ns` each,
matching the naive estimate closely. This retry behavior, not a uniform
slowness, is the direct cause of both the irregular rotation counts across
the grid and (Section 5 below) a pervasive current-reporting artifact.

## 5. A pervasive numerical artifact in the flying-capacitor branch
   currents -- found in every cell, reported plainly, not silently
   excluded

**`ICS1`/`ICS2`/`ICS3` (flying-capacitor branch current) `.meas` values
are contaminated by a solver-convergence artifact in ALL 9 cells**,
ranging from several hundred amps (in the `T_CHARGE_MAX=5 ns` cells,
which never even complete a rotation) up to **~500 kA** (`I_LIMIT=60 A`,
`T_CHARGE_MAX=20 ns`: `ICS3_max=499,843.8 A`, `ICS2_min=-499,865.8 A`).
This was diagnosed directly, not assumed, using the same raw-trace
inspection technique R04E9 used for its own timer diagnosis
(`BOUNDARY.md` Section 5b): the artifact coincides with several
consecutive raw-trace rows sharing an IDENTICAL timestamp to 15+
significant figures, `VC1`/`VC2`/`VC3`/`IL1-4` unchanged across those
rows while `ICS2`/`ICS3` balloon and then partially decay, and
`V(state_mon)` holding a non-integer, "stuck mid-transition" value (e.g.
`3.217`) -- the classic fingerprint of a solver retrying a difficult
timestep, not a physical current. R04E9's own inductor-mediated mechanism
never exceeded `~35 A` anywhere in its 9-cell grid, and even R04E6/E7/E8's
structurally different switch-only mechanism never exceeded `~4.6 kA`; a
jump to `500 kA` is unambiguous.

`analyze_b06_...py` flags (does not silently discard) every
`ICSk_MAX`/`ICSk_MIN` magnitude above `1000 A` as a suspected artifact --
every single one of the 9 cells has at least one flagged branch; the
worst 3 cells (`I_LIMIT=30 A`/`T_CHG=20 ns`, `I_LIMIT=30 A`/`T_CHG=50 ns`,
`I_LIMIT=60 A`/`T_CHG=20 ns`, `I_LIMIT=60 A`/`T_CHG=50 ns`) show
excursions in the tens-of-kA to ~500 kA range. **The `ICS1-3` numbers
reported by this grid's own `.meas` output must NOT be read as physical
flying-capacitor currents** -- they are a direct, reportable side effect
of the same retry/chatter dynamic identified in Section 4, and are a NEW
fragility this experiment's construct introduces beyond anything found in
R04E9 (whose single-timer, current-limit-only `CHARGE_k` never exhibited
this pattern in any of its own 9 cells, because its `CHARGE_k` states
never got anywhere near a difficult multi-branch-race transition -- they
either cleanly hit `I_LIMIT` or stayed latched forever).

## 6. Inductor currents (the trustworthy peak-current indicator here)

Unlike `ICS1-3`, `IL1-4` (phase inductor currents) show no sign of this
artifact -- they remain smooth, bounded, and consistent with the
commanded `I_LIMIT` throughout every cell, the same pattern R04E9 found
for its own single successfully-limited phase:

- The single largest inductor current anywhere in the whole 9-cell grid
  is `IL1_max=60.173 A` (the `I_LIMIT=60 A` cells), matching the commanded
  limit plus the same small ~0.3% overshoot margin R04E3/R04E4/R04E9
  already documented.
- The most negative value anywhere is `IL2_min=-52.84 A` (all three
  `I_LIMIT=60 A` cells, a repeatable floor value), and `IL1_min=-40.79 A`
  (`I_LIMIT=60, T_CHG=50 ns`).
- Every inductor current in the grid stays comfortably inside the
  `+/-250 A` safety bound (`BOUNDARY.md` Section 9) -- worst-case
  magnitude `60.17 A`, `24%` of that bound, essentially the same margin
  ratio R04E9 reported for its own grid.
- **On this trustworthy measure, peak currents stay in the same
  physically-plausible range R04E9 established** -- multi-rotation
  operation and the new retry/chatter dynamic do NOT push inductor
  currents toward R04E6-E8's kA-scale regime. The regression toward
  implausible magnitudes is confined to the `ICS1-3` artifact (Section 5),
  not the inductor branches.

## 7. Multi-rotation trend -- does the ladder actually progress?

**Plain-word answer: `Vout` genuinely, monotonically rises across
successive rotations in every one of the 6 cells that complete more than
one rotation.** This is the clearest positive result in this experiment.
`VC1` and `VC3` show a positive NET change over the run in most cells but
are NOT strictly monotonic rotation-to-rotation (a ringing/oscillation
component is superimposed on the upward trend, the same qualitative
signature R04E9 found within its own single `CHARGE2` stall). `VC2` is
the most concerning axis: it moves in the WRONG direction (net negative,
away from its `+24 V` target) in 3 of the 6 multi-rotation cells
(`I_LIMIT=10/T_CHG=20`: `-0.116 V` net; `I_LIMIT=30/T_CHG=20`: `-0.289 V`
net, monotonically decreasing every single rotation; `I_LIMIT=60/T_CHG=20`:
`-0.093 V` net), and only moves in the correct (positive) direction at
`T_CHARGE_MAX=50 ns` for all three `I_LIMIT` values (`+0.152`, `+0.109`,
`+0.720 V` net respectively). **`T_CHARGE_MAX=20 ns` tends to push `VC2`
the wrong way; `T_CHARGE_MAX=50 ns` tends to push it the right way** -- a
real, reportable, axis-dependent effect, not noise (consistent across all
three `I_LIMIT` values at each `T_CHARGE_MAX`).

| Case | Rotations | `Vout` trend | `VC1` net | `VC2` net | `VC3` net |
|---|---:|---|---:|---:|---:|
| `I=10A, T_CHG=20ns` | 17 | monotonic UP (16/16 steps) | +0.478 (not monotonic) | **-0.116 (wrong direction)** | +0.036 (mixed) |
| `I=10A, T_CHG=50ns` | 13 | monotonic UP (12/12 steps) | +0.344 (not monotonic) | +0.152 (right direction) | +0.008 (mixed) |
| `I=30A, T_CHG=20ns` | 4  | monotonic UP (3/3 steps)   | +0.309 (monotonic)     | **-0.289 (wrong, monotonic)** | +0.143 (monotonic) |
| `I=30A, T_CHG=50ns` | 12 | monotonic UP (11/11 steps) | +0.904 (not monotonic) | +0.109 (right direction) | +0.022 (mixed) |
| `I=60A, T_CHG=20ns` | 11 | monotonic UP (10/10 steps) | +1.027 (not monotonic) | **-0.093 (wrong direction)** | -0.083 (wrong, mixed) |
| `I=60A, T_CHG=50ns` | 12 | monotonic UP (11/11 steps) | +1.389 (not monotonic) | +0.720 (right direction) | +0.085 (mixed) |

So: `Vout` progress is unambiguous and consistent. `VC1` makes real net
progress everywhere but rings. `VC3` is mixed/small. `VC2` genuinely
regresses in half the multi-rotation cells -- this is NOT a uniform
"multi-rotation always helps" result; it is axis- and value-dependent, and
is reported exactly that way rather than averaged into a single verdict.

## 8. How close does any cell get to handoff?

Not close, in absolute terms, but measurably closer than R04E9's own
single-pass residual. The best cell (`I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`,
12 rotations) reaches:

| Quantity | R04E10 best (`I=60,T_CHG=50`) | R04E9 best (`I=60,Tfw=1000ns`) | Target | R04E10 fraction of target |
|---|---:|---:|---:|---:|
| `Vout` | `0.0141 V` | `0.00437 V` | `1 V` | `1.41%` |
| `VC1` | `1.983 V` | (not R04E9's best cell for VC1) | `36 V` | `5.51%` |
| `VC2` | `0.619 V` | `0.0296 V` | `24 V` | `2.58%` |
| `VC3` | `0.087 V` | `~0` | `12 V` | `0.73%` |

R04E10's best cell reaches roughly `3x` to `20x` further toward each
target (in absolute voltage) than R04E9's own best single-pass cell,
confirming that letting multiple rotations occur DOES make measurable
additional progress -- but every quantity remains `95-99%` short of its
target. `T_HANDOFF` FAILs (never fires) in all 9 cells
(`Measurement "t_handoff" FAIL'ed` in every log). At the observed
per-rotation `Vout` growth rate in the best cell (`~11.4 mV` net over 12
rotations, i.e. roughly `1 mV`/rotation average, though not uniform),
reaching the `0.95 V` handoff floor by simple linear extrapolation would
require on the order of several hundred more rotations -- and Section 4's
own finding (highly irregular, sometimes 70x-inflated per-rotation
duration due to the retry pattern) means that extrapolation cannot be
trusted as a time estimate; it is offered only as a rough sense of scale,
not a projection.

## 9. Comparison against R04E9 (single-pass stall)

R04E9: 0/9 cells complete any rotation; permanently latched in `CHARGE2`;
peak current `60.17 A`; `Vout`/`VC1-3` stay 3-4 orders of magnitude below
target with no mechanism to progress further (confirmed by R04E9's own
pilot extension to `20 us`, which produced bit-identical results to its
`3 us` run -- a genuine equilibrium, not a truncation).

R04E10: 6/9 cells complete 4-17 rotations; `Vout` rises monotonically in
all 6; peak inductor current `60.17 A` (same bound as R04E9, confirming
the timeout addition does not by itself push inductor currents toward
implausible levels); best cell reaches `1.4-5.5%` of target across the
four state variables, `3x`-`20x` further than R04E9's own best cell. **The
core question this experiment set out to answer -- does adding a
`CHARGE_k` timeout let rotations complete and let repetition make
progress -- is answered YES for `T_CHARGE_MAX in {20, 50} ns`.** But this
comes with two costs R04E9 did not have: (a) `T_CHARGE_MAX=5 ns`
reproduces R04E9's OWN total stall exactly (0 rotations), despite passing
isolated verification -- so the fix is not simply "add any timeout,
however small"; and (b) the flying-capacitor current reporting is
pervasively contaminated by a new solver artifact not present in R04E9's
simpler single-timer construct.

## 10. Comparison against R04E7/R04E8 (ladder-only mechanism, for
    calibration)

R04E7/R04E8's switch-only EPE2019 ladder mechanism reached `DONE`
(`LADDER_ERR` `0.045-0.207`, meaning within roughly `4.5-21%` of the
target ratio on a normalized error measure) in **5-8 cycles**, at
absolute voltages of `VC1~=35.6 V` (R04E7's best cell, `98.9%` of the
`36 V` target). R04E10, by contrast, after **11-17 rotations** (more
cycles than R04E7/E8 needed), reaches only `VC1=1.1-2.0 V`
(`3-5.5%` of target) in its best cells. **R04E10's inductor-mediated
timeout-gated mechanism converges MUCH more slowly per-cycle than
R04E7/E8's switch-only ladder mechanism**, even though it uses MORE
cycles. This is a direct, quantifiable confirmation of the same
structural trade-off R04E9 already identified qualitatively: routing
charge through a genuinely current-limited series inductor (this
mechanism, and R04E9's) is far more physically plausible on the inductor
branches than a bare switch-to-switch capacitor path (R04E6/E7/E8's
mechanism) -- but it is also far less effective, per cycle, at actually
moving charge onto the flying capacitors, because each phase's own
current-limit or timeout ceiling caps how much charge transfers per visit
much more tightly than a comparatively unconstrained switch-only path
does.

## 11. Acceptance condition (`BOUNDARY.md` Section 9)

Not met in any of the 9 cells for the `LOCAL_PASS` bar (handoff). The
weaker `CONTROLLER_GUARD_PASS` success bar (at least one full rotation
completes, current stays bounded) IS met in 6/9 cells (`T_CHARGE_MAX in
{20, 50} ns`), and is NOT met in the 3 `T_CHARGE_MAX=5 ns` cells, which
reproduce R04E9's own permanent-stall outcome instead.

## 12. First failure boundary

Two distinct, compounding failure boundaries, not one:

1. **The retry/chatter dynamic (Section 4/`BOUNDARY.md` Section 5b)**:
   even where rotations do eventually complete, the machine does not
   advance cleanly; it repeatedly makes partial forward progress and
   reverses before escaping. At `T_CHARGE_MAX=5 ns` this retry loop never
   resolves within the `20 us` window in any of the 3 `I_LIMIT` cells --
   the boundary is not crossed at all.
2. **Charge-transfer-per-cycle is too small relative to the handoff gap**
   (Section 8/10): even in the 6 cells that DO complete many rotations,
   the absolute voltage gained per rotation is small (order `1-100 mV`
   depending on the variable and cell) relative to the `~1-36 V` targets,
   so tens of rotations still leave every cell `95-99%` short.

## 13. Grade

- `T_CHARGE_MAX=5 ns` cells (3/9): **`CONTROLLER_GUARD_PASS`** in the
  weakest sense -- reproduces R04E9's own permanent single-state stall
  (0 rotations, current bounded, no divergence), despite this experiment's
  entire premise being to avoid exactly that outcome.
- `T_CHARGE_MAX in {20, 50} ns` cells (6/9): **`CONTROLLER_GUARD_PASS`**
  with genuine partial progress -- multiple rotations complete, `Vout`
  rises monotonically, but the handoff condition is never reached and
  `VC2` regresses in 3 of the 6 cells. None of the 9 cells earns
  `LOCAL_PASS`.
- Overall grid label: **`SENSITIVITY_ONLY`** (all swept values are
  engineering/sensitivity choices, not paper values, per `BOUNDARY.md`
  Section 11) with an explicit sub-finding of **construct fragility**
  (Sections 4-5) that is itself a first-class result of this experiment,
  not a side note.

## 14. Which module should be adjusted next

- The `T_CHARGE_MAX=5 ns` total-stall finding suggests the retry/chatter
  dynamic (Section 4) has its own characteristic timescale that a future
  experiment should investigate directly (e.g. instrument WHY the machine
  reverses from `CHARGE3`/`CHARGE4` back to `FREE1` instead of continuing
  forward, rather than only observing that it does) -- this experiment
  diagnosed the symptom (raw-trace inspection, `BOUNDARY.md` Section 5b)
  but did not trace it to a root cause in the `.machine`/B-source
  construct, since doing so is a further mechanism change outside this
  experiment's single-conceptual-change scope.
- The `ICS1-3` solver artifact (Section 5) should be investigated before
  any future experiment reports flying-capacitor currents from this
  family of constructs as physical results -- possibly by adding explicit
  solver-assistance (e.g. a `.options` timestep cap near known-difficult
  transitions, or an alternate integration method) rather than trusting
  `.meas MAX`/`MIN` blindly.
- The `VC2`-regresses-at-`T_CHARGE_MAX=20ns` / `VC2`-progresses-at-`50ns`
  split (Section 7) is a real, reproducible, axis-dependent effect worth
  a dedicated follow-up sweep (e.g. `T_CHARGE_MAX` at finer resolution
  between `20` and `50 ns`) if a future experiment wants to understand
  why `VC2` specifically is sensitive to this axis while `VC1`/`VC3` are
  less so.
- Per R04E9's own Section 11 (still valid, not superseded by this
  experiment): the fundamental limitation remains that phase 2 (and now,
  by extension, phases 3/4) only receive charge relayed from the phase
  before them, never a direct `Vin` connection -- this experiment shows
  that letting this happen MANY times over MANY rotations does make slow
  progress, but a topology-level or precharge-seeding change (R04E9's own
  options (a)/(b)/(c)) would likely still reach the handoff condition
  faster than waiting for enough slow rotations under this mechanism
  alone.

## 15. What must never be changed because of this failure

- `LPHASE=1.4666667 nH`, the true-zero-energy starting condition
  (`ic=0`), `CFLY=3 uF`, `COUT=4.672 mF` -- unchanged, same reasoning as
  R04E9 `RESULTS.md` Section 12.
- The current-limit exit rule form (`I(Lk)>=I_LIMIT`) and R04E9's own
  `FREE_k` timer construct -- both continue to work exactly as R04E9
  validated; this experiment's new problems (Sections 4-5) are properties
  of the NEW `CHARGE_k` timeout branch and its interaction with the rest
  of the machine, not evidence against the parts reused unchanged from
  R04E9.
- `T_CHARGE_MAX=5 ns` should not be treated as a "smaller must be safer"
  default for any future experiment in this family -- it is uniformly the
  worst value tested here, the opposite of what its clean isolated-pilot
  behavior would suggest.
