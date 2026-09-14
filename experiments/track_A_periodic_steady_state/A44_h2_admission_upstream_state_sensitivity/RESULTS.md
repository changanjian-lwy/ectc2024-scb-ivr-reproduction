# A44 H2 admission-current upstream-state sensitivity diagnostic results

Track: A (periodic steady-state reproduction). **Purely diagnostic** per
BOUNDARY.md: nothing here is solved, no locked parameter was retuned, and no
swept value is promoted to a default. This answers BOUNDARY.md Section 5
directly: holding `IL2_INIT` fixed at A38's seed value, does perturbing each
of the other six state variables (`IL1_INIT`, `IL3_INIT`, `IL4_INIT`,
`VC1_INIT`, `VC2_INIT`, `VC3_INIT`), one at a time, move H2's admission
current or admission time away from A39's pinned baseline?

**Headline answer: no, for four of the six variables -- but VC1_INIT and
VC2_INIT are the exception, and the exception is larger than a mere
sensitivity difference: at just +-0.2-0.5 V they eliminate H2's ZVS
admission event entirely.** See Section 4/6 below.

## 1. Whether the simulation completed normally

Yes for all 25 LTspice runs (1 baseline + 4 perturbation points each for the
6 variables), LTspice exit code 0 for every run
(`subprocess.run(..., check=True)`; a nonzero exit would have raised). Four
of the 25 runs (`VC1_INIT` at `+0.2`/`+0.5 V`, `VC2_INIT` at `-0.2`/`-0.5 V`)
completed normally but never produced an H2 admission event within the
simulated window (`0` to `205 ns`) -- this was verified directly from the
`.raw` waveform (see Section 4), not inferred from an exception: `V(xmod:a1,
xmod:a2)` (H2's `Vds`) never reaches `<=0` in these four runs (minimum
residual `0.13-0.43 V`, never crossing zero), so the `.machine`'s admission
gate `time>=50ns AND V(a1,a2)<=0` is never satisfied and H2's gate
(`V(xmod:gh2)`) stays at `0` for the entire run. This is a genuine physical
non-event (`MISSED_ZVS_SLOT` per protocol Section VI), not a script error or
a missing trace.

## 2. Parameters actually used

Locked, unchanged from A39/A38/A37/A36/A35/A27: topology, `Coss` (385 pF
high-side / 770 pF low-side), ideal reverse-clamp (`Vf=0`, `Ron=1 mOhm`),
`LPHASE=1.466666666666667 nH`, `TON=16.6667 ns`, `PHASE=50 ns`,
`NEG_FRAC=.09` (`INEG=11.25 A`), `RHS=7 mOhm` (`GS61008T_RDS_TYP_25C`),
`RLS=3.5 mOhm`, ideal `1 V` output clamp, timestep/solver options. Netlist
template: A38's own final `.cir`
(`A38_h2_h3_local_peak_and_100ns_zvs_solve.cir`), read-only, never modified.

**Baseline seven-state seed** (read directly from A38's own
`best_candidate.json`, byte-identical to A39 Part 2's single representative
run -- confirmed by reproducing A39's exact reported baseline numbers before
running any perturbation, see Section 3):

```text
IL1_INIT = 5.2947                  (A36 solved)
IL2_INIT = 21.205095337            (A38 seed; held fixed throughout A44)
IL3_INIT = 56.32056566312004       (A38 solved, full precision)
IL4_INIT = 84.1447433786           (A37/A38 frozen)
VC1_INIT = 36.000066454            (A37 solved)
VC2_INIT = 23.9999142326           (A37 solved)
VC3_INIT = 12.0006048777           (A37 solved)
```

**Perturbations** (each applied to exactly one variable, all others held at
the baseline seed above; all `SENSITIVITY_ONLY`):
- Currents (`IL1_INIT`, `IL3_INIT`, `IL4_INIT`): `{-2, -1, +1, +2} A`.
- Capacitor voltages (`VC1_INIT`, `VC2_INIT`, `VC3_INIT`): `{-0.5, -0.2,
  +0.2, +0.5} V`.

`IL2_INIT` was never perturbed (A39 already covers it).

## 3. When each key event occurred

Baseline run (all seven variables at the seed above) reproduces A39 Part
2's own reported baseline exactly:

| Quantity | A39 Part 2 (reported) | A44 baseline (this run) |
|---|---:|---:|
| H2 admission time | 50.0007 ns | 50.00072 ns |
| `iL2` at H2 admission | -1.2858 A | -1.28584 A |

