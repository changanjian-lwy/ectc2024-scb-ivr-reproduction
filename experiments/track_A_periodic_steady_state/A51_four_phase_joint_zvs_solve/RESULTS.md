# A51 result - searching for a self-consistent four-phase joint periodic ZVS state

Track: A. Python-solver experiment (no SPICE run). Boundary: `BOUNDARY.md` in
this directory, unmodified by this run.

---

## 0. Verdict, stated first

**At the operating point `BOUNDARY.md` specifies** (`d = 2.15 ns` from A48's own
bracket, `CFLY = 3 uF`, GS61008T `385 pF / 770 pF`, `48 V -> 1 V`, 250 W per
module, `5 MHz`, `Ton = 16.6667 ns`):

> **A genuine fixed point `z* = F(z*)` was found** -- relative residual
> **`2.258e-11`**, four Newton iterations, against the pre-declared `1e-6`
> tolerance -- **and NOT ONE of the four phases achieves a natural zero-voltage
> crossing.** All four hard-switch, each absorbing essentially its entire
> blocking voltage: `12.046 / 11.811 / 11.811 / 12.562 V`.

That is **`BOUNDARY.md` Section 6's SECOND named outcome**: a fixed point found,
with phases hard-switching. It is the headline result of this experiment.

The failure is not marginal and it is not a device limitation. Each phase needs
roughly `-10 A` to `-11.6 A` of negative current at its own turn-on window to
commutate; the self-consistent periodic state supplies `-0.79 A` to `-0.87 A`,
i.e. **`7%` to `9%` of what is required**. The reason is a ripple/load balance
that is fixed by the topology and the duty, quantified in Section 7.

**A second, larger result.** Because the fast solver makes it cheap, the search
was repeated across a load ladder with **everything else held at
`BOUNDARY.md`'s own values** -- same `2.15 ns` dead time, same `CFLY = 3 uF`,
same GS61008T, same `Ton = 16.6667 ns`. At **`190 W` nominal** the solver
converges (residual `4.78e-07`, inside the `1e-6` tolerance) to a fixed point at
which **all four phases achieve a natural zero-voltage crossing**, on a
flying-capacitor ladder that stays balanced (`35.78 / 23.79 / 11.79 V` against
the nominal `36 / 24 / 12`) at `Vout = 0.9716 V`:

> | | phase 1 | phase 2 | phase 3 | phase 4 |
> |---|---:|---:|---:|---:|
> | natural ZVS | **yes** | **yes** | **yes** | **yes** |
> | minimum `\|Vds\|` | `11.79 mV` | `10.68 mV` | `11.10 mV` | `19.27 mV` |
> | crossing delay | `1537.2 ps` | `1511.9 ps` | `1512.0 ps` | `1027.0 ps` |
> | margin inside the `2150 ps` window | `612.8 ps` | `638.1 ps` | `638.0 ps` | `1123.0 ps` |

**As far as this project's own records go, this is the first self-consistent
four-phase joint periodic ZVS state found by any method** (Section 9,
independently verified with step-size convergence in Section 9.4). It is
reached by lowering the load by about `24%` from P24's rated `250 W`, and it is
`SENSITIVITY_ONLY`: `190 W` is **not** a P24 operating point and this is **not**
a P24/P25 reproduction. What it establishes is that the obstruction found at
`250 W` is a load/ripple balance with a sharp, locatable boundary (between `190`
and `200 W` for phases 1-3, between `200` and `225 W` for phase 4), not a
structural impossibility of the topology or a limitation of the GS61008T.

A third fixed point with four natural crossings exists at `d = 10 ns` (Section
8.1), but it is far less interesting: it sits at `0.706 V` / `124.7 W` on a badly
unbalanced ladder (`39.23 / 17.19 / 8.53 V`) with phase 2 carrying `129.4 A`
against `76 A` in the other three.

All three fixed points are **locally stable** (spectral radii `0.9825`, `0.9927`,
and Section 9.4 for the `190 W` one), so none is a knife-edge artifact.

Every number below comes from the scripts in this directory and is recorded in
`results.json`. Nothing is quoted from memory.

---

## 1. Step 2 - independent re-verification of `BOUNDARY.md` Section 1 (CFLY)

`BOUNDARY.md` Section 1 reports a `CFLY = 53.8 uF` vs `3 uF` sensitivity check.
A51 builds on that conclusion, so it was re-derived rather than trusted.

