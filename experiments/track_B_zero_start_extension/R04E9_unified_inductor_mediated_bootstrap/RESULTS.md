# R04E9 result - unified inductor-mediated four-phase bootstrap

## Outcome, stated first

All 9 cells of the `(I_LIMIT, T_FREEWHEEL_MAX)` grid completed normally
in LTspice (batch mode, exit code 0, non-empty `.log`/`.raw` for every
case, verified directly). **No cell reaches the handoff condition.** All
9 cells park permanently in state `CHARGE2` -- the machine completes
phase 1's charge and freewheel, begins phase 2's charge, and then never
reaches phase 2's own current limit, so it never proceeds to phase 3 or
4, and completes **zero** full four-phase rotations in any cell. This is
a `CONTROLLER_GUARD_PASS` / `SENSITIVITY_ONLY` result, reported honestly
per Ground Rule 7: the grid is complete and fully run, but the outcome is
a negative (no-handoff) one in all 9 cells.

## 1. Simulation completion

All 9 cases ran to completion (LTspice exit code 0). Verified directly:
every case has a non-empty `.log` (4.7-4.8 KB) and non-empty `.raw`
(~4.86 MB), confirming a completed transient run, not a truncated one.

## 2. Parameters actually used

Fixed for every cell (`BOUNDARY.md` Section 4): `Vin=48 V`, `nP=4`,
`nM=4`, full four-phase P24 connectivity, `LPHASE=1.4666667 nH`,
`CFLY=3 uF`, `COUT=4.672 mF`, GS61008T device data (1 HS / 2 parallel
LS), true-zero-energy initial conditions (`ic=0` throughout, `UIC`).

Swept: `I_LIMIT` in `{10, 30, 60} A` x `T_FREEWHEEL_MAX` in
`{50, 200, 1000} ns`, 9 cells. Every cell run to a common
`TSTOP=3 us` / `TMAX=50 ps` (pilot-justified, Section 6).

## 3. The sensitivity grid

| `I_LIMIT` (A) | `T_FW_MAX` (ns) | Final state | Rotations | `IL1_max` (A) | `IL2_max` (A) | `ICS1_max` (A) | `Vout` final (V) | `VC1` final (V) | `VC2` final (V) | Handoff? |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 10 | 50   | CHARGE2 | 0 | 10.159 | 6.822  | 5.930  | 8.99e-5 | 0.01070 | 0.00826 | NO |
| 10 | 200  | CHARGE2 | 0 | 10.159 | 4.548  | 3.910  | 3.22e-4 | 0.00739 | 0.01157 | NO |
| 10 | 1000 | CHARGE2 | 0 | 10.159 | 0.385  | 0.298  | 7.36e-4 | 0.00895 | 0.01001 | NO |
| 30 | 50   | CHARGE2 | 0 | 30.156 | 20.052 | 17.634 | 2.69e-4 | 0.01456 | 0.00844 | NO |
| 30 | 200  | CHARGE2 | 0 | 30.156 | 13.285 | 11.639 | 9.58e-4 | 0.00577 | 0.01724 | NO |
| 30 | 1000 | CHARGE2 | 0 | 30.156 | 0.467  | 0.361  | 2.19e-3 | 0.01087 | 0.01214 | NO |
| 60 | 50   | CHARGE2 | 0 | 60.173 | 39.966 | 35.195 | 5.41e-4 | 0.02413 | 0.01268 | NO |
| 60 | 200  | CHARGE2 | 0 | 60.173 | 26.458 | 23.233 | 1.92e-3 | 0.00719 | 0.02959 | NO |
| 60 | 1000 | CHARGE2 | 0 | 60.173 | 0.746  | 0.577  | 4.37e-3 | 0.01742 | 0.01939 | NO |

Full numeric detail (min currents, `ICS2`/`ICS3` currents, all five
trajectory checkpoints, rotation-boundary measurements) is in
`results.csv`/`results.json`.

## 4. When each key event occurred

In every one of the 9 cells, the machine advances through
`CHARGE1(0) -> FREE1(1) -> CHARGE2(2)` within the first ~1 us and then
**never advances again** for the remainder of the 3 us window:

