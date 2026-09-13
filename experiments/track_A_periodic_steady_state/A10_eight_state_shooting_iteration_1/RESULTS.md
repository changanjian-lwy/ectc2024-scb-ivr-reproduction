# A10 results

The first eight-state fixed-point substitution ran successfully. It reduced
the maximum current residual to 0.1859 A, but did not close the output state:
`dVout=-3.1305 mV` over one 200 ns period. Flying-capacitor residuals remained
within approximately 0.113 mV per period.

This is an incomplete periodic-state solve. It supports separating passive
flying-capacitor balance from output-voltage regulation; it does not support a
1 V steady-state, self-balance, or full four-phase 8% ZVS claim.
