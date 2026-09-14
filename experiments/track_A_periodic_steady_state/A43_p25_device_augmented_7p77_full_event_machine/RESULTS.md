# A43 result - 7.77% does not transfer unchanged into the full event machine

## Outcome

The run completed numerically, but the four-phase sequence stopped in
`P1_M5`, before phase 2 was admitted. The earliest electrical failure is:

`P1_M5: wait for Vds(H2)=0 -> event never occurs`.

The controller behaved correctly: it blocked H2 rather than hard-switching
it. H3 and H4 are downstream non-events, not independent failures.

## Event chain

| Physical event | State transition | Time |
|---|---|---:|
| H1 fixed on-time ends | `P1_M1 -> P1_M2` | 16.668 ns |
| phase-1 low-node commutation completes | `P1_M2 -> P1_M3` | 16.805 ns |
| `iL2` crosses zero | `P1_M3 -> P1_M4` | 30.847 ns |
| `iL2` reaches the 7.77% negative target | `P1_M4 -> P1_M5` | 45.340 ns |
| H2 reaches ZVS and is admitted | `P1_M5 -> P2_M1` | **never** |

At low-side release, `iL2` is approximately `-9.714 A`, consistent with the
`-9.7125 A` target to switching/numerical resolution. After release:

- minimum `Vds(H2)` = `1.418 V` at `47.852 ns`;
- `Vds(H2)` at the nominal 50-ns phase slot = `9.589 V`;
- H2, H3 and H4 never turn on;
- final event-machine state remains `P1_M5`.

## Why this differs from A42

A42 established 7.76%-7.77% only for a local P24 `t2->t3` state with its own
chained node voltages and single commutating phase path. A43 preserves A37's
full four-phase `LOCAL_SOLVED_SEED`, coupled flying-capacitor state and
simultaneously conducting low-side paths. Those are different energy states.

Therefore, the negative-current percentage is **not a topology-independent
constant**. Transferring 7.77% without transferring the complete local state
does not reproduce A42's voltage trajectory. This is precisely why A43 was
run without re-solving the state: the portability failure remains visible.

For comparison, A37's same full machine at 9% admitted H2 near 50 ns, although
it later failed at the H3 handoff and was not periodic. Reducing only the
threshold to 7.77% moves the first failure upstream from H3 to H2.

## Grade and next step

Grade: `LOCAL_EVENT_PROGRESS / H2_ZVS_FAIL / CONTROLLER_GUARD_PASS`.

Do not optimize all seven initial-state coordinates yet. The next controlled
test should keep the complete A37 state fixed and scan only `NEG_FRAC` between
7.77% and 9% to find the full-machine H2 admission boundary. That separates
the effect of the threshold from the effect of re-solving a periodic state.
Only after that boundary is known should a new state-solve branch be opened.