H2 admission time across all 25 runs stayed in a `50.0007-50.0014 ns` band
(i.e. essentially pinned to the `50 ns` fixed floor plus a sub-picosecond-
to-picosecond-scale residual) for every run that admitted at all -- in sharp
contrast to A39's own finding that `IL2_INIT` moves admission time by
`~1.45 ns` per `1 A` (reaching `52.9 ns` at `IL2_INIT+2 A`). None of these
six variables move the admission *time* the way `IL2_INIT` does; the only
qualitative effect any of them has on the admission *event* is the binary
one described next.

## 4. Key voltages and currents -- full sensitivity table

Sensitivity computed as the secant slope across the full tested span for
each variable (`-2 A` to `+2 A` for currents, `-0.5 V` to `+0.5 V` for
voltages) where the run admitted at all. Where one or more points did not
admit, the admitting sub-range is used instead and flagged.

| Variable | Perturbation | `iL2` at admission (A) | `Delta i2` vs baseline (A) | Admission time (ns) | `Delta t` vs baseline (ns) | Implied sensitivity |
|---|---|---:|---:|---:|---:|---:|
| baseline | 0 | -1.28584 | -- | 50.00072 | -- | -- |
| `IL1_INIT` | -2 A | -1.27763 | +0.00821 | 50.00137 | +0.00065 | |
| `IL1_INIT` | -1 A | -1.28193 | +0.00391 | 50.00095 | +0.00023 | |
| `IL1_INIT` | +1 A | -1.28663 | -0.00079 | 50.00074 | +0.00002 | |
| `IL1_INIT` | +2 A | -1.28504 | +0.00080 | 50.00080 | +0.00008 | **-0.00185 A/A** (secant -2..+2), **-0.00014 ns/A** |
| `IL3_INIT` | -2 A | -1.28285 | +0.00299 | 50.00075 | +0.00003 | |
| `IL3_INIT` | -1 A | -1.28440 | +0.00144 | 50.00078 | +0.00006 | |
| `IL3_INIT` | +1 A | -1.28628 | -0.00044 | 50.00076 | +0.00004 | |
| `IL3_INIT` | +2 A | -1.28439 | +0.00145 | 50.00078 | +0.00006 | **-0.00039 A/A** (secant -2..+2), **+0.0000084 ns/A** |
| `IL4_INIT` | -2 A | -1.28328 | +0.00256 | 50.00074 | +0.00002 | |
| `IL4_INIT` | -1 A | -1.28414 | +0.00170 | 50.00074 | +0.00002 | |
| `IL4_INIT` | +1 A | -1.28376 | +0.00208 | 50.00076 | +0.00004 | |
| `IL4_INIT` | +2 A | -1.28643 | -0.00059 | 50.00077 | +0.00005 | **-0.00079 A/A** (secant -2..+2), **+0.0000072 ns/A** |
| `VC3_INIT` | -0.5 V | -1.28202 | +0.00382 | 50.00075 | +0.00003 | |
| `VC3_INIT` | -0.2 V | -1.28135 | +0.00449 | 50.00076 | +0.00004 | |
| `VC3_INIT` | +0.2 V | -1.28541 | +0.00043 | 50.00072 | -0.00000 | |
| `VC3_INIT` | +0.5 V | -1.28789 | -0.00205 | 50.00080 | +0.00008 | **-0.0059 A/V** (secant -0.5..+0.5), **+0.0000458 ns/V** |
| `VC1_INIT` | -0.5 V | -1.34352 | -0.05768 | 50.00090 | +0.00018 | pointwise (0..-0.5): **+0.1154 A/V** |
| `VC1_INIT` | -0.2 V | -1.29291 | -0.00707 | 50.00099 | +0.00026 | pointwise (0..-0.2): **+0.0354 A/V** |
| `VC1_INIT` | **+0.2 V** | **NO ADMISSION -- `MISSED_ZVS_SLOT`** | -- | -- | -- | H2 never turns on in `[0,205] ns` |
| `VC1_INIT` | **+0.5 V** | **NO ADMISSION -- `MISSED_ZVS_SLOT`** | -- | -- | -- | H2 never turns on in `[0,205] ns` |
| `VC2_INIT` | **-0.5 V** | **NO ADMISSION -- `MISSED_ZVS_SLOT`** | -- | -- | -- | H2 never turns on in `[0,205] ns` |
| `VC2_INIT` | **-0.2 V** | **NO ADMISSION -- `MISSED_ZVS_SLOT`** | -- | -- | -- | H2 never turns on in `[0,205] ns` |
| `VC2_INIT` | +0.2 V | -1.28689 | -0.00105 | 50.00135 | +0.00063 | pointwise (0..+0.2): **-0.0053 A/V** |
| `VC2_INIT` | +0.5 V | -1.33248 | -0.04664 | 50.00117 | +0.00045 | pointwise (0..+0.5): **-0.0933 A/V** |

