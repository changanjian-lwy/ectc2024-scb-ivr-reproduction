# Step 27 - R04E0 startup-voltage supervisor (static observer test)

## Purpose and source boundary

P24 is retained as the four-phase power-stage target.  P24 does not publish a
zero-initial-energy startup-release law.  Therefore this detector is labelled
`EXPLORATORY_ASSUMPTION`; it is a replaceable controller slot and is not a P24
result.  It observes voltages and currents only.  It does not drive a P24 switch,
precharge a capacitor, or force the `36/24/12 V` periodic-state candidate.

## Fixed boundary

- `Vin = 48 V`, `nP = 4`; neither is omitted.
- Target adjacent segment voltage: `Vin/nP = 12 V`.
- Exploratory acceptance window: `10...14 V` (`12 V +/- 1/6`).
- Exploratory safe-current boundary: `abs(iLk) <= 1 A` for all four phases.
- Ordered ladder is required: `Vin >= VC1 >= VC2 >= VC3 >= 0`.
- The tolerance and current limit are controller design inputs, not values
  reported by P24 or P25.

The evaluated voltages are

`[Vin-VC1, VC1-VC2, VC2-VC3, VC3]`.

Absolute agreement with `36/24/12 V` is deliberately not the release rule.

## Executed cases and actual results

| Case | Change relative to E0 | Computed segments (V) | Result |
|---|---|---:|---|
| E0 | periodic-state reference `36/24/12 V` | `12,12,12,12` | READY |
| E1 | nodes changed to `37/25/13 V` | `11,12,12,13` | READY |
| E2 | planted absolute-node trap `39/21/15 V` | `9,18,6,15` | BLOCKED |
| E3 | E0 voltages, phase-3 current changed to `1.01 A` | `12,12,12,12` | BLOCKED |
| E4 | true zero stored energy `0/0/0 V` | `48,0,0,0` | BLOCKED |

The planted trap demonstrates why an absolute-node-only detector is unsafe:
each node is within 3 V of the ideal absolute level, yet the segment voltages
are not balanced.

## Verification

All project unit tests pass: `94 tests`, including five new supervisor tests.
Machine-readable output is stored at
`project/outputs/diagnostics/R04E0_startup_supervisor_static.json`.

## Result and next boundary

Status: **PASSED_STATIC_OBSERVER_ONLY**.

This does **not** show that the P24 circuit can build its ladder from zero.
E4 correctly shows the circular startup problem: a detector that waits for all
four final segment voltages cannot itself create them.  The next experiment must
be a separate, explicitly exploratory, current-limited pulse sequencer connected
to the zero-initial-energy P24 power stage.  Its pass criterion is monotonic
movement toward the segment window without capacitor overvoltage or phase-current
limit violation; numerical convergence alone is not a pass.