Method (`run_cfly_reverification.py`): A50's own committed `a42_local_
validation.py` is imported and run **unmodified**; the only intervention is
rebinding its module-level constant `CFLY_A42_F` at runtime before calling
`build_case`. No A50 file is edited. Both values are run over A50's own sub-step
ladder, because A50 Section 3.3 established that a single sub-step cannot answer
a millivolt-margin ZVS question under backward Euler.

| `CFLY` | `7.76%` min `\|Vds\|` @ `0.0625 ps` | `BOUNDARY.md` Section 1 | `7.76%` crossed | `7.77%` crossed | `7.77%` sign change @ `0.0625 ps` | `BOUNDARY.md` Section 1 |
|---|---:|---:|:---:|:---:|---:|---:|
| `53.8 uF` | **`7.867228 mV`** | `7.867 mV` | no | yes | **`23.14711541 us`** | `23.14711541 us` |
| `3 uF` | **`9.093753 mV`** | `9.094 mV` | no | yes | **`23.14711995 us`** | `23.14711995 us` |

**Both rows reproduce `BOUNDARY.md` Section 1 to every published digit**, and
the qualitative conclusion holds: the `7.76%`-no-cross / `7.77%`-cross bracket is
unchanged by the correction. Richardson-extrapolated values are
`7.430187 mV` / `23.14711387 us` (`53.8 uF`) and `8.656738 mV` / `23.14711821 us`
(`3 uF`).

Two honest corrections to `BOUNDARY.md` Section 1's own prose, neither of which
changes its conclusion:

1. Section 1 writes the crossing-time agreement as "within `5 ns` of an `23 us`-
   scale absolute time". The measured difference is **`4.5389 ps`**, three orders
   of magnitude tighter than claimed. The conclusion is stronger than stated.
2. Section 1 says `CFLY` "does not appear in it at all". That is true of
   `analytic_lossless_commutation`'s closed form, but not of the full
   descriptor: the measured `7.76%` minimum `|Vds|` moves by
   **`+1.2265 mV` (`+15.6%` of that quantity)** when `CFLY` is corrected. The
   size is exactly what the series-capacitance loading predicts
   (`CH/CFLY = 385pF/3uF = 1.28e-4` of an `11.98 V` swing `= 1.5 mV`), so it is a
   real, explainable `CFLY` effect and not numerical noise. It does not move the
   bracket, so the Section 1 conclusion stands, but "`CFLY` is irrelevant" is
   accurate only for the idealized closed form.

One new caveat this re-verification adds, in A50's own spirit: **at a `1 ps`
sub-step the corrected `CFLY = 3 uF` case reports NO crossing at `7.77%`**
(min `|Vds| = 1.6296 mV`) while the legacy `53.8 uF` case reports a crossing
(`0.4022 mV`). The corrected value needs `<= 0.5 ps` to resolve the same verdict.
A50's own "`50 ps` is inadequate" warning tightens by another factor of two under
the corrected `CFLY`.

A51 uses `CFLY = 3 uF` throughout, per `BOUNDARY.md` Section 1.

---

## 2. The one-period map `F(z)` (`BOUNDARY.md` Section 3)

`a51_period_map.py`. A50's `solver_copy/` is imported read-only through
`sys.path`; **no file under `A50_zvs_capable_solver_prototype/` is modified, and
`src/scb_ivr/` is neither imported nor read** (asserted at runtime, test 1 of
Section 2.2 below).

### 2.1 Period reference and interval structure

`t0` is A37's own `T0`: phase 1's own commanded high-side turn-on instant,
`BASE_PERIOD_INDEX * T + d/2 = 23.001075 us` -- the 116th period, past the
`22.87 us` input ramp so the descriptor's constant-`Vin` precondition holds (the
same base period A50's own gate 2 used). With `T = 200 ns`, `Ton = 16.6667 ns`,
`d = 2.15 ns` the period `[t0, t0+T)` tiles exactly, with no gap and no overlap,
into all eight commanded dead-time windows and the conduction intervals between
them (local ns, relative to `t0`):

```
ph1 HIGH [0, 14.5167)   ph1 turn-OFF DT [14.5167, 16.6667)   normal [16.6667, 47.85)
ph2 turn-ON DT [47.85, 50)    ph2 HIGH [50, 64.5167)   ph2 turn-OFF DT [64.5167, 66.6667)
ph3 turn-ON DT [97.85, 100)   ph3 turn-OFF DT [114.5167, 116.6667)
ph4 turn-ON DT [147.85, 150)  ph4 turn-OFF DT [164.5167, 166.6667)
ph1 turn-ON DT [197.85, 200)
```

### 2.2 Why `F` is not affine, and how each window is resolved

With a purely time-commanded schedule the model would be linear and `F` affine.
It is not, because the switching instants are **state-dependent**, exactly as in
A37's own event machine:

* **turn-ON window of phase `p`**: A50's own `resolve_deadtime_window` is called
  UNCHANGED on the whole commanded window and produces the reported ZVS verdict.
  If `Vds_p` reaches zero inside it (A37's own `.rule ... V(vin,a1)<=0`
  admission rule, A27's ideal reverse clamp), the high side is forced on from
  that instant -- NATURAL ZVS. Otherwise the commanded schedule turns it on at
  the window end with whatever `Vds` remains -- HARD SWITCH, and that residual is
  recorded.
* **turn-OFF window of phase `p`**: the low side is admitted at `V(x_p) <= 0`,
  mirroring A37's own `.rule P1_M2 P1_M3 V(x1)<=0`.

**Sub-grid crossing refinement.** Each admission instant is refined off the
sub-step grid by bisection (`_refine_crossing`). This is not cosmetic: at a
low-side crossing `dV/dt` is of order `100 V/ns`, so a `5 ps` grid would put a
`~0.5 V` staircase discontinuity into `F`, which would floor the attainable
fixed-point residual near `1e-2` relative and make the Jacobian meaningless.
With refinement, the finite-difference derivative `dF/d(iL1)` is stable to four
digits across `h = 1e-3 ... 1e-6 A`.

### 2.3 Self-tests (`run_map_selftests.py`, all pass)

| Test | Result |
|---|---|
| Import isolation | no `scb_ivr*` module loaded; no `solver_copy` module resolves under `src/scb_ivr/` |
| A50's kernel used unchanged | `_advance_forced` with the commanded mode is **bitwise identical** to `advance_fixed_diode_step` (max difference `0.0` over 8 sampled steps) |
| Interval cover exact | no gaps, total `2.0000000000000147e-07 s` vs `T = 2e-07 s`, exactly four turn-on and four turn-off windows |
| Seed conversion round-trip | `VC1/VC2/VC3` and `IL1..IL4` recovered from the 20-vector, worst deviation `0.0` |
| `I_VSTEP` is algebraic | `\|E[:,I_VSTEP]\|inf = 0.0`; perturbing it by `1e6` leaves `F(z)` bitwise unchanged |

### 2.4 Step-size convergence of `F` itself (`BOUNDARY.md` Section 4.4 discipline)

At the A37 seed, both discretizations were laddered. Differences halve cleanly
(first-order backward Euler, as A50 Section 3.3 established), and **the ZVS
verdicts are identical at every rung**:

| sub-step | rel. residual | ZVS flags | `\|z_next\|` change vs previous rung |
|---:|---:|---|---:|
| `50 ps` | `9.296797e-02` | `[F,F,T,T]` | - |
| `20 ps` | `9.316088e-02` | `[F,F,T,T]` | `8.012e-02` |
| `10 ps` | `9.323116e-02` | `[F,F,T,T]` | `2.773e-02` |
| `5 ps` (search) | `9.326867e-02` | `[F,F,T,T]` | `1.440e-02` |
| `2 ps` | `9.329183e-02` | `[F,F,T,T]` | `8.582e-03` |
| `1 ps` | `9.329964e-02` | `[F,F,T,T]` | `2.895e-03` |

| coarse step | rel. residual | ZVS flags | `\|z_next\|` change |
|---:|---:|---|---:|
| `0.5 ns` | `9.341170e-02` | `[F,F,T,T]` | - |
| `0.25 ns` | `9.332934e-02` | `[F,F,T,T]` | `4.871e-02` |
| `0.125 ns` | `9.328879e-02` | `[F,F,T,T]` | `2.363e-02` |
| `0.0625 ns` (search) | `9.326867e-02` | `[F,F,T,T]` | `1.172e-02` |
| `0.03125 ns` | `9.325865e-02` | `[F,F,T,T]` | `5.839e-03` |

The search runs at `sub_step = 5 ps`, `coarse_step = 0.0625 ns` (the latter is
A50 gate 1's own published step). **This sets an honest floor on what `z*` means:
`F` is deterministic, so the fixed-point residual can and does reach `1e-11`,
but `z*` itself is only defined to about `1e-2 V` absolute (`~3e-4` relative)
across the discretization ladder.** Section 8 re-solves at `20 ps` and `1 ps` and
confirms the ZVS verdicts and the orbit do not depend on this.

---

## 3. Step 4 - the seed-state conversion, shown explicitly

A37's netlist is node-for-node the descriptor's own topology (`SH1 vin a1`,
`SH2 a1 a2`, `SH3 a2 a3`, `SH4 a3 x4`; `SL1..SL4 x1..x4 g`; `C1 a1 x1`,
`C2 a2 x2`, `C3 a3 x3`; `LIND1..4 x1..x4 out`), so A37's own seven published
coordinates map directly. A37's `.ic` line supplies eight more. Five descriptor
variables have no A37 analog at all (A37 has a hard `48 V` source, no source
inductance and no precharge divider) and are stated as such:

| descriptor variable | seed value | source |
|---|---:|---|
| `src` | `48` | A37 `V1 vin 0 {VIN}` hard source; equals `input_voltage_v(t0)` post-ramp |
| `src_r` | `48` | no A37 analog; seeded equal to `src` (zero drop across `source_resistance_ohm`) |
| `vin` | `48` | A37 `.ic V(xmod:a1)=48` with `SH1` closed at `T0` => `vin = a1` |
| `tap3` | `36` | **no A37 analog** (Track-B precharge divider); equal-series equilibrium `3*48/4` |
| `tap2` | `24` | **no A37 analog**; `2*48/4` |
| `tap1` | `12` | **no A37 analog**; `1*48/4` |
| `a1` | `48` | A37 `.ic V(xmod:a1)=48` |
| `a2` | `24` | A37 `.ic V(xmod:a2)=24` |
| `a3` | `12` | A37 `.ic V(xmod:a3)=12` |
| `x1` | `11.999933546` | A37 `.ic V(xmod:x1)={48-VC1_INIT}`, carries `VC1_INIT=36.000066454` |
| `x2` | `8.57674000017e-05` | A37 `.ic V(xmod:x2)={24-VC2_INIT}`, carries `VC2_INIT=23.9999142326` |
| `x3` | `-0.000604877700001` | A37 `.ic V(xmod:x3)={12-VC3_INIT}`, carries `VC3_INIT=12.0006048777` |
| `x4` | `0` | A37 `.ic V(xmod:x4)=0` (phase 4's low side conducting) |
| `out` | `1` | A37 `.ic V(out)=1` |
| `LPAR_IN` | `5.20833333333` | **no A37 analog**; `250 W / 48 V` average input current |
| `L1` | `5.2947` | A37 `IL1_INIT` |
| `L2` | `21.205095337` | A37 `IL2_INIT` |
| `L3` | `41.5782701063` | A37 `IL3_INIT` |
| `L4` | `84.1447433786` | A37 `IL4_INIT` |
| `I_VSTEP` | `-5.20833333333` | **algebraic** -- its column of `E` is exactly zero, so it provably cannot influence `F` (self-test 5); seeded `-LPAR_IN` for MNA sign consistency |

The conversion is asserted in code: the table's own variable order must equal
`assemble_descriptor`'s own `variable_names`, and `a_j - x_j` must reproduce
`VCj_INIT` exactly (worst deviation `0.0`). The ordering check is what makes
this a conversion rather than an assumption.

---

## 4. Steps 3/4 - the fixed-point search

`run_fixed_point_search.py`. Method: **semi-smooth (policy) Newton**. The reason
is structural: with the event structure held fixed, the model is linear and
time-invariant, so `F` is *exactly* affine on that branch and one Newton step
with a finite-difference Jacobian lands exactly on that branch's own fixed
point. Only a change of event structure can spoil it, and that is detected and
the Jacobian rebuilt. Damped Picard is run from the same seed as an independent
check that the Newton answer is not an artifact of the linear solve.

### 4.1 Newton iteration history (relative residual = `|F(z)-z|inf / max(|z|inf,1)`)

| it | relative residual | absolute residual (inf) | natural-ZVS flags | Jacobian rank | out-of-range residual | damping |
|---:|---:|---:|---|---:|---:|---:|
| 1 | `9.326867e-02` | `7.848068e+00` | `[F,F,T,T]` | 17 | `1.605e-07` | `1.0` |
| 2 | `8.583253e-02` | `7.673113e+00` | `[F,F,F,F]` | 17 | `3.576e-08` | `1.0` |
| 3 | `4.267798e-06` | `3.826619e-04` | `[F,F,F,F]` | 17 | `3.764e-12` | `1.0` |
| 4 | **`2.258171e-11`** | **`2.024738e-09`** | `[F,F,F,F]` | - | - | converged |

Converged at iteration 4, **five orders of magnitude inside the pre-declared
`1e-6` tolerance**, with the 50-iteration budget never approached and never
extended. The Jacobian was rebuilt twice (iterations 1 and 2), once per event-
structure change; after iteration 2 the structure was stable and the map was
affine on that branch, which is why iterations 3 and 4 collapse quadratically.
67 `F` evaluations total, 113 s wall clock.

### 4.2 The three-dimensional degeneracy, identified

A50 gate 1 reported "map size / least-squares rank / nullity = 20 / 17 / 3"
without saying which three directions. A51 measured it: the singular values of
`(J - I)` at the seed are

```
269.3, 47.0, 26.5, 22.0, 12.4, 1.015, 1.000, 1.000, 1.000, 0.99991,
0.99921, 0.97846, 6.12e-3, 3.48e-3, 2.61e-3, 2.00e-3, 8.14e-5,
2.18e-9, 1.69e-9, 4.84e-11
```

and the right-singular vectors of the three smallest are supported almost
entirely on `tap3`, `tap1` and `tap2`. **The nullity-3 is exactly the three
precharge-divider tap voltages**: `F` is the identity on them. Measured directly
by perturbing each tap by `1 V` and propagating one period:

| tap | identity defect after one period | largest effect on any stage variable |
|---|---:|---:|
| `tap3` | `-2.771e-13 V` | `1.833e-10 V` |
| `tap2` | `-5.222e-13 V` | `1.247e-10 V` |
| `tap1` | `+2.984e-13 V` | `5.575e-10 V` |

Leaving them in the least-squares solve divides a `~1e-10` residual by a `~1e-9`
singular value and throws the taps to physically meaningless voltages (a first
attempt did exactly that: `tap3 = 95.9 V`, `tap2 = -56.1 V`, `tap1 = 123.4 V`,
with `103.6 V` of precharge-diode forward bias) while changing nothing
electrically. They are therefore **pinned at their seeded equal-series values and
excluded from the unknowns**, and the resulting divider admissibility is audited
in Section 8.3. This is a reported modelling decision, not a silent one.

### 4.3 Damped Picard, from the same seed - and what it found

Picard (`z <- z + 0.5 (F(z) - z)`, 25 iterations) **does not converge**. It falls
to `~1.2e-2` relative by iteration 17 and then oscillates between `1.2e-2` and
`1.6e-2` without further progress:

| it | 1 | 3 | 5 | 7 | 9 | 11 | 13 | 15 | 17 | 19 | 21 | 23 | 25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rel. residual | `9.33e-2` | `5.26e-2` | `3.70e-2` | `2.54e-2` | `2.31e-2` | `1.89e-2` | `1.33e-2` | `1.23e-2` | `1.20e-2` | `1.43e-2` | `1.57e-2` | `1.55e-2` | `1.37e-2` |
| ZVS flags | `[F,F,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,T,T]` | `[T,T,F,T]` | `[T,T,F,T]` |

This is itself informative and is reported rather than discarded: **states in
which all four phases DO cross naturally exist in the neighbourhood of the A37
seed -- Picard visits them for twenty consecutive iterations -- but they are not
periodic.** Their one-period non-closure sits at `1.2e-2` relative, i.e. about
`0.6 V` / order-`1 A` of drift per period, nine orders of magnitude above the
fixed point Newton actually reaches. ZVS-capable and self-consistent are
different properties here, and only the latter is what `BOUNDARY.md` asks for.

---

## 5. The recovered fixed point `z*` and its orbit

`d = 2.15 ns`, `CFLY = 3 uF`, `Rds(on) = 1 uOhm` (framework default, A50's own
validated configuration), 250 W nominal, relative residual `2.258171e-11`.

| variable | `z*` | | variable | `z*` |
|---|---:|---|---|---:|
| `src` | `48.0000000000` | | `x2` | `-2.8813e-05` |
| `src_r` | `47.9594621045` | | `x3` | `-5.8943e-05` |
| `vin` | `47.9641165251` | | `x4` | `-8.9663e-05` |
| `tap3` / `tap2` / `tap1` | `36` / `24` / `12` (pinned) | | `out` | `0.877870955` |
| `a1` | `35.9203342987` | | `LPAR_IN` | `4.0537895594` |
| `a2` | `23.8807510516` | | `L1` | `-0.7939768532` |
| `a3` | `11.9423331966` | | `L2` | `29.0111790317` |
| `x1` | `0.1012125634` | | `L3` | `58.9426607004` |
| | | | `L4` | `89.6627460474` |
| | | | `I_VSTEP` | `-4.0537895594` |

Orbit metrics over the recovered period:

| quantity | value |
|---|---|
| flying-capacitor voltages `VC1/VC2/VC3` at `z*` | `35.8191 / 23.8808 / 11.9424 V` |
| phase-current minima | `-0.7940 / -0.8372 / -0.8372 / -0.8673 A` |
| phase-current maxima | `110.3376 / 110.0287 / 110.0287 / 110.8370 A` |
| average output voltage | `0.877903 V` |
| average load power | `192.679 W` |
| average input-inductor current | `4.0538 A` |

Two observations that matter for reading the rest of this document:

1. **The flying-capacitor ladder is well balanced** (`35.82 / 23.88 / 11.94 V`
   against the ideal `36 / 24 / 12`), so this fixed point is the physically
   expected balanced operating point, not a degenerate one.
2. **The output settles at `0.878 V`, not `1.006 V`.** This is not an error: the
   dead time removes `2.15 ns` from each `16.667 ns` commanded on-time, and
   `1.006 * 14.5167/16.6667 = 0.876 V`. Dead time costs duty, and at a fixed
   `Ton` there is no loop to recover it. A50 gate 1's own `1.00601 V` was the
   `d = 0` ideal orbit; this is the same orbit with real dead time.

---

## 6. Step 5 - per-phase ZVS verdicts, each verified independently

`run_final_verification.py`, at `z*`. Every phase is treated separately -- **no
symmetry is assumed anywhere**, per A44's own finding, and Section 6.2 shows how
right A44 was. Each window's verdict comes from A50's own unchanged
`resolve_deadtime_window`.

### 6.1 Sub-step convergence, per phase (A50 Section 5's mandatory discipline)

Minimum `|Vds|` over each phase's own commanded `2.15 ns` turn-on window (V):

| sub-step | phase 1 | phase 2 | phase 3 | phase 4 |
|---:|---:|---:|---:|---:|
| `50 ps` | `12.027732692` | `11.800492880` | `11.800467858` | `12.214287197` |
| `20 ps` | `12.038336244` | `11.806866372` | `11.806840869` | `12.214287197` |
| `10 ps` | `12.041948710` | `11.809066643` | `11.809040975` | `12.214287197` |
| `5 ps` | `12.043782246` | `11.810188834` | `11.810163081` | `12.214287197` |
| `2 ps` | `12.044888417` | `11.810867579` | `11.810841780` | `12.214287197` |
| `1 ps` | `12.045258152` | `11.811094734` | `11.811068922` | `12.214287197` |
| `0.5 ps` | `12.045443242` | `11.811208487` | `11.811182661` | `12.214287197` |
| `0.25 ps` | `12.045535850` | `11.811265412` | `11.811239554` | `12.214287197` |
| `0.125 ps` | `12.045582219` | `11.811293867` | `11.811268026` | `12.214287197` |
| `0.0625 ps` | `12.045605471` | `11.811308094` | `11.811282245` | `12.214287197` |
| **Richardson** | **`12.045628724`** | **`11.811322322`** | **`11.811296463`** | **`12.214287197`** |

**No phase crosses at any sub-step.** The differences halve cleanly (first
order), and the verdict is identical from `50 ps` to `0.0625 ps` -- unlike A50's
own gate-2 case, this one is nowhere near a resolution-sensitive margin. The
worst normalized linear-system backward error anywhere was `~2e-17`, so this is
physics, not a failing solve.

Per-phase detail at `z*`:

| | phase 1 | phase 2 | phase 3 | phase 4 |
|---|---:|---:|---:|---:|
| window (local ns from `t0`) | `[197.85, 200.00)` | `[47.85, 50.00)` | `[97.85, 100.00)` | `[147.85, 150.00)` |
| high-side branch | `vin-a1` | `a1-a2` | `a2-a3` | `a3-x4` |
| `Vds` at window start | `12.144853 V` | `12.210239 V` | `12.210234 V` | `12.214287 V` |
| minimum `\|Vds\|` (Richardson) | `12.045629 V` | `11.811322 V` | `11.811296 V` | `12.214287 V` |
| **natural ZVS** | **no** | **no** | **no** | **no** |
| **residual `Vds` at forced turn-on** | **`12.045605 V`** | **`11.811308 V`** | **`11.811282 V`** | **`12.562362 V`** |
| `iL` at window entry | `+0.678743 A` | `+0.368614 A` | `+0.368580 A` | `+1.154924 A` |
| `iL` minimum over the orbit | `-0.7940 A` | `-0.8372 A` | `-0.8372 A` | `-0.8673 A` |

Phase 4 is the worst of the four and is worth calling out: its `Vds` never even
starts to fall -- it **rises** from `12.214 V` to `12.562 V` across the window,
so the forced turn-on absorbs `0.348 V` *more* than the blocking voltage it
started with. Phases 1-3 at least dip, by `99 / 399 / 399 mV` respectively.

### 6.2 Measured participating capacitance - A44 was right, and by how much

A50 Section 3.1 argued *structurally* that phase 4 commutates `1155 pF` while
phase 1 commutates `1540 pF`, because node `a1` carries two high-side switches.
A51 **measured** it, by perturbing only that phase's own inductor current inside
the held dead-time mode and reading the initial `dV(x_p)/dt` (`measure_node_
capacitance_f`; a differential measurement, so no closed form or network
assumption enters):

| phase | measured participating capacitance | A50's structural prediction | agreement |
|---|---:|---:|---:|
| 1 | **`1539.1625 pF`** | `1540 pF` | `0.054%` |
| 2 | **`1538.5264 pF`** | (`1540 pF`, "worse still") | `0.096%` |
| 3 | **`1538.5746 pF`** | (`1540 pF`, "worse still") | `0.093%` |
| 4 | **`1154.3617 pF`** | `1155 pF` | `0.055%` |

(step ladder `2 / 1 / 0.5 / 0.25 ps`, converged to the 4th digit.)

So **phases 1-3 must commutate `33.3%` more capacitance than phase 4**, which is
the concrete, measured form of A44's "the phases are not interchangeable". It has
a direct consequence in Section 7.2.

### 6.3 Free-resonance probe - would a longer dead time have helped *here*?

`resolve_deadtime_window` cannot answer this: pushing its `window_end_s` past the
real window end simply lets the *commanded* turn-on happen and reports a
meaningless `Vds ~ 0`. (This experiment made exactly that mistake on a first pass
and it is recorded here so the corrected probe is not mistaken for the same
thing.) `free_resonance_probe` instead **holds the dead-time mode** for the whole
duration. It is exact for all other phases for up to `Ton - d/2 = 15.6 ns` after
a turn-on window opens, because no other phase has a commanded transition inside
that span.

| phase | `Vds` start | deepest `Vds` over `10 ns` | at | downward excursion | crossed zero |
|---|---:|---:|---:|---:|:---:|
| 1 | `12.144853 V` | `10.170849 V` | `5.6920 ns` | `1.974004 V` | **no** |
| 2 | `12.210239 V` | `10.386588 V` | `5.3040 ns` | `1.823651 V` | **no** |
| 3 | `12.210234 V` | `10.386596 V` | `5.3040 ns` | `1.823638 V` | **no** |
| 4 | `12.214287 V` | `9.771847 V` | `5.3600 ns` | `2.442440 V` | **no** |

(sub-step converged: e.g. phase 1 gives `10.173610 / 10.170849 / 10.169466 /
10.168774 V` at `4 / 2 / 1 / 0.5 ps`.)

**At this fixed point, no dead time of any length would produce ZVS.** The
resonance simply lacks amplitude: the deepest swing is `2.44 V` against a
`12.21 V` requirement -- `16-20%` of the way. This is a much stronger statement
than "the `2.15 ns` window was too short".

---

## 7. Why it fails, quantitatively

### 7.1 Each phase's own threshold current, and the size of the gap

For each phase, its own inductor current at its window entry was bisected (40
iterations, all other coordinates held at the orbit value -- the same
deliberately-local construction A42 used) until the free resonance just reaches
zero:

| phase | threshold current | as a fraction of `125 A` | orbit minimum actually delivered | deficit | delivered / required |
|---|---:|---:|---:|---:|---:|
| 1 | `-11.525290 A` | `9.2202%` | `-0.7940 A` | `10.7313 A` | **`6.9%`** |
| 2 | `-11.593830 A` | `9.2751%` | `-0.8372 A` | `10.7566 A` | **`7.2%`** |
| 3 | `-11.594010 A` | `9.2752%` | `-0.8372 A` | `10.7568 A` | **`7.2%`** |
| 4 | `-10.043825 A` | `8.0351%` | `-0.8673 A` | `9.1765 A` | **`8.6%`** |

(sub-step converged: phase 1 gives `-11.525290 / -11.518932 / -11.515755 A` at
`2 / 1 / 0.5 ps`; the others likewise move in the fourth digit.)

Two independent cross-checks that these thresholds are right:

* **Against A42/A50.** Phase 4 is A50's own exact capacitive analog of A42's
  cell. A51 measures its threshold at `8.0351%` of `125 A`; A42 published a
  `7.76%-7.77%` bracket and A50's own extrapolated threshold was `7.76530%`.
  The `3.5%` difference is fully accounted for by this orbit's own operating
  point: phase 4's blocking voltage here is `12.2143 V` rather than A42's
  `11.9806 V`, and `Vout` is `0.8779 V` rather than `1 V`.
* **Against the closed form.** The isolated-LC solution
  `Vout + sqrt((x_0 - Vout)^2 + i^2 L/C) = V_target`, using **A51's own measured**
  capacitances from Section 6.2, gives `11.506 A` for phase 1 and `10.026 A` for
  phase 4, against the bisected `11.516 A` and `10.034 A` -- **`0.1%`** on both.

### 7.2 A48's `2.15 ns` does NOT transfer to phases 1-3

Even if the threshold current were somehow supplied, the commanded `2.15 ns`
dead time would still be too short for three of the four phases. At its own
threshold current, each phase's crossing lands at:

| phase | crossing instant after window start | fits inside the commanded `2.15 ns`? |
|---|---:|:---:|
| 1 | `2.4760 ns` | **no** |
| 2 | `2.4760 ns` | **no** |
| 3 | `2.4760 ns` | **no** |
| 4 | `2.1440 ns` | yes (`6 ps` to spare) |

This is the direct consequence of Section 6.2: the resonant quarter period scales
as `sqrt(C)`, and `sqrt(1539/1154) = 1.155`, so phases 1-3 need `2.476 ns` where
phase 4 needs `2.144 ns` -- a ratio of `1.155`, matching to three digits.
**A48's own `2.15 ns` bracket was derived on A42's isolated cell, which is
phase 4's geometry; `BOUNDARY.md` Section 4.2 asked to "report plainly if a
different dead time turns out to be needed for the coupled case", and the answer
is yes: phases 1-3 need at least `~2.48 ns`, about `15%` more.**

### 7.3 The structural cause: a ripple/load balance, not a device limit

Over one period each phase ramps from its own minimum `i_min` to its peak
`i_peak` and back, so `i_avg = (i_min + i_peak)/2` and
`i_min = i_avg - dI/2` with `dI = i_peak - i_min`. Both terms are pinned:

* `dI` is set by `L`, the switching-node voltage and the effective on-time:
  `(12.145 - 0.878)/1.4667 nH * 14.5167 ns = 111.5 A`, against the measured
  `110.3 - (-0.79) = 111.1 A`.
* `i_avg` is set by the LOAD: `Vout/Rload/4 = 0.878/0.004/4 = 54.9 A`, against
  the measured `(110.34 - 0.79)/2 = 54.8 A`.

So `i_min = 54.9 - 55.5 = -0.6 A`, against the measured `-0.79 A`. **The two
terms nearly cancel, and that near-cancellation -- not the device, not the
capacitance, not the dead time -- is what leaves the periodic state a factor of
thirteen short of its own ZVS threshold.** Everything in Sections 8 and 9 is a
consequence of this one relation.

### 7.4 A44-style state sensitivity at `z*`

Derivative of the free probe's own deepest `Vds` with respect to each coordinate
at each phase's window entry (V per unit):

| | `d/dVC1` | `d/dVC2` | `d/dVC3` | `d/d(own iL)` |
|---|---:|---:|---:|---:|
| phase 1 | `-1.000000` | `0` | `0` | `-0.756315` |
| phase 2 | `+1.000000` | `-1.000000` | `0` | `-0.647244` |
| phase 3 | `0` | `+1.000000` | `-1.000000` | `-0.647212` |
| phase 4 | `0` | `0` | `+1.000000` | `-1.008481` |

The flying-capacitor sensitivities are exactly `+/-1` and are simply the
blocking-voltage identities (`Vds1 = vin - x1 - VC1`, `Vds2 = a1 - a2`, and so
on) -- A44's high-leverage coordinates are confirmed as high-leverage, but they
act through the *target* rather than through the commutation. The phase current
is the coordinate that acts on the commutation itself, at `0.65-1.01 V/A`, which
is why Section 7.1's `~10 A` deficit and the `~12 V` gap are the same statement.

---

## 8. Robustness sweeps - and the `d = 10 ns` four-phase ZVS state

`run_robustness_sweeps.py` re-solves the whole fixed point, from the same A37
seed, with each engineering choice varied one at a time.

| case | converged | residual | natural ZVS `1/2/3/4` | min `\|Vds\|` per phase (V) | `iL` minima (A) | `Vout` (V) |
|---|:---:|---:|---|---|---|---:|
| `d = 1.00 ns` | yes | `1.344e-07` | `0,0,0,0` | `12.172 / 12.133 / 12.132 / 12.191` | `-0.299 / -0.518 / -0.518 / -0.126` | `0.94876` |
| **`d = 2.15 ns` (boundary)** | yes | `2.258e-11` | `0,0,0,0` | `12.044 / 11.810 / 11.810 / 12.214` | `-0.794 / -0.837 / -0.837 / -0.867` | `0.87790` |
| `d = 5.00 ns` | yes | `3.644e-09` | `1,0,1,1` | `0.00057 / 13.159 / 0.00527 / 0.01252` | `-11.13 / -38.52 / -11.30 / -11.53` | `0.72148` |
| **`d = 10.0 ns`** | yes | `7.038e-11` | **`1,1,1,1`** | `0.01286 / 0.01506 / 0.00082 / 0.00655` | `-11.92 / -41.04 / -12.08 / -12.25` | `0.70619` |
| sub-step `20 ps` | yes | `1.666e-07` | `0,0,0,0` | `12.037 / 11.805 / 11.805 / 12.214` | `-0.788 / -0.831 / -0.831 / -0.858` | `0.87754` |
| sub-step `1 ps` | yes | `9.725e-08` | `0,0,0,0` | `12.046 / 11.811 / 11.811 / 12.214` | `-0.796 / -0.839 / -0.839 / -0.870` | `0.87800` |
| taps lowered `1 V` | yes | `1.427e-11` | `0,0,0,0` | identical to the boundary case | identical | `0.87790` |
| `Rds(on) = 3.5 mOhm` | yes | `9.444e-11` | `0,0,0,0` | `5.452 / 5.166 / 5.166 / 4.547` | `-6.09 / -6.58 / -6.58 / -5.80` | `0.72912` |
| `Rds(on) = 7 mOhm` | yes | `1.027e-10` | `0,0,0,0` | `1.978 / 1.777 / 1.778 / 0.915` | `-9.54 / -10.05 / -10.05 / -8.90` | `0.61262` |

Stage-state inf-norm difference from the boundary case: `4.08e-02` (`20 ps`),
`1.13e-02` (`1 ps`), `1.70e-09` (taps). **The numerical choices do not move the
answer; the physical ones do.** Note that both `Rds(on)` rows and every larger
dead time move in the *same direction* -- more loss or less effective duty means
lower `Vout`, lower load current, and (Section 7.3) a more negative `i_min`.
That is one mechanism, not four coincidences.

### 8.1 The `d = 10 ns` state: what it is

At `d = 10 ns` the solver converges (residual `7.038e-11`) to a fixed point where
**all four phases cross naturally**:

| | phase 1 | phase 2 | phase 3 | phase 4 |
|---|---:|---:|---:|---:|
| `Vds` at window start | `8.78847 V` | `22.16945 V` | `8.83299 V` | `8.70826 V` |
| minimum `\|Vds\|` over the window | `12.86 mV` | `15.06 mV` | `0.82 mV` | `6.55 mV` |
| sign change, local ns from `t0` | `191.2474` | `45.5457` | `91.2349` | `140.8729` |
| admission delay from window start | `1.2474 ns` | `5.5457 ns` | `1.2349 ns` | `0.8729 ns` |
| phase current at the crossing | `-8.5397 A` | `-34.5400 A` | `-8.7320 A` | `-9.9471 A` |
| `iL` minimum over the orbit | `-11.923 A` | `-41.044 A` | `-12.084 A` | `-12.246 A` |

Independently verified per phase (`final_verification_deadtime_10ns.json`), with
the same `50 ps` to `0.0625 ps` ladder. **The sign-change instant converges
cleanly at every rung**:

| phase | sign-change delay, `50 ps` -> `0.0625 ps` | measured node capacitance |
|---|---|---:|
| 1 | `1.2666 -> 1.2535 -> 1.2494 -> 1.2474 -> ... -> 1.2454 ns` | `1539.16 pF` |
| 2 | `5.6033 -> 5.5639 -> 5.5516 -> 5.5457 -> ... -> 5.5399 ns` | `1538.53 pF` |
| 3 | `1.2535 -> 1.2409 -> 1.2368 -> 1.2349 -> ... -> 1.2329 ns` | `1538.57 pF` |
| 4 | `0.8845 -> 0.8766 -> 0.8741 -> 0.8729 -> ... -> 0.8717 ns` | `1154.36 pF` |

**One honest numerical caveat this case exposes.** The `|Vds| < 1 mV` flag that
`resolve_deadtime_window` reports (A42's own published precision convention) is
*not* reliable here: it flickers with the sub-step -- phase 2 reads
`F,F,F,F,F,T,F,T,T,T` down the ladder -- because whether any grid point happens
to land within `1 mV` of zero is a sampling accident when `dV/dt` is this large.
The *sign change* is detected at every single rung for all four phases and its
timing converges to five digits. **For a fast transition the sign change, not the
`1 mV` sample, is the verdict to use.** At the `190 W` state of Section 9 the
transitions are slower and both agree at every rung, so this caveat does not
affect the headline result -- but it is a real trap for anyone reusing
`crossed_tolerance` and it belongs alongside A50's own `50 ps` warning.

### 8.2 The `d = 10 ns` state: everything that must be said about it

It is a real fixed point of this model with four real zero crossings. It is also
**not a P24 operating point, and not balanced**:

1. **The dead time is `4.65x` A48's own bracket** and consumes `60%` of the
   commanded `16.6667 ns` on-time.
2. **`Vout = 0.70619 V`, load power `124.68 W`** -- against P24's `1 V` / `250 W`.
   The output is `30%` low and the module delivers half its rated power.
3. **The flying-capacitor ladder is badly unbalanced**: `VC1/VC2/VC3 =
   39.2316 / 17.1943 / 8.5342 V` against the nominal `36 / 24 / 12 V`. The
   `d = 2.15 ns` fixed point, by contrast, sits at `35.82 / 23.88 / 11.94 V`.
4. **The phases are grossly unequal**: phase 2 peaks at `129.43 A` while phases
   1, 3 and 4 peak at `76.30 / 76.14 / 75.99 A`, and phase 2's own blocking
   voltage is `22.17 V` against `~8.8 V` for the others. Phase 2 reaches ZVS by
   carrying `-41 A` of negative current, four times the others'.
5. At `d = 5 ns` the same solve gives ZVS on phases 1, 3, 4 but **not** phase 2
   (`min |Vds| = 13.159 V`) -- the imbalance is already present there and phase 2
   is the phase it hurts.

So the honest statement is: **a self-consistent four-phase joint periodic state
in which all four phases achieve natural ZVS does exist for this model, and A51
found one -- at a de-rated, capacitor-unbalanced operating point that is not
P24's.** Whether a *balanced* four-phase ZVS state exists at P24's own `1 V` /
`250 W` point is not answered by this experiment, and Section 7.3 gives a
concrete reason to doubt it.

### 8.3 Are these fixed points attractors? And is the frozen-diode model honest?

`run_stability_and_divider_checks.py`. Two questions that decide how much a
recovered fixed point is worth.

**Local stability.** `F(z*) = z*` says an orbit closes; it does not say a
converter would ever sit on it. The eigenvalues of `dF/dz` at `z*` do (rebuilt by
the same finite differences the search used, with the three tap directions
excluded because `F` is the identity on them and they would contribute three
spurious eigenvalues at exactly 1):

| fixed point | residual | natural ZVS | spectral radius of `dF/dz` | locally stable | five largest `\|eigenvalue\|` |
|---|---:|---|---:|:---:|---|
| `d = 2.15 ns` (boundary) | `2.258e-11` | `0,0,0,0` | **`0.982532`** | **yes** | `0.9825, 0.9747, 0.9306, 0.8733, 0.8180` |
| `d = 5.00 ns` | `3.644e-09` | `1,0,1,1` | **`0.993362`** | **yes** | `0.9934, 0.9624, 0.8859, 0.8164, 0.8164` |
| `d = 10.0 ns` | `7.038e-11` | `1,1,1,1` | **`0.992711`** | **yes** | `0.9927, 0.8527, 0.8527, 0.8420, 0.8420` |

**All three are attractors.** The `d = 10 ns` four-phase ZVS state is therefore
not a mathematical curiosity balanced on a knife edge: within this model a
converter started nearby would settle onto it, with a slowest mode decaying at
`0.9927` per period (a `~137`-period, `~27 us` settling time). The same is true
of the boundary case's own hard-switching fixed point (`0.9825`, `~57` periods),
which is why that one is the operating point this converter actually has.

**Precharge-diode admissibility.** The whole experiment freezes the three
precharge diodes OFF, which is `advance_fixed_diode_step`'s own contract, and
that is only honest while every off diode stays reverse-biased. The audit at the
three fixed points found `0.40 V` of forward bias at `d = 2.15 ns` but `43.3 V`
and `46.3 V` at `d = 5` and `d = 10 ns` -- because the taps are pinned at the
equal-series `36/24/12 V` while those orbits' own ladders have drifted far from
nominal. Each case was therefore re-solved with the taps pushed below every
ladder node on the orbit, so that **no** diode is forward-biased anywhere:

| case | taps moved to | max off-diode forward | stage `\|z*\|` difference | ZVS verdicts | `Vout` |
|---|---|---:|---:|---|---:|
| `d = 2.15 ns` | `30.60 / 18.60 / 6.60 V` | `0.4014 V` -> **`-5.0000 V`** | `1.015e-08` | unchanged `0,0,0,0` | `0.87790 V` unchanged |
| `d = 5.00 ns` | `-12.34 / -24.34 / -36.34 V` | `43.3416 V` -> **`-5.0000 V`** | `5.542e-07` | unchanged `1,0,1,1` | `0.72148 V` unchanged |
| `d = 10.0 ns` | `-15.25 / -27.25 / -39.25 V` | `46.2519 V` -> **`-5.0000 V`** | `9.173e-09` | unchanged `1,1,1,1` | `0.70619 V` unchanged |

**The divider is confirmed irrelevant to every four-phase result in this
document.** Removing all forward bias moves the stage state by at most `5.5e-7`
(volts or amps) and changes no verdict, no crossing and no output voltage. This
is what should be expected -- A37's own netlist contains no divider at all, and
the descriptor's own `1e12 Ohm` off-diodes pass at most `46 pA`, i.e.
`9.3e-18 C` per period, `~3 pV` on a `3 uF` flying capacitor -- but it is
measured here rather than assumed, because the raw forward-bias numbers would
otherwise look alarming in `results.json`.

---

## 9. Load sweep - where the four-phase ZVS boundary actually is

Section 7.3 says `i_min = i_avg - dI/2`, that `dI` is fixed by the topology and
`i_avg` by the load, and that at 250 W the two nearly cancel. That is a testable
prediction, and the fast solver makes it cheap to test: `run_load_sweep.py`
re-solves the entire fixed point, from the same A37 seed, at a ladder of nominal
module powers, **with everything else exactly at `BOUNDARY.md`'s own values --
`d = 2.15 ns`, `CFLY = 3 uF`, GS61008T `385/770 pF`, `Ton = 16.6667 ns`.**

| `P` nominal | `P` actual | `Vout` | natural ZVS `1/2/3/4` | `iL` minima (A) | ripple (A) | residual |
|---:|---:|---:|---|---|---|---:|
| **250 W** (P24 rated) | `192.679 W` | `0.87790 V` | `0,0,0,0` | `-0.79 / -0.84 / -0.84 / -0.87` | `111.1 / 110.9 / 110.9 / 111.7` | `2.26e-11` |
| 225 W | `189.804 W` | `0.91846 V` | `0,0,0,0` | `-5.03 / -5.33 / -5.33 / -5.76` | `114.8` all four | `8.31e-07` |
| 200 W | `184.375 W` | `0.96014 V` | `0,0,0,`**`1`** | `-11.37 / -11.67 / -11.67 / -12.42` | `120.0` all four | `1.05e-08` |
| **190 W** | `179.366 W` | `0.97161 V` | **`1,1,1,1`** | `-14.13 / -14.37 / -14.37 / -14.74` | `121.4` all four | `4.78e-07` |
| 185 W | `175.992 W` | `0.97535 V` | `1,1,1,1` | `-15.45 / -15.68 / -15.68 / -15.96` | `121.9` all four | `1.33e-08` |
| 180 W | `172.310 W` | `0.97841 V` | `1,1,1,1` | `-16.76 / -16.98 / -16.98 / -17.19` | `122.2` all four | `1.71e-09` |
| 175 W | `168.405 W` | `0.98098 V` | `1,1,1,1` | `-18.06 / -18.27 / -18.27 / -18.43` | `122.5` all four | `4.90e-08` |
| 150 W | `146.905 W` | `0.98963 V` | `1,1,1,1` | `-24.49 / -24.68 / -24.68 / -24.70` | `123.6` all four | `2.50e-09` |
| 100 W | `99.671 W` | `0.99835 V` | `1,1,1,1` | `-37.27 / -37.40 / -37.40 / -37.35` | `124.7` all four | `1.32e-10` |
| 50 W | `50.818 W` | `1.00815 V` | (see below) | (see below) | (see below) | **`9.56e-02`** |

The `50 W` row **did not converge** (residual `9.56e-02`, five orders of
magnitude outside tolerance) and its state is therefore not a fixed point and is
not counted. Its ZVS flags and phase minima are wildly unequal
(`-7.4 / -6.6 / -23.3 / -14.9 A` at the crossings) exactly as one expects of a
non-periodic point. It is reported rather than dropped because `BOUNDARY.md`
Section 6's third bullet requires non-convergence to be stated plainly. No
attempt was made to rescue it; it is outside this experiment's question.

### 9.1 The result: a balanced four-phase joint ZVS periodic state at `190 W`

**At `190 W` nominal -- on `BOUNDARY.md`'s own dead time, own `CFLY`, own device
and own `Ton`, changing only the load -- the solver converges to a fixed point
(residual `4.78e-07`, inside the `1e-6` tolerance) at which all four phases
achieve a natural zero-voltage crossing, and the flying-capacitor ladder stays
balanced.**

| | phase 1 | phase 2 | phase 3 | phase 4 |
|---|---:|---:|---:|---:|
| `Vds` at window start | `12.18428 V` | `12.24823 V` | `12.24825 V` | `12.03740 V` |
| minimum `\|Vds\|` over the window | `11.79 mV` | `10.68 mV` | `11.10 mV` | `19.27 mV` |
| **natural ZVS** | **yes** | **yes** | **yes** | **yes** |
| crossing delay from window start | `1537.22 ps` | `1511.94 ps` | `1512.01 ps` | `1027.03 ps` |
| margin inside the `2150 ps` dead time | `612.8 ps` | `638.1 ps` | `638.0 ps` | `1123.0 ps` |
| phase current at the crossing | `-8.1551 A` | `-8.4752 A` | `-8.4754 A` | `-10.9391 A` |
| `iL` minimum over the orbit | `-14.13 A` | `-14.37 A` | `-14.37 A` | `-14.74 A` |

* Flying-capacitor voltages at `z*`: `35.7782 / 23.7863 / 11.7869 V` against the
  nominal `36 / 24 / 12` -- **balanced to within `1.8%`**, unlike the `d = 10 ns`
  state of Section 8.
* Output `0.97161 V`, i.e. **`97.2%` of the nominal `1 V`**, versus `0.878 V`
  (`87.8%`) at 250 W.
* Phase ripple `121.4 A` on all four phases, and phase-current minima equal to
  within `4%` across phases. This is a symmetric operating point.
* Per-phase step-size convergence and its independent verification are in
  Section 9.3; stability and divider admissibility in Section 9.4.

### 9.2 The boundary is sharp, and it is exactly where Section 7.3 predicted

The transition is not gradual:

| `P` nominal | phases 1-3 min `\|Vds\|` | phase 4 |
|---:|---|---|
| 250 W | `12.04 / 11.81 / 11.81 V` (no dip at all) | `12.21 V` (rises) |
| 225 W | not crossing | not crossing |
| 200 W | **`0.473 / 0.241 / 0.242 V`** -- within `0.5 V` of ZVS | **crosses**, `9.05 mV` |
| 190 W | **crosses**, `11.8 / 10.7 / 11.1 mV` | crosses, `19.3 mV` |

So the four-phase ZVS threshold for this boundary lies **between `190 W` and
`200 W` nominal for phases 1-3, and between `200 W` and `225 W` for phase 4** --
phase 4 turns on ZVS first, exactly as Section 6.2's `1154 pF` versus `1539 pF`
predicts. The ordering of the four phases is a measured consequence of ladder
position, not an assumption.

Section 7.3's arithmetic predicted the crossover at the load where
`i_avg = dI/2 - i_threshold`: with `dI/2 ~ 60 A` and `i_threshold ~ -11.5 A`
that is `i_avg ~ 48.5 A` per phase, `194 A` output, **`~190 W` at `0.97 V`**.
The measured boundary is between `190` and `200 W`. The mechanism identified in
Section 7.3 is therefore confirmed quantitatively, not merely asserted.

### 9.3 Note on Section 7.1's thresholds versus the in-window requirement

Section 7.1 measured each phase's own *graze* threshold -- the current at which
the free resonance just touches zero -- as `-11.53 / -11.59 / -11.59 / -10.04 A`,
and Section 7.2 noted that at exactly that current phases 1-3 cross at `2.476 ns`,
too late for the `2.15 ns` window. The load sweep shows how both are true at
once: at `200 W` phases 1-3 sit at `-11.67 A`, just past the graze threshold, and
still fail *because the crossing arrives after the window closes* -- their
min `|Vds|` is `0.24-0.47 V`, not `12 V`. Only at `190 W`, where they reach
`-14.4 A`, does the crossing move in to `1512-1537 ps`,
inside the window. **The graze threshold is necessary but not sufficient; the
dead-time-compatible requirement is about `24%` more negative current.**

### 9.4 Independent verification of the `190 W` four-phase ZVS state

Same discipline as Section 6, applied to the `190 W` fixed point
(`final_verification_190w.json`, `stability_and_divider_190w.json`). Relative
residual at the verified state: `4.7788e-07`.

**Sub-step ladder, per phase.** The crossing instant (sign change of the signed
`Vds`) is detected at **every rung from `50 ps` to `0.0625 ps` for all four
phases**, and converges to five digits:

| sub-step | phase 1 | phase 2 | phase 3 | phase 4 |
|---:|---:|---:|---:|---:|
| `50 ps` | `1.5721 ns` | `1.5448 ns` | `1.5449 ns` | `1.0440 ns` |
| `20 ps` | `1.5483` | `1.5225` | `1.5226` | `1.0325` |
| `10 ps` | `1.5409` | `1.5154` | `1.5155` | `1.0288` |
| `5 ps` | `1.5372` | `1.5119` | `1.5120` | `1.0270` |
| `2 ps` | `1.5351` | `1.5099` | `1.5100` | `1.0260` |
| `1 ps` | `1.5343` | `1.5092` | `1.5093` | `1.0256` |
| `0.5 ps` | `1.5340` | `1.5089` | `1.5089` | `1.0254` |
| `0.25 ps` | `1.5338` | `1.5087` | `1.5088` | `1.0254` |
| `0.125 ps` | `1.5337` | `1.5086` | `1.5087` | `1.0253` |
| `0.0625 ps` | **`1.5337 ns`** | **`1.5086 ns`** | **`1.5086 ns`** | **`1.0253 ns`** |

Every one of those is inside the `2.150 ns` commanded window, with
`615 / 641 / 641 / 1125 ps` of margin at the converged values. **The ZVS verdict
is `yes` for all four phases at every sub-step tested** -- it is not a resolution
artifact. (As in Section 8.1, the `|Vds| < 1 mV` sampling flag flickers on the
coarser rungs while the sign change does not; the sign change is the verdict.)

**Cross-check against A42/A50.** Measured at this state, each phase's own graze
threshold is `-11.4616 / -11.5287 / -11.5289 / -9.7958 A`, i.e.
`9.1693 / 9.2230 / 9.2231 / 7.8366%` of `125 A`. **Phase 4 -- the phase whose
cell A50 proved is A42's exact capacitive analog -- lands at `7.8366%`, against
A42's own published `7.76%-7.77%` bracket and A50's own extrapolated
`7.76530%`.** That is `0.9%` agreement with A42's own SPICE result, on a
four-phase joint orbit that A42 never simulated, with this orbit's own
`Vout = 0.9716 V` and blocking voltage `12.0374 V` (versus A42's `1 V` and
`11.9806 V`) fully accounting for the remainder. The single-phase physics A50
validated is reproducing correctly inside the coupled four-phase solve.

The orbit delivers `-14.09 / -14.34 / -14.34 / -14.71 A` at the window entries,
i.e. **`1.23x / 1.24x / 1.24x / 1.50x` each phase's own graze threshold** -- the
margin Section 9.3 says is needed to pull the crossing inside the window.

**Measured node capacitances** are `1539.16 / 1538.53 / 1538.57 / 1154.36 pF`,
identical to the `250 W` state's (Section 6.2) to six digits, as they must be
since they are a property of the network, not the operating point. This is a
consistency check on the measurement itself.

**Stability and divider admissibility** (Section 8.3's method):

| | value |
|---|---|
| spectral radius of `dF/dz` | **`0.950810`** -> **locally stable** |
| five largest `\|eigenvalue\|` | `0.9508, 0.9167, 0.8160, 0.8160, 0.7858` |
| precharge-diode forward bias, as solved | `0.2173 V` |
| after moving taps to `30.78 / 18.78 / 6.78 V` | **`-5.0000 V`, all strictly reverse-biased** |
| stage `\|z*\|` difference from that move | `4.166e-07` |
| ZVS verdicts and `Vout` after that move | unchanged `1,1,1,1`, `0.97161 V` |

The `190 W` state is the **most** stable of the four fixed points this
experiment recovered (`0.9508`, a `~20`-period settling time), it is
divider-clean, and its safety margin is the widest: max `|iL| = 107.2643 A`,
`42.9%` of the `250 A` bound.

---

## 10. Step 6 - safety

`BOUNDARY.md` Section 6's last bullet: every phase current within `+/-250 A`
throughout the search. This is checked at **every sub-step of every `F`
evaluation**, not only at accepted iterates -- that includes all twenty
finite-difference Jacobian probes and every line-search trial, and the check
raises rather than continuing if it is ever exceeded.

| stage | evaluations | max `\|iL\|` | within `+/-250 A` |
|---|---:|---:|:---:|
| main search (Newton + Picard, `d = 2.15 ns`) | 92 | **`117.2950 A`** | yes |
| final per-phase verification at `z*` | - | **`110.8370 A`** | yes |
| robustness sweeps (9 full re-solves) | - | **`129.6865 A`** (`d = 10 ns`) | yes |
| load sweep (10 full re-solves) | - | **`117.2950 A`** (250 W row) | yes |

The largest phase current seen anywhere in this experiment, across roughly
**1,900 one-period map evaluations**, is **`129.6865 A`** -- `51.9%` of the
bound. The bound was never approached and never violated.

The two deliberately hypothetical probes that go outside the orbit -- the
threshold-current bisections of Sections 7.1 and 9 -- were bracketed at
`-249 A` by construction, i.e. inside the bound by `1 A`; they are local
diagnostics on a single window, not states the search ever occupied.

---

## 11. Verdict against `BOUNDARY.md` Section 6

`BOUNDARY.md` Section 6 names three possible outcomes. **Which one happened
depends on the operating point, and both of the first two occurred**, so both
are reported:

**At `BOUNDARY.md`'s own specified operating point (250 W, `d = 2.15 ns`) --
Section 6's SECOND outcome, "a fixed point found but one or more phases do NOT
cross naturally":**

* Fixed point found, relative residual `2.258171e-11` (absolute inf-norm
  `2.024738e-09`), four Newton iterations of a 50-iteration budget. The budget
  was **not** extended.
* **All four** phases hard-switch. Residual `Vds` at forced turn-on:
  `12.045605 / 11.811308 / 11.811282 / 12.562362 V`. Verified over a `50 ps` to
  `0.0625 ps` sub-step ladder per phase, plus Richardson; the verdict is
  identical at every rung.
* Which coordinates the failure is sensitive to (Section 6 asks for this
  explicitly): the flying-capacitor voltages act only on the *target*
  (`d(Vds)/dVCj = +/-1` exactly, since `Vds` is a ladder difference), while the
  phase current acts on the *commutation* at `0.65-1.01 V/A`. The deficit is
  `9.18-10.76 A` of negative current per phase. A44's flying capacitors are
  confirmed high-leverage, but through the blocking voltage, not the swing.
* The four phases are **not** interchangeable, quantitatively: measured
  participating capacitance `1539.16 / 1538.53 / 1538.57 / 1154.36 pF`, so
  phases 1-3 must move `33.3%` more charge than phase 4 and need `15%` longer to
  do it. A48's own `2.15 ns`, derived on phase 4's geometry, does not transfer.

**At `190 W` on the same boundary -- Section 6's FIRST outcome, "a genuine fixed
point with all four phases independently confirmed to cross naturally":**

* Fixed point found, relative residual `4.78e-07`, inside the `1e-6` tolerance.
* All four phases cross naturally, with `613-1123 ps` of margin inside the
  `2150 ps` dead-time window, on a ladder balanced to `1.8%` at `0.9716 V`.
* Independently verified per phase with step-size convergence (Section 9.4).
* **Flagged prominently as Section 6 requires** -- and equally prominently
  qualified: this is at `76%` of P24's rated load, so it is
  `SENSITIVITY_ONLY` and is **not** a P24 reproduction, not a claim that the
  2024 converter achieves ZVS, and not a substitute for the SPICE cross-check
  `BOUNDARY.md` Section 7 requires before any such claim could be made.

Section 6's third outcome ("no fixed point found within the budget") did **not**
occur for any case reported as a result. It did occur for the `50 W` row of the
load sweep (residual `9.56e-02`), which is reported in Section 9 and counted as
a non-result rather than quietly dropped.

Damped Picard, run from the same seed as an independent check, does **not**
converge (Section 4.3) -- it stalls around `1.2e-2` and oscillates. Newton's
answer does not depend on it; it is reported because Picard's trajectory is
itself informative about ZVS-capable-but-non-periodic states.

---

## 12. What this experiment does not establish

Repeating `BOUNDARY.md` Section 7, which still binds, plus what this run adds:

* **No P24/P25 reproduction is claimed.** The `190 W` four-phase ZVS state is
  on the `9%`-branch-adjacent boundary A37 established, at `76%` of rated load,
  with `SENSITIVITY_ONLY` device and dead-time plug-ins. `BOUNDARY.md`
  Section 7 is explicit that even a positive result is "strong grounds for a
  SPICE cross-check ... not a substitute for one". **That SPICE cross-check has
  not been performed and is the obvious next experiment.**
* **This is a Python solver result, not SPICE.** It inherits every caveat of
  A50's own validation, which was against A42's single-phase case only. The
  four-phase joint case has never been cross-validated against SPICE.
* **Constant `Co(tr)` capacitance only**, matching A42/A50's convention -- not
  A47's nonlinear digitized `Coss(V)`, which A47 showed makes ZVS slightly
  harder. The `190 W` boundary would move under nonlinear `Coss`.
* **A single global switch on-resistance.** The framework cannot express A42's
  `RHS = 7 mOhm` / `RLS = 3.5 mOhm` split. The search runs at the framework's
  own `1 uOhm` default (A50's validated configuration); Section 8 shows both
  device values move the answer substantially in the ZVS-favourable direction,
  so the `190 W` boundary is conservative with respect to conduction loss but
  the real split was never modelled.
* **`dead_time_s` remains an engineering choice**, not hardware data
  (`MINIMUM_INFORMATION_REQUEST.md`'s own standing gap). A51 adds a concrete,
  quantified request to that list: A48's `2.15 ns` is a phase-4 number, and
  phases 1-3 need `>= ~2.48 ns` at their own graze threshold.
* **`z*` is defined only to the discretization floor.** `F` is deterministic, so
  the residual reaches `1e-11`, but `z*` itself moves by `~1e-2 V` between the
  `20 ps` and `1 ps` sub-steps (Section 8). All ZVS verdicts are unchanged across
  that range, but no coordinate of `z*` should be quoted beyond about four
  significant figures.
* **`src/scb_ivr/` is not modified and is not imported** under any outcome, and
  no file under `A50_zvs_capable_solver_prototype/`, `A37_...`, `A42_...`,
  `A48_...`, `paper_locked/02_ectc2024_main/` or `results/` is touched.
* **Only the GS61008T and only the `9%`-adjacent branch.** P24's primary `1-2%`
  branch is untouched, the same standing limitation as A37.
* **The load sweep is not a claim about the real converter's efficiency,
  regulation or loop.** It varies a resistive load on a fixed open-loop duty;
  a real regulated converter would move `Ton`, which this experiment does not
  model.

---

## 13. Files

| File | Role |
|---|---|
| `a51_period_map.py` | the one-period map `F(z)`, seed conversion, window resolvers, free-resonance probe, capacitance measurement |
| `run_cfly_reverification.py` | step 2 -- re-verifies `BOUNDARY.md` Section 1 |
| `run_map_selftests.py` | import isolation, kernel identity, interval cover, seed round-trip, `I_VSTEP`, step-size convergence of `F` |
| `run_fixed_point_search.py` | steps 3/4/6 -- semi-smooth Newton, damped Picard, tap degeneracy, diode audit, safety |
| `run_final_verification.py` | step 5 -- per-phase sub-step ladders, free-resonance probes, measured capacitance, threshold currents, sensitivity |
| `run_robustness_sweeps.py` | dead time, sub-step, taps, `Rds(on)` |
| `run_load_sweep.py` | the load ladder and the four-phase ZVS boundary |
| `run_stability_and_divider_checks.py` | spectral radius of `dF/dz`; precharge-diode admissibility |
| `build_results.py` | assembles `results.json` from the run artifacts |
| `cfly_reverification.json`, `map_selftests.json`, `fixed_point_search.json`, `final_verification.json`, `robustness_sweeps.json`, `load_sweep.json`, `stability_and_divider.json`, `final_verification_190w.json`, `stability_and_divider_190w.json`, `final_verification_deadtime_10ns.json` | run artifacts |
| `_sweeps/`, `_load_sweep/`, `_checks/`, `_checks190/` | per-case fixed-point solves behind the sweep tables |
| `*_log.txt` | captured console output of each run |
| `results.json` | the assembled key numbers |
