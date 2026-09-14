# A38 H2-to-H3 local two-residual solve results

Branch: `CROSS_PAPER_EXTENSION`, labelled P25 9% negative-current branch. Not a
2024-primary (`P24_EXPLICIT` 1-2%) result; see BOUNDARY.md Section 8.

> **Model-layer clarification (2026-09-14):** this run is
> `P25_DEVICE_AUGMENTED`. The `PHYSICAL_BOUNDARY_FAIL` grade below is limited
> to its original mixed requirement of reaching the P24 ideal 125-A reference
> with the non-ideal, event-gated device model while preserving ZVS. It is not
> evidence that the P24 topology or lossless Eq. (2) fails. The initial-state
> values remain `LOCAL_SOLVED_SEED`, not `VALID_PERIODIC_INITIAL_STATE`.

## 1. Whether the simulation completed normally

Yes. All 11 LTspice batch invocations in `solver_history.json` completed with
exit code 0 (no solver non-convergence; `subprocess.run(..., check=True)`
would have raised otherwise). Three of the eleven (iterations 1-3, probing
`IL2_INIT` below the A37 seed) produced no `V(xmod:gh2)` falling edge at all
inside the 205 ns observation window -- this is the controller correctly
reporting that H2 never completed (or never started) its own fixed-`TON`
conduction interval, the same kind of admission-blocking behavior A35-A37
already documented for H3/H4, recurring here for H2 itself. It is recorded as
`"h2_admission_missing": true` in those rows, not treated as a script error.

## 2. Parameters actually used

Locked (unchanged from A37/A36/A35, see BOUNDARY.md Section 3): topology,
`Coss` (385 pF high-side / 770 pF low-side), ideal reverse-conduction clamp
(`Vf=0`, `Ron=1 mOhm`), `LPHASE=1.466666666666667 nH`, `TON=16.6667 ns`,
`PHASE=50 ns`, `NEG_FRAC=.09`, output held at ideal 1 V, timestep/solver
options.

Frozen at A37's `best_candidate.json` seed (read from disk, not retyped):

| Variable | Frozen value |
|---|---:|
| `IL1_INIT` | 5.2947 A |
| `IL4_INIT` | 84.1447433786 A |
| `VC1_INIT` | 36.000066454 V |
| `VC2_INIT` | 23.9999142326 V |
| `VC3_INIT` | 12.0006048777 V |

Free variables and final values:

| Variable | Seed | Final | Changed? |
|---|---:|---:|:---:|
| `IL2_INIT` | 21.205095337 A | 21.205095337 A | **no** (deliberately left at seed; see Section 6) |
| `IL3_INIT` | 41.5782701063 A | 56.32056566312004 A | yes (solved) |

## 3. When each key event occurred (final candidate)

| Event | Time | Value |
|---|---:|---:|
| H1 on | 0.0007 ns | -- |
| H1 off (fixed `TON`) | 16.6681 ns | `iL1`=124.999908 A |
| H2 admission (natural `Vds=0` crossing) | 49.9998 ns | `Vds(H2)`=-0.000153 V |
| H2 off (fixed `TON`) | ~66.67 ns | `iL2`=117.7638 A |
| **H3 admission (natural `Vds=0` crossing)** | **100.0007 ns** | `Vds(H3)`=-0.000427 V, `iL3`=-1.265 A |
| H3 off (fixed `TON`) | 116.6681 ns | `iL3`=117.8069 A |
| H4 nominal slot (150 ns) | 150 ns | `Vds(H4)`=11.949 V -- **still `MISSED_ZVS_SLOT`, out of this experiment's scope (BOUNDARY.md Section 8)** |

H3 is now admitted essentially exactly on its 100 ns nominal slot, under
genuine ZVS (`Vds`=-0.43 mV, a small negative admission current of -1.265 A,
consistent with the reverse-conduction/negative-current ZVS mechanism used
throughout this project) -- this is the H2-to-H3 `MISSED_ZVS_SLOT` gap A37
diagnosed (67-79 ns against the 100 ns slot) fully closed. H4's own slot at
150 ns remains missed, exactly as expected: A38 does not touch phase 4 and
makes no claim about it (BOUNDARY.md Section 8).

## 4. Key voltages and currents

Final candidate residuals (target 0 for every residual; tolerance `2e-4` in
the residual's own unit, matching A36's achieved order of magnitude, per
BOUNDARY.md Section 6):

