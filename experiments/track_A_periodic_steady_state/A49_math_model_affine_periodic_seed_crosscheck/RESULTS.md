# A49 math-model affine periodic-seed cross-check -- results

Branch: `CROSS_PAPER_EXTENSION`. Not a P24/P25 periodic-state reproduction
claim (BOUNDARY.md Section 0/7). This is a cross-check between the parallel
`src/scb_ivr/` ideal-switch periodic-orbit solution and A37's own real-device,
real-event-driven four-phase construct (BOUNDARY.md Section 4).

## 1. Whether the simulation completed normally

Yes. `A49_math_model_affine_periodic_seed_crosscheck.cir` was run to its full
`.tran 0 {T0+T+5n} 0 5p UIC` window (0 to 205 ns) with no solver
non-convergence, exit code 0, `Total elapsed time: 6.952 seconds`.

**Tooling note, not a circuit issue**: the committed netlist's own absolute
path is 261 characters, at/above the `~250-259`-character LTspice-runner
path-length threshold this project's own `R04E14`
(`paper_locked/00_boundaries/EXPERIMENT_REGISTRY.md`) already diagnosed as
silently dropping all `.meas` output from the `.log` file (symptom: `unable
to open database file`, zero `.meas` lines, `.raw` otherwise complete and
correct). That symptom reproduced exactly here: the committed netlist's own
`.log` has no `.meas` output. Two independent, cross-checked recovery paths
were used, not one:

1. Direct binary parsing of the committed run's own `.raw` file (41,858
   points, 27 variables, `real forward nocompression` format; every `FIND
   ... AT` and `WHEN ... RISE/FALL` `.meas` directive in the netlist was
   reimplemented in Python against these raw samples, using the same linear
   interpolation LTspice itself uses).
2. A byte-for-byte electrically identical copy of the same netlist (only the
   three `.include` paths rewritten to absolute Windows-style paths so the
   copy is self-contained, and placed at a short path, `/tmp/a49chk/
   a49chk.cir`, purely to stay under the path-length threshold) was
   independently re-run in the same LTspice build. Its `.log` this time
   contains full, real `.meas` output.

