# Step 09 - R04 latched single-phase boundary audit

## Why this method was selected

The tested transition sequence is not an invented controller law:

- P24 Eq. (1)/(3) supplies `D=1/12` and `Ton=16.667 ns`.
- P24 Eq. (2) supplies the `125 A` phase-peak target.
- P24 Sec. II-B supplies the `-1%` to `-2%` negative-current target.
- P24 Sec. II-B itself supplies the ordered high-side, low-side, zero-crossing
  and 1%-2% small-negative-current intervals. P25 is not required to establish
  this local sequence; it may only supplement unpublished controller details.
- The variable-timing/ZCD controller family is supported by the ISSCC-2019
  work cited by both P24 and P25.

LTspice `.machine` is used only to give these published transition conditions
state memory. It introduces no detector threshold, blanking delay, Coss or
dead-time value.

## Scope boundary

This is a single-phase analytical periodic-state test with a derived 12-V
phase rail (`Vin/nP`) and stiff 1-V output. It is not a full-converter startup,
flying-capacitor-balance or ZVS claim. The run ends after validating entry into
the negative-current interval; the unsupported Coss commutation stage is not
modelled.

## Initial implementation failure retained

The first state-machine execution produced zero inductor current because the
initial clock condition skipped the high-side state and the `.output` readout
scale was interpreted incorrectly. This was an LTspice interface failure, not a
power-stage result. Only the state-machine readout and initial wait state were
corrected; no paper parameter changed.

## Two non-fitted inductance cases

| Case | Inductance source | Current at end of Ton | Peak current | Zero crossing | Reaches -2.5 A |
|---|---|---:|---:|---:|---:|
| R04A-1 | P24 printed Eq. (4): 1.46667 nH | 124.815 A | 125.109 A | 201.147 ns | 204.813 ns |
| R04A-2 | P24 Table I: 2.68 nH | 68.307 A | 68.468 A | 201.158 ns | 207.858 ns |

Both cases use `Ton=16.667 ns`; the 1-ns offset in absolute timestamps is the
declared state-machine trigger time and is not part of the paper on-time.

## Conclusion

The equation-derived `1.46667 nH` reproduces the published `125 A` peak within
the ideal-switch numerical tolerance. The Table-I `2.68 nH` case produces only
about `68.5 A` under the same published voltage and on-time boundaries.

Therefore the Table-I inductance and peak-current entries cannot both be used
as simultaneous truth for this row. The conflict is demonstrated by an
independent state-locked transient run. By user decision, subsequent main
models use the Eq.-(4) recalculation `1.46667 nH`; the Table-I `2.68 nH` value
remains only as a documented audit discrepancy.

## Next allowed experiment

Use `Lcrit=1.46667 nH`, recalculated from Eq. (4), for the subsequent main
four-phase state construction. Do not create a Table-I 2.68-nH branch.

Neither case may claim hardware ZVS until `CH/CL`, device Coss and transition
delay are sourced. The full-model low-side opening must not occur with finite
current unless the published capacitance-commutation path is present.
