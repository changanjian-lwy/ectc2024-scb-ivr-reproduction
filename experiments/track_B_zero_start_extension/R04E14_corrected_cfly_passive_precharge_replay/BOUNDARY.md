# R04E14 - corrected-Cfly replay of the R02A/R02B passive-precharge module (BOUNDARY)

## 1. Parent and why this experiment exists

**R02A/R02B** (`paper_locked/02_ectc2024_main/STEP_06_R02_LITERATURE_STARTUP_MODULE.md`,
netlists `paper_locked/02_ectc2024_main/spice/R02A_ipec2018_passive_precharge_only.cir`
and `R02B_passive_precharge_charge_ramp_sweep.cir`) tested a purely passive
startup module (IPEC 2018 Fig. 8(e)'s N-level input-divider + ideal-diode
extension, generalized to `N=4`), isolated from any PWM/active control,
using the EPE2019-Table-I-sourced `CFLY=53.8 uF` value. Both R02A and R02B
found this passive network badly UNDERCHARGES that flying-capacitor value
(`R02A`: `VC1/VC2/VC3=7.62/1.06/0.14 V` vs. `36/24/12 V` targets, `-79%` to
`-99%` error; `R02B`'s best of 12 swept cells, `CDIV=1076 uF`,
`TRAMP=100 us`, still only reaches `34.05/21.79/10.63 V`, `-5.4%` to
`-11.4%` error, at `150 A` source peak) -- a `FAILED_CAPACITANCE_TRANSFER`
/ `NO PASS CLAIM` result.

