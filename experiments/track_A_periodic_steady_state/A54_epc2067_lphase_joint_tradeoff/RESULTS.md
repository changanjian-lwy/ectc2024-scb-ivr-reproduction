# A54 result - joint device+inductance search: does EPC2067 find a net-positive ZVS balance at rated load?

Track: A. Python-solver experiment (no SPICE run). Boundary: `BOUNDARY.md` in
this directory, unmodified by this run.

---

## 0. Verdict, stated first

**Confirmed before bisecting** (`BOUNDARY.md` Section 3 step 2's own "confirm,
not assume" instruction): at EPC2067's own device parameters (`Ron=1.55
mOhm`, `CH_TOTAL=3720 pF`, `CL_TOTAL=5580 pF`) and the paper's own nominal
`LPHASE=1.4666667 nH`, all four phases hard-switch at P24's rated `250 W`
(natural ZVS flags `F/F/F/F`, converged, residual `2.633e-08`) -- exactly the
same qualitative starting point A53 found with GS61008T.

A critical `LPHASE` was found by bisection at which all four phases first
achieve natural ZVS at `250 W`:

> **`LPHASE_critical = 0.62741 nH`, a `57.22 %` reduction from the paper's
> own nominal `1.4666667 nH`** -- confirmed converged (Newton relative
> residual `2.571e-09`) and confirmed all-four-ZVS across a `{5, 2, 1, 0.5}
> ps` sub-step ladder with no disagreement between rungs.

`BOUNDARY.md` Section 1's own pre-stated `~3x` capacitance-driven threshold
estimate is directly confirmed, and if anything understated: the required
reduction (`57.22 %`) is **more than 3x** A53's own GS61008T reduction
(`18.44 %`), not merely proportionally larger.

**The net Watts comparison is still decisively negative, but MATERIALLY LESS
NEGATIVE than A53's own GS61008T result:**

> | | nominal (hard-switch) | critical (ZVS) | `10 %` margin (ZVS) |
> |---|---:|---:|---:|
> | `LPHASE` | `1.46667 nH` | `0.62741 nH` (`-57.22 %`) | `0.56467 nH` (`-61.50 %`) |
> | conduction loss (`I_rms^2 * 1.55 mOhm`, 4 phases) | `26.94 W` | `65.67 W` | `77.09 W` |
> | capacitive switching loss eliminated | -- | `17.98 W` | `17.98 W` |
> | **net Watts (switching saved - conduction added)** | -- | **`-20.75 W`** | **`-32.17 W`** |

**This is `BOUNDARY.md` Section 5's FIRST named outcome, "less bad" case**:
the conduction-loss penalty still exceeds the capacitive switching-loss saved
(by `1.2x`-`1.8x`, not the `18x`-`27x` A53 found), so achieving ZVS at rated
load via EPC2067 + a re-bisected `LPHASE` remains **not a net efficiency
win** under this project's own partial loss model -- but it is a genuine,
quantified **improvement over GS61008T on the SAME lever**: net Watts moves
from `-38.43 W`/`-56.45 W` (A53, GS61008T) to `-20.75 W`/`-32.17 W` (A54,
EPC2067), an improvement of `17.68 W` at critical and `24.29 W` at margin.
EPC2067's `4.5x` lower resistance does help, materially -- it is just not
enough, on its own plus a re-bisected `L`, to flip the sign of the tradeoff at
P24's own rated `250 W` load, because the `~7-9x` larger switch capacitance
both raises the switching-loss ceiling that can be "saved" AND forces a much
deeper `LPHASE` cut (hence far more ripple current and far more conduction
loss) to reach it.

Every phase current stayed within the `+/-250 A` safety bound throughout the
ENTIRE search (not just the three reported points), but with **much less
margin than A53's own GS61008T search**: the maximum observed anywhere among
ACTUAL SOLVED (Newton-accepted) candidates was `232.54 A` (at the margin
point's own bisection-script solve), `93.0 %` of the limit, only `7.0 %`
headroom -- vs A53's `60.1 %`/`40 %` headroom. This is reported plainly as a
real, quantitative safety-margin cost of the much deeper `LPHASE` reduction
EPC2067 requires (Section 5 below).

---

## 1. Method actually used

Structurally identical to `A53`'s own method (`BOUNDARY.md` Section 3 step 1
requires this): `a54_boundary.py` is a new, sibling local wrapper (NOT an
edit to A53's own `a53_boundary.py`) that reuses A51's own
`a51_period_map.py` functions read-only via `sys.path`, with EPC2067's own
device parameters plugged in (`switch_on_resistance_ohm` stays at the
near-ideal `1e-6` default for the SOLVER's own dynamics, exactly as A51/A53
do; the conduction-loss `Ron=1.55 mOhm` is a separate, post-hoc estimate
applied downstream). `run_bisection.py` and `run_three_point_analysis.py`
import A53's own `a53_solve.py` (its `solve_fixed_point`/`RmsMonitor`/
`evaluate_period_map_with_rms` machinery) READ-ONLY via `sys.path` --
verified beforehand that this module is fully device-agnostic (it accepts a
`boundary` object and never references any device parameter by name), so
reusing it via read-only import (the SAME discipline already used for A51's
own module) avoids duplicating ~450 lines of generic Newton+Picard search
code without touching A53's own file.

**Step 1 (confirm, not assume):** at EPC2067's own parameters and nominal
`LPHASE`, one Newton solve from A37's own seed confirmed all-four hard-switch
(Section 0 above) before any bisection began, per `BOUNDARY.md` Section 3
step 2's explicit instruction.

**Step 2 (diagnostic probe):** exactly as A53 did, a raw one-shot evaluation
of A37's own fixed seed state (NOT Newton-solved) was run across twelve
`LPHASE` values under EPC2067's parameters. It shows the raw seed itself
exceeds `+/-250 A` once `LPHASE` drops below roughly **`0.65 nH`** --
essentially the SAME threshold A53 found with GS61008T (`~0.6-0.65 nH`),
confirming this raw-seed instability is driven by the phase INDUCTANCE
dynamics (how fast current changes for a given voltage, independent of
switch capacitance), not by the device swap. Continuation is therefore
required below that point, for the same reason A53 already established.

**Step 3 (continuation ladder + bisection):** each `LPHASE` candidate below
nominal was warm-started from the immediately preceding, already-converged
fixed point (never re-seeded from A37's own raw values below the first
step). A `10 %` multiplicative step-down ladder walked from nominal; **no
step ever tripped the safety bound or needed the halving safeguard** -- every
continuation step converged safely on its first attempt, `"attempts": 1`
throughout. Given `BOUNDARY.md`'s own `~3x`-threshold warning, `FLOOR_LPHASE_H`
was set to `0.08 nH` in this experiment's own script (well below A53's own
`0.4 nH` floor, since the crossing point was not known in advance) -- **the
crossing was found at `0.5682 nH`, well above this floor, so the bracket was
never actually widened past the originally-proposed `0.5 nH` starting
candidate** (`bracket_was_widened_past_proposed_start: false` in
`bisection_search.json`); the wider floor was a precaution that, as it
turned out, was not needed. Five further bisection iterations (each
candidate's ZVS verdict checked at both `5 ps` and `1 ps` sub-steps, `2 ps`
reserved for any disagreement -- none occurred) narrowed the critical
`LPHASE` to `[0.62741, 0.62938] nH` (`0.31 %` of nominal, inside the
`0.2 %`-of-nominal tolerance target). A `10 %`-further margin point
(`0.56467 nH`, `61.50 %` below nominal) was solved the same way and confirmed
all-four ZVS (residual `5.379e-10`).

The nominal point's residual, `2.633e-08`, is a fresh solve (not expected to
match A51's own `2.258e-11` bit-for-bit, since EPC2067's device parameters
change the boundary being solved) -- included here as this experiment's own
convergence check, not a fidelity cross-check against A51 the way A53's own
device-unchanged nominal residual was.

---

## 2. Bisection search history

| Step | `LPHASE (nH)` | Converged | Residual | ZVS (1/2/3/4) | max\|iL\| (A) |
|---|---:|---|---:|---|---:|
| nominal (A37-seeded) | `1.46667` | yes | `2.633e-08` | F/F/F/F | `117.51` |
| ladder 1 | `1.32000` | yes | `2.435e-11` | F/F/F/F | `125.57` |
| ladder 2 | `1.18800` | yes | `1.242e-11` | F/F/F/F | `133.91` |
| ladder 3 | `1.06920` | yes | `1.762e-11` | F/F/F/F | `143.29` |
| ladder 4 | `0.96228` | yes | `1.554e-11` | F/F/F/F | `153.88` |
| ladder 5 | `0.86605` | yes | `1.266e-11` | F/F/F/F | `165.84` |
| ladder 6 | `0.77945` | yes | `2.983e-11` | F/F/F/F | `179.39` |
| ladder 7 | `0.70150` | yes | `2.404e-07` | F/F/F/**T** | `194.76` |
| ladder 8 | `0.63135` | yes | `1.762e-09` | F/F/F/**T** | `212.12` |
| ladder 9 | `0.56822` | yes | `1.698e-12` | **T/T/T/T** | `231.33` |
| bisect 1 | `0.59978` | yes | `6.631e-10` | **T/T/T/T** | `215.34` |
| bisect 2 | `0.61557` | yes | `8.362e-08` | **T/T/T/T** | `208.79` |
| bisect 3 | `0.62346` | yes | `1.909e-09` | **T/T/T/T** | `205.71` |
| bisect 4 | `0.62741` | yes | `2.571e-09` | **T/T/T/T** | `204.52` |
| bisect 5 | `0.62938` | yes | `2.948e-10` | F/T/T/T | `204.00` |
| margin (0.9x critical) | `0.56467` | yes | `5.379e-10` | **T/T/T/T** | `232.54` |

Every ladder and bisection row's ZVS verdict was confirmed identical at both
`5 ps` and `1 ps` sub-steps (`sub_step_convergence_disagreement: false` on
every row in `bisection_search.json`). Ladder step ratio was `0.9` and
`"attempts": 1` on every row -- the adaptive step-halving safeguard was never
triggered, exactly as in A53.

**Phase 1 is again the last to achieve ZVS** as `LPHASE` shrinks (bisect 5
flips phase 1 back to hard-switching while 2/3/4 remain ZVS), matching A51's
and A53's own finding that phase 1 carries the largest participating
capacitance (node `a1` holds two high-side switches) and is structurally the
hardest phase to commutate -- this structural finding is device-independent,
confirmed again here with EPC2067's own numbers.

The full ladder-and-bisection history, the diagnostic probe, and the
per-candidate safety log are in `bisection_search.json`. The three converged
states used below (`nominal`, `critical`, `margin`) are persisted in
`key_states.json`.

---

## 3. Three-point table: convergence, ZVS, currents, losses

All three points solved with the full search-plus-report rigor: Newton to
the saved seed's own fixed point, a `25`-iteration damped-Picard cross-check
from the same seed, and a `{5, 2, 1, 0.5} ps` sub-step ladder on the ZVS
verdict.

| | nominal | critical | margin (`10%` below critical) |
|---|---:|---:|---:|
| `LPHASE (nH)` | `1.46667` | `0.62741` | `0.56467` |
| reduction from nominal | -- | `57.22 %` | `61.50 %` |
| Newton converged | yes | yes | yes |
| Newton relative residual | `2.633e-08` | `2.571e-09` | `5.379e-10` |
| natural ZVS (1/2/3/4) | F/F/F/F | **T/T/T/T** | **T/T/T/T** |
| sub-step ladder consistent (4 rungs) | yes | yes | yes |
| peak \|iL\| per phase (A) | `113.53/113.34/113.34/115.84` | `204.55/203.91/203.91/203.80` | `222.74/221.99/221.99/222.21` |
| RMS iL per phase (A) | `65.52/65.37/65.37/67.38` | `103.09/102.83/103.12/102.63` | `111.67/111.37/111.61/111.37` |
| conduction loss, 4 phases (`I_rms^2*1.55mOhm`) | `26.94 W` | `65.67 W` | `77.09 W` |
| max \|iL\| observed at this point (A) | `115.82` | `204.52` | `222.70` |

RMS current is the actual time integral of the solved periodic waveform
(right-endpoint, time-weighted, `1 ps` sub-step inside every dead-time
window, `62.5 ps` elsewhere), via A53's own `RmsMonitor`/
`evaluate_period_map_with_rms`, imported read-only -- not an estimate from
peak and average.

**Capacitive switching loss (nominal/hard-switching point only)**, per
`BOUNDARY.md` Section 3 step 4, using EPC2067's OWN measured participating
capacitance and hard-switch residual voltage, measured DIRECTLY at this run's
own nominal `z*` (via `measure_node_capacitance_f`, A51's own function,
imported read-only, fed each phase's own turn-on-window ENTRY state -- the
same fix A53 needed, since the raw period-start state sits in a different
switch-mode branch and gives nonsense) at `f_sw = 5 MHz`. **Unlike A53, this
could NOT be reused from A51's own published `final_verification.json`** --
that file's own measured capacitances (`1539/1539/1539/1154 pF`) are
GS61008T-specific (`385/770 pF` raw switch capacitance) and do not apply to
EPC2067's `3720/5580 pF`; measuring fresh here is the only correct option for
this device, and is exactly what `BOUNDARY.md` Section 3 step 4 asks for:

| Phase | measured `C_phase` (this run) | `Vds` at forced turn-on (this run) | `0.5*C*V^2*f_sw` |
|---|---:|---:|---:|
| 1 | `12944.72 pF` | `12.0682 V` | `4.7132 W` |
| 2 | `12888.22 pF` | `12.1693 V` | `4.7716 W` |
| 3 | `12891.80 pF` | `12.1687 V` | `4.7725 W` |
| 4 | `9243.03 pF` | `12.6969 V` | `3.7252 W` |
| **total** | | | **`17.9825 W`** |

The per-phase pattern reproduces A51's own structural finding exactly:
phases 1-3 (node `a1`/`a2`/`a3`, each carrying two high-side switches in
series with a flying capacitor) commutate noticeably more capacitance than
phase 4 (`~12.9 nF` vs `~9.2 nF`, a `1.39x` ratio -- close to A53's own
`1539/1154 = 1.33x` ratio with GS61008T), and phase 4's own measured value
(`9243 pF`) sits almost exactly at `CH_TOTAL+CL_TOTAL = 3720+5580 = 9300 pF`
(a `0.6 %` difference), the same clean structural match A53 found for
GS61008T (`1154 pF` measured vs `1155 pF` raw sum).

---

## 4. The net Watts comparison, and the explicit comparison against A53

| | critical | margin |
|---|---:|---:|
| capacitive switching loss eliminated | `17.983 W` | `17.983 W` |
| conduction loss increase (vs. nominal) | `38.731 W` | `50.148 W` |
| **net Watts (saved - added)** | **`-20.749 W`** | **`-32.166 W`** |

Both remain decisively negative -- the conduction-loss penalty is still
`1.2x`-`1.8x` larger than the switching-loss saved, not a close call this
estimate's own uncertainty could plausibly flip. But this is a MUCH smaller
gap than A53 found with GS61008T (`18x`-`27x`).

**Direct side-by-side against A53's own already-published GS61008T numbers**
(`BOUNDARY.md` Section 3 step 5, the actual point of this experiment):

| | GS61008T (A53) | EPC2067 (A54, this run) | delta (EPC2067 - GS61008T) |
|---|---:|---:|---:|
| `Ron` (uniform, raw single-device) | `7 mOhm` | `1.55 mOhm` | `-4.5x` |
| `CH_TOTAL` / `CL_TOTAL` | `385 pF` / `770 pF` | `3720 pF` / `5580 pF` | `~9.7x` / `~7.2x` |
| critical `LPHASE` | `1.19625 nH` | `0.62741 nH` | |
| critical reduction from nominal | `18.44 %` | `57.22 %` | `+38.78 pp` (`3.10x` larger cut) |
| margin `LPHASE` | `1.07663 nH` | `0.56467 nH` | |
| margin reduction from nominal | `26.59 %` | `61.50 %` | `+34.91 pp` (`2.31x` larger cut) |
| conduction loss, nominal | `113.09 W` | `26.94 W` | `-86.15 W` (`4.2x` lower, tracks `Ron`) |
| conduction loss, critical | `153.61 W` | `65.67 W` | `-87.94 W` |
| conduction loss, margin | `171.63 W` | `77.09 W` | `-94.54 W` |
| capacitive switching loss eliminated | `2.087 W` | `17.983 W` | `+15.90 W` (`8.6x` higher, tracks capacitance) |
| conduction loss increase, critical | `40.513 W` | `38.731 W` | `-1.78 W` (essentially a wash) |
| conduction loss increase, margin | `58.540 W` | `50.148 W` | `-8.39 W` |
| **net Watts, critical** | **`-38.426 W`** | **`-20.749 W`** | **`+17.677 W` (less bad)** |
| **net Watts, margin** | **`-56.453 W`** | **`-32.166 W`** | **`+24.287 W` (less bad)** |
| safety maximum over whole search | `150.13 A` (`60.1 %` of limit) | `232.54 A` (`93.0 %` of limit) | far less headroom |

**Reading this plainly:** EPC2067's `4.5x` lower resistance drives conduction
loss down sharply at every fixed `LPHASE` (nominal conduction loss `4.2x`
lower), and this is the dominant reason net Watts improves. But the
`~8x`-higher capacitance does two things that work AGAINST the device swap
at the same time: (a) it raises the switching-loss "prize" being chased
(`17.98 W` vs `2.09 W`, `8.6x` higher -- a bigger number to save, but also a
sign the device is intrinsically less ZVS-friendly), and (b) critically, it
forces a `>3x` DEEPER `LPHASE` cut to actually reach that ZVS threshold,
which drives RMS ripple current (hence conduction loss) up almost as much as
the lower `Ron` drives it down -- the conduction-loss INCREASE from nominal
to critical is `40.51 W` (GS61008T) vs `38.73 W` (EPC2067), **essentially
unchanged**, because the `Ron` reduction and the ripple-current increase
from the much deeper `L` cut largely cancel in the *increase* (though not in
the *absolute level*, which stays lower throughout thanks to the lower
`Ron`). The net improvement in the Watts comparison comes almost entirely
from the switching-loss side (`+15.90 W` eliminated) plus a small conduction
help (`-1.78 W`/`-8.39 W` smaller increase), NOT from conduction loss being
generally lower (that helps the ABSOLUTE loss level at every point, but
barely helps the tradeoff's sign because the comparison is against nominal,
which is also `Ron`-scaled down by the same `4.5x`).

**This is `BOUNDARY.md` Section 5's first named outcome's "less bad" case,
stated honestly**: EPC2067 + a re-bisected `LPHASE` is a genuine, quantified
improvement over A53's own GS61008T result on the identical lever (roughly
halving the net loss at both the critical and margin points), but it does
NOT flip the sign -- achieving ZVS at P24's own rated `250 W` load is still
not shown to be a net efficiency win with EITHER device under this project's
own partial loss model. P24's own Table-3-specified device for this
operating point is a better choice than GS61008T for this specific tradeoff,
but "better" here means "less bad," not "good."

---

## 5. Safety

Every phase current was checked against `+/-250 A` at every sub-step of
every one-period evaluation used in the ACTUAL search (the nominal solve,
every ladder and bisection candidate including Newton's own finite-difference
Jacobian probes and line-search trials, and the margin point):

> **Maximum `|iL|` observed anywhere among ACTUAL SOLVED (Newton-accepted)
> candidates in the entire search: `232.54 A`** (at the margin point's own
> solve inside `run_bisection.py`), **`93.0 %`** of the `+/-250 A` limit,
> **`7.0 %`** headroom remaining. No accepted candidate ever exceeded the
> bound, and the adaptive step-halving safeguard was never triggered -- every
> continuation step converged safely on its first attempt (`"attempts": 1`
> on every ladder row).

This headroom is **much tighter than A53's own `40 %`** (GS61008T's
`150.13 A` max, `60.1 %` of the limit) -- a direct, quantified consequence of
the much deeper `LPHASE` cut EPC2067's higher capacitance requires: smaller
`LPHASE` means more ripple current at the same average load current, and
EPC2067's critical point sits at `57 %` below nominal vs GS61008T's `18 %`.
This is worth flagging as a real engineering cost of the EPC2067 route, even
though it was not asked to be quantified as a loss term: less safety margin
against overcurrent at the SAME `250 A` bound, for the same rated load.

**On the diagnostic probe's own raw (un-Newton-solved) readings**: exactly
as A53 found with GS61008T, the RAW SEED ITSELF (never an accepted
candidate, never fed forward, evaluated once with no Newton correction
purely to motivate the continuation method) exceeds `+/-250 A` once `LPHASE`
drops below roughly `0.65 nH`, reaching as high as `775 A` at `0.2 nH` --
this is reported plainly in `bisection_search.json["diagnostic_probe"]` and
is NOT a violation by any candidate this search actually used; it is the
reason continuation (not raw re-seeding) was required, exactly as A53's own
precedent established. This threshold (`~0.65 nH`) is essentially the SAME
value A53 found (`~0.6-0.65 nH`) despite the completely different device
capacitance, confirming (as expected from the physics) that the raw-seed
instability is driven by the phase inductance's own dynamics, not by the
switch capacitance.

---

## 6. Provenance (repeats `BOUNDARY.md` Section 4, filled in)

| Value | Source | Category |
|---|---|---|
| `EPC2067_RDS_TYP_25C=1.55 mOhm` | `paper_locked/04_component_models/EPC2067_typical_params.lib`, EPC datasheet rev. 2021-10-21 | `EXTERNAL_DEVICE_DATA` |
| `EPC2067_COTR_0_20V=1860 pF` | Same source | `EXTERNAL_DEVICE_DATA`, `0-20V`-vs-`~12V`-actual extrapolation caveat inherited unresolved |
| `NHS=2`, `NLS=3` | `paper_locked/04_component_models/EPC2067_commutation_capacitance.lib`, P24's own printed Table 3, `nP=4`/`nM=4` row | `P24_EXPLICIT` |
| `module_power_w = 250 W` | fixed throughout, P24's own rated load | `P24_EXPLICIT` |
| `LPHASE` nominal `1.4666667 nH` | unchanged from `A24-A53` | `P24_EXPLICIT`-adjacent |
| `LPHASE_critical = 0.62741 nH` | found by bisection here | `SENSITIVITY_ONLY` |
| `LPHASE_margin = 0.56467 nH` (`10%` below critical) | derived from the above | `SENSITIVITY_ONLY` |
| `Ron = 1.55 mOhm` uniform (conduction-loss estimate only; the SOLVER itself keeps A51's own `1 uOhm` idealized `switch_on_resistance_ohm`) | `BOUNDARY.md` Section 2, mirroring A51/A53's own simplification | `NUMERICAL_IDEALIZATION`, inherited |
| Conduction-loss formula (`I_rms^2*Ron`) | textbook | `NUMERICAL_IDEALIZATION` |
| Capacitive switching-loss formula (`0.5*C*V^2*f`) | textbook, same form A53 used | `NUMERICAL_IDEALIZATION` |
| Measured capacitances / hard-switch `Vds` at nominal `L` | measured fresh in THIS run (`measure_node_capacitance_f`, A51's own function, read-only) -- NOT A51's own published `final_verification.json`, which is GS61008T-specific | `SENSITIVITY_ONLY` |
| `CFLY=3uF`, `d=2.15ns` | unchanged from `A50/A51/A52/A53` | see those `BOUNDARY.md` files |
| GS61008T reference numbers used in the side-by-side comparison (Section 4) | `A53_lphase_zvs_load_tradeoff/RESULTS.md`, already published | quoted read-only, unchanged |

No new paper-sourced or external-device data is introduced -- both EPC2067
`.lib` files already existed in this repository (`A45`) before this
experiment.

---

## 7. What this experiment cannot prove (repeats `BOUNDARY.md` Section 6)

- Does not resolve the `0-20V`-vs-`~12V` capacitance-extrapolation caveat
  (`BOUNDARY.md` Section 1) -- inherits it from the existing `.lib` file
  unchanged.
- Does not include a SPICE cross-check of any specific recommended operating
  point -- same standing follow-up A53 already deferred, now also applying
  to EPC2067's own critical/margin points.
- Does not use a more detailed, non-uniform, population-corrected `Ron` for
  either device -- keeps the SAME simplification as A51/A53 for direct
  comparability (`BOUNDARY.md` Section 2).
- A "less bad than GS61008T" result here does NOT constitute a P24/P25
  reproduction claim, nor validate EPC2067 as "the" P24 Section II-B ZVS
  mechanism device (`SOURCE_COVERAGE_MATRIX.md`'s own standing uncertainty
  is unchanged by this experiment) -- it is a P24 Section IV/Table-3
  embedded-package device choice, tested here purely for its ZVS/loss
  trade-off properties.
- The switching-loss estimate covers only node-capacitance charge/discharge
  energy -- NOT a complete device loss model (no gate-drive loss, no reverse
  recovery). Because EPC2067's own switching-loss estimate (`17.98 W`) is
  much closer in scale to the conduction-loss increase (`38.73 W`-`50.15 W`)
  than GS61008T's was (`2.09 W` vs `40.51 W`-`58.54 W`), this incompleteness
  matters MORE here than it did for A53 -- a `1.2x`-`1.8x` gap is not
  necessarily robust to omitted terms the way A53's `18x`-`27x` gap was. This
  is flagged explicitly: the "less bad, still negative" verdict is somewhat
  less certain to survive a fuller loss model than A53's "decisively
  negative" verdict was.
- Does not revisit the Table-I `2.68 nH` vs Eq.(4) `1.4667 nH` inductance
  conflict -- the nominal baseline is the same `1.4667 nH` value used
  throughout `A24-A53`.
- Does not modify `src/scb_ivr/`, or A37/A42/A45/A48/A50/A51/A52/A53's own
  committed files -- imports A50/A51's own `solver_copy`/`a51_period_map.py`
  and A53's own `a53_solve.py` read-only.
- No P24/P25 reproduction claim of any kind. `SENSITIVITY_ONLY` throughout.
- Does not revisit A51/A52's own separate, positive finding that ZVS IS
  achievable at rated `LPHASE` by reducing LOAD instead (to `~190 W`,
  SPICE-confirmed by A52, with GS61008T) -- a distinct lever, untouched here.

---

## 8. Files

| File | Role |
|---|---|
| `a54_boundary.py` | local wrapper exposing `phase_inductance_h` on `build_boundary`, with EPC2067's own `switch_capacitance` (`CH=3720pF`/`CL=5580pF`) replacing GS61008T's |
| `run_bisection.py` | diagnostic probe, continuation ladder, bisection refine, margin point (imports A53's own `a53_solve.py` and A51's own `a51_period_map.py` read-only); writes `bisection_search.json`, `key_states.json` |
| `run_three_point_analysis.py` | full-rigor re-solve of the three key points, RMS/peak currents, EPC2067 conduction loss (`Ron=1.55mOhm`), capacitive switching loss (measured fresh, not reused from A51's GS61008T-specific published file), net Watts; writes `three_point_analysis.json` |
| `build_results.py` | assembles `results.json`, including the explicit side-by-side comparison against A53's own already-published GS61008T numbers |
| `bisection_search.json`, `key_states.json`, `three_point_analysis.json`, `results.json` | run artifacts |
| `bisection_log.txt`, `three_point_log.txt` | captured console output |
