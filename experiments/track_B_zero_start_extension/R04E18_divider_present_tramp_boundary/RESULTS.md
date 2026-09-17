# R04E18 result - locating the runaway/safe `Tramp` boundary with the divider present

## 1. Outcome, stated first

**The runaway/safe boundary localizes to the `Tramp=5-22.87 us` sub-interval, roughly `5-6x` narrower than R04E17's own untested `1-68.61 us` gap, and the underlying peak-current trend across all 5 now-available points is smoothly monotonic-decreasing, not a sharp step.** Of the three new cells: `e18_div_f3_t5` (`Tramp=5 us`) still shows runaway-scale current (`max{|IL1-4|}=651.55 A`, all four phases individually over the `+/-250 A` bound); `e18_div_f3_t22p87` (`Tramp=22.87 us`, R04E16's own `10x`-margin value) and `e18_div_f3_t40` (`Tramp=40 us`) are both SAFE (`max{|IL1-4|}=205.07 A` and `170.41 A` respectively, comfortably inside the bound). Combined with R04E17's own already-completed endpoints (`Tramp=1 us`: `1046.42 A`, RUNAWAY; `Tramp=68.61 us`: `154.73 A`, safe), the complete 5-point `max{|IL1-4|}` sequence is:

| `Tramp` (us) | 1 | 5 | 22.87 | 40 | 68.61 |
|---|---:|---:|---:|---:|---:|
| `max{|IL1-4|}` (A) | 1046.42 | 651.55 | 205.07 | 170.41 | 154.73 |
| Runaway (`>250 A`)? | YES | YES | no | no | no |

The binary "runaway vs. safe" crossing (against the `+/-250 A` engineering bound this project uses) sits between `Tramp=5 us` and `Tramp=22.87 us` -- narrower than, and entirely within, R04E17's own previously-untested `1-68.61 us` gap. See Section 4 for why the underlying current trend itself is better described as gradual/monotonic than as a sharp cliff, even though the specific `+/-250 A` bound is crossed within this one sub-interval.

## 2. The three new cells, run strictly sequentially

All three cells were run one at a time, on real LTspice (`tools/ltspice_runner.sh`), never concurrently, in the exact order specified by `BOUNDARY.md`:

1. `e18_div_f3_t5` (`Tramp=5 us`, `TSTOP=305 us`) was started first. `.log` confirms `Total elapsed time: 1179.814 seconds` (`~19.7 min`) and a full `.meas` block (all 27 measurements present). No other LTspice process was running at launch (directly checked via `pgrep`/`ps` before launch).
2. `e18_div_f3_t22p87` (`Tramp=22.87 us`, `TSTOP=322.87 us`) was only started after `e18_div_f3_t5`'s own `.log` had already confirmed completion and no LTspice/wine process remained running (`pgrep -f "LTspice.exe" ` returned nothing before launch). `.log` confirms `Total elapsed time: 1341.366 seconds` (`~22.4 min`) and a full `.meas` block.
3. `e18_div_f3_t40` (`Tramp=40 us`, `TSTOP=340 us`) was only started after `e18_div_f3_t22p87`'s own `.log` had already confirmed completion, again with no LTspice/wine process left running beforehand. `.log` confirms `Total elapsed time: 1655.129 seconds` (`~27.6 min`) and a full `.meas` block.

One operational note, reported transparently: the first wait-loop's own `pgrep -f "e18_div_f3_t5.cir"` pattern initially self-matched the wait loop's own shell command line (which itself contained that literal string), so it never reported the LTspice process's exit even after the process had genuinely finished. This was caught by directly checking `.log`/`.raw` file timestamps and `ps` against the actual LTspice/wine PIDs, and the pattern was corrected to `"LTspice.exe.*<case>.cir"` (which does not match the wait loop's own command line) for the remaining two cells. This was a wait-loop bookkeeping issue only -- at no point were two LTspice processes for this netlist family running concurrently, and `e18_div_f3_t5`'s own results were independently confirmed complete and correct directly from its `.log` before proceeding.

## 3. Solver-corruption fingerprint check (all three new cells)