**This session's own 2026-09-15 audit** (`paper_locked/00_boundaries/
CURRENT_ASSUMPTION_CROSSCHECK.md` "Flying capacitor" row,
`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`) found `53.8 uF` is a cross-topology
provenance error (EPE2019 Table I is that paper's own CSC-buck prototype
parts list, not a value for P24's conventional SC buck), and derived an
independent, first-principles candidate range of `~0.6-8.7 uF` from P24's
own operating point -- already adopted as `CFLY=3 uF` throughout
R04E8-R04E13. **R02A/R02B's own passive-precharge-only conclusion has
never been re-tested against this corrected value.** Since R02A/B's own
stated failure mode was explicitly diagnosed as "a charge-budget and
capacitance-ratio failure" (STEP_06 R02A section) -- i.e. the passive
divider could not supply enough charge for the (oversized) `53.8 uF`
target -- and the corrected value is `6-90x` smaller, this experiment
exists to determine whether that specific failure mode still holds once
the flying-capacitor target itself is corrected. This is a single
conceptual change (swap `CFLY`, and re-scale the swept `CDIV` range to
match, per Section 4) on an otherwise UNCHANGED, already-documented
circuit -- not a new startup-circuit design.

Per explicit user direction 2026-09-16: this is Track B's candidate
direction (b) (R04E9 `RESULTS.md` Section 11), pursued in parallel with a
literature review of the four-phase release/handoff sequence paper P25
directly cites (Roberts & Prodić 2024, DOI `10.1109/OJPEL.2024.3417017`)
-- that review is a SEPARATE task, not part of this experiment, and per
`STEP_06`'s own "Next hard gate - PWM takeover" section, **this experiment
does NOT combine precharge with PWM/the P24 switching stage** -- that
remains explicitly blocked until the release-sequence literature review
is complete, exactly as `STEP_06` already required before any R02C-style
handoff was attempted.

## 2. What changed relative to R02A/R02B, exactly

**Single conceptual change**: `CFLY` is swapped from `53.8 uF`
(cross-topology-suspect) to the corrected candidate value(s) this
project's own Track-B lineage already adopted, and `CDIV` is re-swept over
a range re-scaled to match (Section 4) -- because R02A's own finding
("the IPEC prototype works near a `CDIV:CFLY=10:1` scale") is a RATIO
finding, not an absolute one, so re-testing at the old absolute `CDIV`
values against a `6-90x` smaller `CFLY` would not isolate the same
question. Every other element of R02A/R02B's own circuit is copied
UNCHANGED: the four-equal-input-divider-capacitor topology, `LPAR=5 nH`/
`RPAR=10 mOhm` source parasitics (IPEC 2018 Table II, unchanged
cross-source candidate), the three ideal precharge diodes (`Ron=1m
Roff=1T Vfwd=0`), the flying capacitors' lower terminals held at the
module reference (R02A's own explicit "all-low-side-on precharge state"
approximation, NOT re-derived here), true-zero-energy initial conditions
(`UIC`, no `36/24/12 V` IC statements), and the absence of any PWM,
high-side switch, or output load (this remains, exactly as R02A/B were,
an isolated startup-module-only test, not a P24 reproduction).

## 3. What did not change

- The IPEC-2018-Fig.-8(e) four-level passive-divider-plus-diode topology
  itself -- copied unchanged from R02A/R02B.
- `LPAR=5 nH`, `RPAR=10 mOhm` (IPEC 2018 Table II) -- unchanged cross-source
  candidate, not re-derived or re-justified here.
- Ideal diode model (`Ron=1m Roff=1T Vfwd=0`), `RLEAK=1G` DC-reference
  leakage -- unchanged.
- True-zero-energy initial conditions, no PWM, no high-side switches, no
  output load -- unchanged; this remains an isolated startup-module test.
- The flying capacitors' lower terminals tied to the module reference
  (ground) -- R02A's own stated simplification for "the all-low-side-on
  precharge state"; NOT the same as the real converter's floating
  adjacent-capacitor connection the active R04E9-R04E13 netlists use.
  This experiment inherits R02A's own simplification unchanged and does
  not attempt to reconcile the two circuit models against each other.

## 4. Swept grid

**Primary grid** (mirrors R02B's own `CDIV x TRAMP` table shape exactly,
for direct before/after comparability, with `CDIV`'s range shifted down
to match the corrected `CFLY`): `CFLY=3 uF` fixed (this project's own
standing corrected candidate, R04E8's value) x `CDIV` in `{10, 30, 100,
300} uF` (re-scaled around R02A's own found `10:1` ratio, i.e. `30 uF`,
plus one smaller and two larger points, replacing R02B's `{10, 53.8, 538,
1076} uF` which was scaled for the old `53.8 uF` target) x `TRAMP` in
`{1, 10, 100} us` (unchanged from R02B) = 12 cells.

**Secondary grid**: at the single best-performing `(CDIV, TRAMP)` cell
from the primary grid by normalized ladder error (R02B's own metric,
Section 6), re-run with `CFLY` at the two extremes of this project's own
first-principles candidate range (`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`):
`0.6 uF` and `8.7 uF`, 2 more cells -- to bound how the answer changes
across the full derived range, since `CFLY` itself remains an unconfirmed
sensitivity value, not a settled one.

Total: 14 cells.

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `CFLY=3 uF` (primary grid) | R04E8's own corrected candidate, already adopted throughout R04E8-R04E13 | `SENSITIVITY_ONLY`, inherited |
| `CFLY=0.6 uF`, `8.7 uF` (secondary grid) | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own derived range extremes | `SENSITIVITY_ONLY`, inherited |
| `CDIV` swept values `{10, 30, 100, 300} uF` | New for this experiment: re-scaled around R02A's own found `10:1` `CDIV:CFLY` ratio (`30 uF` for `CFLY=3 uF`), with one smaller and two larger points | `SENSITIVITY_ONLY` |
| `TRAMP` swept values `{1, 10, 100} us` | Unchanged from R02B | `SENSITIVITY_ONLY`, inherited |
| `LPAR=5 nH`, `RPAR=10 mOhm` | IPEC 2018 Table II | `EXTERNAL_DEVICE_DATA`, unchanged from R02A/B |
| The N=4 passive-divider topology itself | IPEC 2018 Fig. 8(e), generalized to N=4 by R02A (an explicit test hypothesis, not a topology drawn in P24/P25) | `CROSS_PAPER_EXTENSION`, unchanged from R02A/B |
| Ideal diode model, `RLEAK`, all-low-side-on ground reference | R02A's own numerical idealizations | `NUMERICAL_IDEALIZATION`, unchanged |

**No new paper-sourced, cross-paper, or external-device data is
introduced** beyond what R02A/B already carried; the only new element is
the corrected `CFLY` value itself (already established, not re-derived
here) and the re-scaled `CDIV` sweep range.

## 6. What question this experiment is meant to answer

Does correcting `CFLY` from the cross-topology-suspect `53.8 uF` to this
project's own `0.6-8.7 uF` first-principles range change R02A/B's own
`FAILED_CAPACITANCE_TRANSFER` verdict for the passive-divider-only startup
module? Specifically: (a) can some `(CDIV, TRAMP)` combination reach a
substantially better ladder error than R02B's own best (`0.260` normalized
error at `CDIV=1076 uF`/`TRAMP=100 us` against the old `53.8 uF` target)
using a much smaller, more physically plausible divider capacitance; (b)
does peak source/diode current fall to a more plausible range than R02B's
own `19-3430 A` span; (c) does the answer depend sensitively on exactly
which point in the `0.6-8.7 uF` first-principles range is used?

## 7. Success condition

`PASS_TOPOLOGY_PRINCIPLE`-style success (R02A's own Step-1 grading
language): a cell reaches a normalized ladder error comparable to or
better than R02A's own best passive result (`Step 1`, `CFLY=1 uF`,
errors `-1.41%/-8.93%/-13.27%`) at a peak current at least as favorable as
R02B's best (`150.15 A` at `CDIV=1076 uF`/`TRAMP=100 us`), using the
corrected `CFLY`. `FEASIBLE_TREND`-style partial success (R02B's own
grading language): a clear, monotonic improvement trend exists but no
cell reaches that bar. `FAILED_CAPACITANCE_TRANSFER` (unchanged verdict):
no meaningful improvement over R02B's own old-`CFLY` results even after
the correction -- a legitimate, informative negative result if that is
what the data shows, per Ground Rule 7.

## 8. Failure conditions

- Peak source or diode current at any tested cell exceeds a clearly
  unphysical range (this module has no established safety bound the way
  the active R04E-series netlists have `+/-250 A`; report the actual
  magnitude and flag anything above `~500 A`, R02B's own upper range, as
  requiring explicit comment, not a hard pass/fail cutoff).
- No meaningful improvement over R02B's own results -- reported plainly,
  not forced into a favorable reading.
- Solver non-convergence -- reported as its own outcome.

## 9. What this experiment cannot prove

- It does not combine precharge with PWM/the P24 switching stage --
  explicitly blocked pending the Roberts & Prodić 2024 literature review
  (Section 1), per `STEP_06`'s own pre-existing gate. A result here,
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
  confirmation of the real flying-capacitor part.
- A result here, positive or negative, is specific to this passive-only
  module in isolation; it says nothing about R02C's active-current
  alternative (which this experiment does not re-test) or about R04E9-
  R04E13's structurally different inductor-mediated active mechanism.
- Does not modify, overwrite, or invalidate R02A/R02B's own committed
  results -- those remain the correct record for the OLD `CFLY=53.8 uF`
  value; this is a new, separately-numbered comparison, not a correction
  of their own numbers.