- `CHARGE1 -> FREE1` (the `I(L1)>=I_LIMIT` current-limit event) fires at
  `t~=0.93 ns` regardless of `I_LIMIT` or `T_FREEWHEEL_MAX` (verified
  directly for the `I_LIMIT=30` row: `t=9.256e-10 s`) -- the very first
  turn-on is Coss/LC-transient-dominated, the same finding R04E3/R04E4
  already documented for their own first pulse.
- `FREE1 -> CHARGE2` fires at the COMMANDED `T_FREEWHEEL_MAX` (small
  overshoot, same margin R04E3/R04E4 documented for their own event):
  confirmed directly for `I_LIMIT=30`, `T_FREEWHEEL_MAX=50 ns`, the
  transition lands at `t=52.27 ns`. This confirms the timer mechanism
  (Section 2 of `BOUNDARY.md`) now genuinely controls this transition,
  not the natural `I(L1)<=0` event, for every tested `T_FREEWHEEL_MAX`
  value (all three are far below R04E3's own `1.63 us` natural-crossing
  finding, so the timeout branch of the OR-rule always wins the race).
- `CHARGE2 -> FREE2` (the `I(L2)>=I_LIMIT` rule): **never fires in any of
  the 9 cells.** `IL2_max` never reaches the commanded `I_LIMIT` in any
  cell (closest approach: `39.966 A` vs a `60 A` limit, `67%` of the way
  there, in the most favorable cell). The machine is permanently latched
  in `CHARGE2`.

## 5. Key voltages and currents

