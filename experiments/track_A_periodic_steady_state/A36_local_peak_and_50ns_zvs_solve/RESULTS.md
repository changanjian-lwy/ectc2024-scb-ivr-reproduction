# A36 local two-residual solution

Final local candidate:

| Quantity | Result |
|---|---:|
| `IL1_INIT` | 5.2947 A |
| `IL2_INIT` | 21.205095337 A |
| H1 off | 16.66807 ns |
| `iL1` at H1 off | 124.999989 A |
| H1 peak residual | -0.000011 A |
| H2 on | 50.00075 ns |
| `Vds(H2)` at 50 ns | -0.000175 V |
| `Vds(H2)` at admission | -0.000531 V |

Both selected local residuals converge within numerical edge tolerance. The
hybrid controller admits H2 under ZVS at its nominal slot without extending H1
TON or changing a power-stage parameter.

## Non-periodic limitation

This is not a full solution. H2 current at its fixed-TON falling edge is only
117.766 A, H3 is not slot-ready at 100 ns, and the 200 ns current residuals for
phases 3/4 remain large. Changing `IL2_INIT` alone to repair the H2 peak would
also move the already-solved H2 ZVS time. The next solve therefore requires the
coupled slow-state vector, not another independent current adjustment.
