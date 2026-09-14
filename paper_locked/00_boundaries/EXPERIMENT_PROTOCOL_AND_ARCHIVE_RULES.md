# Simulation experiment principles, classification and archiving rules

Adopted 2026-09-14 as the standing protocol for every experiment in this
project. Any new contributor, human or AI, must read this file before
generating a netlist, running a simulation, or reporting a result. It
supplements, and does not replace, `PAPER_LOCKED_REPRODUCTION_BASELINE.md`,
`SEQUENCE_SOURCE_MATRIX.md` and the other files in this directory.

## I. Overall research principles

1. The primary goal is to reproduce the 2024 ECTC paper.
2. Content explicitly stated by the 2024 paper must be used first.
3. Content the 2024 paper does not state may be supplemented from the 2025
   APEC paper or other literature only where 2024 is silent.
4. Where 2024 and 2025 differ or conflict, two independent branches must be
   created; they are never automatically merged.
5. External datasheet parameters may be added as device modules, but their
   source and applicable conditions must always be labelled.
6. A value the literature does not provide must never be presented as if it
   were a paper parameter.
7. Simulation failure is an acceptable outcome; a boundary must never be
   changed merely to produce an attractive number.
8. Before starting any new experiment, check whether it is still grounded in
   the 2024 paper's mechanism.
9. A successful local result must never be announced as a complete paper
   reproduction.
10. A validated model must never be overwritten in place; a new experiment
    must be copied from its parent.

## II. Parameter classification

Every parameter must belong to exactly one of the following categories.

### P24_EXPLICIT

Data or relationships explicitly given by the 2024 paper, e.g. `Vin=48 V`,
`Vo=1 V`, `Po=1 kW`, `nP=4`, `nM=4`, `fs=5 MHz`, the 1-2% negative-current
range, the `Ton` equation.

### P25_SUPPLEMENT

Content the 2025 paper supplies to fill a 2024 silence, e.g. Mode 2'/5', GaN
reverse conduction, the all-inactive-low-side control branch, the 5-10%
negative-current sensitivity range, the GS61008T device/driver part numbers.
These must never be silently relabelled as 2024 parameters.

### CROSS_PAPER_EXTENSION

Extending a 2025 three-phase method to the 2024 four-phase system, e.g.
rotating "all other low sides on" to four phases, or rotating the 2025
Mode 1-6 sequence into a four-phase state machine. Must always be explicitly
labelled as a cross-paper extension.

### EXTERNAL_DEVICE_DATA

Parameters from a datasheet or other paper, e.g. `RDS(on)`, `Coss`, `Qoss`,
reverse voltage drop, driver delay, package parasitics. The device model,
datasheet revision and test conditions must always be recorded.

### NUMERICAL_IDEALIZATION

Ideal parameters added only to make the simulation solvable, e.g. an ideal
reverse clamp (`Vf=0`), numerical damping resistance, an ideal output-voltage
boundary, an ideal switch control voltage. Results built on these must never
be called a hardware prediction.

### SENSITIVITY_ONLY

Values swept only to observe a direction, e.g. a `Coss` multiplier sweep, an
assumed 0.5 ns delay, an assumed 0.5 nH package parasitic, or comparing 5%,
8%, 9%, 10% negative current. A sensitivity value must never be silently
promoted to a default model parameter.

### UNKNOWN_BLOCKING

Parameters the papers do not provide and that block a hardware-level
conclusion, e.g. the real dead time, complete driver propagation delay,
nonlinear `Coss(V)`, real `Qoss`, package/via parasitics, the real snubber
capacitance.

## III. Experiment tracks

### Model-fidelity and peak-current acceptance layers

Every Track-A experiment must declare exactly one electrical-model layer. A
result may not use an acceptance target from one layer while silently using
the device equations of the other layer.

#### `P24_IDEAL`

- Purpose: reproduce the analytical relationships printed in the 2024 paper.
- The high-side conduction path is lossless for the Eq. (2)/(4) peak-current
  check (`RDS(on)=0` for that check).
- The published analytical reference remains `IL,pk=125 A` with
  `Ton=16.6667 ns` and the adopted Eq.-(4) `L=1.4667 nH`.
- A mismatch against `125 A` may be graded against the P24 analytical target
  only when the run actually uses this ideal electrical layer.

#### `P25_DEVICE_AUGMENTED`

- Purpose: retain the P24 topology/timing while adding a device module from
  P25 and/or an external datasheet, such as `RDS(on)=7 mOhm`.
- `125 A` remains a separately reported P24 ideal reference; it is not the
  sole pass/fail endpoint for the non-ideal current ramp.
