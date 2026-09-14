# A28/A30 phase-2 energy and event audit

| Case | Intended threshold | Actual release current | Magnetic energy at release | Minimum SH2 Vds | Interpretation |
|---|---:|---:|---:|---:|---|
| A28, equation L=1.4667 nH | 2% = 2.5 A | 6.5405 A = 5.23% | 31.371 nJ | 4.371 V | threshold missed during TON lockout |
| A30, Table-1 L=2.68 nH | 2% = 2.5 A | 2.5007 A = 2.00% | 8.379 nJ | 7.518 V | true 2% captured, no ZVS |
| A28B, equation L=1.4667 nH | labelled P25 extension 9% | approximately 11.25 A | approximately 92.8 nJ | reaches zero | local ZVS pass |

The comparison separates two problems:

1. **event placement/state problem:** A28's inherited `iL2(0)` makes the 2%
   crossing occur before release is allowed;
2. **commutation sufficiency problem:** when A30 captures a true 2% crossing,
   its available magnetic energy still does not complete the assumed Coss
   transition.

The next experiment must not tune the clock or threshold. It must first solve
the periodic phase-state boundary, then audit the effective Qoss/voltage path.