| Residual | Value | Unit | Converged? |
|---|---:|---|:---:|
| **R1** = `iL2(TON2 end) - 125A` | -7.236176 | A | **NOT converged** |
| **R2** = `Vds(H3)@100ns - 0V` | -0.0000343 | V | **CONVERGED** |
| R2 (crossing-time form, for reference) | -0.0000208 | ns | **CONVERGED** |
| Recheck: `peak_error_h1_a` (A36's R1) | -0.0000916 | A | **CONVERGED** (held) |
| Recheck: `Vds(H2)@50ns` (A36's R2, voltage form) | -0.0001526 | V | **CONVERGED** (held) |
| Recheck: H2 crossing-time form, for reference | -0.0001942 | ns | **CONVERGED** (held) |

A36's original two residuals (H1's own peak-current residual and H2's own
ZVS-timing residual) remain converged at their pre-A38 tolerance because
`IL2_INIT` was deliberately never moved (Section 6). R2 (the new H2-to-H3 ZVS
residual this experiment targeted) is fully converged. R1 (H2's own
fixed-`TON` peak-current shortfall) is **not** converged and, per Section 6
below, could not be converged by adjusting `IL2_INIT` without destroying the
already-converged H2 admission-timing residual.

Corroborating evidence that the ~7.2 A shortfall is structural rather than a
consequence of the specific `IL2_INIT` value: **H3, whose own admission
current and `IL3_INIT` were freely solved in this experiment, shows the same
shortfall** -- `iL3` at H3's own fixed-`TON` off is 117.807 A, an error of
-7.193 A against the 125 A target, essentially identical to H2's -7.236 A.
Neither phase's initial-current variable was tuned to fix this; it recurs
independently in both, consistent with a shortfall built into the
fixed-`RDS(on)`/fixed-`TON`/admission-near-`-INEG` volt-second budget itself,
not into either phase's specific initial condition.

## 5. Whether the acceptance condition was met

No. BOUNDARY.md Section 6's success condition requires **both** R1 and R2 to
converge. R2 converges to numerical-edge tolerance; R1 does not, and Section 6
of this report shows it cannot be driven to zero via `IL2_INIT` inside the
region where H2 still achieves its own admission at all.

## 6. Where the first failure boundary occurred, and why `IL2_INIT` was left unmoved

Per BOUNDARY.md Section 6, `IL2_INIT` was empirically probed (not assumed)
before any correction was applied, because A36's one-shot affine correction
(`il1_new = il1 - peak_error`, slope~1) relies on H1's `TON` beginning at an
*absolute* time (`t=0`); H2's own turn-on is *event*-gated
(`(time>=50ns)*(Vds(H2)<=0)`, itself preceded by `I(LIND2)` having to cross 0
then `-INEG`), so the same slope assumption is not guaranteed to hold and had
to be checked first.

`IL2_INIT` was perturbed by `{-2, -1, -0.5, +0.5, +1, +2}` A around the seed
(iterations 1-6), holding `IL3_INIT` at its own seed. The result is a sharp,
asymmetric structural boundary:

| `IL2_INIT` delta | H2 admission? | `peak_error_h2_a` | H2's own crossing time |
|---:|:---:|---:|---:|
| -2.0 A | **missing** (no `TON2` window at all) | -- | -- |
| -1.0 A | **missing** | -- | -- |
| -0.5 A | **missing** | -- | -- |
| 0 (seed) | yes | -7.2343 A | 49.9998 ns |
| +0.5 A | yes | -7.2281 A | 50.7215 ns |
| +1.0 A | yes | -7.2209 A | 51.4430 ns |
| +2.0 A | yes | -7.2037 A | 52.8852 ns |

Two findings follow directly from this table:

1. **The A36-solved seed sits within about 0.5 A of a hard admission cliff.**
   Any tested decrease breaks H2's own fixed-`TON` window outright (not a
   small ZVS-timing degradation -- H2 simply never completes `TON2` inside
   the observation window). This was not previously visible because A37's
   joint search barely moved `IL2_INIT` away from its converged value.
2. **The empirical local slope of R1 against `IL2_INIT` is only
   `+0.0162 A per A`** (linear fit across the four working probe points).
   Reaching `R1=0` from the seed's `-7.234 A` would require
   `Delta(IL2_INIT) = 7.234 / 0.0162 ~= 446 A` -- three orders of magnitude
   past the `+2 A` range in which H2 still achieves admission at all, and
   already at just `+2 A` the admission time has drifted `2.89 ns` past its
   `50 ns` slot (a `+1.45 ns` drift per A), which would blow through A36's
   converged ZVS-timing residual long before R1 could move meaningfully.