Direct waveform confirmation of the four `MISSED_ZVS_SLOT` cases (minimum
value of `V(xmod:a1,xmod:a2)` -- H2's `Vds` -- anywhere after `t=45 ns`,
read from `.raw`, not inferred):

| Case | min `Vds(H2)` after 45 ns |
|---|---:|
| `VC1_INIT+0.2 V` | `0.129 V` (never reaches 0) |
| `VC1_INIT+0.5 V` | `0.431 V` |
| `VC2_INIT-0.2 V` | `0.128 V` |
| `VC2_INIT-0.5 V` | `0.428 V` |

`V(xmod:gh2)` is confirmed at a constant `0` for the entire `205 ns` window
in each of these four cases -- H2's high side never conducts at all, not
merely "admits late."

## 5. Whether the acceptance condition was met (per BOUNDARY.md Section 6)

Yes. BOUNDARY.md Section 6 requires a complete one-at-a-time sensitivity
table across all six variables, each with the perturbation applied, the
resulting admission-current change, and the resulting admission-time change,
read directly from `.raw` waveforms. All six variables were swept at four
points each (24 perturbation runs plus 1 baseline, all completed, all
measured directly via `spicelib.RawRead` using A39's own edge-detection
functions applied to `I(XMOD:LIND2)` and `V(xmod:gh2)`), and the table above
is complete. Section 6 also states explicitly that a table showing uniform
insensitivity is itself a valid, complete result -- and equally, per Section
7, a table showing a variable that *does* move the pinned value must name
it and its magnitude rather than being folded into a vague "some sensitivity
exists" statement. Both are done here.

## 6. Where the first failure boundary occurred / named decisive factor

There is no "failure boundary" in the solve sense (this is a diagnostic, not
a solve). The decisive finding is:

**`IL1_INIT`, `IL3_INIT`, `IL4_INIT`, and `VC3_INIT` reproduce A39's
"pinned" finding almost exactly** -- all four show admission-current
sensitivities of `0.0004-0.006` (A/A or A/V), the same order of magnitude as
A39's own `IL2_INIT` finding (`~0.007 A/A`, i.e. `0.014 A` over `2 A`), and
all four admit at every tested perturbation point with the admission time
essentially unmoved (`<0.001 ns` change per unit).

**`VC1_INIT` and `VC2_INIT` are decisive exceptions, and the exception is
larger than a sensitivity difference -- it is a categorical one.** Two
independent pieces of evidence:

1. **Where they still admit, the sensitivity magnitude is 15-30x larger**
   than any of the other four variables: `VC1_INIT` shows `+0.035` to
   `+0.115 A/V` (pointwise, growing as the perturbation approaches the point
   where admission is lost), and `VC2_INIT` shows `-0.005` to `-0.093 A/V`
   (same growing-toward-the-boundary pattern). These are an order of
   magnitude above the `~0.0004-0.006` range every other variable, including
   `IL2_INIT` itself, showed.