- For a locally near-constant drive voltage `VDRV`, total series resistance
  `RPATH`, fixed `Ton`, inductance `L`, and measured current at actual high-side
  admission `IADMIT`, the device-layer endpoint prediction is

  ```text
  IEND_DEVICE = VDRV/RPATH
              + (IADMIT - VDRV/RPATH)*exp(-RPATH*Ton/L)
  ```

  with the continuous limit `IEND_DEVICE=IADMIT+VDRV*Ton/L` when
  `RPATH -> 0`.
- `VDRV` and `IADMIT` must be read at that phase's physical admission event;
  a single fixed `118 A` or `119 A` value must not be installed as a global
  target. Capacitor motion or other non-constant effects must be reported as
  the residual between the simulated endpoint and this local prediction.
- Every result reports two quantities separately: deviation from
  `IEND_DEVICE`, which validates the augmented model, and deviation from
  `125 A`, which quantifies departure from the P24 ideal reference. The latter
  alone is not a `PHYSICAL_BOUNDARY_FAIL` of the P24 topology.

Using a P25 device parameter does not convert a cross-paper control sequence
into a P24-primary result. Sequence provenance, negative-current branch and
model-fidelity layer remain independent labels.

Experiments are organized into at least these tracks.

### Track A: periodic steady-state reproduction

Studies one or more periods of the paper's normal operating state: peak
current, negative current, ZVS, four-phase interleaving, flying-capacitor
balance, 200 ns period closure.

### Track B: zero start

Starting from `VC1=VC2=VC3=0`, studies precharge, current limiting,
narrow/repeated pulsing, voltage-ladder establishment, startup stress, and the
transition into steady-state control.

A Track A success never implies a Track B success; the two conclusions must
never be mixed.

### Auxiliary: 2025 support experiments

Experiments that specifically validate a 2025-supplied mechanism, e.g. the
5-10% negative current, the three-phase Mode 1-6, all-inactive-low-side
conduction, GaN reverse conduction and Mode 2'/5'. These must never directly
override the 2024 mainline.

### Legacy: superseded models

Earlier models with a principled problem, superseded by a newer framework but
still worth keeping for reference. Failed experiments must never be deleted,
because they record where the error occurred, which method was already
attempted, and why it cannot be reused.

## IV. Required files per experiment

Every experiment gets its own folder, for example:

```text
A36_local_peak_and_50ns_zvs_solve/
├── A36_local_peak_and_50ns_zvs_solve.cir
├── BOUNDARY.md
├── RESULTS.md
├── solver_history.json
└── best_candidate.json
```

### `BOUNDARY.md` must state

1. Who the parent experiment is.
2. What changed relative to the parent, exactly.
3. Which parameters did not change.
4. The provenance of every changed value.
5. What question this experiment is meant to answer.
6. The success condition.
7. The failure condition.
8. What this experiment cannot prove.

### `RESULTS.md` must state

1. Whether the simulation completed normally.
2. The parameters actually used.
3. When each key event occurred.
4. Key voltages and currents.
5. Whether the acceptance condition was met.
6. Where the first failure boundary occurred.
7. Whether the result is a pass, a local pass, a sensitivity trend, or a
   failure.
8. Which module should be adjusted next.
9. Which parameters must never be changed because of this failure.

## V. One-variable principle

In principle, every experiment changes exactly one variable or module, e.g.:

```text
A27 -> A28: only the controller event logic changes
A28 -> A29: only a non-ideal sensitivity plugin is added
A28 -> A30: only the inductor branch changes
A31 -> A32: only the Coss multiplier is swept
A35 -> A36: only two initial current states are solved
```

If multiple variables must change together, the change must be defined as an
explicit solve vector with every residual recorded; it must never be called a
one-variable experiment.

## VI. Boundary-control principle

Fixed-time boundaries and physical-event boundaries must always be kept
distinct.

### Fixed-time boundaries

- Switching frequency `fs=5 MHz`.
- Period `T=200 ns`.
- Four-phase spacing `T/nP=50 ns`.
- High-side on-time `Ton=16.667 ns`.

### Physical-event boundaries

- Low-side `Vds=0`.
- Inductor current crossing zero.
- Reaching the negative-current target.
- High-side `Vds=0`.
- Current reaching its peak.

A fixed time may never substitute for a physical event. For example, if
`50 ns` arrives but the high side's `Vds != 0`, the model must block the
high-side turn-on and record `MISSED_ZVS_SLOT`; it must never hard-switch
just to preserve the nominal frequency. Likewise, if the current has not
reached `125 A`, `Ton` must never be extended; instead record
`r_I = iL(Ton) - 125 A`.

## VII. Control-latching principle

An instantaneous event only triggers a state transition; after the
transition, the new state must be latched. For example:

```text
Vds(H2)=0
    -> triggers H2 turn-on
    -> H2 stays on
    -> until the fixed Ton ends
```

`Vds=0` must never be required to hold throughout the entire high-side
conduction interval. The same applies to negative-current detection:

