# A55 - joint LPHASE + dead-time partial-loss optimization (BOUNDARY)

Track: A (periodic steady-state reproduction).

Status: `LOCAL_JOINT_GRID_AND_STEP_REFINEMENT_COMPLETED` (2026-09-27).
The asymmetric-Ron baseline and local ZVS-boundary refinement have run. A
3x3 L/dead-time grid has completed, under `JOINT_GRID_BOUNDARY.md`; see
`JOINT_GRID_RESULTS.md`. No global or rated-power optimization is claimed.
The selected 0.621524 nH / 4.3 ns point retains all-eight-ZVS after two
successive step halvings (5 -> 2.5 -> 1.25 ps commutation steps). The finest
run delivers approximately 219.99 W with approximately 39% negative entry
current, so it still fails the combined rated-output/small-negative-current
paper target. See `joint_refinement.json` for each phase and actual branch power.

### 2026-09-26 correction: phase current is not switch-branch current

The earlier path gate separates time intervals correctly, but substitutes the
phase inductor current for the enabled switch's channel current. In the SCB
network, flying-capacitor currents can make these different. Therefore the
historical 8.592/21.404/25.259 W numbers below must be read as **phase-current
loss proxies**, not validated switch-channel losses.

`audit_accepted_orbit.py` now meters each actual enabled resistive branch as
`P = integral(v_branch^2/R_branch dt)/T`, using accepted trajectory samples
with provisional/backtracked samples removed. At the old margin point this
gives 28.9099 W, versus the earlier proxy's 25.2590 W. At the old critical
point it gives 24.6144 W versus 21.4043 W. Dynamics and ZVS verdicts are not
changed by this measurement correction. Revalidate this branch accounting
before publishing a joint-loss optimum. The prior path-gate PASS below is
historical, not acceptance of the proxy as the final objective.

The current local boundary search varies only L between the re-solved
0.564665 and 0.627406 nH endpoints at 2.15 ns dead time. It uses seven
bisections, then independently re-solves both bracket endpoints at
31.25 ps/2.5 ps instead of 62.5 ps/5 ps. Failed convergence or a current-screen
violation stops the bracket update; step-sensitive ZVS classifications are
reported as unresolved. Bisection identifies a local transition, not global
monotonicity or an optimum.

This inherits A51's fixed 5 MHz command windows and early zero-voltage
admission/ideal-clamp surrogate; failed admission produces recorded hard
switching at the window end. It does not implement the complete native
P24 negative-current-threshold controller. The +/-250 A limit is a project
screen, not a sourced EPC2067 safe-operating-area limit. Three isolated
divider coordinates stay pinned for the fast periodic solve; flying-capacitor
voltages are solved rather than forced to 36/24/12 V.

## 0. Scope statement

This is a `SENSITIVITY_ONLY` continuation of A53/A54, not a P24/P25
reproduction. It asks whether jointly varying `LPHASE` and dead time at the
P24 rated `250 W/module` boundary can improve the electrical-loss trade-off
found by A54 for the EPC2067 candidate.

The objective is deliberately called a **partial electrical-loss proxy**, not
"total loss" or "system-level loss". Gate-drive loss, third-quadrant
conduction, magnetic loss, temperature rise, package loss and control power
are not all available. Several of those omitted terms vary with the search
variables and therefore cannot be dismissed as harmless constants.

## 1. Why dead time is a new lever

A53/A54 held dead time at A48/A51's `2.15 ns` while changing the resonant
capacitance and/or phase inductance. Since the commutation time scales roughly
with `sqrt(L*C)`, the inherited dead time need not remain appropriate after
those changes. A55 therefore treats dead time as a search variable rather
than carrying `2.15 ns` forward as a claimed optimum.

The earlier `2.15 ns` value is a **seed/reference point only**. It is not a
physically justified lower bound for the joint search. Because no sourced
driver limit is available, A55 adopts `[0.5, 10] ns` strictly as a
`SENSITIVITY_ONLY` range: `0.5 ns` is A48's lowest previously exercised value,
and `10 ns` is below the `16.67 ns` high-side on-time so the commanded states
do not overlap. This range is not a hardware capability claim.

## 2. Device and population contract

The candidate device and population are fixed by the selected P24 Table-3
`nP=4, nM=4` row:

