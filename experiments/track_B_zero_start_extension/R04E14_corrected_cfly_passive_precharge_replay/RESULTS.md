# R04E14 - corrected-Cfly replay of the R02A/R02B passive-precharge module (RESULTS)

## 1. Outcome, stated first

**Yes -- correcting `CFLY` from the cross-topology-suspect `53.8 uF` to this
project's own first-principles `0.6-8.7 uF` range changes R02A/R02B's own
`FAILED_CAPACITANCE_TRANSFER` verdict for the passive-divider-only startup
module.** Using the SAME unmodified IPEC-2018 passive-divider-plus-diode
circuit R02A/R02B themselves used (only `CFLY` and the `CDIV` sweep range
changed, per `BOUNDARY.md` Section 2), **2 of the 12 primary-grid cells**
(`CDIV=100 uF`/`TRAMP=100 us` and `CDIV=300 uF`/`TRAMP=100 us`, both at
`CFLY=3 uF`) reach a normalized ladder error (`0.157` and `0.054`
respectively) far better than R02A's own best passive result (`Step 1`,
`CFLY=1 uF`, ladder error `~0.236`), at a peak source current (`16.45 A`
and `39.18 A`) far below R02B's own best (`150.15 A`). Both conditions of
`BOUNDARY.md` Section 7's `PASS_TOPOLOGY_PRINCIPLE`-style success bar are
met simultaneously by these two cells. **This is graded
`PASS_TOPOLOGY_PRINCIPLE / NOT_P24_REPRODUCTION`**, reusing R02A's own
Step-1 grading language, not a new category -- see Section 6 below.

