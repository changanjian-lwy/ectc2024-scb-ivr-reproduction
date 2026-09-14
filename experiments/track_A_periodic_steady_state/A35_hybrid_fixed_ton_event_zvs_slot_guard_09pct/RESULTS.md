# A35 hybrid-controller result

LTspice completed normally. The hybrid controller enforced relative `TON` for
H1, retained event-driven commutation, and required both the 50 ns phase-2 slot
and H2 zero voltage before admission.

| Quantity | Result | Boundary |
|---|---:|---|
| H1 off | 16.6681 ns | fixed `TON=16.6667 ns`: pass within numerical edge tolerance |
| `iL1` at H1 off | 119.2558 A | target 125 A: fail |
| peak-current residual | -5.7442 A | must converge to zero |
| early H2 zero-voltage opportunity | approximately 26.10 ns | occurs before slot |
| `Vds(H2)` at 50 ns | 9.9585 V | zero required: fail |
| H2 command | blocked | correct protection behavior |
| final sequence state | P1-M5 | waiting for slot-qualified H2 ZVS |

## Conclusion

The recommended hybrid logic behaves correctly and fails closed: it neither
extends H1 conduction to manufacture 125 A nor hard-switches H2 at 50 ns. The
current inherited state produces two independent residuals:

1. `iL1(TON)-Ipeak = -5.7442 A`;
2. `Vds(H2, 50 ns)-0 = 9.9585 V`.

The next iteration must solve periodic state/physical-model inputs against
these residuals. Gate-order retuning is not authorized by this result.