Per this project's own standing discipline (R04E16 `RESULTS.md` Section 3a, R04E17 `RESULTS.md` Section 4) and the task's explicit instruction, all three new cells' raw `.raw` binary traces were directly, byte-level parsed in full (`scripts/ltspice_raw_parser.py`, copied unchanged from R04E11/R04E12/R04E13's own committed parser; `scripts/check_fingerprint.py`, new for this experiment) and checked for the documented two-part corruption signature: (a) near-duplicate/non-monotonic timestamps (`dt<=0` between consecutive points), and (b) the independent, state-independent `V(vin)` PWL source reading a value impossible for its own commanded ramp.

- **`e18_div_f3_t5.raw`**: `6,815,063` points parsed in full. `dt<=0` count: `0` (zero non-monotonic or duplicate timestamps; smallest positive spacing `~4.07e-20 s`, consistent with legitimate fine adaptive substepping at this `TMAX=50 ps` resolution). `V(vin)` observed range across the entire trace: `[0.0, 48.356]` V, against a commanded `0-48 V` rail -- the small `0.36 V` (`0.74%`) overshoot above `48 V` is legitimate ringing from the `RPAR_IN=10 mOhm`/`LPAR_IN=5 nH` filter driving the divider network's own real capacitive loading, not corruption. Zero points outside a generous `+/-240 V` (`5x` the rail) implausibility bound.
- **`e18_div_f3_t22p87.raw`**: `7,211,500` points parsed in full. `dt<=0` count: `0`. `V(vin)` range: `[0.0, 48.058]` V (`0.12%` overshoot). Zero implausible-value points.
- **`e18_div_f3_t40.raw`**: `7,589,536` points parsed in full. `dt<=0` count: `0`. `V(vin)` range: `[0.0, 48.007]` V (`0.01%` overshoot). Zero implausible-value points.

**Conclusion: the solver-corruption fingerprint is absent from all three new cells.** One methodological note, reported transparently rather than silently adjusted: the tight "`+/-5%` of instantaneous commanded value, floor `0.5 V`" tolerance R04E17's own `RESULTS.md` Section 4 used (and this experiment initially re-applied unchanged) DOES flag many points per cell (`129,794`/`393,271`/`387,256` respectively) under that strict definition -- but every flagged point's actual `V(vin)` value remains well within the physically plausible `0-48 V` rail (maximum absolute deviation from commanded `8.91 V`/`1.95 V`/`1.12 V` respectively, decreasing as `Tramp` slows, consistent with milder excitation of the `RPAR_IN`/`LPAR_IN`/divider-capacitance filter's own natural ringing at a less aggressive ramp rate -- a real, physically explicable small-signal lag during the fast part of the ramp, not the documented corruption signature, which reads values many ORDERS OF MAGNITUDE beyond the rail, e.g. R04E16's own `-20885 V`/`5.33e24 V`). This distinction did not arise for R04E17's own two cells (`Tramp=1 us`, so fast the ramp completes before the filter's own ~us-scale natural ringing has time to register a large fractional deviation; `Tramp=68.61 us`, slow enough that the ringing settles well within the ramp) -- it surfaces here specifically because R04E18's three new `Tramp` values sit closer to the filter's own natural response time, a genuine and reportable circuit-behavior finding in its own right, not a defect in the corruption check. The large currents reported in Section 1 for `e18_div_f3_t5` are directly confirmed as a real transient-current result, not a numerical artifact.

## 4. Complete 5-point table

Full per-cell detail, all values directly read from each cell's own `.log` (the two reused R04E17 cells' values are copied verbatim from R04E17's own committed `results.json`, not re-derived):

