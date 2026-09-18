# R04E25 - does state 4's resonant ring amplitude scale with I_NEG, and by how much is it short of ZVS? (RESULTS)

See `BOUNDARY.md` for the full scope statement, provenance and explicit
limitations. This document reports what actually happened; read Section 0
of `BOUNDARY.md` before interpreting anything below.

## 1. Outcome, stated plainly, first

**All four new cells behave exactly like R04E24's own single cell,
qualitatively: state 3 exits, state 4 is entered, and `t_high_side_zvs`
FAILs in every one.** `STATE_FINAL=4` at `t=100us` in all four cells --
**none of the four new cells reaches state 5.** This does NOT reverse
R04E24's own conclusion; per BOUNDARY.md Section 6's third bullet, that
would have required at least one cell to reach `state_final=5`, which did
not happen anywhere in this sweep.

**The ring-depth-vs-`I_NEG` scaling question IS answered cleanly: the
ring's closest approach to `0V` (`ring_min`) is linear in `I_NEG` to
extremely high precision (`R^2=0.99999998`) across all five available
points (four new + R04E24's own cited point), confirming BOUNDARY.md
Section 4's LC-tank first-principles hypothesis directly with real SPICE
data, not just the earlier back-of-envelope estimate.** Extrapolating the
fitted line to `ring_min=0V` gives `I_NEG=10.586A` -- within `2%` of
BOUNDARY.md's own pre-registered back-of-envelope estimate (`~10.6A`) --
which is **`4.78x`** R04E23's own observed natural ceiling for this
bootstrapped operating point (`~2.215A`). This is a **large, multi-x
shortfall**, confirming BOUNDARY.md Section 6's FIRST anticipated outcome:
the diagnosed energy-insufficiency conclusion is confirmed cleanly, and
closing this stall via `I_NEG`/`I_LIMIT` tuning alone is infeasible for
this bootstrapped operating point.

## 2. The four new cells: exact measurement outcomes

Built as byte-identical copies of R04E24's own
`r04e24_neg1p6pct_t100us.cir`, changing only the `NEG_FRAC` line in each
(confirmed by `diff`, Section 3 below). All four ran cleanly on real
LTspice (`Total elapsed time`: `70.990s` / `84.678s` / `81.303s` /
`89.772s`), each launched and confirmed complete (via its own process
exit and `.log`'s `Total elapsed time` line) before the next was started
-- run strictly one at a time, never concurrently.

| Cell | `NEG_FRAC` | `I_NEG` | `t_energy_end` | `t_low_side_zvs` | `t_neg_target` | `t_high_side_zvs` | `state_final` | `vout_final` |
|---|---:|---:|---:|---:|---|---|---:|---:|
| `r04e25_neg0p4pct` | `.004` | `0.5A` | `6.3702883197e-9s` | `6.47330761463e-9s` | **PASS** `@1.71916498415e-6s` | **FAIL** | `4` | `1.95343918818e-8V` |
| `r04e25_neg0p8pct` | `.008` | `1.0A` | `6.3702883197e-9s` | `6.47330761463e-9s` | **PASS** `@1.8313932808e-6s` | **FAIL** | `4` | `1.93568716611e-8V` |
| `r04e25_neg1p2pct` | `.012` | `1.5A` | `6.3702883197e-9s` | `6.47330761463e-9s` | **PASS** `@1.99112055056e-6s` | **FAIL** | `4` | `1.89297804098e-8V` |
| `r04e25_neg1p72pct` | `.0172` | `2.15A` | `6.3702883197e-9s` | `6.47330761463e-9s` | **PASS** `@2.49643794178e-6s` | **FAIL** | `4` | `1.68115477095e-8V` |

`t_energy_end`/`t_low_side_zvs`/`t_il1_zero` (`1.63197919454e-6s` in all
four) are identical across all four cells, as expected -- these
transitions occur before the `LOW_BUILD_NEGATIVE` state where `NEG_FRAC`
first enters the physics, and are also identical to R04E24's own values.
`t_neg_target` PASSES in **all four** cells (confirming BOUNDARY.md
Section 6's stated expectation that all four targets sit below R04E23's
own observed `~2.215A` natural ceiling), with the transition time
increasing monotonically with `I_NEG` (`1.719us` at `0.5A` up to
`2.496us` at `2.15A`), consistent with a larger negative-current target
simply taking longer to reach along the same underlying `IL1(t)`
trajectory. `t_high_side_zvs` FAILs in all four -- state 4 is entered but
never exited within `TSTOP=100us`. `VC2_FINAL`/`VC3_FINAL` remain
numerically zero (`~-2.8e-8V` to `~-3.1e-8V`) in all four cells,
confirming phases 2-4 stayed at R04E3's own hardcoded zero-energy
configuration throughout, unchanged from R04E24.

## 3. The four netlists built

Each `diff`-confirmed to change EXACTLY the `NEG_FRAC` line relative to
R04E24's own `r04e24_neg1p6pct_t100us.cir` (comment lines excluded), and
nothing else:

```
r04e25_neg0p4pct.cir:   .param I_LIMIT=125 NEG_FRAC=.004  I_NEG={NEG_FRAC*I_LIMIT}
r04e25_neg0p8pct.cir:   .param I_LIMIT=125 NEG_FRAC=.008  I_NEG={NEG_FRAC*I_LIMIT}
r04e25_neg1p2pct.cir:   .param I_LIMIT=125 NEG_FRAC=.012  I_NEG={NEG_FRAC*I_LIMIT}
r04e25_neg1p72pct.cir:  .param I_LIMIT=125 NEG_FRAC=.0172 I_NEG={NEG_FRAC*I_LIMIT}
```

`TSTOP=100u`, `I_LIMIT=125`, the bootstrapped initial conditions
(`VC1_IC=35.85894624845418`, `IL1_IC=75.96527862548828`), `CFLY=3u`, the
5-state `.machine` block's own rule structure, phases 2-4's own hardcoded
R04E3 configuration, the `WHEN`-based `.meas` lines, the `IL1_MIN`/
`IL1_MAX` `FROM 0 TO 20u` window, and `.options` are all byte-identical to
R04E24's own file in every one of the four new cases (only the
header/provenance comments carry no simulated behavior and were rewritten
to document this experiment's own provenance, per this project's own
standing convention -- see R04E24's own `RESULTS.md` Section 3 for the
identical practice).

## 4. State-4 ring-depth analysis (the core measurement)

`scripts/state4_ring_analysis.py` (new for this experiment; reuses
`scripts/ltspice_raw_parser.py`, byte-for-byte copied unchanged from
R04E24's own committed script) directly, byte-level parses each `.raw`
file, restricts to the window `t_neg_target <= t <= min(t_high_side_zvs,
TSTOP)` (here always `t_neg_target` to `TSTOP=100us`, since
`t_high_side_zvs` FAILs in all four) AND `3.9 <= V(state_mon) <= 4.1`
(the same half-integer state-4 bucket convention this project's own
`.machine` construct uses, matching R04E24's own verification method),
and computes the min/max of `V(vin,xmod:a1) = V(vin)-V(xmod:a1)` (the
`4->5` rule's own quantity, needing `<=0V`) within that window:

| Cell | `I_NEG` | `state4_n_points` | `ring_min` (closest approach) | at `t=` | `ring_max` | at `t=` | `ring_amplitude` (`max-min`) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `r04e25_neg0p4pct` | `0.5A` | `411,055` | `11.350894927978516V` | `1.7212332246571946e-6s` | `12.476264953613281V` | `1.7253016714323123e-6s` | `1.125370V` |
| `r04e25_neg0p8pct` | `1.0A` | `436,779` | `10.78805923461914V` | `1.833454686969502e-6s` | `13.038650512695312V` | `1.8375549515951712e-6s` | `2.250591V` |
| `r04e25_neg1p2pct` | `1.5A` | `452,056` | `10.22528076171875V` | `1.9931795937313962e-6s` | `13.601112365722656V` | `1.997280146372366e-6s` | `3.375832V` |
| `r04e25_neg1p72pct` | `2.15A` | `466,334` | `9.494003295898438V` | `2.49848066564832e-6s` | `14.332759857177734V` | `2.5025961144143737e-6s` | `4.838757V` |
| (cited) `r04e24_neg1p6pct_t100us` | `2.0A` | (per R04E24's own already-committed analysis) | `9.662612915039062V` | `2.2909270415129772e-6s` | `14.163780212402344V` | (per R04E24 `results.json`) | `4.501167V` |

In every one of the four new cells, `ring_min` occurs at the very first
trough right after state-4 entry (within `~20-50ns` of `t_neg_target`),
matching R04E24's own finding exactly -- the closest approach to `0V` is
never a late near-miss, it is the initial ring's own first trough. All
five points' `ring_min` occurs progressively later in absolute time as
`I_NEG` increases, simply because `t_neg_target` itself occurs later (a
larger `-I_NEG` target takes longer to reach along the same `IL1(t)`
trajectory, Section 2 above), not because the ring dynamics themselves
change shape.

**A separate cross-check**: all four new cells' `V(vin,xmod:a1))` settle
to the identical final DC value, `11.924385070800781V`, at `t=100us` --
matching R04E24's own reported `~11.92V` settled value to full precision
and confirming that `I_NEG` only controls the INITIAL ring's amplitude
(the transient overshoot magnitude), not the eventual DC operating point
the ring damps toward (which is set by the fixed `CH1`/`CS1`/`CL1`/`Vin`
network, unaffected by `NEG_FRAC`).

## 5. The 5-point scaling fit -- linear-amplitude hypothesis directly confirmed

Least-squares linear fit on all five `(I_NEG, ring_min)` points (four new
cells plus R04E24's own already-committed, cited point):

```
ring_min(I_NEG) = 11.913528 - 1.125425 * I_NEG      R^2 = 0.99999998
```

Residuals (`actual - predicted`) are all under `1.4e-4 V` in magnitude
across the full `0.5A`-`2.15A` span -- an essentially perfect fit, not a
rough qualitative trend. The equivalent fit on `ring_amplitude
(=ring_max - ring_min)` is, if anything, even cleaner:

```
ring_amplitude(I_NEG) = 0.0000674 + 2.250543 * I_NEG   R^2 = 0.9999999995
```

The intercept is numerically indistinguishable from `0` (`6.7e-5V`,
`<0.002%` of the smallest measured amplitude), exactly as the LC-tank
stored-energy hypothesis predicts (`0.5*L*I_NEG^2` stored energy -> zero
`I_NEG` gives zero excess ring amplitude). **This is a clean, high-
confidence confirmation that state 4's resonant ring amplitude scales
linearly with `I_NEG` across the full reachable range -- not merely
"roughly linear," but linear to 4+ significant figures.**

**Extrapolation**: setting `ring_min(I_NEG)=0` in the fitted line gives:

```
I_NEG_needed_for_0V = 11.913528 / 1.125425 = 10.5858 A
```

This is within `2%` of BOUNDARY.md Section 1's own pre-registered
back-of-envelope estimate (`~10.6A`), now confirmed directly by real
SPICE data spanning the actual reachable range rather than a single-point
extrapolation. Compared against R04E23's own observed natural ceiling for
this bootstrapped operating point (`~2.215A`):

```
ratio = 10.5858 / 2.215 = 4.78x
```

**This is a large, multi-x shortfall (~4.8x), not a small one.** Per
BOUNDARY.md Section 6's own explicit success/failure framing, this
directly matches the FIRST anticipated outcome: ring depth scales
linearly with `I_NEG`, and extrapolation confirms a large shortfall at
the natural ceiling. The diagnosed energy-insufficiency conclusion (first
established qualitatively by R04E24) is now confirmed QUANTITATIVELY:
closing this stall via `I_NEG`/`I_LIMIT` tuning alone, within this
bootstrapped operating point's own reachable range, is infeasible -- even
the largest safely-reachable cell tested here (`I_NEG=2.15A`,
`97%` of R04E23's own natural ceiling) only reaches `ring_min=9.49V`,
barely `1.7%` closer to `0V` than R04E24's own `2.0A` cell
(`9.66V`), a `9.5V` gap that would require roughly `4.8x` more stored
negative current than this operating point can naturally reach.

## 6. Current-safety check (`+/-250 A` bound, full trace, all four cells)

Per BOUNDARY.md Section 6's explicit requirement, reported regardless of
outcome. Byte-level `.raw` scan (`scripts/check_fingerprint.py`, copied
unchanged from R04E24's own reference script):

| Cell | `IL1_MAX` (full trace) | `IL1_MIN` (full trace) | `max|IL1|` | Points `>250A` |
|---|---:|---:|---:|---:|
| `r04e25_neg0p4pct` (`I_NEG=0.5A`) | `125.39020538330078A` | `-0.5000494718551636A` | `125.390A` | `0` |
| `r04e25_neg0p8pct` (`I_NEG=1.0A`) | `125.39020538330078A` | `-1.0000169277191162A` | `125.390A` | `0` |
| `r04e25_neg1p2pct` (`I_NEG=1.5A`) | `125.39020538330078A` | `-1.500006079673767A` | `125.390A` | `0` |
| `r04e25_neg1p72pct` (`I_NEG=2.15A`) | `125.39020538330078A` | `-2.150001049041748A` | `125.390A` | `0` |

`IL1_MAX` is identical across all four cells (`125.390A`, at the
state-0/state-1 transition, unaffected by `NEG_FRAC`, matching
R04E22-R04E24's own value). `IL1_MIN` tracks each cell's own `-I_NEG`
target essentially exactly (`0.0000A`-`0.0002A` above the commanded
target in each case, solver-step/interpolation precision). **Phase 1's
own current stays well within the `+/-250A` engineering bound throughout
all four cells** (worst case `125.390A`, far below the bound), consistent
with R04E24's own single cell (`125.39A` max) and BOUNDARY.md Section 6's
own stated expectation ("not expected to differ materially").

## 7. Solver-corruption fingerprint check (all four cells)

`scripts/check_fingerprint.py` directly, byte-level parsed all four
`.raw` files:

| Cell | Points | `dt_nonpos_count` | `vin_min` | `vin_max` | `implausible_vin_count` | `il1_over_250a_count` |
|---|---:|---:|---:|---:|---:|---:|
| `r04e25_neg0p4pct` | `413,175` | `0` | `0.0` | `48.0` | `0` | `0` |
| `r04e25_neg0p8pct` | `439,005` | `0` | `0.0` | `48.0` | `0` | `0` |
| `r04e25_neg1p2pct` | `454,445` | `0` | `0.0` | `48.0` | `0` | `0` |
| `r04e25_neg1p72pct` | `469,218` | `0` | `0.0` | `48.0` | `0` | `0` |

Zero non-monotonic or duplicate timestamps in any of the four traces;
`V(vin)` stays exactly within its own commanded `0-48V` step in all four;
no point in any trace exceeds the `+/-250A` current bound. **All four new
traces are confirmed free of the documented solver-corruption fingerprint
(R04E10, R04E16-R04E24).** Point counts increase monotonically with `I_NEG` (`413,175` at `0.5A` up
to `469,218` at `2.15A`), with the `2.15A` cell's own `469,218` slightly
ABOVE R04E24's own `465,821` (at `2.0A`) -- consistent with the larger
`I_NEG` target taking marginally longer to reach and the ring itself
forcing a correspondingly longer fine-step interval, reflecting the same
finer-solver-step-during-the-ring effect R04E24 already documented, not a
data-integrity concern.

## 8. Which BOUNDARY.md Section 6 outcome was actually met

**BOUNDARY.md Section 6's FIRST anticipated outcome: "Ring depth scales
linearly (or near-linearly) with `I_NEG`, and extrapolation confirms a
large (multi-x) shortfall at the natural ceiling."** This is exactly what
happened:

- Ring depth (`ring_min`) scales linearly with `I_NEG` to `R^2=0.99999998`
  across all five available points -- not "near-linear" with meaningful
  deviation, but linear to within measurement/solver precision.
- The extrapolated `I_NEG` needed to reach `ring_min=0V` (`10.586A`) is
  `4.78x` R04E23's own observed natural ceiling for this bootstrapped
  operating point (`~2.215A`) -- a large, multi-x shortfall, not a small
  or marginal one.
- **No cell in this sweep reaches `state_final=5`** -- `t_high_side_zvs`
  FAILs in all four new cells, exactly as it did in R04E24's own cell.
  R04E21's own diagnosed hypothesis, already REFUTED by R04E24, remains
  REFUTED; this sweep does not reverse that finding at any tested point.

**Per BOUNDARY.md Section 6's own explicit instruction for this outcome:
this confirms the diagnosed energy-insufficiency conclusion cleanly.
Closing this stall via `I_NEG`/`I_LIMIT` tuning alone is infeasible for
this bootstrapped operating point; a circuit-level change (e.g. larger
`LPHASE`) would be required, out of this experiment's own minimal
scope.** This is reported plainly per this project's own Ground Rule 7 --
not forced into a more favorable-sounding "maybe with more tuning"
conclusion than the data supports. The data is unambiguous: the fit is
essentially perfect, and the shortfall is nearly `5x`, not a marginal
`10-20%` gap that further `I_LIMIT` tuning might plausibly close.

## 9. Explicit adherence to BOUNDARY.md Section 0/7 -- what this does NOT show

Same standing limitations as R04E21-R04E24's own Section 7/8:

- **Not a P24 periodicity result.** Unaffected either way by this run's
  own outcome; that question remains independently unresolved.
- **Not a four-phase handoff test.** Phases 2-4 stayed at R04E3's own
  hardcoded, zero-energy, single-phase-isolation configuration throughout
  all four cells (`VC2_FINAL`/`VC3_FINAL` both `~-3e-8V`, numerically
  zero, in every cell).
- **Not a validation of R04E3's own controller as "the" P24 controller.**
- **Does NOT identify what specific circuit-level change would fix the
  stall.** This experiment confirms the shortfall is large and
  quantifies it precisely, but does not test `LPHASE`, `CFLY`, device
  capacitance, or any other circuit-level intervention -- BOUNDARY.md
  Section 7 explicitly reserves that for a separate, new experiment with
  its own explicit boundary, not performed here.
- **Per BOUNDARY.md Section 7's own explicit instruction**: this is
  intended as a stopping point for this minimal-scope sub-investigation,
  since the energy-insufficiency conclusion is now confirmed, not merely
  suspected. Further open-ended `I_NEG`/`I_LIMIT` parameter tuning beyond
  this sweep should not proceed without a fresh, explicit boundary
  decision.
- Neither R04E24's, R04E23's, R04E22's, R04E21's, nor R04E3's own
  committed files or results were modified.

## 10. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `NEG_FRAC` in `{.004, .008, .012, .0172}` | New for this experiment: chosen to bracket the reachable `I_NEG` range with roughly even spacing (BOUNDARY.md Section 4) | `SENSITIVITY_ONLY`, derived from this project's own prior committed results (R04E23's ceiling), not external or paper-sourced |
| The fitted linear relationship `ring_min(I_NEG)`/`ring_amplitude(I_NEG)` and its `R^2` | New for this experiment: least-squares fit on this experiment's own directly-measured SPICE data (4 new points) plus R04E24's own already-committed cited point | Direct empirical result of this experiment, not assumed or paper-sourced |
| The `10.586A` extrapolation and `4.78x` ratio | New for this experiment: algebraic extrapolation of the fitted line above, cross-checked against BOUNDARY.md's own pre-registered `~10.6A`/`~5x` back-of-envelope estimate | Direct empirical result, corroborating (not merely repeating) the pre-registered hypothesis |
| Everything else (`I_LIMIT=125`, `TSTOP=100u`, `VC1_IC`, `IL1_IC`, `CFLY=3uF`, R04E3's own machine structure, phases 2-4's own hardcoded config, `.options`) | Copied unchanged from R04E24's own already-verified netlist | inherited, unchanged (see R04E21-R04E24 `BOUNDARY.md`/`RESULTS.md` for original provenance) |

No new paper-sourced, cross-paper, or external-device data is
introduced.

## 11. Classification

`SENSITIVITY_ONLY`, `NOT_P24_REPRODUCTION`, negative result (state 5
never reached in any of the four new cells; R04E21's own diagnosed
hypothesis remains REFUTED, unchanged from R04E24). The state-4
resonant-ring linear-amplitude-vs-`I_NEG` hypothesis (BOUNDARY.md Section
4) is CONFIRMED directly by SPICE data (`R^2=0.99999998`), and the
resulting extrapolation confirms a large (`~4.8x`) shortfall between the
`I_NEG` needed to reach `0V` (`10.586A`) and this bootstrapped operating
point's own natural ceiling (`~2.215A`), per BOUNDARY.md Section 6's
FIRST anticipated outcome.