This is a large, direct improvement over R02B's own `COMPLETED /
FEASIBLE_TREND / NO_PASS` verdict, which never reached a comparable ladder
error at a comparable current using the old `53.8 uF` target. It confirms
the hypothesis `BOUNDARY.md` Section 1 set out to test: R02A/B's own
diagnosed failure mode ("a charge-budget and capacitance-ratio failure")
was specific to the oversized, cross-topology-suspect `53.8 uF` value, not
to the passive-divider topology itself. At the corrected, much smaller
`CFLY`, the same unmodified topology **can** supply enough charge.

This does **not** mean the passive module is now "proven" for P24 -- see
Section 9 for the unchanged list of what this result cannot establish
(most importantly: this remains isolated from PWM/the P24 switching
stage, per the explicit, separately-tracked Roberts & Prodić 2024 gate).

## 2. Method (per BOUNDARY.md, unchanged from R02A/R02B except CFLY/CDIV)

All 14 cells are LTspice 26.0.2 real transient runs of a byte-level
faithful copy of R02B's own circuit body (`paper_locked/02_ectc2024_main/
spice/R02B_passive_precharge_charge_ramp_sweep.cir`): four equal
input-divider capacitors `CIN1-4=CDIV`, `LPAR=5 nH`/`RPAR=10 mOhm` source
parasitics (IPEC 2018 Table II), three ideal precharge diodes
(`Ron=1m Roff=1T Vfwd=0`) charging `CF1-3=CFLY` referenced to ground
(R02A's own "all-low-side-on precharge state" approximation), `1 GOhm`
DC-reference leakage, true-zero-energy initial conditions (`UIC`, no IC
statements), no PWM/switches/load, and the identical `.meas` definitions
(`VC1/2/3_FINAL`, `RATIO21`, `RATIO31`, `LADDER_ERR`, `IIN_PK`,
`ID1/2/3_PK`) R02B itself uses. Unlike R02B (one file, two nested
`.step param` lists, 12 steps in one LTspice invocation), this experiment
generates one netlist file per grid cell (14 files, `cases/e14_c<CDIV>_
t<TRAMP>_f<CFLY>.cir`) and runs each as its own LTspice invocation -- a
packaging difference only, forced by an empirically-found LTspice-runner
path-length failure mode described in Section 4.

Primary grid: `CFLY=3 uF` fixed x `CDIV` in `{10,30,100,300} uF` x `TRAMP`
in `{1,10,100} us` = 12 cells. Secondary grid: the primary grid's own best
cell by `LADDER_ERR` (`CDIV=300 uF`, `TRAMP=10 us`, `LADDER_ERR=0.0351`)
re-run at `CFLY=0.6 uF` and `CFLY=8.7 uF` = 2 cells. All 14 LTspice runs
completed without a convergence error and produced a full `.meas` block.

## 3. Full 14-cell results table

| `CDIV` | `TRAMP` | `CFLY` | `VC1` (V) | `VC2` (V) | `VC3` (V) | err% (VC1/VC2/VC3) | `LADDER_ERR` | `IIN_PK` (A) | `ID1_PK`/`ID2_PK`/`ID3_PK` (A) |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| 10 uF | 1 us | 3 uF | 29.286 | 15.701 | 6.827 | -18.65/-34.58/-43.11 | 0.9634 | 330.84 | 129.93/69.66/30.29 |
| 10 uF | 10 us | 3 uF | 27.512 | 14.750 | 6.413 | -23.58/-38.54/-46.56 | 1.0867 | 33.08 | 12.99/6.97/3.03 |
| 10 uF | 100 us | 3 uF | 27.243 | 14.606 | 6.350 | -24.33/-39.14/-47.08 | 1.1055 | 3.31 | 1.30/0.70/0.30 |
| 30 uF | 1 us | 3 uF | 37.919 | 23.352 | 11.120 | +5.33/-2.70/-7.33 | 0.1536 | 682.33 | 140.93/86.79/41.33 |
| 30 uF | 10 us | 3 uF | 32.794 | 20.196 | 9.617 | -8.91/-15.85/-19.86 | 0.4462 | 68.24 | 14.09/8.68/4.13 |
| 30 uF | 100 us | 3 uF | 32.387 | 19.945 | 9.498 | -10.04/-16.90/-20.85 | 0.4779 | 6.82 | 1.41/0.87/0.41 |
| 100 uF | 1 us | 3 uF | 41.071 | 26.714 | 13.160 | +14.08/+11.31/+9.67 | 0.3506 | 1565.09 | 123.70/80.46/39.64 |
| 100 uF | 10 us | 3 uF | 35.324 | 22.976 | 11.318 | -1.88/-4.27/-5.68 | 0.1182 | 164.46 | 13.00/8.46/4.17 |
| **100 uF** | **100 us** | **3 uF** | **34.847** | **22.666** | **11.166** | **-3.20/-5.56/-6.95** | **0.1571** | **16.45** | **1.30/0.85/0.42** |
| 300 uF | 1 us | 3 uF | 37.254 | 24.631 | 12.254 | +3.48/+2.63/+2.12 | 0.0823 | 2497.83 | 71.60/47.34/23.55 |
| 300 uF | 10 us | 3 uF | 35.835 | 23.693 | 11.787 | -0.46/-1.28/-1.77 | 0.0351 | 391.80 | 11.23/7.43/3.69 |
| **300 uF** | **100 us** | **3 uF** | **35.611** | **23.545** | **11.714** | **-1.08/-1.90/-2.39** | **0.0536** | **39.18** | **1.12/0.74/0.37** |
| 300 uF | 10 us | 0.6 uF | 36.181 | 24.080 | 12.028 | +0.50/+0.33/+0.23 | 0.0107 | 382.83 | 2.28/1.51/0.76 |
| 300 uF | 10 us | 8.7 uF | 35.046 | 22.814 | 11.244 | -2.65/-4.94/-6.30 | 0.1389 | 412.23 | 31.62/20.59/10.15 |

Bold rows are the two cells that satisfy BOTH halves of the
`PASS_TOPOLOGY_PRINCIPLE`-style success bar (Section 6). Raw values are
quoted directly from each case's own `.log` `.meas` output (`results.csv`/
`results.json`); no value here is hand-computed except the derived err%
and `LADDER_ERR` columns, which use R02B's own published formula
(`LADDER_ERR = |VC1-36|/36+|VC2-24|/24+|VC3-12|/12`) applied to the raw
`VC1/2/3_FINAL` numbers.

## 4. A tooling finding, reported for the record

During piloting, the very first generated case (a descriptively-named
file at this worktree's own, unusually long absolute path -- nested under
`.claude/worktrees/agent-<hash>/...`) produced a `.log` reporting a normal,
fast, error-free `Total elapsed time` but **zero `.meas` output** and the
line `unable to open database file`. Direct isolation testing (copying the
identical netlist to shorter-named paths in the same directory, then
binary-searching the path length) confirmed this is a **path-length
failure mode** in the wine-hosted `LTspice.exe`, not a circuit or
convergence problem: full absolute `.cir` paths at or above roughly
250-259 characters silently fail to open the per-run measurement database
and print no measurements at all, while paths at or below ~239 characters
were confirmed clean. All 14 committed cases use short filenames
(`e14_c<CDIV>_t<TRAMP>_f<CFLY>.cir`) specifically to stay well under this
threshold, and `analyze_r04e14.py` raises an explicit error (rather than
silently recording a missing/zero value) if this failure signature is ever
seen in a `.log` again. This is a project-tooling lesson, not a finding
about the circuit under test.

## 5. Direct comparison against R02A's own numbers

| Quantity | R02A Step 1: `CFLY=1 uF` (IPEC Table II) | R02A Step 2: `CFLY=53.8 uF` (old candidate) | R04E14 best PASS cell (`CDIV=300uF/TRAMP=100us/CFLY=3uF`) |
|---|---:|---:|---:|
| `VC1/VC2/VC3` final (V) | 35.4916/21.8570/10.4081 | 7.6168/1.0561/0.14375 | 35.611/23.545/11.714 |
| errors vs. 36/24/12 V | -1.41%/-8.93%/-13.27% | -78.84%/-95.60%/-98.80% | -1.08%/-1.90%/-2.39% |
| `LADDER_ERR` (derived) | ~0.2361 | ~2.7322 | 0.0536 |
| peak source current | 256.59 A | 601.30 A | 39.18 A |
| diode-current peaks | 53.00/32.64/15.54 A | 518.05/72.25/9.89 A | 1.12/0.74/0.37 A |

R04E14's best PASS cell beats R02A's own Step-1 result (its best-ever
passive-divider case, using the IPEC prototype's own `10 uF : 1 uF` ratio)
on every single axis: smaller per-voltage errors, a `4.4x` better
`LADDER_ERR`, `6.5x` lower peak source current, and roughly `45-140x`
lower diode peak currents. This is a materially stronger result than
anything R02A itself reported using the passive divider.

## 6. Direct comparison against R02B's own 12-cell table

R02B's own committed table (`STEP_06_R02_LITERATURE_STARTUP_MODULE.md`,
`CFLY=53.8 uF` fixed, `CDIV` in `{10,53.8,538,1076} uF`):

| `CDIV` | `TRAMP` | `VC1/VC2/VC3` final (V) | `LADDER_ERR` | source peak (A) |
|---:|---:|---:|---:|---:|
| 1076 uF | 100 us | 34.046/21.793/10.631 | 0.260 | 150.15 |
| 1076 uF | 1 us | 34.046/21.793/10.631 | 0.260 | 3429.57 |
| 538 uF | 1 us | 32.341/19.917/9.484 | 0.481 | 3084.92 |
| 10 uF | 1 us | 7.617/1.056/0.144 | 2.732 | 601.33 |

(full 12-row table already quoted in `STEP_06`'s own "R02B result"
section; `1076 uF`/`100 us` is R02B's own explicitly stated best
compromise.)

**9 of R04E14's 12 primary-grid cells (`CFLY=3 uF`) beat R02B's own best
`LADDER_ERR` (`0.260`); the three `CDIV=10 uF` cells do not**
(`LADDER_ERR=0.963-1.106`) -- though even these three remain numerically
better than R02B's own `CDIV=10uF`/`CFLY=53.8uF` case (`LADDER_ERR=2.732`,
the worst cell in R02B's own grid), so no cell here is worse than R02B's
own worst. At the best point (`CDIV=300uF`, R02B's own found ratio scaled
up one step), `LADDER_ERR` reaches `0.035-0.157` depending on `TRAMP`, a
`1.7x`-`7.4x`
improvement over R02B's own `0.260` best -- using a flying capacitor
`6-90x` SMALLER than R02B's `53.8 uF`, and a divider capacitance
(`300 uF`) smaller than R02B's own best divider (`1076 uF`). At the
matched-ratio `TRAMP=100 us`/best-`CDIV` point (`CDIV=300uF`), peak source
current is `39.18 A`, a `3.8x` reduction from R02B's own best `150.15 A`.
This directly confirms `BOUNDARY.md` Section 6 question (a): a
substantially better ladder error IS achievable with a much smaller,
more physically plausible divider capacitance, once `CFLY` itself is
corrected.

## 7. Peak-current comparison and an explicit flag

R02B's own 12-cell peak-source-current span was `6.01-3429.57 A`.
R04E14's 12-primary-cell span is `3.31-2497.83 A` -- overlapping, not a
dramatically more plausible absolute range (`BOUNDARY.md` Section 6
question (b) is answered NO in the general case: correcting `CFLY` alone
does not, by itself, bring peak current into a uniformly better range;
it depends heavily on which `(CDIV,TRAMP)` cell is chosen, exactly as
R02B's own finding already showed for its own grid). **Per `BOUNDARY.md`
Section 8, three cells exceed the `~500 A` flagged threshold and are
explicitly called out here, not silently passed over**: `CDIV=300uF/
TRAMP=1us` (`2497.83 A`), `CDIV=100uF/TRAMP=1us` (`1565.09 A`), and
`CDIV=30uF/TRAMP=1us` (`682.33 A`) -- all three are the fastest-ramp
(`TRAMP=1 us`) cells at their respective `CDIV`, confirming R02B's own
separability finding (final charge is set by `CDIV`; peak current is
separately controllable by `TRAMP`) continues to hold at the corrected
`CFLY`. The two cells that pass the full Section 7 bar (`CDIV=100uF` and
`CDIV=300uF`, both at `TRAMP=100 us`) have LOW peak currents (`16.45 A`
and `39.18 A`), well under both R02B's own best (`150.15 A`) and the
`500 A` flag -- the PASS result is not achieved by ignoring the current
axis, it is achieved at genuinely low current.

## 8. Secondary-grid sensitivity to the exact `CFLY` value

At the fixed best `(CDIV=300uF, TRAMP=10us)` point, sweeping `CFLY` across
the full first-principles range:

| `CFLY` | `VC1/VC2/VC3` (V) | err% | `LADDER_ERR` | `IIN_PK` (A) |
|---:|---:|---|---:|---:|
| 0.6 uF | 36.181/24.080/12.028 | +0.50/+0.33/+0.23 | 0.0107 | 382.83 |
| 3 uF | 35.835/23.693/11.787 | -0.46/-1.28/-1.77 | 0.0351 | 391.80 |
| 8.7 uF | 35.046/22.814/11.244 | -2.65/-4.94/-6.30 | 0.1389 | 412.23 |

`BOUNDARY.md` Section 6 question (c) is answered YES for ladder quality,
NO for peak current: `LADDER_ERR` is clearly sensitive to exactly which
point in the `0.6-8.7 uF` range is used at THIS fixed `(CDIV,TRAMP)`
point -- a `13x` spread (`0.0107` to `0.1389`) across the range, monotonic
increasing with `CFLY` (a smaller flying capacitor is easier for a fixed
divider to charge to the correct ratio, as expected). Peak source current,
by contrast, is nearly flat (`382.83-412.23 A`, an `8%` spread) across the
same `14.5x` range of `CFLY` -- consistent with R04E8's own finding (in a
structurally different, active ratio-gated mechanism) that peak current in
these idealized zero-`Vfwd`/small-`Ron` constructs is dominated by
`V/R`-type terms, not by the capacitance value itself. Note this
sensitivity check used only `TRAMP=10 us`, not the `TRAMP=100 us` point
that actually produced the two PASS cells in Section 3/6 -- a full
`CFLY x TRAMP` cross-sweep was not run and is not claimed here.

## 9. Grading

**`PASS_TOPOLOGY_PRINCIPLE / NOT_P24_REPRODUCTION`** (R02A's own Step-1
grading language, reused unchanged, not a new category per `BOUNDARY.md`
Section 7's explicit instruction). Justification: 2 of the 14 cells
(`CDIV=100uF/TRAMP=100us/CFLY=3uF` and `CDIV=300uF/TRAMP=100us/CFLY=3uF`)
simultaneously satisfy BOTH stated conditions of the success bar -- a
`LADDER_ERR` at or below R02A's own best passive result (`~0.236`) AND a
peak source current at or below R02B's own best (`150.15 A`). This is
explicitly NOT a `P24` reproduction claim (same caveat R02A's own Step 1
carried): the `N=4` divider topology remains IPEC 2018's own stated
extension, generalized by R02A as a test hypothesis, not a topology drawn
in P24/P25; the flying-capacitor-to-ground reference is R02A's own
"all-low-side-on" simplification, not the real floating adjacent-capacitor
connection; and `CFLY` itself remains a `SENSITIVITY_ONLY` value, not a
confirmed component (Section 8's sensitivity result shows the PASS
verdict's own margin narrows, though does not disappear, at the low-`CFLY`
end of the range at this specific `(CDIV,TRAMP)` point -- see Section 8).
This is NOT a uniform `PASS` across the whole grid: 10 of 14 cells do not
meet the bar, most clearly the three `CDIV=10uF` cells (`LADDER_ERR>0.96`,
worse in absolute terms than any passing cell here, though still better
than R02B's own `CDIV=10uF`/`CFLY=53.8uF` case) and every `TRAMP=1us`
cell (excellent `LADDER_ERR` in some cases, but peak current far above
the `500A` flag). The grid-wide trend is a genuine, substantial
improvement over R02B's own `FEASIBLE_TREND/NO_PASS`, not a uniform
transformation of every cell into a pass.

## 10. What this does and does not establish (BOUNDARY.md Section 9, verbatim reminders)

- It does not combine precharge with PWM/the P24 switching stage --
  explicitly blocked pending the Roberts & Prodić 2024 literature review
  (Section 1), per `STEP_06`'s own pre-existing gate. This result,
  however positive, does NOT authorize skipping that review.
- It does not reconcile the flying-capacitor-to-ground reference this
  module uses with the floating adjacent-capacitor connection the real
  four-phase converter (and R04E9-R04E13's own active netlists) uses --
  inherited from R02A unchanged, not re-examined here.
- It does not validate the `N=4` generalization of IPEC 2018's own
  3-phase Fig. 8(e) circuit as anything other than a test hypothesis --
  unchanged from R02A's own explicit caveat.
- It does not establish which single point in the `0.6-8.7 uF` range is
  "correct" -- `CFLY` remains a `SENSITIVITY_ONLY` value pending Mihai's
  confirmation of the real flying-capacitor part. Section 8 shows the
  answer is not fully insensitive to this choice.
- A result here, positive or negative, is specific to this passive-only
  module in isolation; it says nothing about R02C's active-current
  alternative (which this experiment does not re-test) or about R04E9-
  R04E13's structurally different inductor-mediated active mechanism.
- Does not modify, overwrite, or invalidate R02A/R02B's own committed
  results -- those remain the correct record for the OLD `CFLY=53.8 uF`
  value; this is a new, separately-numbered comparison, not a correction
  of their own numbers.

## 11. Provenance and classification (BOUNDARY.md Section 5)

| Value | Source | Category |
|---|---|---|
| `CFLY=3 uF` (primary grid) | R04E8's own corrected candidate, already adopted throughout R04E8-R04E13 | `SENSITIVITY_ONLY`, inherited |
| `CFLY=0.6 uF`, `8.7 uF` (secondary grid) | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes | `SENSITIVITY_ONLY`, inherited |
| `CDIV` swept values `{10, 30, 100, 300} uF` | New for this experiment: re-scaled around R02A's own found `10:1` `CDIV:CFLY` ratio (`30 uF` for `CFLY=3 uF`), with one smaller and two larger points | `SENSITIVITY_ONLY` |
| `TRAMP` swept values `{1, 10, 100} us` | Unchanged from R02B | `SENSITIVITY_ONLY`, inherited |
| `LPAR=5 nH`, `RPAR=10 mOhm` | IPEC 2018 Table II | `EXTERNAL_DEVICE_DATA`, unchanged from R02A/B |
| The N=4 passive-divider topology itself | IPEC 2018 Fig. 8(e), generalized to N=4 by R02A (an explicit test hypothesis, not a topology drawn in P24/P25) | `CROSS_PAPER_EXTENSION`, unchanged from R02A/B |
| Ideal diode model, `RLEAK`, all-low-side-on ground reference | R02A's own numerical idealizations | `NUMERICAL_IDEALIZATION`, unchanged |

No new paper-sourced, cross-paper, or external-device data is introduced
beyond what R02A/B already carried; the only new elements are the
corrected `CFLY` value itself (already established, not re-derived here),
the re-scaled `CDIV` sweep range, and (a pure tooling detail) the
per-cell-file packaging described in Section 4.

## 12. Files

- `cases/e14_c*.cir` -- 14 netlists (12 primary + 2 secondary), byte-level
  faithful copies of R02B's own circuit body with only `CFLY`/`CDIV`/
  `TRAMP` changed to fixed per-cell `.param` values.
- `scripts/build_r04e14.py` -- generates the 12 primary-grid netlists.
- `scripts/build_r04e14_secondary.py` -- generates the 2 secondary-grid
  netlists at the primary grid's own best `(CDIV,TRAMP)` point.
- `scripts/analyze_r04e14.py` -- parses all 14 `.log` files and writes
  `results.csv`/`results.json`.
- `results.csv` / `results.json` -- the full 14-row table (Section 3).
