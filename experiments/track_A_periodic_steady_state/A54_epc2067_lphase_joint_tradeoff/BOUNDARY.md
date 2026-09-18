# A54 - joint device+inductance search: does P24's own Table-3 device (EPC2067) find a net-positive ZVS balance at rated load? (BOUNDARY)

Track: A (periodic steady-state reproduction). Main-line continuation
per explicit user direction 2026-09-19 ("联合调整有没有说法" -- is there a
rationale for a joint adjustment -- followed by "跑 边界标记清楚" -- run it,
mark the boundary/classification clearly).

## 0. Scope statement

This does not claim a P24/P25 reproduction. `A53` found that reducing
`LPHASE` alone, holding GS61008T's own device parameters fixed, is NOT a
net efficiency win at P24's rated `250 W` (conduction-loss penalty
exceeds capacitive switching-loss saved by 18-27x). This experiment
tests whether a JOINT change -- swapping to a different device AND
re-bisecting `LPHASE` -- can find a genuinely net-positive balance point,
using the SAME already-validated `A50`/`A51`/`A53` methodology, changed
only in which device's own parameters are plugged in.

## 1. Why EPC2067, specifically, and not an arbitrary device guess

`EPC2067` is not a new candidate invented for this experiment -- it is
**P24's own Table 3, `nP=4`/`nM=4` row's own specified device and
population** (`2` parallel high-side, `3` parallel low-side), already
present in this repository's own component library
(`paper_locked/04_component_models/EPC2067_typical_params.lib`,
`EPC2067_commutation_capacitance.lib`) since an earlier, separate
investigation (`A45_epc2067_table3_candidate_commutation`) that never
fed this device into the ZVS-search chain (`A50-A53`) at all -- every
prior fast-solver/SPICE result in that chain used GS61008T instead. This
is therefore BOTH a genuine joint-parameter search AND a more
paper-faithful device choice for this specific operating point than
anything used so far in `A50-A53`.

**The device trade-off, stated with real numbers before running
anything** (both from the already-existing `.lib` files, `EXTERNAL_
DEVICE_DATA`, quoted verbatim, not re-derived):

| | GS61008T (A50-A53's own choice) | EPC2067 (P24 Table 3's own choice) |
|---|---:|---:|
| Per-device `Rds(on)` | `7 mOhm` | `1.55 mOhm` (`4.5x` lower) |
| Per-device `Co(tr)` | `385 pF` (`0-50 V` window) | `1860 pF` (`0-20 V` window, `4.8x` higher per device) |
| Table-3 population (this row) | `NHS=1`, `NLS=2` (P25 supplement) | `NHS=2`, `NLS=3` (P24 Table 3 itself) |
| Resulting `CH_TOTAL`/`CL_TOTAL` | `385 pF` / `770 pF` | `3720 pF` / `5580 pF` (`~7-9x` higher) |

