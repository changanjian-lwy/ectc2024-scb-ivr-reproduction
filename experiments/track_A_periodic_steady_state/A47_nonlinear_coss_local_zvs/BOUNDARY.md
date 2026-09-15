# A47 nonlinear Coss(V) local ZVS boundary

Track: A, local P24 `t1->t2->t3` mechanism experiment (interval 1 -> interval
2 -> interval 3 chain), the same mechanism A42 and A45 studied. This is not
a periodic-orbit, four-phase, or startup experiment.

## Why this experiment exists

A46 (`experiments/track_A_periodic_steady_state/A46_cross_experiment_capacitance_scaling/`)
fit A41+A42+A45's own committed constant-capacitance results and found that
reaching P24's literally-stated 1%-2% negative-current ZVS threshold would
require an effective commutation capacitance roughly 1-2 orders of
magnitude smaller than either device's constant `Co(tr))` value (GS61008T
257 pF effective series capacitance, EPC2067 2232 pF). Real GaN `Coss(V)`
is strongly nonlinear -- much larger near `Vds=0` and falling off steeply as
`Vds` rises, which is exactly why manufacturers publish `Co(er)`/`Co(tr)`
"effective" constants at all (they are single-number corrections for this
nonlinearity, valid only over the *stated* test voltage range, e.g. 0-50V
for GS61008T). Since the local ZVS event this chain studies only needs the
voltage to complete the *last* part of its swing toward 0V -- exactly where
a real `Coss(V)` curve is largest -- a constant-capacitance model may be
overestimating the charge needed to finish that swing. This experiment
builds a real, digitized (not fabricated) `Coss(V)` model and reruns the
exact same local chain to see whether the threshold moves, and by how much.

## Parent and fixed quantities

Electrical parents (the full chain, re-run stage by stage, exactly as A45
did for its own device-swap experiment, not just the final stage):

- Stage 0: `paper_locked/02_ectc2024_main/spice/R04D0_p24_first_interval_shared_ladder.cir`
- Stage 1: `paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir`
- Stage 2: `paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir`

The following remain identical to the R04D0/R04D2A/R04D3A chain and to
A42/A45's zero-snubber baseline:

- P24 topology, local state sequence and event-latch/control-machine
  structure (`.machine`/`.state`/`.rule`/`.output` blocks, unchanged);
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `nM=4` configuration context (the local
  subnetwork itself models `nM=1`, matching R04D0/R04D2A/R04D3A), `Ipk=125 A`
  (P24 Eq. 2), `Ton=16.667 ns`;
- locked Eq.-(4) `L=1.4666667 nH` (NOT the 2.68 nH Table-I value);
- device: GS61008T, 1 high-side / 2 parallel low-side (P25 Table III
  population), the SAME device A42 used -- this is a same-device,
  capacitance-model-only comparison against A42, not a device swap like A45;
- `Ron`: `RHS=GS61008T_RDS_TYP_25C/1`, `RLS=GS61008T_RDS_TYP_25C/2`,
  numerically identical to A42's values, unchanged;
- no added snubber, delay, dead time, or retuning;
- the same negative-current sweep convention as A42/A45 (coarse 1%-10% grid
  in 1-percentage-point steps, `P24_EXPLICIT`/`DIAGNOSTIC_BRIDGE`/
  `P25_SUPPLEMENT` row labelling, widened only if it does not bracket the
  threshold);
- `CFLY=53.8 uF` flying-capacitor placeholder (EPE2019-derived, unchanged,
  not fitted here either).

## Only changed variable

The constant-capacitance `CH1`/`CL1` devices (a plain LTspice
`Cxxx n1 n2 <value>` reading a single fixed `Co(tr)` scalar from
`GS61008T_commutation_capacitance.lib`) are replaced with a nonlinear,
voltage-dependent `Coss(V)` model built from `paper_locked/04_component_models/GS61008T_nonlinear_coss.lib`,
for the SAME device (GS61008T) A42 used. Ron, population, topology, timing
and sweep convention are all unchanged from A42.

## Data source and provenance (Step 1)

