# A17 - P24 Interval 1 observation on the A16 periodic candidate

## Parent

- Electrical parent: `A16_tighten_04_C3/A16_tighten_only_C3_from_A15.cir`.
- Source event: P24 Sec. II-B Interval 1, `t0` to `t1`.
- Command state under test: `QH1=ON` and `QS2=ON`.
- Termination condition: the paper-derived fixed high-side on-time expires,
  `TON = NP * VO / VIN / FSW = 16.6666667 ns`.

## Only change from A16

There is no electrical or state change. This is an observation-only experiment
that re-runs A16 and extracts the first P24 interval. It does not alter topology,
initial state, switch commands, component values, Coss, negative-current target,
output clamp, or numerical settings.

## Locked boundaries

- Track A periodic steady-state only; this is not a zero-start test.
- Single four-phase module carrying the 250 W share of the P24 four-module row.
- `VIN=48 V`, ideal isolation boundary `VO=1 V`, `FSW=5 MHz`, `NP=4`.
- `LPHASE=1.4666666667 nH`, obtained from the printed P24 equation. The P24
  Table-I value `2.68 nH` remains an unresolved source conflict.
- P24 `2%` negative-current branch remains selected, although that threshold is
  not exercised during Interval 1.
- Flying-capacitor and output-capacitor values remain cross-source candidates.
- The theoretical capacitor ladder and shooting current seed are periodic-state
  coordinates, not a demonstrated startup state.

## Acceptance checks

1. `iL1` must increase during `t0-t1`.
2. The rise must be consistent in sign and scale with `vL1/L1`.
3. `iL1(t1)` should be near the P24 phase target `IPEAK=125 A`; any mismatch is
   reported, not tuned away.
4. The result cannot establish startup, full periodic closure, ZVS, loss, or
   four-module performance.