Lower resistance helps conduction loss directly. Higher total
capacitance hurts the ZVS threshold (`threshold ~ sqrt(C/L)`, already
established in `A50`'s own `threshold_current_a` formula) -- a rough
`sqrt(9)~=3x` increase in required negative current from capacitance
alone, before any `LPHASE` re-bisection. **Whether the resistance
benefit outweighs the capacitance penalty, once `LPHASE` is re-bisected
to compensate, is not knowable in advance and is exactly what this
experiment tests -- it is not assumed to be a win.**

**Known extrapolation risk, inherited from the existing `.lib` file's own
caveat, not newly discovered here**: EPC2067's `Co(tr)` is characterized
over a `0-20 V` transition (`BVDSS=40 V`), while this design's actual
per-switch blocking voltage is roughly `Vin/nP ~= 12 V` -- closer to,
but not exactly, the characterized window. This is flagged, not
resolved, exactly as `EPC2067_typical_params.lib`'s own header already
states.

## 2. What changes relative to A53, exactly

- **Device parameters**: `Ron` uniform value changed from GS61008T's raw
  single-device `7 mOhm` to EPC2067's own raw single-device `1.55 mOhm`
  -- deliberately NOT population-divided, mirroring EXACTLY how `A51`/
  `A53` used GS61008T's own raw `RDS_TYP_25C` value uniformly for both
  sides without population correction (Section 2 of `A52`'s own
  `BOUNDARY.md` already established this as `A51`'s own inherited
  simplification; this experiment keeps the SAME simplification with the
  new device's own raw value, for direct comparability -- not
  introducing a new modeling choice alongside the device change, which
  would confound the two).
- **Switch capacitance**: `CH=3720 pF`, `CL=5580 pF` (EPC2067, Table 3's
  own `NHS=2`/`NLS=3` population, `CommutationCapacitance` with
  `high_device_f=2*1860p`, `low_device_f=3*1860p`) replacing GS61008T's
  `385 pF`/`770 pF` -- this DOES keep the correct high/low asymmetry
  (unlike resistance, capacitance was already modeled per-side correctly
  throughout `A50-A53`).
- **`module_power_w=250.0` fixed** (P24's own rated load), same as `A53`.
- Everything else -- `CFLY=3 uF`, `dead_time_s=2.15 ns`, the seed
  (`A37`'s own best candidate, same conversion `A51`/`A53` already
  established), the bisection/three-point methodology itself -- unchanged
  from `A53`.

## 3. Method

Identical structure to `A53`'s own Sections 2-2.5, substituted with
EPC2067's own device parameters:

1. Reuse `A51`'s own already-committed `a51_period_map.py` functions
   read-only (same discipline as `A53`); do not modify `A51`'s or `A53`'s
   own files.
2. First, at EPC2067's own device parameters and the PAPER's OWN nominal
   `LPHASE=1.4666667 nH`, confirm (not assume) whether all four phases
   hard-switch at `250 W` -- given the capacitance increase, this is very
   likely but must be confirmed, not presumed, before bisecting.
3. Bisect `LPHASE` downward (same continuation-from-previous-converged-
   point method `A53`'s own agent found necessary for safety) to find the
   critical `LPHASE` at which all four phases first achieve natural ZVS
   at `250 W`, under EPC2067's own device parameters.
4. At three points (paper's nominal `LPHASE` with EPC2067, critical
   `LPHASE` with EPC2067, and a `10%`-below-critical margin point),
   report convergence, per-phase ZVS verdicts (with step-size
   convergence, not a single sub-step), peak/RMS phase currents, and:
   - Conduction loss: `sum of I_rms^2 * Ron` with EPC2067's own `Ron=
     1.55 mOhm` (uniform, Section 2).
   - Capacitive switching-loss estimate at the nominal-`LPHASE`
     (hard-switching) point, using EPC2067's own measured participating
     capacitance and hard-switch residual voltages at `f_sw=5 MHz` --
     same formula `A53` already used (`0.5*C*V^2*f`), same explicit
     "partial estimate, not a full device loss model" caveat.
5. **Report the net Watts comparison directly against A53's own already-
   published GS61008T numbers** (conduction loss at critical/margin `L`
   minus switching loss eliminated, for BOTH devices side by side) --
   this direct comparison, not just EPC2067's own standalone numbers, is
   the actual answer to "does the joint device+inductance choice do
   better than inductance alone."

## 4. Provenance of every value

| Value | Source | Category |
|---|---|---|
| `EPC2067_RDS_TYP_25C=1.55 mOhm` | `paper_locked/04_component_models/EPC2067_typical_params.lib`, EPC official datasheet rev. 2021-10-21 | `EXTERNAL_DEVICE_DATA` |
| `EPC2067_COTR_0_20V=1860 pF` | Same source | `EXTERNAL_DEVICE_DATA`, with the same `0-20V`-vs-`~12V`-actual extrapolation caveat the `.lib` file itself already states |
| `NHS=2`, `NLS=3` | `paper_locked/04_component_models/EPC2067_commutation_capacitance.lib`, P24's own printed Table 3, `nP=4`/`nM=4` row (independently re-verified against the printed HS/LS peak-current formula values per that file's own header) | `P24_EXPLICIT` |
| `module_power_w=250 W`, `LPHASE` nominal `1.4666667 nH` | Same as `A53` | `P24_EXPLICIT` |
| Everything else | See `A50`/`A51`/`A53` `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced or external-device data is introduced -- both
EPC2067 `.lib` files already existed in this repository before this
experiment.

## 5. Success/failure conditions

- **A critical `LPHASE` is found, and the net Watts comparison is
  positive (switching loss eliminated exceeds conduction loss added) OR
  is less negative than `A53`'s own GS61008T result**: report clearly,
  with the same partial-estimate caveats `A53` already stated. Even a
  "less bad" result (smaller net loss than GS61008T) is a genuinely
  informative, reportable improvement from the joint change.
- **The net Watts comparison is worse than `A53`'s own GS61008T result**
  (capacitance penalty dominates): report plainly -- this would mean
  EPC2067, despite its much lower resistance, is not a better choice for
  THIS specific tradeoff, a real and useful negative finding given this
  is P24's own specified device.
- **No critical `LPHASE` is found within a reasonable bracket** (the
  `~3x` higher threshold estimate suggests this is a real possibility --
  report the bracket actually explored and where it was abandoned, per
  Ground Rule 7, exactly as `A53`'s own method already allows for.
- Every phase current must stay within `+/-250 A` throughout (use `A53`'s
  own established continuation-from-previous-point method if a raw
  from-scratch seed proves unsafe at any candidate `LPHASE`, exactly as
  `A53`'s own agent found necessary -- do not re-attempt an unsafe
  from-scratch seeding approach).

## 6. What this experiment cannot prove

- Does not resolve the `0-20V`-vs-`~12V` capacitance-extrapolation
  caveat (Section 1) -- inherits it from the existing `.lib` file.
- Does not include a SPICE cross-check of any specific recommended
  operating point -- same standing follow-up `A53` already deferred.
- Does not use a more detailed, non-uniform, population-corrected `Ron`
  for either device -- keeps the SAME simplification as `A51`/`A53` for
  direct comparability (Section 2).
- A positive result here would still not constitute a P24/P25
  reproduction claim, nor validate EPC2067 as "the" P24 Section II-B
  device (`SOURCE_COVERAGE_MATRIX.md`'s own standing uncertainty about
  which device the ZVS mechanism itself assumes is unchanged by this
  experiment).
- Does not modify `src/scb_ivr/`, or A37/A42/A45/A48/A50/A51/A52/A53's
  own committed files.
