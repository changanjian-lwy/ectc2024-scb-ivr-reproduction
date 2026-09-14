# A34 two-cycle observation results

Only the observation horizon changed from A33. The rotating controller returned
to H1 and repeated the same nonuniform event pattern.

| High-side sequence | First rise | Second rise | Repetition interval |
|---|---:|---:|---:|
| H1 | 0.0007 ns | 211.6104 ns | 211.6097 ns |
| H2 | 26.0959 ns | 237.8366 ns | 211.7407 ns |
| H3 | 79.1701 ns | 290.8888 ns | 211.7186 ns |
| H4 | 137.8222 ns | 349.8904 ns | 212.0682 ns |

Successive high-side gaps were approximately:

`26.10, 53.07, 58.65, 73.79, 26.23, 53.05, 59.00 ns`.

This is a repeatable approximately 211.7 ns orbit, not a startup-only anomaly
and not the required uniform 50 ns spacing. The controller therefore preserves
event order but does not yet enforce the P24 `T=200 ns`, `T/nP=50 ns` timing
contract.

The present compiler also ends each high-side state on the current-peak event.
P24/P25 state that the high-side conduction duration is `TON` and that current
reaches its peak at the end. Those two conditions must be checked together in
the next hybrid fixed-time/event controller; neither may silently replace the
other.

Status: **REPETITIVE EVENT RING PASS / PERIOD AND UNIFORMITY FAIL**.