| Quantity | Value | Provenance |
|---|---:|---|
| EPC2067 per-device typical `Rds(on)` at 25 C | `1.55 mOhm` | locked external-device library |
| high-side parallel count | `NHS=2` | P24 Table 3 |
| low-side parallel count | `NLS=3` | P24 Table 3 |
| effective high-side typical resistance | `0.775 mOhm` | `1.55/2` |
| effective low-side typical resistance | `0.5167 mOhm` | `1.55/3` |
| high-side commutation capacitance | `3720 pF` | `2*1860 pF` |
| low-side commutation capacitance | `5580 pF` | `3*1860 pF` |

The parallel counts are not an optional population sweep: they are part of
the chosen paper row and must be applied. A future experiment may vary
population, but A55 does not.

Conduction loss must be path-resolved:

```text
Pcond = sum_phases [
    RHS_eff/T * integral_HS(i_phase^2 dt)
  + RLS_eff/T * integral_LS(i_phase^2 dt)
]
```

It is invalid to multiply whole-period phase-current RMS by the raw
single-device `1.55 mOhm`, because the high- and low-side paths have different
parallel counts and different conduction intervals. The reusable contract is
implemented in `src/scb_ivr/conduction_loss.py`.

## 3. Pre-execution implementation gates

A55 must not run until all of these gates pass:

1. **Path gate** - the period evaluator separately accumulates
   `integral_HS(i^2 dt)`, `integral_LS(i^2 dt)` and dead-time
   `integral(i^2 dt)` for every phase.
2. **Dynamics gate** - the periodic state is re-solved with distinct
   population-corrected high- and low-side on-resistances. A state solved
   with the old uniform `1 uOhm` switch boundary followed by a post-hoc real
   loss calculation is not self-consistent enough for A55's comparison.
3. **Dead-time-bound gate** - the search interval is explicitly sourced or
   labelled as sensitivity-only. A48's `2.15 ns` may be an initial sample but
   not an assumed lower bound.
4. **Baseline gate** - nominal, A54-critical and A54-margin points are all
   re-solved under the same new resistance/path-loss contract. A54's legacy
   `44.92 W` proxy may be quoted only as historical context, not used as the
   new optimization baseline.
5. **Regression gate** - automated tests confirm population scaling, path
   separation, dead-time exposure and preservation of the prior 247-test
   baseline. Eighteen new contract/path/dynamics checks raise the local total
   to 265 and the portable CI total to 246.

Current gate status:

| Gate | Status | Evidence |
|---|---|---|
| path gate | `PASS` | `path_resolved_period.py`, `run_path_gate_smoke.py`, `path_gate_smoke.json` |
| dynamics gate | `PASS` | asymmetric matrix extension plus nominal/critical/margin re-solves converge safely |
| dead-time-bound gate | `PASS (SENSITIVITY ONLY)` | `[0.5,10] ns`; inherited numerical coverage, not driver data |
| baseline gate | `PASS` | all three historical comparison points re-solved under the new contract |
| regression gate | `PASS` | 265 local / 246 portable tests |

## 4. Included objective terms

After Section 3 passes, define:

```text
partial_loss_proxy(LPHASE, dead_time)
    = path_resolved_channel_conduction_loss
    + residual_capacitive_turn_on_loss
```

- Channel conduction uses Section 2's path-resolved expression.
- Residual capacitive turn-on loss is evaluated per phase from that phase's
  residual switch voltage. A natural-ZVS phase contributes zero to this
  particular term; a hard-switched phase contributes the stated capacitance
  approximation.
- Every candidate must be evaluated at its own converged four-phase periodic
  state. Continuation from a nearby converged point is allowed and must be
  logged.

The constant-capacitance approximation remains a caveat. EPC2067's `Co(tr)`
is specified for a 0-to-20 V transition, while this model's switch swing is
approximately 12 V. An `Eoss(V)`/`Qoss(V)` model would be preferable if
traceable data are added later.

### Nominal-point dynamics smoke result

`asymmetric_nominal_smoke.json` records the first re-solve at P24's rated
`250 W/module` load setting and nominal `LPHASE=1.4666667 nH`, using
`RHS=0.775 mOhm` and `RLS=0.5167 mOhm` in the descriptor dynamics:

