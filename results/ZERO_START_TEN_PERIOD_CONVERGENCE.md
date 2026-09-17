# Zero-start theoretical solver: ten-period checkpoint

## Frozen boundary

The boundary is unchanged from the first-period audit: one idealized 250 W
module, `Cfly=3 uF`, `Cdiv=300 uF`, `Tramp=22.87 us`, 5 MHz fixed PWM from
`t=0`, zero initial stored energy. Only the integration step is compared.
Ten periods equal `2 us`; the commanded source is then about `4.1976 V`.

## Step-size comparison at 2 us

| Quantity | 0.125 ns | 0.0625 ns | Absolute difference |
|---|---:|---:|---:|
| Diode transitions | 60 | 60 | 0 |
| `a1` | 1.739876 V | 1.739864 V | 12.10 uV |
| `a2` | 1.150142 V | 1.150134 V | 7.84 uV |
| `a3` | 0.572037 V | 0.572034 V | 3.51 uV |
| `Vout` | 7.701110 mV | 7.700842 mV | 0.268 uV |
| `IL1` | 16.878685 A | 16.880724 A | 2.04 mA |
| `IL2` | 16.936451 A | 16.939573 A | 3.12 mA |
| `IL3` | 17.922333 A | 17.927149 A | 4.82 mA |
| `IL4` | 20.845555 A | 20.846727 A | 1.17 mA |
| Input-parasitic-inductor current | 170.720687 A | 170.724833 A | 4.15 mA |

The event count and physical states agree closely, so the reference solver is
numerically stable over this checkpoint. This is still not a startup-success
claim.

## Physical interpretation

The four equal 300 uF divider capacitors have a 75 uF series equivalent. A
22.87 us linear 0-to-48 V ramp therefore demands about `157.4 A` from divider
charging alone. The solved `170.7 A` input current is only about 8.5% higher,
consistent with added switching-stage current and source-network dynamics.

This establishes a useful necessary screen:

`Tramp >= Cdiv*Vin/(4*Ilimit)`.

At the project's provisional 250 A screen, `Tramp >= 14.4 us`; this falls
inside the independently observed LTspice transition bracket of `5-22.87 us`.
The divider charge demand is therefore a primary mechanism, not an incidental
simulation detail.