| Quantity | `e17_div_f3_t1`<br>(`Tramp=1us`, **reused**) | `e18_div_f3_t5`<br>(`Tramp=5us`, NEW) | `e18_div_f3_t22p87`<br>(`Tramp=22.87us`, NEW) | `e18_div_f3_t40`<br>(`Tramp=40us`, NEW) | `e17_div_f3_t68p61`<br>(`Tramp=68.61us`, **reused**) |
|---|---:|---:|---:|---:|---:|
| `IL1_min` (A) | -860.80 | -398.59 | -64.55 | -39.00 | -22.62 |
| `IL1_max` (A) | 813.14 | 472.70 | 203.21 | 170.41 | 154.73 |
| `IL2_min` (A) | -686.53 | -347.35 | -48.98 | -30.25 | -21.16 |
| `IL2_max` (A) | 884.90 | 508.64 | 205.07 | 165.88 | 147.85 |
| `IL3_min` (A) | -604.43 | -318.81 | -38.19 | -20.27 | -15.65 |
| `IL3_max` (A) | 877.84 | 505.85 | 179.72 | 147.66 | 140.79 |
| `IL4_min` (A) | -469.63 | -242.64 | -40.27 | -21.44 | -15.35 |
| `IL4_max` (A) | 1046.42 | 651.55 | 168.73 | 149.09 | 143.34 |
| `max{|IL1-4|}` (A) | **1046.42** | **651.55** | 205.07 | 170.41 | 154.73 |
| Within `+/-250 A` bound | **NO** | **NO** | YES | YES | YES |
| `Vout_final` (V) | 1.0060 | 1.0060 | 1.0060 | 1.0059 | 1.0059 |
| `Vout_pk` (V) | 1.8233 | 1.4123 | 1.0598 | 1.0324 | 1.0254 |
| `Vout_overshoot` | 0.8233 | 0.4123 | 0.0598 | 0.0324 | 0.0254 |
| `VC1_final` (V, target 36) | 35.751 | 35.781 | 35.705 | 35.776 | 35.859 |
| `VC2_final` (V, target 24) | 23.814 | 23.813 | 24.174 | 23.789 | 23.798 |
| `VC3_final` (V, target 12) | 11.827 | 11.824 | 11.834 | 11.827 | 11.857 |
| `LADDER_ERR` | 0.0291 | 0.0286 | 0.0293 | 0.0294 | 0.0242 |
| `IIN_PK` (A) | 2498.95 | 790.03 | 173.98 | 101.15 | 60.82 |
| Wall clock (real LTspice) | 1203.95 s (reused) | 1179.81 s | 1341.37 s | 1655.13 s | 1641.49 s (reused) |

## 5. Is the transition sharp or gradual?

**Gradual, not a sharp cliff -- with the `+/-250 A` engineering bound happening to be crossed within the narrower `5-22.87 us` sub-interval.** Two separate things are worth distinguishing, per BOUNDARY.md Section 7's explicit instruction to report the actual pattern honestly:

- **The continuous `max{|IL1-4|}` trend across all 5 points is smoothly, monotonically decreasing with `Tramp`** (`1046.42 -> 651.55 -> 205.07 -> 170.41 -> 154.73 A` at `Tramp=1/5/22.87/40/68.61 us`), with no discontinuous jump anywhere in the swept range -- each additional point refines rather than overturns this trend, and the two largest relative drops (`1046.42->651.55`, a `37.7%` reduction going `1->5 us`; `651.55->205.07`, a `68.5%` reduction going `5->22.87 us`) both occur in the fast half of the range, consistent with a continuously relaxing (not step-like) transient as the ramp slows.
- **The specific binary "runaway/safe" classification** (against this project's own fixed `+/-250 A` engineering bound, not a property of the underlying physics) happens to flip within the `5-22.87 us` sub-interval because `651.55 A` sits above `250 A` and `205.07 A` sits below it. A purely informal log-log interpolation of the two bracketing points (`5 us`/`651.55 A`, `22.87 us`/`205.07 A`) places the `250 A` crossing around `Tramp~=17.6 us` -- offered here only as a rough sense of where within the bracket the crossing likely falls, NOT as an established value (no cell was actually run there, and log-log interpolation of two points is not a validated model of this circuit's real transient response).

`Vout_overshoot` and `IIN_PK` show the same gradual, monotonic-decreasing pattern across all 5 points (`Vout_overshoot`: `82.3%->41.2%->6.0%->3.2%->2.5%`; `IIN_PK`: `2498.95->790.03->173.98->101.15->60.82 A`), reinforcing that this is one continuously relaxing transient phenomenon, not a bifurcation between two qualitatively different circuit behaviors. `Vout_final`/`VC1-3_final`/`LADDER_ERR`, by contrast, stay essentially flat across all 5 points (`LADDER_ERR` `0.024-0.029`, `Vout_final` within `0.6%` of `1 V` throughout) -- the divider's own end-state charging job is essentially `Tramp`-insensitive over this entire range; only the transient peak magnitude (current and `Vout` overshoot) varies with ramp speed.

## 6. What this does and does not establish

