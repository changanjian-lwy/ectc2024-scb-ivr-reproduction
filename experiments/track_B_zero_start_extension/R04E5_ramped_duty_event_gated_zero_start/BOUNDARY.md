# R04E5 - ramped-duty, event-gated zero start (BOUNDARY)

## 1. Parents

This experiment has **two** joint parents. It is a synthesis, not a
one-variable perturbation of either alone (see Section 9).

- **PARENT 1: R03D**, `paper_locked/02_ectc2024_main/STEP_08_R03_LITERATURE_GUIDED_TAKEOVER.md`
  and `paper_locked/02_ectc2024_main/spice/R03D_epe2019_duty_ramp_takeover.cir`.
  Mechanism: the commanded high-side on-time is ramped **linearly from 0 to
  the locked P24 value over a declared-sensitivity `TSOFT` window** (R03D
  used `TSOFT=100 us`), instead of snapping straight to full duty as R03A
  did. Result: `Vout` correctly bootstraps to 0.994-1.007 V, but with
  **no current limiting at all**, phase currents swing to hundreds of amps
  (`L1`: -225.75 A to 382.55 A; `L4`: -268.49 A to 390.96 A). Registry
  status: `PARTIAL_SUCCESS_OUTPUT / FAILED_CURRENT_BOUNDARY`.
- **PARENT 2: R04E3**, `paper_locked/02_ectc2024_main/STEP_30_R04E3_ZERO_START_EVENT_CONTROLLER.md`
  and `paper_locked/02_ectc2024_main/spice/R04E3_P24_minimal_zero_start_event_cycle.cir`.
  Mechanism: an **event-driven, latched `.machine`/`.state`/`.rule`**
  controller starting from true zero energy, turning the high side off at
  a per-phase current limit (a physical event, not a fixed time) and
  waiting for physical zero-current/negative-current events before
  admitting the next high-side ZVS turn-on. Result: it correctly detects
  that a full P24 t0-t3 cycle cannot yet close at zero start (`iL1=0`
  took 1.63 us, not ~200 ns) and safely refuses to proceed -- no chatter,
  no divergence -- but during the long wait the current keeps rising past
  the commanded 10-A gate-off limit, reaching 43.68 A. Registry status:
  `LOGIC_PASS; P24_ZERO_START_LOCAL_CYCLE_FAILS_BEFORE_T3`.
- **Supporting correction inherited from R04E4** (`paper_locked/02_ectc2024_main/STEP_31_R04E4_ZERO_START_GATEOFF_SWEEP.md`,
  same immediate track-B lineage as R04E3, not itself a declared parent):
  the powered-rail-present-before-controller-enable boundary
  (`VRAIL` flat at `VIN` from `t=0`; controller enable delayed to
  `TENABLE=10 ns`) is reused unchanged. R04E4 found that enabling the
  controller simultaneously with rail establishment lets Coss displacement
  current falsely trigger the current comparator before any commanded
  power pulse; separating the two removes that artifact. This is a
  numerical-boundary detail carried forward, not a third mechanism.

## 2. What changed relative to each parent

Relative to R03D:

- The fixed-clock, complementary-PWM scheduling (`mod(time-TSTART,T)`) is
  replaced entirely by R04E3's event-driven `.machine` skeleton.
