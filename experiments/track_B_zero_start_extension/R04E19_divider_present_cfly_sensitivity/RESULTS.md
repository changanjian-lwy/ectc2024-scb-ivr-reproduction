# R04E19 result - Cfly sensitivity of the divider-present runaway/safe boundary

## 1. Outcome, stated first

**The runaway/safe picture is genuinely more complex at `Cfly=0.6/8.7 uF`
than it was at `Cfly=3 uF` -- it is per-phase asymmetric, not a single
clean number, and the simple "smaller `Cfly` = uniformly safer, larger
`Cfly` = uniformly more dangerous" prediction does NOT hold cleanly.**
This is reported plainly rather than forced into the resonance-scaling
narrative the experiment set out to test, per `BOUNDARY.md` Section 7's
own explicit instruction.

Using `max(|IL_min|, IL_max)` per phase (the correct absolute-magnitude
measure -- checking only `IL_max` understates the hazard, since some
phases' most extreme excursion is on the negative side; see Section 3):

| Cell | `Cfly` | `Tramp` | IL1 \|max\| | IL2 \|max\| | IL3 \|max\| | IL4 \|max\| | Any phase `>250A`? |
|---|---:|---:|---:|---:|---:|---:|---|
| `e19_f0p6_t5` | `0.6 uF` | `5 us` | **411.8** | **321.2** | **397.5** | **1022.2** | **ALL FOUR** |
| `e19_f0p6_t30p68` | `0.6 uF` | `30.68 us` (30x margin) | 129.98 | 135.06 | 154.60 | **251.0** | only IL4, barely |
| `e19_f8p7_t22p87` | `8.7 uF` | `22.87 us` | **371.6** | 224.5 | 167.1 | **300.5** | IL1, IL4 |
| `e19_f8p7_t116p84` | `8.7 uF` | `116.84 us` (30x margin) | 169.6 | 140.9 | 131.7 | 157.8 | none -- comfortably safe |

Reference points already established (R04E17/R04E18, `Cfly=3 uF`, same
`Tramp` values, reused by citation, not re-run here): `Tramp=5 us` ->
ALL FOUR phases over `250A` (`max{|IL1-4|}=651.55A`); `Tramp=22.87 us` ->
all four phases safe (`max{|IL1-4|}=205.07A`).

**`e19_f0p6_t5` (smaller `Cfly`, same fast `Tramp`) is NOT safer than the
`Cfly=3uF` reference -- it is comparably bad, and on phase 4 specifically
WORSE (`1022.2A` vs. `651.55A` at `Cfly=3uF`).** This directly
contradicts the simple form of the resonance-scaling prediction (smaller
`Cfly` -> higher resonance frequency -> same `Tramp` should be
relatively safer). **`e19_f8p7_t22p87` (larger `Cfly`, same
previously-safe `Tramp`) DOES become unsafe on 2 of 4 phases** (`IL1=
371.6A`, `IL4=300.5A`), consistent with the OTHER half of the
prediction (larger `Cfly` needs more margin) -- but not uniformly across
all four phases, unlike the clean, phase-symmetric pattern R04E17/R04E18
found at `Cfly=3 uF`. **Both `30x`-margin, model-recommended cells are
close to the boundary, not comfortably safe**: `e19_f0p6_t30p68`
(`Cfly=0.6uF`) has one phase (`IL4`) marginally OVER `250A`
(`251.02A`, a `0.4%` overshoot of the bound); only `e19_f8p7_t116p84`
(`Cfly=8.7uF`) is comfortably and uniformly safe across all four phases.

## 2. Cells run and their history

Per explicit user direction, this experiment's four cells were run
across two separate sessions with a user-directed pause in between:
`e19_f0p6_t5`, `e19_f0p6_t30p68`, and `e19_f8p7_t22p87` were run to
completion first (all with `Total elapsed time` confirmed in their own
`.log`); the user then explicitly paused the experiment ("没跑的就别跑
了" -- "don't run the ones that haven't been run yet") before the fourth
cell was started, and a background subagent working on this experiment
was stopped. **This was a deliberate, explicit user decision to pause,
not a technical failure or an abandoned/incomplete experiment** -- no
cell was left mid-run when the pause happened (confirmed directly: no
LTspice process was running, and `e19_f8p7_t116p84.cir` had no `.log`
yet at the time of the pause). The user later explicitly resumed
("继续跑第四组" -- "continue running the fourth cell"), and
`e19_f8p7_t116p84` was run to completion in the SAME already-existing
worktree (reusing the three already-completed cells' real compute rather
than discarding it and starting over), directly by the orchestrating
session (not a fresh subagent), per the user's own preference to avoid
wasting the already-invested compute.

All four cells ran strictly sequentially, never concurrently (confirmed
via `ps`/direct file-timestamp inspection before each launch), consistent
with the `~20x` throughput-collapse constraint R04E16's own `RESULTS.md`
Section 3b documented for this netlist family. Wall-clock times:
`1305.7s`, `1471.1s`, `1375.5s`, `1639.4s` respectively (`~22-27` minutes
each).

## 3. Why `max(|IL_min|, IL_max)`, not `IL_max` alone

A first pass at this analysis (caught and corrected before this document
was written) used only each phase's own `IL_max` value, which
understates the hazard for phases whose largest-magnitude excursion is on
the NEGATIVE side. Concretely, for `e19_f0p6_t5`: `IL1_max=231.8A`
(under `250A`) but `IL1_min=-411.8A` (well over `250A` in magnitude) --
the correct per-phase hazard measure is `max(|IL_min|, IL_max)=411.8A`,
not `231.8A`. Using the correct measure, ALL FOUR phases of
`e19_f0p6_t5` exceed `250A`, not three of four as an `IL_max`-only
reading would suggest. This correction is applied throughout this
document and `results.csv`/`results.json` (columns `il{1-4}_over_250`
use the correct `max(|min|,max)` definition).

## 4. Solver-corruption fingerprint check (all four cells)

Per this project's own standing discipline (R04E16/R04E17/R04E18), all
four cells' raw `.raw` binary traces were directly, byte-level parsed in
full (`scripts/ltspice_raw_parser.py`, unchanged from R04E11-R04E18's own
committed parser; `scripts/check_fingerprint.py`, new for this
experiment) and checked for the documented two-part corruption
signature: non-monotonic/duplicate timestamps, and the independent,
state-independent `V(vin)` PWL source reading a value implausible for its
own commanded `0-48V` ramp.

| Cell | Points parsed | `dt<=0` count | `V(vin)` range (V) | Max deviation from rail |
|---|---:|---:|---|---:|
| `e19_f0p6_t5` | `6,836,121` | `0` | `[0.0, 48.41]` | `0.41 V` (`0.85%`) |
| `e19_f0p6_t30p68` | `7,416,245` | `0` | `[0.0, 48.03]` | `0.03 V` (`0.06%`) |
| `e19_f8p7_t22p87` | `7,209,112` | `0` | `[0.0, 48.10]` | `0.10 V` (`0.20%`) |
| `e19_f8p7_t116p84` | `9,283,415` | `0` | `[0.0, 47.98]` | `0.0 V` (`0%`, never exceeds rail) |

**Zero non-monotonic timestamps and zero implausible `V(vin)` values in
any of the four cells** -- every observed deviation is a small (`<1%`),
physically explicable overshoot from the `RPAR_IN`/`LPAR_IN`/divider-
capacitance filter's own ringing (matching R04E18's own Section 3
finding for its own three cells), many orders of magnitude below the
documented corruption signature (R04E16's own `-20885V`/`5.33e24V`).
**The solver-corruption fingerprint is absent from all four cells; the
large currents reported in Section 1 are confirmed real, not numerical
artifacts.**

## 5. Does the resonance-scaling prediction hold? A qualified, partial answer

`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own physics predicts the
flying-capacitor resonance frequency `f1,4 ∝ 1/√Cfly`, so a smaller
`Cfly` should tolerate a faster ramp, and a larger `Cfly` should need a
slower one, for the same margin. `BOUNDARY.md`'s own pre-run caveat
(added by the delegated agent before any cell was run, and retained here
unchanged) already flagged that this experiment cannot cleanly isolate
that law from the simultaneously-changing `CDIV/Cfly` charge-sharing
ratio (`500` at `Cfly=0.6uF` vs. `~34.5` at `Cfly=8.7uF`, for the fixed
`CDIV=300uF`) -- the results below should be read as evidence about the
COMPLETE divider-present system, not a clean test of the resonance law in
isolation.

- **The large-`Cfly` direction is qualitatively consistent** with the
  prediction: `Tramp=22.87 us`, safe at `Cfly=3uF`, becomes unsafe (2 of
  4 phases `>250A`) at `Cfly=8.7uF`. Larger `Cfly` does appear to need
  more ramp margin, as predicted.
- **The small-`Cfly` direction is NOT consistent** with the simple form
  of the prediction: `Tramp=5 us`, already unsafe at `Cfly=3uF`, remains
  (and on one phase, becomes WORSE) at `Cfly=0.6uF`, rather than becoming
  safer. If the `CDIV/Cfly` ratio (rather than, or in addition to, the
  resonance frequency alone) is the dominant driver, this asymmetry is
  plausible: `CDIV/Cfly=500` at `Cfly=0.6uF` means the divider is
  relatively HUGE compared to the flying capacitor, which could dominate
  the transient's early charge-sharing dynamics in a way the pure
  `1/√Cfly` resonance picture does not capture. This experiment's own
  4-cell design cannot distinguish between "the resonance-scaling
  prediction is simply wrong at the fast end" and "a second effect
  (`CDIV/Cfly` charge-sharing) dominates and masks it" -- both remain
  live explanations, not resolved here.
- **Per-phase asymmetry itself is a new, unexplained finding.** At
  `Cfly=3uF` (R04E16-R04E18), all four phases moved together, roughly
  uniformly over or under `250A`, for every tested `(Tramp)` value. At
  `Cfly=0.6/8.7 uF`, phases diverge substantially (e.g. `e19_f8p7_t22p87`:
  `IL1=371.6A`, `IL2=224.5A`, `IL3=167.1A`, `IL4=300.5A` -- a `2.2x`
  spread across phases at the SAME `Cfly`/`Tramp`). Why phase symmetry
  breaks down away from `Cfly=3uF` is not explained by anything in this
  experiment's own model or diagnosed further here -- a genuine open
  question for a future, more targeted investigation (e.g. examining
  each phase's own individual node voltages/timing relative to the
  divider's own charge delivery, phase by phase).
- **The `30x`-margin recommendation is NOT uniformly comfortable.** Only
  `Cfly=8.7uF`'s own `30x`-margin cell is comfortably, uniformly safe;
  `Cfly=0.6uF`'s own `30x`-margin cell has one phase marginally over the
  bound (`251.0A` vs. `250A`, a `0.4%` overshoot -- functionally
  borderline, not a large excursion, but not the "significantly below"
  margin Roberts' own text calls for either).

## 6. `Vout`/ladder behavior across all four cells

Unlike `Cfly=3uF`'s own near-`Tramp`-insensitive `LADDER_ERR`/`Vout_final`
(R04E17/R04E18), both vary substantially here:

| Cell | `Vout_final` (V) | `Vout_overshoot` | `LADDER_ERR` |
|---|---:|---:|---:|
| `e19_f0p6_t5` | `1.0363` | `31.3%` | `0.1381` |
| `e19_f0p6_t30p68` | `1.0361` | `4.65%` | `0.1342` |
| `e19_f8p7_t22p87` | `1.0013` | `5.68%` | `0.0189` |
| `e19_f8p7_t116p84` | `1.0014` | `1.17%` | **`0.00947`** |

`Cfly=8.7uF`'s own two cells reach substantially better `LADDER_ERR`
(`0.009-0.019`) than `Cfly=0.6uF`'s own two (`0.134-0.138`) -- the
larger flying capacitor achieves a noticeably more accurate final ladder
regardless of `Tramp`, and `e19_f8p7_t116p84`'s own `LADDER_ERR=0.00947`
is the BEST value reached anywhere in this project's entire Track-B
zero-start lineage to date (better than R04E17's own best, `0.0242`).
`Vout_final` itself exceeds `1V` by a larger margin at `Cfly=0.6uF`
(`3.6%` steady-state error, not just transient overshoot) than at
`Cfly=8.7uF` (`~0.14%`) -- a second respect in which smaller `Cfly`
appears to behave less favorably than larger `Cfly` in this specific
divider-present construct, independent of the peak-current runaway
question.

## 7. What this does and does not establish

**Established:**
- The runaway/safe boundary DOES shift with `Cfly`, but not as a single
  clean threshold -- the pattern is per-phase asymmetric at `Cfly=0.6uF`
  and `8.7uF`, unlike the phase-symmetric pattern at `Cfly=3uF`.
- The large-`Cfly` direction of the resonance-scaling prediction
  (needs MORE margin) is qualitatively supported; the small-`Cfly`
  direction (should tolerate LESS margin) is NOT supported by this data
  -- `Tramp=5us` remains unsafe, on one phase more severely so, at the
  smaller `Cfly=0.6uF`.
- Neither `30x`-margin cell is comfortably safe across the board;
  `Cfly=0.6uF`'s own recommended value is marginally over the `250A`
  bound on one phase.
- `Cfly=8.7uF` reaches substantially better ladder/`Vout` accuracy than
  `Cfly=0.6uF` at comparable `Tramp` fractions, independent of the
  current-safety question -- `e19_f8p7_t116p84`'s own `LADDER_ERR=
  0.00947` is this project's best Track-B result to date.
- All four cells' raw traces are confirmed free of the documented
  solver-corruption fingerprint (Section 4).

**NOT established:**
- Whether the small-`Cfly` anomaly is caused by the resonance law itself
  failing, by the `CDIV/Cfly` ratio dominating, or by some other
  mechanism -- this 4-cell design cannot distinguish these explanations
  (Section 5).
- Why phase symmetry breaks down away from `Cfly=3uF` -- an open
  question, not investigated further here.
- A precise `Cfly`-vs-boundary-`Tramp` curve -- only two `Cfly` points
  at two `Tramp` values each.
- Whether re-optimizing `CDIV` per `Cfly` (not done here, per
  `BOUNDARY.md` Section 2's deliberate scope limit) would change this
  picture.
- Any claim about `Vout`/handoff bootstrap beyond what is reported here.
- Any modification, overwrite, or invalidation of R04E16/R04E17/R04E18's
  own committed results -- their cells are reused here strictly by
  citation.
- A P24 reproduction claim of any kind -- the same standing Track-B
  limitation as every other experiment in this lineage.

## 8. Provenance and classification

| Value | Source | Category |
|---|---|---|
| `Cfly=0.6 uF`, `8.7 uF` | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes | `SENSITIVITY_ONLY`, inherited |
| `Tramp=5 us` (at `Cfly=0.6uF`), `Tramp=22.87 us` (at `Cfly=8.7uF`) | R04E18's own already-tested `Cfly=3uF` values, reused unchanged at new `Cfly` | inherited, reused for direct comparability |
| `Tramp=30.68 us`, `116.84 us` | `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own `30x`-margin recommendation for `Cfly=0.6/8.7 uF` respectively | `CROSS_PAPER_EXTENSION`, inherited |
| `CDIV=300 uF` (fixed, not re-optimized) | R04E15's own best-point value at `Cfly=3 uF` | `SENSITIVITY_ONLY`, inherited |
| Everything else | See R04E17/R04E18 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced. Classification, following this track's own established
language: **`SENSITIVITY_ONLY` / `NOT_P24_REPRODUCTION`** -- a
mechanism-sensitivity finding about this project's own Track-B
constructs, not a claim about P24's own reported behavior. Per
`BOUNDARY.md` Section 7, this is reported as a genuinely mixed,
partially-confirming/partially-disconfirming result, not forced into
either a clean "prediction confirmed" or "prediction refuted" verdict.

## 9. Files

- `cases/e19_f0p6_t5.cir`, `cases/e19_f0p6_t30p68.cir`,
  `cases/e19_f8p7_t22p87.cir`, `cases/e19_f8p7_t116p84.cir` -- the four
  netlists (`.log`/`.raw` gitignored per this project's convention).
- `scripts/ltspice_raw_parser.py` -- unchanged from R04E11-R04E18's own
  committed parser.
- `scripts/check_fingerprint.py` -- the solver-corruption fingerprint
  check (Section 4), new for this experiment.
- `results.csv`/`results.json` -- the complete 4-row table, including
  per-phase `il{1-4}_over_250` boolean columns using the corrected
  `max(|min|,max)` definition (Section 3).