Every value from path (1) matches path (2)'s own real LTspice `.meas` engine
output to full double precision (e.g. `DVC1`: `0.3439586265` (path 2) vs.
`0.34395862649` (path 1) computed independently). All FAIL/PASS classifications
also match exactly. The numbers below are path (2)'s own real `.meas` log
values (`/tmp/a49chk/a49chk.log`, not committed -- a disposable verification
artifact, not part of this experiment's deliverables), cross-validated against
path (1).

## 2. Full `.meas` results

### Initial/final state samples (`t=T0+2ps` / `t=T0+T+2ps`)

| Quantity | Initial (`t=2ps`) | Final (`t=T+2ps`) | `D` (final-initial) |
|---|---:|---:|---:|
| `VC1` | 35.845505 V | 36.189464 V | `DVC1` = **+0.343959** V |
| `VC2` | 23.886563 V | 23.884403 V | `DVC2` = **-0.002160** V |
| `VC3` | 11.927849 V | 11.927992 V | `DVC3` = **+0.000143** V |
| `VO` | 1.0 V | 1.0 V | `DVO` = **0.0** V |
| `IL1` | 0.144863 A | -9.009348 A | `DIL1` = **-9.154211** A |
| `IL2` | 62.724599 A | 0.703233 A | `DIL2` = **-62.021365** A |
| `IL3` | 62.722527 A | -66.056676 A | `DIL3` = **-128.779204** A |
| `IL4` | 63.030984 A | -65.831609 A | `DIL4` = **-128.862593** A |

### Fixed-`TON` peak-current edges

| Quantity | Value |
|---|---:|
| `T_H1_OFF` | 16.6681 ns |
| `IL1_H1_OFF` | 120.708066 A |
| `PEAK_ERROR_H1` | **-4.291934 A** |
| `T_H2_OFF` / `IL2_H2_OFF` / `PEAK_ERROR_H2` | **FAILED** (H2 never turns on) |
| `T_H3_OFF` / `IL3_H3_OFF` / `PEAK_ERROR_H3` | **FAILED** (H3 never turns on) |
| `T_H4_OFF` / `IL4_H4_OFF` / `PEAK_ERROR_H4` | **FAILED** (H4 never turns on) |

### ZVS nominal-slot voltages (whatever `Vds` actually is at the slot, admitted or not)

| Quantity | Slot time | Value |
|---|---:|---:|
| `VDS_H2_SLOT` | 50 ns | **12.250698 V** |
| `VDS_H3_SLOT` | 100 ns | **11.956992 V** |
| `VDS_H4_SLOT` | 150 ns | **11.929647 V** |
| `VDS_H1_SLOT` | 200 ns | **11.779631 V** |

### Admission diagnostics (actual turn-on instant/voltage, not itself a residual)

| Quantity | Result |
|---|---|
| `T_H2_ON` / `VDS_H2_ON` | **FAILED** -- H2 never admitted in the 205 ns window |
| `T_H3_ON` / `VDS_H3_ON` | **FAILED** -- H3 never admitted |
| `T_H4_ON` / `VDS_H4_ON` | **FAILED** -- H4 never admitted |
| `T_H1_ON2` / `VDS_H1_ON2` | **FAILED** -- H1's next-cycle re-admission never reached |

## 3. What actually happens physically (from direct raw-trace inspection)

The `.machine` state trace (`V(xmod:sequence_state)`) shows the rotation
advances through exactly four real state transitions and then permanently
stalls:

| Time | Transition | Trigger |
|---:|---|---|
| 16.6681 ns | `P1_M1`->`P1_M2` | `V(gh1_ton)>=2.5` (fixed `TON` elapsed) |
| 16.8083 ns | `P1_M2`->`P1_M3` | `V(x1)<=0` |
| 89.8196 ns | `P1_M3`->`P1_M4` | `I(LIND2)<=0` (IL2 decays from its 62.72 A seed to zero) |
| 106.6532 ns | `P1_M4`->`P1_M5` | `I(LIND2)<=-INEG=-11.25 A` |
| (never) | `P1_M5`->`P2_M1` | requires `(time>=50ns)*(V(a1,a2)<=0)` -- **never satisfied** |

`Vds(H2)=V(a1,a2)` reaches a minimum of **0.252 V at t=109.14 ns** (very
close, but never crosses to `<=0`) and then rises back to ~10-12 V and stays
there (a decaying ring, not a genuine commutation) for the rest of the
observation window. `gh2`, `gh3`, `gh4` are identically 0 V for the entire
run (confirmed directly: `max(V(gh2))=max(V(gh3))=max(V(gh4))=0.0`). The
state machine ends the run parked at state `P1_M5` (`sequence_state=4`),
never reaching `P2_M1`, so H2, H3 and H4 never turn on at all, and H1's own
second-cycle re-admission is never reached either -- a strictly earlier
stall point than A37's own best candidate (which completed the H1->H2
transition and stalled only at H2->H3, see Section 4).

This directly confirms BOUNDARY.md Section 4's own explicit flag: the
period-averaged `IL2_INIT=62.724 A` proxy for phase 2's mid-cycle state
(the approximation Section 4 called "the weakest approximation in this
experiment") requires an extra ~59 ns beyond A37's own natural window just
to decay through zero and past `-INEG` before the controller is even
permitted to check `Vds(H2)<=0` -- and by the time it can check, `Vds(H2)`
is already past its own closest approach and settling back upward instead
of completing the crossing.

## 4. Explicit comparison against A37's own published best candidate

A37's own `RESULTS.md` (`3 of 15 residuals converged`, `peak_error_h1_a`,
`zvs_error_h2_v`, `periodic_error_vc3_v`; H3/H4 never admitted; H1->H2
succeeded, `Vds(H2)@50ns=-0.000531 V`) is the comparison baseline, per
BOUNDARY.md Section 6.

### Per-residual convergence (tolerance `2e-4` in the residual's own unit, same as A37)

