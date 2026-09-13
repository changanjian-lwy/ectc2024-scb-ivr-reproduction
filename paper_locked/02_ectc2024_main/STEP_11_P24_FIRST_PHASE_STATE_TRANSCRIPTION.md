# Step 11 - Joint P24/P25 operating-state transcription

## Mandatory source order

1. P24 Fig. 3, Fig. 4 and Sec. II-B define the target four-phase architecture
   and its three broad intervals.
2. P25 Fig. 2, Fig. 3 and Sec. II supply circuit-level subdivisions for
   capacitance commutation and control implementation.
3. Neither source silently overrides the other. Agreement is merged, missing
   detail may be supplemented, and conflicts require a user-selected branch.
4. A three-to-four-phase rotation remains labelled `CROSS_PAPER_EXTENSION`.

## What P24 explicitly states for phase 1

### P24 interval 1: t0 to t1

- `QH1` and adjacent-phase low-side `QS2` conduct.
- `L1` charges through `Vin -> QH1 -> C1 -> L1 -> Co/load`.
- `iL1` rises to twice its phase-average current at the boundary.
- End condition: the fixed high-side on-time ends at `t1`.

P24 does not enumerate the gate states of every remaining low side in this
paragraph. They must not be assigned from ordinary complementary PWM.

### P24 interval 2: t1 to t2

- `QH1` turns OFF.
- Positive `iL1` charges the output capacitance of `QH1` and discharges the
  output capacitance of `QL1`.
- `QL1` can turn ON when its drain-source voltage reaches zero.
- End boundary described by P24: `iL1` reaches zero at `t2`.

The exact sub-time at which `Vds(QL1)=0`, the added parallel capacitance and the
dead time are not numerically published in P24.

### P24 interval 3: t2 to t3

- `iL1` crosses zero and becomes negative while `QL1` remains conducting.
- P24 states `1%-2%` of phase peak in the negative direction before `QL1`
  turns OFF under
  near-zero current/zero switching loss.
- Negative `iL1` then flows through the high-side output capacitance and returns
  energy toward the input, reducing `Vds(QH1)`.
- When `Vds(QH1)=0` at `t3`, `QH1` may turn ON under ZVS and the cycle repeats.

## P25 subdivision used only as auxiliary implementation evidence

For its three-phase module, P25 expands the rotating sequence to 15 modes. Its
first handoff provides these implementation details:

| P25 mode | Command/event | Physical role | Relation to P24 |
|---|---|---|---|
| 1 | `SH1` ON; `SL2` and `SL3` ON | `iL1` rises; other phase currents freewheel/fall | expands P24 interval 1 |
| 2/2' | `SH1` OFF; `iL1` commutates `CH1/CL1`; diode interval possible | brings `Vds(SL1)` to zero | early P24 interval 2 |
| 3 | `SL1` ON; `SL2/SL3` remain ON | phase currents fall | late P24 interval 2 |
| 4 | `iL2` crosses zero; `SL2` remains ON until the P25 negative target | prepares `SH2` ZVS | conflicts numerically with P24 and requires branch selection |
| 5/5' | `SL2` OFF; negative `iL2` commutates `CH2/CL2` | brings `Vds(SH2)` to zero | subdivides transition to next phase |
| 6 | `SH2` ON; `SL1/SL3` continue freewheeling | phase 2 begins rising | rotated equivalent of P24 interval 1 |

P25 explicitly supports other low-side freewheel conduction. It does **not**
support generating those commands as independent fixed complements of their own
high-side clocks.

## Four-phase control construction allowed by the sources

The only currently allowed rotation rule is:

`H1 rise -> L2 zero/negative -> H2 rise -> L3 zero/negative -> H3 rise -> L4
zero/negative -> H4 rise -> L1 zero/negative -> H1 rise`.

During each high-side interval, the remaining positive-current low sides stay
in their cross-phase freewheel states. A low side is released because its own
current reaches the selected, source-labelled negative target—not simply
because its high-side clock edge arrives.

## Unresolved items that block the next primary run

- P24 does not publish the four-phase expanded 20-mode state table.
- P25 prints only 9 of its 15 three-phase modes; the remaining phase-3 modes are
  declared identical rotations rather than individually drawn.
- P24 uses a 1%-2% negative-current target; P25 uses 5%-10% in its mode text and
  up to 5% in design Eq. (20). These remain separate branches.
- `CH/CL`, nonlinear Coss, dead time and ZCD delay remain unknown.

## User-selected bring-up branch

For the first executable commutation/state-machine bring-up, the selected
negative-current target is `10%` of phase peak, the upper end of the P25
Interval-4 range. This branch is selected because it provides the largest
commutation-energy margin and is therefore the easiest supported value with
which to establish operation.

It is not treated as the P24 optimum or final design value. After the state
sequence runs, identical margin tests must be repeated at P25 `5%` and P24
`2%`; lower circulating current is preferred if commutation still completes.

## Pre-run decision

No new four-phase LTspice run is authorized yet. First generate a full command
truth table for the four rotated handoffs and verify, on paper, that:

1. every finite inductor current has a conducting path;
2. no same-leg high/low pair is simultaneously commanded ON;
3. each flying capacitor has a paired charge and discharge path;
4. every state transition has a P24 condition or a clearly labelled P25
   subdivision;
5. unknown Coss commutation timing remains symbolic rather than guessed.