**Attempted first, per the task's stated preference order: an official
manufacturer SPICE/behavioral model with a real nonlinear Coss(V).** Web
search and direct fetch attempts against gansystems.com (DNS no longer
resolves -- GaN Systems is now an Infineon-owned product line and the old
domain is dead), infineon.com's GS61008T product/part pages, and the
Infineon Developer Community's GaN board (`community.infineon.com`,
`hemtgan` board) located only a "GaN Systems Spice Model User Guide"
(rev. 190729, mirrored at
`https://community.infineon.com/gfawx74859/attachments/gfawx74859/hemtgan/499/2/Spice%20Model%20User%20Guide.pdf`)
confirming that GaN Systems DOES publish LTspice/PSpice models with
voltage-dependent capacitance for its GS66xxx family, but no downloadable
`.lib`/`.asy` file specifically for GS61008T could be located or fetched in
this environment (the modern Infineon product pages are JavaScript-rendered
and returned only navigation-shell content to this session's fetch tool;
no model-download endpoint for this specific part number was found). This
path is therefore recorded as attempted and exhausted, not skipped.

**Used instead: digitizing the datasheet's own Coss-vs-Vds graph (Step 1,
option 2).** Source:

- **Document**: GS61008T datasheet, **Rev 200402**, (c) 2009-2020 GaN
  Systems Inc. -- the exact same datasheet revision already used elsewhere
  in this project for `GS61008T_typical_params.lib` /
  `GS61008T_commutation_capacitance.lib` (confirmed identical by the
  "Rev 200402" text printed on every page and by the Electrical
  Characteristics table matching `RDS(on)=7 mOhm typ`, `COSS=250 pF`,
  `CO(ER)=302 pF`, `CO(TR)=385 pF`, all already recorded in this project).