```text
iL2 reaches the negative-current threshold
    -> triggers L2 turn-off
    -> L2 stays off
```

## VIII. Periodic initial-state principle

`36/24/12 V` may only be used as an initial guess for the periodic solve
(`VC1~=36 V`, `VC2~=24 V`, `VC3~=12 V`). An ideal voltage source must never
force the flying capacitors to permanently hold these values while the result
is then presented as a demonstration of natural balancing.

The periodic steady state must satisfy `x(T)=x(0)`, where the state vector is
at least

```text
x = [VC1, VC2, VC3, Vo, IL1, IL2, IL3, IL4]
```

A local solve success must never substitute for full period closure.

Initial-state outputs use the following mandatory names:

- `LOCAL_SOLVED_SEED`: one or more local event/endpoint residuals converge,
  but the complete state vector has not satisfied `x(T)=x(0)`. It remains a
  numerical solver coordinate and may seed the next experiment, but is not a
  demonstrated steady-state initial condition.
- `VALID_PERIODIC_INITIAL_STATE`: every declared state in the complete vector
  satisfies the period-closure tolerances and the event sequence remains
  valid throughout the period.

A positive solved `ILk_INIT` may compensate a device-layer conduction drop
inside a local calculation, but that reconciliation is physically admissible
as a steady-state initial current only after it earns the
`VALID_PERIODIC_INITIAL_STATE` label. Until then it must remain
`LOCAL_SOLVED_SEED`; it may not be described as natural balance or a valid
periodic orbit.

## IX. Naming convention

The 2024 Fig. 3 devices map uniformly as:

```text
S1a -> H1    S1b -> L1
S2a -> H2    S2b -> L2
S3a -> H3    S3b -> L3
S4a -> H4    S4b -> L4
```

- `Hk`: phase-`k` high-side switch.
- `Lk`: phase-`k` low-side switch.
- `LINDk`: phase-`k` inductor.
- `Xk`: phase-`k` switching node.
- `Ck`: the corresponding flying capacitor.

The inductor must never also be written `Lk`, which would collide with the
low-side switch `Lk`; code must use the canonical name `LINDk`.

## X. Result grades

Every experiment must be assigned exactly one of the following grades:

- `PASS`: every predefined acceptance condition was met.
- `LOCAL_PASS`: only one phase or one stage was completed.
- `SENSITIVITY_ONLY`: only shows a direction of change.
- `EXPECTED_FAILURE`: failure caused by a known missing parameter or boundary.
- `PHYSICAL_BOUNDARY_FAIL`: a physical condition was not reached.
- `CONTROLLER_GUARD_PASS`: the controller correctly blocked an unsafe action.
- `NOT_PERIODIC`: the end-of-period state did not return to the initial state.
- `BLOCKED_BY_MISSING_DATA`: a required paper or device parameter is missing.
- `REJECTED`: the model or measurement method has a principled error; the
  result must not be used.

## XI. Prohibited actions

1. Never raise the negative current to achieve ZVS while still calling it the
   2024 2% result.
2. Never extend the paper-specified `Ton` to reach 125 A.
3. Never treat `50 ns` as a commutation duration.
4. Never treat `Vds=0` as a condition that must hold permanently.
5. Never mask a natural-balancing failure by changing the initial capacitor
   voltages.
6. Never call a 2025 three-phase sequence a 2024 four-phase sequence
   automatically.
7. Never call a constant-`Coss` model a real nonlinear GaN model.
8. Never call a single-phase local success a complete four-phase success.
9. Never delete a failed experiment or overwrite a parent experiment.
10. Never report only the final number without the boundary and the failure
    location.

## XII. GitHub archiving principle

After completing an explainable experiment or module:

```text
complete the experiment
  -> fill in BOUNDARY.md
  -> fill in RESULTS.md
  -> run the full test suite
  -> review the diff
  -> git commit
  -> push to GitHub
```

Uploaded: Python source, SPICE netlists, parameter libraries, `BOUNDARY.md`,
`RESULTS.md`, solver history, best-candidate parameters, automated tests.

Not uploaded: paper PDFs, `.raw`, `.log`, `.db`, temporary output, personal
report material, credentials or private data.

A failed experiment may only be committed once its boundary and conclusion are
completely written. A file from a run that is still in progress must never be
committed.

## XIII. Hand-off checklist

A new contributor (human or AI) taking over must, before running anything:

1. Read every core boundary file.
2. Check the latest Git commits.
3. Run the complete test suite.
4. Confirm the local working tree is clean.
5. Summarize what is completed and what is not.
6. Identify the parent experiment for the next step.
7. Identify the single changed variable (or the explicit solve vector).
8. Only run a simulation after this boundary check.

If the new contributor cannot state the current parent experiment, the
current branch, the parameter provenance, the changed variable, the success
condition, and the failure condition, they must not proceed.