- Newton-converged relative residual: `1.91684e-12`;
- natural-ZVS flags: `[False, False, False, False]`;
- average output: `0.876876 V`;
- actual resistive-load power: `192.228 W`;
- maximum absolute phase current: `113.888 A` (`+/-250 A` gate passes);
- path-resolved channel-conduction loss: `8.59175 W`;
- dead-time current is present and remains unmodelled.

This is a dynamics/interface smoke result, not an optimization result. Its
large difference from A54's legacy `26.94 W` nominal conduction estimate
demonstrates why A54's raw-single-device/whole-period-RMS value cannot be used
as A55's baseline. Critical and margin points must be re-solved before any
trade-off conclusion is revisited.

The subsequent `asymmetric_baseline_points.json` recalculation closes the
three-point baseline gate:

| historical point | `LPHASE` | ZVS flags after asymmetric-Ron re-solve | actual load power | max `abs(iL)` | partial channel loss |
|---|---:|---|---:|---:|---:|
| nominal | `1.46667 nH` | `F/F/F/F` | `192.228 W` | `113.888 A` | `8.592 W` |
| A54 critical | `0.627406 nH` | `F/F/F/T` | `219.476 W` | `204.243 A` | `21.404 W` |
| A54 margin | `0.564665 nH` | `T/T/T/T` | `224.007 W` | `222.997 A` | `25.259 W` |

Thus A54's old critical point is no longer the all-phase-ZVS boundary once
the paper-specified parallel population is included in the dynamics. The
margin point remains all-phase ZVS, leaving only about `10.8%` current
headroom. A55 must locate a new critical boundary; it may not inherit A54's
old one.

## 5. Explicitly unmodelled terms

- **Gate-drive loss:** no locked `Qg` value is currently available. With
  device population, gate voltage and frequency fixed it is an additive
  constant across this two-variable search, so omitting it does not change
  the mathematical argmin, but it prevents an absolute total-loss claim.
- **Third-quadrant/reverse-conduction loss:** varies with dead time and may
  move the optimum. Its omission has no pre-declared favorable or unfavorable
  direction. Dead-time `i^2` exposure must still be exported so a sourced
  model can be inserted later.
- **Magnetic loss:** varies with the physical inductor used to realize a new
  `LPHASE`; it is not constant and may move the optimum. No material/geometry
  model is currently locked.
- **Thermal feedback:** the `1.55 mOhm` value is a 25 C typical value. A55
  does not yet solve junction temperature and temperature-dependent Ron.

## 6. Search and verification rules

- `module_power_w=250 W`, `Vin=48 V`, target `Vout=1 V`, `f_sw=5 MHz`, four
  phases and the existing flying-capacitor boundary remain fixed.
- Start the `LPHASE` exploration from `[0.62741, 1.4666667] nH`, inherited
  from A54, but do not assume A54's critical point remains critical after the
  dynamics model changes.
- Sweep dead time over `[0.5,10] ns` as a sensitivity range, always including
  the inherited `2.15 ns` reference point.
- Use a documented coarse search plus local refinement. Do not report a
  single evaluation as an optimum without a neighborhood check.
- At the selected point, repeat the established sub-step convergence ladder
  and report every phase separately.
- Every accepted candidate must remain inside `+/-250 A`; rejected/unsafe
  continuation probes remain logged but cannot become optimization points.

## 7. Permitted conclusions

A55 may compare its **partial loss proxy** against re-solved baselines under
the identical contract. It may identify a promising or unfavorable region
for a later complete device/magnetic model.

A55 may not claim:

- complete system-level or hardware loss;
- P24/P25 reproduction;
- hardware efficiency or thermal feasibility;
- that parameter retuning in this topology is "exhausted";
- a validated EPC2067 Section-II-B device choice (Table 3 belongs to the
  package-design section and does not identify the ZVS-mechanism device with
  certainty);
- SPICE confirmation until the selected point receives its own separately
  bounded cross-check.

## 8. Historical results retained, not silently rewritten

A53 and A54 remain valid as explicitly labelled sensitivity experiments under
their own uniform-Ron/post-hoc loss convention. Their files and numerical
results are not overwritten. A55 introduces a stricter contract; comparisons
must display both contracts rather than presenting recalculated A54 numbers as
if they were A54's original output.