| # | Residual | A37 value | A37 | A49 value | A49 |
|---|---|---:|:---:|---:|:---:|
| 1 | `peak_error_h1_a` | -0.0000076 A | **CONVERGED** | -4.291934 A | not converged |
| 2 | `peak_error_h2_a` | -7.2343 A | not converged | FAILED (H2 never conducts) | not converged |
| 3 | `peak_error_h3_a` | -125.0 A | not converged | FAILED | not converged |
| 4 | `peak_error_h4_a` | -125.0 A | not converged | FAILED | not converged |
| 5 | `zvs_error_h2_v` | -0.000175 V | **CONVERGED** | 12.250698 V | not converged |
| 6 | `zvs_error_h3_v` | 11.246 V | not converged | 11.956992 V | not converged |
| 7 | `zvs_error_h4_v` | 13.916 V | not converged | 11.929647 V | not converged |
| 8 | `zvs_error_h1_v` | 11.978 V | not converged | 11.779631 V | not converged |
| 9 | `periodic_error_il1_a` | -11.003 A | not converged | -9.154211 A | not converged |
| 10 | `periodic_error_il2_a` | 1.249 A | not converged | -62.021365 A | not converged |
| 11 | `periodic_error_il3_a` | -40.615 A | not converged | -128.779204 A | not converged |
| 12 | `periodic_error_il4_a` | -134.059 A | not converged | -128.862593 A | not converged |
| 13 | `periodic_error_vc1_v` | 0.002247 V | not converged | 0.343959 V | not converged |
| 14 | `periodic_error_vc2_v` | 0.018205 V | not converged | -0.002160 V | not converged |
| 15 | `periodic_error_vc3_v` | -0.0000139 V | **CONVERGED** | 0.000143 V | **CONVERGED** |

**A49: 1 of 15 residuals converge (`periodic_error_vc3_v` only). A37: 3 of 15
converge.** A49 loses both of A37's own local-transition successes
(`peak_error_h1_a`, `zvs_error_h2_v`) and keeps only the coincidental
capacitor-balance residual A37's own RESULTS.md Section 7 already flagged
as "apparently coincidental."

### ZVS admission count

| Phase transition | A37 | A49 |
|---|---|---|
| H1->H2 | **admitted** (`t=50.0007 ns`, `Vds=-0.000531 V`) | **not admitted** (`Vds` min `0.252 V` at `t=109.14 ns`, never crosses) |
| H2->H3 | not admitted (`MISSED_ZVS_SLOT`) | not admitted (H2 never turned on, so this transition is never even reached) |
| H3->H4 | not admitted (cascade) | not admitted (cascade, earlier) |
| H4->H1(next) | not admitted (cascade) | not admitted (cascade, earlier) |

**A37 achieves 1 of 4 phase-transition ZVS admissions (H1->H2). A49 achieves
0 of 4.** A49's rotation stalls one transition earlier than A37's own best
candidate.

### Verdict

**A49 performs strictly worse than A37's own best candidate on both metrics
BOUNDARY.md Section 6 names**: fewer converged residuals (1 vs. 3) and fewer
successful ZVS admissions (0 vs. 1). The ideal-switch math model's own
period-average-current seed for phases 2-4 does not transfer to a working
real-device admission state -- if anything it is worse than A37's own blind
optimizer-search seed at the one transition (H1->H2) A37's optimizer had
already solved.

**Caveat on the `DVC1`-`DVC3` magnitude comparison**: `CFLY` differs between
the two runs (A37: `53.8 uF`; A49: `3 uF`, `17.93x` smaller, per BOUNDARY.md
Section 2's required correction). A given charge imbalance produces a
proportionally larger voltage swing on the smaller capacitance, so the raw
`DVCk` magnitudes are not directly comparable without adjustment. Scaling
A37's own `DVC1`/`DVC2` by `17.93x` (an order-of-magnitude estimate of what
the same charge imbalance would produce at A49's `CFLY`) gives `~0.040 V`
and `~0.326 V` respectively -- on that adjusted basis A49's `DVC1=0.344 V` is
still worse than the `CFLY`-adjusted A37 comparison (`~0.040 V`), while
A49's `DVC2=-0.00216 V` is much better than the `CFLY`-adjusted A37
comparison (`~0.326 V`). This adjustment is an order-of-magnitude estimate,
not a rigorous correction, and does not change the verdict above, which
rests on the residual-count and admission-count metrics BOUNDARY.md Section
6 actually specifies.

## 5. Safety check: phase currents

| Inductor | Min | Max | `|value|<=250A`? |
|---|---:|---:|:---:|
| `I(XMOD:LIND1)` | -12.291161 A | 121.132202 A | PASS |
| `I(XMOD:LIND2)` | -11.293266 A | 62.725754 A | PASS |
| `I(XMOD:LIND3)` | -68.661919 A | 62.724010 A | PASS |
| `I(XMOD:LIND4)` | -68.438370 A | 63.032532 A | PASS |

All four phase currents stay well inside `+/-250 A` throughout the full
205 ns window (largest magnitude observed: `121.13 A`, `48.5%` of the bound).

## 6. Solver-corruption fingerprint check

Direct inspection of the committed run's own `.raw` file (41,858 time
points):

