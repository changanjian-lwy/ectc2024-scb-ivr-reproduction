# Parameter-only feasibility envelope

## Purpose

This audit answers what can still be derived before the unpublished device and
timing values are known. It does not insert guessed `Coss`, snubber or dead-time
values and it does not claim a complete ZVS reproduction.

## Frozen boundary

- P24 case: 48 V to 1 V, 1 kW, `nP=4`, `nM=4`, 5 MHz.
- P25 calibration: 12 V to 1 V, 200 W, `nP=3`, `nM=3`, 0.5 MHz.
- Equal ladder segment voltage `Vin/nP` and constant inductor voltage are local
  steady-state analytical boundaries, not proofs of startup or self-balance.
- The local available commutation energy is bounded by
  `Eavail = 0.5 L Ineg^2`.
- The charge that can be moved in an available interval is bounded by
  `Qavail = |Ineg| dt`.
- A complete ZVS claim additionally requires the real nonlinear commutation
  energy/charge and the real available time.

## Two peak-current conventions must remain separate

The zero-valley triangular relation printed in the paper gives

`Ipk,paper = 2 Io / (nP nM)`.

If a negative valley `Imin = -alpha Ipk` is introduced while the same average
output current is enforced, the consistent mathematical extension is

`Ipk,corr = Ipk,paper / (1-alpha)`.

The papers do not explicitly reconcile these conventions. The software
therefore reports both rather than silently selecting one.

## Representative calculated bounds

| Case | alpha | Ipk,paper | Ipk,corr | Ineg,corr | L needed with paper peak | L needed with corrected peak |
|---|---:|---:|---:|---:|---:|---:|
| P24 | 1% | 125.00 A | 126.26 A | 1.26 A | 1.452 nH | 1.438 nH |
| P24 | 2% | 125.00 A | 127.55 A | 2.55 A | 1.438 nH | 1.409 nH |
| P24 | 5% | 125.00 A | 131.58 A | 6.58 A | 1.397 nH | 1.327 nH |
| P24 | 8% | 125.00 A | 135.87 A | 10.87 A | 1.358 nH | 1.249 nH |
| P25 | 5% | 44.44 A | 46.78 A | 2.34 A | 32.143 nH | 30.536 nH |
| P25 | 8% | 44.44 A | 48.31 A | 3.86 A | 31.250 nH | 28.750 nH |
| P25 | 10% | 44.44 A | 49.38 A | 4.94 A | 30.682 nH | 27.614 nH |

For P24 with `L=1.4667 nH`, the local energy budget rises from about
`1.17 nJ` at 1% to `4.77 nJ` at 2%, `31.74 nJ` at 5% and `86.64 nJ` at 8%.
These are ceilings available from the selected negative current, not the
unknown energy required by the real switching network.

For P25 at 5%, `L=22 nH` provides about `60.19 nJ`, while `L=32.1 nH`
provides about `87.82 nJ`. The same operating point requires about 30.54 nH
under the negative-valley-corrected current convention. This independently
preserves the previously observed 22 nH versus 31-32 nH tension.

## Result

Unknown numerical values do not stop the analytical audit. They convert the
ZVS question into two explicit necessary inequalities:

`Ecomm <= 0.5 L Ineg^2`

`Qcomm <= |Ineg| dt_available`.

Until `Ecomm` or `Qcomm` and `dt_available` are supplied, the program returns
`undetermined`, not `pass`. Once those inputs are inserted, the same module
evaluates the gates without changing topology, sequence or operating point.

Run `PYTHONPATH=src python3 scripts/analyze_parameter_envelope.py` to generate
the full deterministic JSON table.