The driver script (`solve_a38_h2_h3_local.py`) encodes this decision rule
explicitly (`r1_pursuable_via_il2_init`, computed from the probed slope and
range, not asserted): it is `false` for this run, so `IL2_INIT` was left at
A37's seed value rather than silently retuned, and `IL3_INIT` alone was then
bracketed and secant-solved against R2 (mirroring A36's method exactly),
converging in 4 further evaluations (iterations 7-10) to
`IL3_INIT=56.32056566312004 A`.

**This is a `PHYSICAL_BOUNDARY_FAIL` on R1, not a `LOCAL_PASS` traded against
A36's residuals**, because A38 never moved `IL2_INIT` away from its
A36/A37-validated value -- A36's own two residuals are therefore still
converged (Section 4), at the direct cost of R1 remaining unconverged. Per
BOUNDARY.md Section 7's first bullet ("If no (IL2_INIT, IL3_INIT) pair
satisfies both R1 and R2 simultaneously... report exactly which residual
could not be driven to zero and what the best achievable joint value was"):
the residual that cannot be driven to zero is R1 (`peak_error_h2_a`); the
best achievable joint value is
`(IL2_INIT, IL3_INIT) = (21.205095337, 56.32056566312004)`, at which R2 and
both of A36's original residuals converge and R1 sits at `-7.236 A`.

## 7. Result grade

**`PHYSICAL_BOUNDARY_FAIL`** (on R1 specifically; R2 and A36's original two
residuals all converged). H2-to-H3's `MISSED_ZVS_SLOT` gap A37 diagnosed is
fully resolved by this experiment: H3 now achieves genuine ZVS admission
almost exactly on its 100 ns nominal slot. But this experiment's own second
residual, H2's own fixed-`TON` peak-current shortfall, was found -- by direct
empirical probing, not assumption -- to be structurally insensitive to
`IL2_INIT` within the entire region where H2's own admission still functions
at all; no `(IL2_INIT, IL3_INIT)` pair exists that satisfies both R1 and R2
without abandoning H2's own admission (which the probed data shows happens
for any `IL2_INIT` decrease, and for the increase needed to move R1
meaningfully). Per BOUNDARY.md Section 6/7, this is graded and reported
exactly as found, not averaged into a partial pass.

## 8. Which module should be adjusted next

Two independent findings, per Section VI/XI neither authorizing retuning
`TON`, `Coss`, capacitor/inductor values, or the 9% label:

1. **The H2-to-H3 ZVS-timing gap is solved and this method generalizes.**
   `IL3_INIT` alone, secant-solved exactly like A36's original H1-to-H2
   method, closed the ~20-30 ns crossing-time gap A37 could not close in its
   blind joint search -- confirming A37's own recommendation that a directed
   local search would succeed where the joint Jacobian could not. The next
   phase pair (H3-to-H4, using `IL3_INIT`/`IL4_INIT` an analogous way) is a
   plausible next directed local search, but BOUNDARY.md Section 8 already
   flags that success there is not guaranteed to compose with this result.
2. **The ~7.2 A fixed-`TON` peak-current shortfall is a separate, structural
   finding that recurs on both H2 and H3 and is not fixable by either
   phase's own initial-current variable.** Since it appears in both phases
   independently of their respective solved/frozen `ILk_INIT` values, the
   next authorized investigation is into what the shortfall's actual driver
   is (e.g., `RDS(on)` drop during `TON`, the `-INEG` admission current level
   itself, or the volt-second budget available during a fixed 16.6667 ns
   window) -- not another local initial-current solve, since Section 6 has
   now shown that lever is exhausted for this residual on both phases where
   it was tested.

## 9. Which parameters must never be changed because of this failure

Per Section XI, unchanged by this result: `TON=16.6667 ns` must never be
extended to force `iL2`/`iL3` up to 125 A; `Coss`, capacitor values, and
`LPHASE` must not be changed to fit a result; the 9% negative-current label
must not be raised to manufacture a peak-current match, and must never be
reported as the 2024 2% result; the reverse clamp must not be held active
without reverse current present (it was not, in any of the 11 runs); and the
100 ns slot definition/tolerance must not be loosened to call R1 converged.
`IL1_INIT`, `IL4_INIT`, and the three `VCk_INIT` values remain frozen exactly
as inherited from A37; this experiment gives no reason to reopen any of them.
`IL2_INIT` must not be silently retuned in a future experiment to chase R1
without explicitly naming that as a new change and accepting that it reopens
(and, per Section 6's data, is very likely to immediately break) A36's own
already-converged H2 admission.