- **Peak currents stay far below R04E6/E7/E8's multi-kilo-amp figures.**
  The single largest current observed anywhere in the whole 9-cell grid
  is `IL1_max=60.173 A` (the `I_LIMIT=60 A` rows, matching the commanded
  limit plus a small ~0.3% overshoot, the same kind of small
  post-limit-event overshoot R04E3/R04E4 already documented). The largest
  flying-capacitor current is `ICS1_max=35.195 A` (also the `I_LIMIT=60`,
  `T_FW=50 ns` cell). **This is roughly two orders of magnitude below**
  R04E6/E7/E8's `ICS1_MAX` figures (`4157.7-4566.9 A` across their whole
  tested `Cfly` range) -- a direct, structural consequence of routing
  every phase's charging current through its own series inductor `Lk`
  (this experiment's mechanism) instead of a bare switch-to-switch
  capacitor path (R04E6/E7/E8's borrowed EPE2019 mechanism, with no
  series inductance limiting `di/dt`).
- Every cell's currents stay comfortably inside the `+/-250 A` safety
  bound (`BOUNDARY.md` Section 6); the worst-case magnitude anywhere in
  the grid is `60.173 A`, `24%` of that bound.
- `Vout` stays at the sub-millivolt to low-millivolt scale in every cell
  (largest final value `4.37e-3 V` at `I_LIMIT=60`, `T_FW=1000 ns`) --
  never remotely close to the `[0.95, 1.05] V` handoff band. `VC1`/`VC2`
  similarly stay at the tens-of-millivolt scale (largest `VC2` final
  value `0.02959 V` at `I_LIMIT=60`, `T_FW=200 ns`) -- three orders of
  magnitude below the `36/24/12 V` targets. `VC3` stays at numerical-zero
  (`~1e-9 to 1e-10 V`) in every cell, because phase 3 is never activated.
- **Within `CHARGE2`, `VC1` and `VC2` visibly RING** (a damped LC
  oscillation, not a monotonic approach): sampled trajectory for
  `I_LIMIT=30, T_FW=200 ns` (fractions of the 3 us window) --

  | Checkpoint | `t` (us) | `Vout` (V) | `VC1` (V) | `VC2` (V) | State |
  |---|---:|---:|---:|---:|---|
  | 20% | 0.6 | 1.089e-3 | -0.0571 | 0.0799  | CHARGE2 |
  | 40% | 1.2 | 1.055e-3 | 0.0629  | -0.0402 | CHARGE2 |
  | 60% | 1.8 | 1.022e-3 | -0.0180 | 0.0411  | CHARGE2 |
  | 80% | 2.4 | 9.90e-4  | 0.0258  | -0.0027 | CHARGE2 |
  | 100%| 3.0 | 9.58e-4  | 0.0058  | 0.0172  | CHARGE2 |

  `VC1`/`VC2` swing sign repeatedly (a damped ring between the two
  flying caps through `SH2`'s series `Ron` and `L2`), decaying in
  amplitude over the window, while `Vout` decays smoothly and
  monotonically (Cout discharging into `Rload` with no further charging
  pulse, the same signature R04E5 documented for its own post-stall
  decay). A pilot extension of this same cell to `TSTOP=20 us` (6.7x
  longer) produced a bit-identical `IL2_max=13.2853393555 A` and, notably,
  `VC1_final==VC2_final` to full printed precision
  (`0.0115051567554 V` both) -- direct evidence the ring has fully
  damped out to a genuine capacitive-divider equilibrium between `C1` and
  `C2` by then, confirming this is a real permanent stall, not slow
  continuing progress truncated by an too-short window.

## 6. Acceptance condition

Not met in any of the 9 cells. `T_HANDOFF` never fires (`Measurement
"t_handoff" FAIL'ed` in every case log).

## 7. First failure boundary

In every cell, the first (and only) failure boundary is the SAME one:
`CHARGE2` never reaches its own `I(L2)>=I_LIMIT` exit condition. Unlike
R04E3/R04E5 (which stalled waiting for a *natural physical event* that
structurally cannot occur, i.e. `V(vin,a1)<=0` or `I(L1)<=-I_NEG`), this
stall is at a *current-limit* rule -- the SAME kind of rule R04E4
validated works reliably for phase 1's own first pulse. The blocker is
not the rule mechanism itself but the available DRIVING VOLTAGE: phase
2's charge path is fed only through `SH2` from node `a1`, whose voltage
is set entirely by `CS1`'s own charge deposited during phase 1's single,
very brief (`~0.93 ns`) current-limited pulse -- there is no direct `Vin`
connection to `a2` (unlike phase 1's own `a1`, fed directly from `Vin`
through `SH1`). This is a genuinely new, and structurally different,
stall location and cause from every predecessor (Section "Comparison"
below).

## 8. Plain-word statement of both swept axes' effects

- **`I_LIMIT` (the current limit): a larger `I_LIMIT` produces a larger
  phase-1 charge pulse, which deposits more charge on `C1`, which in turn
  drives a larger `IL2_max` in phase 2's stalled charge attempt --
  monotonically and consistently across every tested `T_FREEWHEEL_MAX`:
  at `T_FW=50 ns`, `IL2_max` rises `6.822 -> 20.052 -> 39.966 A` as
  `I_LIMIT` rises `10 -> 30 -> 60 A`; the same monotonic-increasing
  pattern holds at `T_FW=200 ns` (`4.548 -> 13.285 -> 26.458 A`) and
  `T_FW=1000 ns` (`0.385 -> 0.467 -> 0.746 A`). **However, in every one
  of the 9 tested cells `IL2_max` still falls short of its own
  `I_LIMIT`** (closest: `39.966` vs `60 A`, `67%` of the way), so a
  larger `I_LIMIT` never actually unsticks the machine within this
  tested range -- it only raises the ceiling `IL2` approaches before
  settling into the same permanent `CHARGE2` stall.
- **`T_FREEWHEEL_MAX` (the freewheel timeout): a SHORTER timeout produces
  a LARGER `IL2_max`** -- the opposite of what a naive "more time to
  decay/settle" intuition might suggest, but with a clear causal
  explanation: a shorter `T_FREEWHEEL_MAX` cuts phase 1's freewheel short
  while `I(L1)` still has more residual (undecayed) current, and that
  larger residual couples more strongly into phase 2's own charge-state
  dynamics once the machine transitions. Monotonic and consistent across
  every tested `I_LIMIT`: at `I_LIMIT=60 A`, `IL2_max` falls
  `39.966 -> 26.458 -> 0.746 A` as `T_FREEWHEEL_MAX` rises
  `50 -> 200 -> 1000 ns`; the same monotonic-decreasing pattern holds at
  `I_LIMIT=30 A` (`20.052 -> 13.285 -> 0.467 A`) and `I_LIMIT=10 A`
  (`6.822 -> 4.548 -> 0.385 A`). **This axis has a clear, real, monotonic
  effect in this grid** -- unlike R04E5's own `TSOFT` axis, which R04E5
  found had NO observed effect at all, because R04E5's machine never
  returned to a state where its swept axis could act. This experiment's
  `T_FREEWHEEL_MAX` axis DOES act, every single cycle -- it is simply not
  enough, by itself, to reach the handoff condition within the tested
  range.
- **No `(I_LIMIT, T_FREEWHEEL_MAX)` combination in this 9-cell grid comes
  close to the handoff condition.** The best cell by every measure
  (`I_LIMIT=60 A`, `T_FREEWHEEL_MAX=50 ns`) reaches `IL2_max=39.966 A`,
  `67%` of that cell's own `I_LIMIT` -- meaningfully closer to unsticking
  than the worst cell (`I_LIMIT=10 A`, `T_FREEWHEEL_MAX=1000 ns`, `IL2_max
  =0.385 A`, `3.85%` of its own limit), but still short. `Vout`/`VC1`/
  `VC2`/`VC3` remain three to four orders of magnitude below their
  respective handoff targets in every cell.

## 9. Comparison against every predecessor this experiment synthesizes

| Predecessor | Vout bootstrap? | Current control? | Where it fails / what it cost |
|---|---|---|---|
| R03A (fixed PWM, precharged) | Rises | NONE | Current runs away to `884 A` |
| R03D (ramped PWM, precharged) | **Succeeds** (`~1 V`) | NONE | Uncontrolled `-268 to 391 A` swings; success purchased by violating the project's own boundary-control principle (fixed-time pulses regardless of physical state) |
| R04E3 (strict event chain, zero start) | Fails (near-zero) | Yes, but overshoots (`10A` limit -> `43.68A` peak) | Permanently stuck waiting for a physical event (`Vds=0`/`I<=-Ineg`) that cannot occur at zero `Vout` |
| R04E5 (R03D ramp + R04E3 chain) | Fails (mV-scale, decays) | Yes, stays `<250A` | Confirms the strict chain itself is the blocker; swept axis (`TSOFT`) has ZERO observed effect because the machine never returns to a state where it matters |
| R04E6 (EPE2019 ladder, blind cycling) | N/A (ladder-only scope) | NONE (switch-only path) | Ladder DRIFTS WORSE with more cycles; `ICS1_MAX` ~1.2e6 A artifact (excluded) / hundreds-3.4kA real |
| R04E7 (ratio-gated EPE2019 ladder) | N/A (ladder-only scope) | NONE (switch-only path) | Ladder CONVERGES (`LADDER_ERR=0.045`) but `ICS1_MAX` up to `4567 A` |
| R04E8 (R04E7 + corrected Cfly) | N/A (ladder-only scope) | NONE (switch-only path) | Same convergence, same `4158-4567 A` peak currents -- confirms peak current is structural, not a `Cfly` artifact |
| **R04E9 (this experiment)** | **Fails** (mV-scale, decays) | **Yes, stays well under `250A` (max `60.17A`, two orders of magnitude below R04E6/E7/E8)** | **Permanently stuck in `CHARGE2` -- a current-limit rule that structurally cannot fire because phase 2 has no direct `Vin` connection, only `CS1`'s own limited charge** |

**Explicit, plain-word verdict on each axis this experiment set out to
synthesize:**

- **Does it get `Vout` up like R03D?** **No.** `Vout` stays at the
  millivolt scale and decays after the stall, the same qualitative
  outcome R04E3/R04E5 already found, not R03D's success. R03D's success
  is not recovered here, and for the same root reason R04E5 already
  identified: any mechanism that genuinely enforces physical-event gating
  (as this one does, even with the added timeout escape hatch) cannot
  freely re-issue pulses the way R03D's boundary-violating fixed-clock
  PWM could.
- **Does it get further than R04E3/R04E5 (which never got unstuck at
  all)?** **Partially, and differently.** R04E3/R04E5 never advance past
  a SINGLE phase's own admission chain (stuck at states 3/4 of a 5-state
  machine, waiting for a natural physical event that cannot occur).
  R04E9 DOES advance further in state-machine terms -- it completes
  phase 1 entirely (`CHARGE1`, `FREE1`) and begins phase 2 -- but then
  stalls at a DIFFERENT kind of boundary (a current-limit rule that
  cannot fire due to insufficient driving voltage, not a natural-event
  rule that cannot fire due to a shallow return slope). This is a
  genuinely new stall location and a genuinely new causal mechanism, not
  a re-discovery of R04E3/R04E5's own finding.
- **Does it avoid R04E6/E7/E8's implausible currents?** **Yes, clearly.**
  Peak currents in every one of R04E9's 9 cells stay within roughly
  `60 A` (bounded directly by the commanded `I_LIMIT` for phase 1, the
  only phase that ever reaches its own current limit) -- two orders of
  magnitude below R04E6/E7/E8's `4-4.6 kA` figures. This directly
  confirms the task's own stated hypothesis: routing every phase's
  charging current through its own series inductor (this experiment's
  central departure from R04E6/E7/E8) produces a far more physically
  plausible current scale than a bare switch-to-switch capacitor path.

## 10. Grade

All 9 cells: **`CONTROLLER_GUARD_PASS`** (the machine safely parks in a
single latched state, `CHARGE2`, for the remainder of every run -- no
chatter, no divergence, no safety-bound violation -- but it also never
reaches a second phase's own admission event, let alone a full rotation
or the handoff condition). Overall grid label: **`SENSITIVITY_ONLY`**
(both axes are swept, non-paper, engineering-choice values; see
`BOUNDARY.md` Section 8 for what cannot be claimed).

## 11. Which module should be adjusted next

The stall is specifically at phase 2's DRIVING VOLTAGE, not at the
current-limit rule mechanism itself (which works correctly, as phase 1's
own successful `CHARGE1->FREE1` transition in every cell demonstrates).
A future experiment should address this directly rather than continue
sweeping `I_LIMIT`/`T_FREEWHEEL_MAX` further (this grid's own monotonic
trends, Section 8, show both axes help somewhat but neither is close to
sufficient within a physically reasonable range) -- for example:
(a) a modified truth table where phase 2's charge state routes through a
node with a more direct `Vin` connection (a genuinely different topology
choice, out of scope for a "reuse the existing P24 connectivity
unchanged" experiment); (b) seeding phase 1 (`C1` only) from a passive
precharge (the R02 family) before starting this experiment's own rotation
machine, so phase 2 inherits a `C1` that already has real charge on it
instead of only the residue of one `~1 ns` current-limited pulse; or (c)
allowing phase 1 to repeat (re-enter `CHARGE1`) several times, building
up `C1`'s charge over multiple pulses, before the machine is allowed to
advance to phase 2 -- a genuinely different admission structure from the
strict round-robin rotation tested here.

## 12. What must never be changed because of this failure

- `LPHASE=1.4666667 nH` (locked Eq.-4 value, unchanged from the whole
  R04E3-R04E8 lineage).
- The true-zero-energy starting condition (`ic=0` throughout). Do not
  mask this stall by presetting capacitor voltages, per
  `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section XI rule 5.
- The current-limit exit rule form (`I(Lk)>=I_LIMIT`) -- validated
  working correctly for phase 1 in every cell; the stall is not evidence
  against this rule mechanism itself, only against the specific
  round-robin admission structure tested here (Section 11).
- `CFLY=3 uF`/`COUT=4.672 mF` -- do not silently swap back to R04E6/E7's
  `53.8 uF` (cross-topology-suspect) value to try to change this outcome;
  see `BOUNDARY.md` Section 4 and `README.md`'s provenance-gap section.