- **Monotonicity**: 0 non-monotonic or non-positive `dt` steps across the
  entire trace; time increases strictly from `0` to `205.0 ns`.
- **Duplicate timestamps**: 0 (41,858 unique timestamps out of 41,858
  points).
- **Timestep range**: as small as `~5e-21 s` (extremely fine adaptive
  stepping around a sharp event) up to the `5 ps` cap set by `.tran ... 5p`;
  both are consistent with healthy event-driven adaptive stepping around the
  circuit's own hard `V=0`/current-threshold crossings, not corruption.
- **Raw-file quirk (not corruption)**: the very first stored point
  (`index 0`, `t=0.0` exactly) holds an all-zero placeholder row for every
  trace, a known LTspice artifact of combining `UIC` initial conditions with
  `.tran`'s own operating-point skip -- the true `t=0+` state appears at
  `index 1` (`t=5.0e-17 s`) and correctly reflects every seeded `.param`
  value (`IL2~62.7257 A`, `IL3~62.7240 A`, `IL4~63.0325 A`, matching
  `IL2_INIT`/`IL3_INIT`/`IL4_INIT`). This artifact does not affect any
  `.meas` value reported above (all `AT`/`WHEN` instants used are `>=2 ps`,
  well past this single spurious row), and is independently proven harmless
  by the exact double-precision agreement between the raw-parsed values and
  LTspice's own real `.meas` engine output (Section 1).

**No solver-corruption fingerprint found.** The run is numerically clean;
the physical stall described in Section 3 is a genuine controller/circuit
outcome, not a solver artifact.

## 7. Which BOUNDARY.md Section 6 outcome was actually met

**"Comparable or worse closure error, similar or more admission failures"
-- specifically WORSE, not merely comparable.** A49 converges fewer
residuals (1 of 15) than A37's own best candidate (3 of 15) and achieves
fewer successful ZVS admissions (0 of 4 phase transitions vs. A37's 1 of 4).
This reinforces the conclusion BOUNDARY.md Section 6 already anticipated
from Track B's own `R04E24`-`R04E26` chain: the ideal-switch model's own
predicted steady-state does not straightforwardly transfer to a real ZVS
admission requirement. The specific, directly-diagnosed mechanism here is
Section 4's own flagged weakest approximation -- using phase 2's period-
average current (`62.724 A`) rather than its own instantaneous state at
A37's `t=0` sampling instant delays phase 2's natural current zero-crossing
by enough (to `t~90-107 ns`, vs. A37's `Vds(H2)` reaching its own natural
crossing band much earlier) that by the time the controller is even
permitted to check `Vds(H2)<=0`, the natural commutation opportunity has
already passed its closest approach (`0.252 V`, not `<=0 V`) and the voltage
is moving away from zero, not toward it. This is not a solver failure
(Section 6 fully clean, per Section 6 above) and is not comparable to A37
-- it is a clear negative result, reported plainly per the task's
instruction not to force a more favorable conclusion than the data
supports.

## 8. What this does and does not establish

Per BOUNDARY.md Section 7, unchanged: this does not resolve the
`MINIMUM_INFORMATION_REQUEST.md` Item 9 gap, does not modify or depend on
`src/scb_ivr/` beyond the one already-published document quoted in
BOUNDARY.md Section 4, does not modify A37's own committed files, and this
negative result does NOT license retuning `TON`, `Coss`, `CFLY`,
`LPHASE`, or `NEG_FRAC` to force a different outcome. The specific, now
directly-diagnosed follow-up question this result motivates (not
authorized here) is whether requesting the math model's own true
per-phase instantaneous snapshot at a single shared timestamp (removing
Section 4's flagged period-average approximation for phases 2-4) would let
phase 2's own natural `Vds=0` crossing land inside its own admission
window, the same way A36's original two-variable local solve found for
phase 1's own transition.