- The linear on-time ramp itself (0 to locked `Ton` over `TSOFT`) is kept,
  but re-expressed as an event-machine rule (an elapsed-on-time ceiling
  compared against `I(L1)>=I_LIMIT`) instead of R03D's `TON*limit((time-
  TSTART)/TSOFT,0,1)` inline PWM-duty expression.
- No current limiting existed in R03D at all; R04E5 adds it (from R04E3).
- `Lphase` changes from R03D's own `2.68 nH` (2024 Table-I) to `1.4666667
  nH` (Eq.-4, R04E3's value and this project's current Track-A mainline)
  -- see Section 4.
- R03D used the R02B passive-divider precharge starting ladder; R04E5
  starts from true zero energy (R04E3's starting point), not a precharged
  ladder -- the harder, more fundamental case.

Relative to R04E3:

- R04E3's fixed `I_LIMIT=10 A` current-only turn-off rule is replaced by
  `(I(L1)>=I_LIMIT) | (V(ton_timer)>=ramped_ceiling(time))` -- the
  high side now turns off at the **earlier** of the current limit or a
  ramped on-time ceiling, not the current limit alone.
- R04E3 deliberately entered a `BLOCK_P24_HANDOFF_UNKNOWN` dead-end state
  after one same-phase cycle attempt and stopped. R04E5's
  `COMMUTATE_HIGH_TO_ZVS` state instead loops back to `ENERGY`, so the
  machine repeats indefinitely -- necessary because a single pulse cannot
  show whether a ramp bootstraps `Vout`; only many repeated cycles can.
- `I_LIMIT` and `TSOFT` are now swept (R04E3 used a single fixed 10 A;
  R04E4 already showed the exact gate-off threshold has no control
  authority over the very first Coss-dominated turn-on impulse -- R04E5
  reuses that lesson, sweeps `I_LIMIT` anyway to see whether it matters
  for LATER cycles once the ramp has partly unwound, which R04E4 did not
  test since R04E4 never looped).

## 3. What did not change

- Topology: the full one-module, four-phase P24 power stage (identical
  `SCB4P_P24_...` subcircuit connectivity to R04E3/R04E4, four phases
  wired, only phase 1 actively commanded -- same simplification R04E3 and
  R04E4 both already made).
- `Vin=48 V`, `Vout target=1 V`, `Pmodule=250 W`, `nP=4`, `nM=4`,
  `fsw=5 MHz`, `D=1/12` as the final ramp target (P24_EXPLICIT:
  `D=NP*Vout/Vin`, `Ton=D*T`, matching the printed Table-I duty and
  Eq.-1).
- `Cfly=53.8 uF`, `Cout=4.672 mF` (both cross-source EPE2019 values,
  unchanged from every prior R03/R04 experiment in this track).
- GS61008T device data: `GS61008T_typical_params.lib` and
  `GS61008T_commutation_capacitance.lib` (same library, same 1 HS / 2
  parallel LS population, `RHS`/`RLS`, `CH`/`CL` as R04E3/R04E4).
- All capacitor and inductor initial conditions: true zero (`ic=0`
  throughout the power stage).
- The 2%-of-commanded-limit negative-current target convention
  (`NEG_FRAC=.02`), unchanged from R04E3.
- `.options` tolerances (`reltol=1e-5 abstol=1e-9 chgtol=1e-16 solver=alt
  cshunt=1e-15`), unchanged from R04E3/R04E4.

## 4. Provenance of every changed/added value

| Value | Source | Category |
|---|---|---|
| `L=1.4666667 nH` | R04E3's own value; this project's adopted Eq.-4 branch, same value A42-A48 all use tonight | P24_EXPLICIT (Eq.-4 branch) |
| `TSOFT in {50,100,200,500} us` | Swept; R03D's own `TSOFT=100 us` is one of the four points, otherwise new | SENSITIVITY_ONLY |
| `I_LIMIT in {10,50,150} A` | Swept; R04E3's own `10 A` is the lowest point, otherwise new | SENSITIVITY_ONLY |
| `NEG_FRAC=0.02` | Unchanged from R04E3 | Inherited, P25-style source-native fraction |
| Elapsed-on-time timer (`CTIMER`/`BTIMER_CHG`/`SRESET`) | Added only to give the event machine a way to compare "on-time so far this pulse" against a ramped ceiling; has no physical counterpart | NUMERICAL_IDEALIZATION |
| `TENABLE=10 ns`, powered-rail-first boundary | R04E4's own already-documented correction | Inherited from R04E4 |
| `CH`, `CL`, `RHS`, `RLS` | GS61008T datasheet Rev 200402, 1 HS / 2 parallel LS (P25 Table III population) | EXTERNAL_DEVICE_DATA (unchanged from R04E3) |
| `Cfly`, `Cout` | EPE2019 Table 1 | CROSS_PAPER_EXTENSION-adjacent cross-source value (unchanged from every R03/R04 ancestor) |

**Why `L=1.4666667 nH`, not R03D's `2.68 nH`:** R03D used the 2024 paper's
own printed Table-I inductance. R04E3 (and every current Track-A
experiment tonight, A42 through A48) uses the Eq.-4-derived `1.4666667
nH`. Since R04E5's controller mechanism comes from R04E3 and must plug
into the same power-stage numbers R04E3/R04E4 already validated
numerically, and since staying on this project's current mainline value
avoids introducing a second, uncontrolled discrepancy on top of the
already-declared two-parent synthesis, `1.4666667 nH` is used throughout.
This is a deliberate departure from R03D's own value, not an oversight,
and it means R04E5's numbers are not directly comparable to R03D's
current-extrema table without accounting for the different `L`.

## 5. Question this experiment answers

Does combining R03D's ramped on-time ceiling with R04E3's event-driven,
latched, per-phase current limit reach a bounded, safe zero-start
trajectory for phase 1 that neither mechanism reached alone -- across a
small (`TSOFT`, `I_LIMIT`) sensitivity grid?

## 6. Success condition

For a given (`TSOFT`, `I_LIMIT`) cell, graded `LOCAL_PASS`: `Vout` rises
toward the 1 V target (this experiment's working definition: `Vout` at
the end of the run is within 5% of 1 V, i.e. in `[0.95, 1.05] V`) **and**
`I(L1)` stays within `+/-250 A` (2x the P24 Eq.-2 phase-peak target of
125 A, the safety bound this experiment adopts up front) for the entire
run, including the late-window check after the ramp completes.

## 7. Failure conditions

- `PHYSICAL_BOUNDARY_FAIL`: `I(L1)` exceeds `+/-250 A` at any point.
- `EXPECTED_FAILURE` / stalled bootstrap: the run completes numerically
  and stays within the current bound, but `Vout` does not approach 1 V
  (stays near-zero or decays) by the end of the run.
- `CONTROLLER_GUARD_PASS`: the machine gets stuck in one state for the
  remainder of the run (e.g. `LOW_FREEWHEEL_TO_ZERO` never resolves)
  without chattering or diverging -- a safe refusal, matching R04E3's own
  finding, reported honestly rather than forced into a pass.
- A solver failure/non-convergence before `TSTOP` is its own outcome,
  reported as such, not silently retried with loosened boundary
  parameters.

## 8. What this experiment cannot prove

- It cannot establish a P24-reported startup sequence. `TSOFT` and
  `I_LIMIT` are swept sensitivity axes, not paper values, and no
  combination tested here may be described as "the" correct startup
  law.
- It cannot claim periodic closure (`x(T)=x(0)` in the sense of Section
  VIII of the protocol) -- this is a startup transient, not a steady-state
  orbit.
- It cannot claim four-phase interleaving beyond the startup transient
  itself. Only phase 1 is actively commanded (phases 2-4's low sides are
  held on / high sides held off, exactly as R04E3/R04E4 already do); no
  phase-rotation logic is exercised or validated here.
- It cannot claim any hardware hard-switching-loss, ZVS, or
  device-level accuracy beyond the ideal-switch/scalar-Coss model already
  used by R04E3/R04E4.
- A `LOCAL_PASS` in this experiment is a single-phase, single-module local
  finding only; it must never be read as a complete P24 startup
  reproduction, and a passing cell here does not imply neighboring
  untested (`TSOFT`, `I_LIMIT`) cells would also pass.

## 9. Honesty about the synthesis

This is explicitly a **two-parent synthesis**, not a one-variable
perturbation of either R03D or R04E3 in the sense of Section V of the
protocol. Two things changed together by construction (the ramped ceiling
mechanism grafted onto the event machine, and the state-4-loops-to-state-0
change needed to observe it over many cycles); both are named above as an
explicit solve vector rather than claimed as a single-variable step.