- **Retrieved via**: the Infineon-hosted republication of the same GaN
  Systems document,
  `https://www.infineon.com/dgdl/Infineon-GS61008T-DataSheet-v01_00-EN.pdf?fileId=8ac78c8c8d2fe47b018e5160eb52522a`
  (the originally-suggested `mouser.com` URL timed out / returned a
  non-PDF response to this session's fetch tools; the Infineon dgdl URL
  above returned the genuine 20-page PDF and was used instead. The
  datasheet PDF itself is EXTERNAL_DEVICE_DATA and is NOT committed to
  this repository, per `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section
  XII; it must be re-fetched from the URL above to rerun
  `digitize_gs61008t_coss.py` end to end).
- **Page/figure**: page 8 of the PDF (0-based page index 7), "Figure 7:
  Typical CISS, COSS, CRSS vs. VDS", in the "Capacitance Characteristics"
  quadrant. Y-axis is log-scale capacitance in pF (1 to 1000), x-axis is
  linear `Vds` 0-100 V.

### Digitization method

`digitize_gs61008t_coss.py`:

1. Renders page index 7 to a 400-DPI raster (a vector-drawn figure
   re-rasterized at high resolution, not a low-quality scan) using
   PyMuPDF, and crops the "Capacitance Characteristics" quadrant.
2. **Calibrates pixel coordinates against the plot's own axis tick labels
   and gridlines** (never against assumed round-number pixel positions):
   - X-axis (linear, 0-100V): the 7 near-full-height vertical lines
     (outer frame + 6 gridlines at V=0,20,40,60,80,100) are auto-detected;
     `col_v0=306`, `col_v100=1163`, `8.57 px/V`.
   - Y-axis (log, decades 1000/100/10/1 pF): the 4 numeral tick-label text
     blocks ("1,000"/"100"/"10"/"1") are located via connected-component
     analysis of the left margin, then a full-width gridline is confirmed
     within +/-25 px of each label's row center. Calibration points used:
     `row(1000pF)=252`, `row(100pF)=560`, `row(10pF)=870`, `row(1pF)=1176`,
     giving a highly consistent `307.7 +/- 1.5 px/decade` (spacings
     309/308/306 px across the 3 decades).
3. **Traces the COSS curve** (the middle of the three CISS/COSS/CRSS
   traces) column-by-column from V=100V (right) to V=0V (left) using a
   nearest-neighbour continuity tracker, seeded at the rightmost column
   where COSS sits unambiguously between the flat CISS trace (~650-700 pF)
   and the CRSS trace (~8-10 pF at V=100). 854 points were traced
   (`gs61008t_coss_digitized_raw.csv`, `Vds_V` from 0.117 to 99.65).

### Calibration cross-check against the datasheet's OWN printed numbers
(never against the plot itself)

| Reference quantity | Datasheet printed value | Digitized value | Relative error |
|---|---:|---:|---:|
| `Coss` at `Vds=50V` | 250 pF (typ) | 244.9 pF | -2.0% |
| `Co(tr)`, 0-50V (time-equivalent, `Q(50V)/50V`) | 385 pF | 374.9 pF | -2.6% |
| `Co(er)`, 0-50V (energy-equivalent, `2E(50V)/50V^2`) | 302 pF | 299.0 pF | -1.0% |

All three independent cross-checks land within 3% of the datasheet's own
printed numbers, which is the honest precision this raster-digitization
method can support -- it is NOT as precise as a real tabulated curve, and
this project's rule is to say so rather than hide it behind false
precision. This is also markedly better agreement than a rough visual
reading would suggest is possible, and gives confidence the axis
calibration (the part most prone to error) is correct.

### Digitization uncertainty, stated honestly

- The three cross-check errors above (-2.0%, -2.6%, -1.0%) bound the
  overall digitization+fit accuracy for `V>~5V`, where CISS/COSS/CRSS are
  visibly separated in the source figure.
- **For `Vds` below roughly 3-5V, COSS is graphically fused with the flat
  CISS trace in the source image** (both sit within a few pixels of each
  other at `V=0`, visually around 650-700 pF) -- the printed resolution of
  this raster does not resolve them as two distinct lines in that narrow
  region. The digitized/fitted curve's value near `V=0` (`Cfloor+A_COSS ~=
  702 pF`, see below) should therefore be read as "COSS is at least this
  large near Vds=0, indistinguishable in this source from CISS," not as an
  independently-resolved measurement at that specific point. This does not
  weaken the experiment's qualitative point (COSS is large near 0V) -- if
  anything a fused/higher true value there only strengthens it -- but the
  exact peak value near V=0 carries materially more uncertainty than the
  cross-checked mid/high-V region.
- Pixel-to-value calibration itself is estimated at about +/-0.5% on the
  x-axis (sub-pixel gridline centers, `8.57 px/V` over an 857-pixel span)
  and about +/-0.5 px on decade spacing (`307.7 px/decade` measured to
  +/-1.5 px, i.e. about +/-0.5% per decade, compounding to roughly +/-1.5%
  over the 3-decade span from 1000 pF to 1 pF).

## Fitted model (Step 2)

`fit_nonlinear_coss.py` fits the digitized points to

```
Coss(V) = C_FLOOR + A_COSS / (1 + (V/V_KNEE)^2)
```

chosen (among several forms tried -- a generalized-logistic form with a
free exponent `m` gave a marginally better R^2=0.98 at `m=4`, and the
task's own suggested `C_floor+A/(1+V/Vknee)^n` form gave at best R^2=0.93
even at its best integer `n=7`) specifically because fixing the exponent at
2 gives the best fit inside the small set of exponents whose `Q(V) =
integral(Coss dV)` has a clean **closed form using only `atan()`**:

```
Q(V) = C_FLOOR*V + A_COSS*V_KNEE*atan(V/V_KNEE)
```

Fitted parameters (nonlinear least squares in log-capacitance space, over
all 854 digitized points):

| Parameter | Value | 1-sigma |
|---|---:|---:|
| `C_FLOOR` | 203.754 pF | 0.80 pF |
| `A_COSS` | 498.502 pF | 5.70 pF |
| `V_KNEE` | 13.143 V | 0.18 V |

Fit quality: `R^2=0.962`, RMSE=25.7 pF, mean relative error 4.5%, max
relative error 18.1% (at `V=18.3V`, right at the steepest part of the
knee -- the region where a simple 2-parameter-knee functional form is
least able to track the datasheet's sharper real transition). The fit's
own datasheet cross-check (evaluating the FIT, not the raw digitized
points): `Coss(50V)=236.0 pF` (datasheet 250, -5.6%), `Co(tr)=375.9 pF`
(datasheet 385, -2.4%), `Co(er)=298.1 pF` (datasheet 302, -1.3%). The
`Coss(50V)` fit residual (-5.6%) is larger than the raw-digitized-point
residual (-2.0%) because the single global 3-parameter fit trades a small
amount of point-wise accuracy for a smooth, closed-form, exactly integrable
curve; this trade-off is deliberate and disclosed, not hidden.

Full numbers: `fit_results.json`.

### Validity and idealization

- Digitized/fit range: `Vds` 0-100V (the full plotted range).
- `Coss(V)` is even and `Q(V)` is odd in `V`, so the model extends smoothly
  to `V<0`. This matters only because a small negative `Vds` overshoot at
  the exact ZVS crossing instant is expected and physically real (the same
  overshoot A42/A45 also measured); the datasheet itself only characterizes
  `V>=0`, so the symmetric extension is an explicit **NUMERICAL_IDEALIZATION**,
  not additional device data, chosen as the least-arbitrary continuation
  available (the alternative -- clamping `Coss` constant for `V<0` --
  would introduce a discontinuous derivative exactly at the point this
  experiment cares about most).
- Population: the same P25 Table III population as
  `GS61008T_commutation_capacitance.lib` (`NHS_NL=1`, `NLS_NL=2`). Because
  parallel same-voltage capacitors sum linearly even when each is
  individually nonlinear (`Q_total(V) = N * Q_device(V)` exactly), the
  single-device `Coss(V)`/`Q(V)` above is reused unmodified for both `CH1`
  (times 1) and `CL1` (times 2).

## LTspice implementation note (unavoidable mechanical consequence, not a
second independent variable)

LTspice's native nonlinear-capacitor syntax, `Cxxx n1 n2 Q=<expr(V)>`, was
tried first. It **pathologically collapsed its own internal timestep to
the order of `1e-17` s** (producing >100 MB `.raw` files for a 5 ns test
window with no sign of converging) for this `Coss(V)` shape -- confirmed
for both the atan-based `Q(V)` above and an alternative closed-form
power-law `Q(V)`, with a floating-node-safety leak resistor present, and
under both the project's standard tight tolerances
(`reltol=1e-7 abstol=1e-10 chgtol=1e-16`) and much looser ones. A plain
linear `Q=C*V` capacitor, by contrast, worked instantly, ruling out a
trivial syntax error.

The numerically robust, LTspice-documented alternative used everywhere in
this experiment is a **behavioral current source using the `ddt()`
time-derivative operator**, which is electrically identical to a
charge-controlled capacitor:

```
B<name> n1 n2 I=ddt(Q(V(n1,n2)))
```

This was validated in isolation (`validate_nlcap_charging.py`: a single
`B1`/`ddt()` element charged by a constant current source) against direct
numerical integration (`scipy.integrate.solve_ivp`) of the identical
`dV/dt = I/Coss(V)` ODE, matching to 5 decimal places (`<0.0001%` relative
error at 1/2/5 ns) -- see the script's own PASS output, reproduced in
RESULTS.md.

Embedding two such `ddt()` sources directly at `CH1`/`CL1` (replacing the
full `Coss(V)` including its constant floor) inside the real stage-1/2
circuit, however, **still failed to converge**, stalling first near the
low-side ZVS switching instant (~0.14 ns) and, after loosening tolerances,
again partway through the freewheel interval (~71 ns) -- regardless of the
size of an added floating-node-safety leak resistor (`1T` vs `1Meg`). The
likely cause: `CH1`/`CL1` sit in a loop made only of capacitors and an
ideal voltage source (`CH1||SH1` + `CF1` + `CL1||SL1`, with `VIN_SRC` an
ideal 0-ohm source) -- a classically stiff SPICE topology that native
capacitors handle via a dedicated companion-conductance model, but which a
generic `ddt()`-based B-source (with no equivalent built-in companion
model) apparently cannot handle robustly when it must represent the ENTIRE
capacitance, including a large constant floor.

**The construction actually used** splits each `Coss(V)` into its constant
floor (a real, native linear capacitor, restoring a proper companion
conductance to the stiff loop) plus the remaining bounded nonlinear
correction term (a `ddt()` B-source, now only carrying `A_COSS*V_KNEE*atan(V/V_KNEE)`,
which saturates rather than diverging):

```
CxxLIN n1 n2 {N*C_FLOOR}                 IC=<the old CH1/CL1 IC=>
Bxx    n1 n2 I=ddt(N*A_COSS*V_KNEE*atan(V(n1,n2)/V_KNEE))
```

This is mathematically identical to the single-source form (`Q_total =
C_FLOOR*V + Bxx`'s integral, exactly as before). Even with this split, the
default trapezoidal integrator still failed to converge; only combining
the split WITH switching the integration method to Gear's method
(`.options ... method=gear`) converged normally (stage 1 completed in
under 15 seconds; the split alone, still under trapezoidal, was observed
to still stall). `method=gear` is a solver-selection change, not a circuit
or physics change. Because the real `CxxLIN` device carries `IC=`, it is also what supplies
each node's correct initial voltage under `UIC` -- a bare top-level
`.ic V(node)=value` directive was tried first and found NOT to be honored
at `t=0` in this circuit (the `.raw` showed `V(a1)=V(x1)=0` at the literal
`t=0` sample despite the `.ic` statement, followed by a large, solver-
punishing jump toward the intended values on the very next timestep); a
real `Cxxx` device's own `IC=` IS honored by `UIC` (exactly how R04D2A's
original `CH1`/`CL1` worked), which is what motivated moving the floor
capacitance into a real device rather than only using it for numerical
conditioning.

None of this changes the modeled physics -- `Coss(V)` is bit-for-bit the
same fitted curve either way -- it is purely an LTspice-numerics
implementation detail, fully disclosed here so the netlists are not
mysterious.

### Solver tolerance (stage 2 sweep, adaptive escalation)

Stage 2's negative-current sweep found that solver-convergence difficulty
under this nonlinear-Coss(V) construction is **not monotonic in tolerance
looseness and not uniform across negative-current percentages**: most rows
converge in a few seconds under the base tier
(`reltol=1e-5 abstol=1e-9 method=gear`), a few rows (4%, 7%, 8% in the
coarse grid; one row in the 0.1%-refinement grid) instead collapse to
sub-attosecond steps under that exact tier while never showing divergence,
and one further test found a row that had already converged fine under the
base tier instead stall under a LOOSER tier -- i.e. looser is not simply
"safer" here. `run_a47_sweep.py` handles this with a per-case adaptive
retry: run under the base tier with a wall-clock budget (30s for the
coarse/refinement/fine grids); if it does not finish, escalate to
`reltol=1e-3 abstol=1e-7 method=gear itl4=500`, then (if needed)
`reltol=1e-2 abstol=1e-6 method=gear itl4=2000`. Every case in this
experiment converged at tier 0 or tier 1; tier 2 was never needed. The
tier actually used per row is reported by the script and is a solver-
efficiency bookkeeping detail, not a per-row physics difference.

**What was directly verified, and what was not:** the standalone `ddt()`
construction was validated against direct numerical integration
(`validate_nlcap_charging.py`) at the tight, non-escalated tolerance
(`reltol=1e-7 abstol=1e-10 chgtol=1e-16`) and matched to <0.0001%. The
escalated-tier mechanism itself was verified to be deterministic and
reproducible: the 4%-row result obtained under tier 1
(`minimum_vds_high_after_release_v=6.463050842285156`) was independently
reproduced bit-for-bit in an ad hoc standalone run using the same tier-1
settings. A direct same-row tier-0-vs-tier-1 comparison (to confirm the
*answer*, not just the mechanism, is tolerance-independent) was attempted
for the 2% row and did not complete in this session's time budget (that
specific row converged promptly at tier 0 but stalled under tier 1,
consistent with the non-monotonic behavior noted above) -- this comparison
is therefore NOT claimed as verified, and is named here rather than
silently dropped. The indirect evidence for tolerance-independence of the
physical answer is: (a) the underlying `ddt()` element's own accuracy is
independently known to be far better than 0.1% regardless of tier, (b) all
ten coarse-grid rows and all twenty-two refinement/fine-refinement rows produced a smooth,
monotonic trend in `minimum_vds_high_after_release_v` vs. percentage with
no discontinuity at the tier-0/tier-1 boundary rows (4%, 7%, 8%), which
would be the expected symptom if a tier change were biasing the physical
result rather than only its convergence speed.

## Success and extraction

Identical to A42/A45's convention: a row passes the local event only when
the low side releases at its exact target and high-side `Vds` subsequently
reaches zero naturally within the observed window; extract release
time/current, ZVS time, commutation duration and current at ZVS. The
1%-10% coarse grid is intended to bracket the threshold; if it does not,
a wider sensitivity search is run and reported honestly as a wider
bracket, matching A45's own precedent.

## Prohibited claims

1. This cannot confirm nonlinear `Coss(V)` as validated real device
   behavior even with a real digitized curve -- digitization/fit carries
   the stated 1-5% (mid/high-V) to qualitatively-larger (near-V=0, fused
   with CISS) uncertainty above, and the model is still a 3-parameter
   analytic approximation to a raster-digitized graph, not a manufacturer
   SPICE model or a tabulated datasheet curve.
2. `Ron` for GS61008T remains exactly A42's own value; this experiment
   changes only the commutation-capacitance model, nothing about
   conduction loss.
3. Cannot establish four-phase closure, a periodic orbit, or startup
   behavior (this is a single-phase local `t1->t2->t3` subnetwork, same
   scope as R04D3A/A42/A45).
4. Cannot replace or override P24's stated 1%-2negative-current range, nor
   A42's own directly-measured 7.76%-7.77% constant-capacitance bracket --
   both remain separately valid, separately labelled results.
5. A result here comparing favorably or unfavorably to A42's threshold is a
   same-device, same-Ron, capacitance-model-only sensitivity comparison; it
   is not by itself a hardware validation of either capacitance model, and
   it does not touch four-phase closure, startup, dead time, or snubber
   behavior.
6. Cannot claim this is "the" real device `Coss(V)` -- it is one digitized
   reading of one datasheet's typical curve, with the stated raster
   uncertainty, not an independently-measured or manufacturer-supplied
   characterization.