2. **Beyond a small perturbation, admission is lost entirely.** At
   `VC1_INIT` seed`+0.2 V` and seed`+0.5 V`, and at `VC2_INIT` seed`-0.2 V`
   and seed`-0.5 V`, H2's `Vds` never reaches `0` anywhere in the simulated
   period -- the `.machine`'s admission gate (`time>=50ns AND
   V(a1,a2)<=0`) is never satisfied, H2's gate signal stays at `0` for the
   entire `205 ns` window, and H2 conducts zero current for the whole
   period. This is `MISSED_ZVS_SLOT` (protocol Section VI's named outcome
   for a physical event that a fixed time boundary cannot substitute for),
   triggered here by a state-vector perturbation rather than a timing
   change, but the same named failure mode.

**Physical mechanism (directly explains why VC1/VC2 differ from the other
four):** H2's admission condition is `time>=50ns AND V(a1,a2)<=0`, i.e. it
requires the *node-to-node* voltage `Vds(H2)=V(a1)-V(a2)` to resonate down
to `<=0` by the `50 ns` floor. Since `VC1=V(a1)-V(x1)` and
`VC2=V(a2)-V(x2)` directly set the DC bias of nodes `a1` and `a2`
respectively, raising `VC1` or lowering `VC2` directly widens the `a1-a2`
gap that the resonant `L`-`Coss` commutation must close within the fixed
window -- and beyond a small margin (between `0 V` and `+-0.2 V` in this
seed's neighborhood) the commutation simply cannot close that gap at all
before the window ends. `IL1_INIT`, `IL3_INIT`, and `IL4_INIT` are other
phases' inductor currents, coupled to this commutation only weakly (through
the shared output node and cross-phase current summation), which is why
they behave like `IL2_INIT` itself. `VC3_INIT` sets phase 3's flying-cap
bias, which has no direct role in the `a1`-`a2` gap that gates H2's own
admission, so it too behaves like the pinned group.

## 7. Result grade

**`SENSITIVITY_ONLY`.** Per BOUNDARY.md and protocol Section X, this is a
diagnostic result, not a PASS/FAIL on any target. It is a complete,
evidenced answer to BOUNDARY.md Section 5, and per Section 7 it names the
variable(s) that move the pinned value (`VC1_INIT`, `VC2_INIT`) explicitly
rather than folding the finding into a vague statement. No swept value here
is promoted to a default model parameter.

**Direct answer to the question this experiment was commissioned to
answer:** A39's "H2's admission current is pinned by local resonant
commutation, not movable by initial-state tuning" finding **does not hold up
against all six of the other coupled state variables.** It holds against
four of them (`IL1_INIT`, `IL3_INIT`, `IL4_INIT`, `VC3_INIT`), each showing
the same sub-`0.01`-unit-scale insensitivity A39 found for `IL2_INIT`
itself. It **does not hold** against `VC1_INIT` and `VC2_INIT`: these two
flying-capacitor voltages move the admission current 15-30x more per unit
perturbation than any of the pinned-group variables, and at perturbations of
just `+-0.2-0.5 V` from the seed -- well within the range this experiment
was asked to test -- they eliminate the ZVS admission event entirely. The
correct restatement of A39's conclusion is therefore: **"H2's admission
current is pinned against its own `IL2_INIT`, and also against
`IL1_INIT`/`IL3_INIT`/`IL4_INIT`/`VC3_INIT`, but it is not pinned against
`VC1_INIT` or `VC2_INIT` -- those two can move it substantially and, beyond
a small margin, can prevent H2 from admitting (turning on) at all in this
seed's neighborhood."**

## 8. Which module should be adjusted next

Not a "module to adjust next" in the solve sense (this diagnostic proves no
solve; BOUNDARY.md Section 8 explicitly frames this experiment as not
authorized to pursue a fix). What the finding does point at: any future
investigation of H2/H3's admission robustness, or of why A37's joint
seven-state solve (`A37_p25_9pct_joint_seven_state_200ns_periodic_solve`)
never reached a jointly converged periodic state, should treat `VC1_INIT`
and `VC2_INIT` as live, high-leverage coordinates for H2's ZVS admission
event -- not dead ones the way `IL2_INIT`/`IL1_INIT`/`IL3_INIT`/`IL4_INIT`/
`VC3_INIT` are for this particular residual. This experiment does not
attempt any such follow-up solve; it only identifies where the leverage
actually is.

## 9. Which parameters must never be changed because of this failure

Per Section XI and BOUNDARY.md Section 7: `TON=16.6667 ns` must never be
extended to force `iL2` up; `RHS`/`RLS`/`Coss`/`LPHASE`/`CFLY` must not be
changed to fit this result; the `9%` negative-current label (`NEG_FRAC`)
must not be raised or lowered because of this finding. No swept `IL1_INIT`,
`IL3_INIT`, `IL4_INIT`, `VC1_INIT`, `VC2_INIT`, or `VC3_INIT` value from
this diagnostic's 24 perturbation points may be promoted to a new default
`.param` value -- all are `SENSITIVITY_ONLY`. A38/A37's own solved/seed
seven-state values are unaffected: this experiment's perturbation runs live
only in the gitignored `A44_solver_work/` directory; A38's and A37's own
archived `best_candidate.json` files were read only, never modified. The
finding that `VC1_INIT`/`VC2_INIT` can cause `MISSED_ZVS_SLOT` must not be
read as evidence that A38's own seed values are wrong or unstable -- the
seed itself admits normally; only externally-imposed perturbations of
`+-0.2 V` or more were shown to break admission, which is a sensitivity
finding about the neighborhood, not a fault in the seed itself.