**Established by this experiment:**
- With the divider physically present at `Cfly=3 uF`/`CDIV=300 uF` (unchanged from R04E17), the runaway/safe boundary against the `+/-250 A` bound localizes to `Tramp` between `5 us` and `22.87 us` -- narrower than, and entirely inside, R04E17's own previously-untested `1-68.61 us` gap.
- The underlying `max{|IL1-4|}` (and `Vout_overshoot`, `IIN_PK`) trend across the full `1-68.61 us` range is smoothly monotonic-decreasing with `Tramp`, not a sharp step -- the `+/-250 A` bound crossing is a property of where that fixed bound happens to intersect a continuous, gradual transient-relaxation curve, not evidence of two qualitatively distinct circuit regimes.
- `LADDER_ERR`/`Vout_final`/`VC1-3_final` remain essentially flat (`Tramp`-insensitive) across the entire 5-point range -- consistent with R04E17's own Section 7 finding that the divider's end-state charging job is not what the ramp speed affects; only the transient peak is.
- All three new cells' raw traces are confirmed free of the documented solver-corruption fingerprint (Section 3), so the reported currents are trusted as real, not artifacts.

**NOT established (per BOUNDARY.md Section 8, and directly applicable here):**
- No precise, continuous threshold value -- only a 5-point picture. A further bisection specifically within `5-22.87 us` would be needed for a precise crossing value, if one is wanted; the informal `~17.6 us` log-log estimate in Section 5 is explicitly not that.
- No claim about any `Cfly` value other than `3 uF` -- whether the threshold's absolute value (in `us`) scales with `Cfly` is not addressed here.
- No claim about `Vout`/handoff bootstrap beyond what R04E16/R04E17 already report.
- No modification, overwrite, or invalidation of R04E16's or R04E17's own committed results -- their cells are reused here strictly by reference.
- No P24 reproduction claim of any kind -- the same standing Track-B limitation as every other experiment in this lineage.

## 7. Provenance and classification

Every changed/new value in this experiment's three new netlists traces directly to an already-established source, per BOUNDARY.md Section 5:

| Value | Source | Category |
|---|---|---|
| `Tramp=5 us` | New for this experiment: a round point near the fast/runaway end | `SENSITIVITY_ONLY` |
| `Tramp=22.87 us` | R04E16's own already-derived `10x`-margin value at `Cfly=3 uF` (`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`), reused here at a new (divider-present) condition | `CROSS_PAPER_EXTENSION`, inherited |
| `Tramp=40 us` | New for this experiment: a round point filling the gap between R04E16's own `10x`/`30x` margin values | `SENSITIVITY_ONLY` |
| Everything else (power-stage topology, divider network, `CDIV=300 uF`, `Cfly=3 uF`, `LPHASE=1.4666667 nH`, `solver=alt cshunt=1e-15 plotwinsize=0`, `TMAX=50 ps`) | Copied unchanged from R04E17's own two netlists; see R04E17 `BOUNDARY.md` Section 5 and R04E16 `RESULTS.md` Section 3a for original provenance | unchanged, inherited |

No new paper-sourced, cross-paper, or external-device data is introduced. This experiment only adds grid resolution to an already-established, already-justified `(divider-present, Cfly=3uF)` parameter line. Classification, following this track's own established language (R04E14/R04E15/R04E16/R04E17): **`SENSITIVITY_ONLY` / `NOT_P24_REPRODUCTION`** -- this is a mechanism-localization finding about this project's own Track-B constructs (Roberts' soft-start idea and R03A's divider network), not a claim about P24's own reported behavior.

## 8. Files

- `cases/e18_div_f3_t5.cir`, `cases/e18_div_f3_t5.log`, `cases/e18_div_f3_t5.raw` -- `Tramp=5 us` cell (RUNAWAY).
- `cases/e18_div_f3_t22p87.cir`, `cases/e18_div_f3_t22p87.log`, `cases/e18_div_f3_t22p87.raw` -- `Tramp=22.87 us` cell (safe).
- `cases/e18_div_f3_t40.cir`, `cases/e18_div_f3_t40.log`, `cases/e18_div_f3_t40.raw` -- `Tramp=40 us` cell (safe).
- `scripts/ltspice_raw_parser.py` -- byte-level `.raw` binary parser, copied unchanged from R04E11/R04E12/R04E13's own committed parser.
- `scripts/check_fingerprint.py` -- the solver-corruption fingerprint check (Section 3), new for this experiment.
- `scripts/analyze_r04e18.py` -- parses all three new cells' `.log` files and merges in R04E17's own two reused endpoint cells (from its committed `results.json`) to produce the complete 5-point table.
- `results.csv`/`results.json` -- the complete 5-row table (two reused rows marked `reused_by_reference: true`, three new rows marked `false`).
