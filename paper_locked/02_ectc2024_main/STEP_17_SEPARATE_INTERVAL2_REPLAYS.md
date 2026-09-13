# Step 17 - Separate P24 and P25 interval-2 replays

## Shared physical-event mapping, separate paper labels

Both branches contain a related capacitance-commutation event after the
phase-1 high side turns off. They do not share the same interval endpoint:

- P24 interval 2 ends when `iL1=0`.
- P25 interval 2 ends when low-side Vds is zero and `SL1` turns on.

The P25 endpoint is therefore an internal zero-voltage event inside the longer
P24 interval when the two descriptions are compared physically. This mapping
does not rename either paper's published `t2`.

## Fair-comparison device plug-in

Both experiments call the same external GS61008T library and the P25 Table III
population: one high-side device and two parallel low-side devices. This makes
the numerical comparison executable but does not turn GS61008T into a P24
specified component.

## P24 branch R04D2A

- Uses the P24-minimal local context `QH1 OFF + QS2 ON`.
- Remaining gates stay unspecified and are omitted, not asserted OFF.
- Ideal event logic turns QL1 on when its Vds reaches zero.
- The accepted run continues until P24 `iL1=0`.

## P25-to-four-phase branch R04D2B

- Uses `SH1 OFF + SL2 + SL3 + SL4 ON`.
- `SL4` is explicitly a three-to-four-phase extension.
- Ideal zero-delay logic minimizes Mode 2-prime and turns SL1 on at zero Vds.
- The accepted interval ends at that P25 `t2`; it does not continue to the P24
  current-zero endpoint.

## Result

Status: **BOTH_BRANCHES_PASSED_WITH_SEPARATE_ENDPOINTS**.

| Quantity | P24 branch R04D2A | P25-to-four-phase branch R04D2B |
|---|---:|---:|
| low-side Vds first reaches zero | 110.525 ps | 110.525 ps |
| `iL1` at low-side zero Vds | 125.308 A | 125.308 A |
| event called `t2` by that paper | `iL1=0` at 152.492 ns | `SL1` ZVS ON at 110.525 ps |
| `iL2` at P25 `t2` | outside branch endpoint comparison | -11.424 A |
| `iL3` at P25 `t2` | unspecified/omitted | -11.424 A |
| `iL4` at P25 `t2` | unspecified/omitted | -11.424 A |

The capacitance commutation is the same physical event under the shared device
plug-in. P25 names that event `t2` and ends Interval 2 there. P24 permits QL1
to turn on there but continues its Interval 2 until the inductor current
reaches zero. The elapsed time between these two P24 events is 152.382 ns in
the present device-plug-in model.

The P24 current-decay duration includes the GS61008T low-side equivalent
`RDS(on)=3.5 mOhm`; therefore it must not be compared to the ideal `L*I/Vo`
duration without accounting for the current-dependent conduction drop.

No fitted value was introduced. Both branches use the same initial state,
inductance, capacitance library and output boundary. Their different reported
endpoints arise only from the different publication definitions.
