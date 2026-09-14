# A30 results - P24 Table-1 2.68 nH sensitivity

LTspice completed normally. Only phase inductance changed from 1.4667 nH to
the 2.68 nH printed in P24 Table 1; the inherited seed was intentionally not
refitted.

| Quantity | Result |
|---|---:|
| `SL2` release | 19.44981 ns |
| `iL2` at release | -2.50067 A |
| negative-current magnetic energy | 8.379 nJ |
| minimum `Vds(SH2)` | 7.5181 V |
| time of minimum | 23.2316 ns |
| reached zero | No |

Status: **2% EVENT CAPTURE PASS / ZVS FAIL / NONPERIODIC SENSITIVITY ONLY**.

Increasing inductance delayed the threshold and allowed the -2.5 A event to be
captured, but did not supply enough commutation under the inherited state and
constant-Coss model. The one-period current residuals are large because the
1.4667 nH seed was not recomputed. Therefore this run establishes direction
and a failed energy boundary only; it is not a Table-1 reproduction.
