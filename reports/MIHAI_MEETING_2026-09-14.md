# ECTC 2024 SCB-IVR Reproduction - Live Progress Brief

> This is the continuously updated report source. When a meeting is confirmed,
> freeze a dated copy from this file rather than rewriting the experiment
> history. Results are organised in two dimensions: the switching sequence is
> decomposed horizontally in time, while each interval is refined vertically
> through device, control, multiphase and periodic-state layers. P24/P25 labels
> identify evidence provenance; they are not themselves the horizontal axis.

## 1. Research objective

The final target remains the 2024 ECTC 48-to-1 V, 1-kW SCB-IVR architecture.
The immediate objective is narrower: determine whether the reported system
specification, topology, analytical relationships, switching events and
device conditions admit a self-consistent four-phase periodic trajectory.

The work does not tune a circuit merely until its output resembles 1 V. It
records the first analytical or physical boundary at which a claimed operating
sequence ceases to be self-consistent.

## 2. Two-dimensional decomposition

### 2.1 Horizontal axis: one phase-to-next-phase switching sequence

The horizontal decomposition follows physical causality rather than paper-local
`t1/t2/t3` names:

| Horizontal segment | Start event | Dominant process | End event | Main quantity checked |
|---|---|---|---|---|
| H1. Energise | present high side admitted | inductor current rises | fixed `Ton` ends | peak current and volt-second relation |
| H2. High-side turn-off | high side opens | high/low output capacitances exchange charge | phase node reaches low-side clamp | turn-off overlap and low-side ZVS opportunity |
| H3. Positive freewheel | low side conducts | inductor current decreases | current reaches zero | DCM boundary and zero-cross detection |
| H4. Negative-current build | current crosses zero | a small reverse current is established | selected `-Ineg` is reached | P24 1-2% versus P25 5-10% rule |
| H5. Next-switch commutation | low side opens | reverse-current energy commutates the next high-side capacitance | next high-side `Vds=0` | available energy, participating Coss and commutation time |
| H6. Next-phase admission | zero-voltage event occurs | next high side turns on and latches | its own fixed `Ton` ends | phase-to-phase handoff and slot timing |

The experiments were deliberately built from left to right. A segment is first
tested locally; its measured terminal state becomes the next segment's initial
state. A later failure is not repaired by silently modifying an earlier
segment's published value.

### 2.2 Vertical axis: model depth applied to every horizontal segment

The first four layers mainly establish the design contract. The active
uncertainty begins at the device layer and propagates into control and
multiphase behaviour.

| Vertical layer | Role in every horizontal segment | Why it can change the result |
|---|---|---|
| V1. System specification | Locks 48 V, 1 V, 1 kW, 5 MHz, `nP=4`, `nM=4` | Defines power/current/time targets |
| V2. Evidence boundary | Labels every value as P24, P25, device data, numerical assumption, unknown or sensitivity | Prevents a successful auxiliary case from becoming a false P24 claim |
| V3. Analytical design | Supplies `D`, `Ton`, peak current, inductance and first energy/time estimates | Exposes equation/table conflicts before SPICE |
| V4. Power topology | Fixes switch, flying-capacitor and inductor connections | Determines the possible current and charge paths |
| V5. Device model | Selects ideal switch, `RDS(on)`, participating `Coss`, reverse conduction and later nonlinear/parasitic models | Directly changes current slope, charge demand, ZVS threshold and commutation time |
| V6. Physical-event detector | Converts waveform conditions into event boundaries | Detection definition/tolerance decides when a mode is considered complete |
| V7. Control state machine | Latches gates and enforces `Ton`, negative-current cutoff, dead time and ZVS permission | A physically available zero crossing can still be missed or blocked by control timing |
| V8. Four-phase coordination | Places the same transition inside the coupled H1-H2-H3-H4 system | Other phase currents and flying-capacitor voltages change the local energy state |
| V9. Periodic closure | Requires all stored-energy states to return after 200 ns | A complete event chain may still drift and therefore not be steady state |
| V10. Startup/implementation | Establishes the periodic state from zero and later adds loss, thermal, package and FEM | A valid periodic orbit does not itself provide a startup method or hardware proof |

### 2.3 The experiment is a matrix, not a one-way chain

The actual reproduction logic is the intersection of both axes:

| Horizontal event | V5 device question | V7 control question | V8/V9 system question |
|---|---|---|---|
| Current rise | Do `RDS(on)` and actual voltage reduce the ideal 125-A endpoint? | Is `Ton` fixed, measured or event-adjusted? | Does every phase reach a compatible peak and return periodically? |
| High-side turn-off | Which high-/low-side capacitances participate? | What dead time permits soft turn-off without excess reverse loss? | Do neighbouring low-side states change the commutation path? |
| Current zero and negative build | What reverse-conduction model is valid? | How is zero crossing latched and where is `-Ineg` measured? | Does using one common percentage work for all phases? |
| Next-switch ZVS | How much charge/energy does the selected Coss model require? | Is the zero-voltage event captured, held and aligned with the phase slot? | Does a locally sufficient threshold remain sufficient in the coupled four-phase state? |

This matrix explains the current result: A42 passed H5 locally at 7.77%, but
A43 failed the same nominal handoff after it was lifted to V8. The local number
was not wrong; its validity boundary was narrower than the full four-phase
state.

### 2.4 Evidence provenance is the label on each matrix cell

The source split remains essential, but it is not a geometric axis of the
decomposition:

| Provenance branch | Electrical target | Use |
|---|---|---|
| `P24_PRIMARY_REPRODUCTION_AUDIT` | 48 V to 1 V, 4 phases, 4 modules, 5 MHz | Preserve and test P24-explicit conditions, including failures |
| `P25_NATIVE_REFERENCE` | 12 V to 1 V, 3 phases, 3 modules | Interpret P25's detailed six-mode mechanism and prototype data |
| `P25_EXTENDED_ON_P24_TOPOLOGY` | 48 V to 1 V, 4 phases | Apply explicitly labelled P25 device/control supplements to the P24 target |

Thus every experiment has three coordinates: horizontal event, vertical model
depth, and evidence provenance.

## 3. System-level meaning of 1 kW and 5 MHz

At `Vo=1 V`, a 1-kW system requires 1000 A. Four modules share 250 A each;
four phases per module share 62.5 A average per phase. Under the paper's
zero-to-peak triangular boundary-mode approximation:

`Iphase,pk ~= 2 x 62.5 A = 125 A`.

Equivalently:

`Ptotal ~= nM x nP x Vo x Iphase,pk/2`

`= 4 x 4 x 1 x 125/2 = 1000 W`.

The active electrical simulation presently represents one repeatable 250-W,
four-phase module, not a completed four-module 1-kW validation.

At 5 MHz, `T=200 ns`. With four interleaved phases, the nominal phase spacing
is `T/nP=50 ns`. P24's duty relationship gives `D=4/48=8.333%`, hence
`Ton=16.667 ns`. The 5-MHz design point is treated as P24's reported nominal
case: it balances nH-scale embedded inductance against short-pulse control and
high-frequency loss. It is not asserted to be a universal optimum.

## 4. Analytical audit

For the P24 four-phase/four-module 5-MHz row, the reported relationships give:

- duty ratio: 8.333%;
- high-side on-time: 16.667 ns;
- phase peak current: 125 A;
- recalculated inductance from the printed equation: 1.4667 nH per phase.

P24 Table I reports 2.68 nH per phase for the same selected row. For strict
reproduction these are two independent P24 branches:

- `P24_TABLE_I_BRANCH`: lock 2.68 nH exactly and measure the resulting current
  and power; never retune it to reach 125 A.
- `P24_EQUATION_CONSISTENCY_BRANCH`: use the recalculated 1.4667 nH to test the
  printed equation and 125-A event sequence.

The current event-development line uses 1.4667 nH and therefore must not be
described as a strict Table-I reproduction. The 2.68-nH branch is preserved in
A30.

## 5. Topology and control decomposition

The reusable power-stage module contains four series high-side switches, four
ground-referenced low-side switch positions, three flying capacitors, four
phase inductors and one common output node. Device `Coss`, reverse conduction
and parasitics are plug-in layers rather than being embedded in control logic.

One phase-to-next-phase transition is represented by physical events:

1. present high side conducts;
2. fixed `Ton` ends and the high side turns off;
3. output capacitances commutate the phase node;
4. low side freewheels and inductor current decreases;
5. current crosses zero and builds a controlled negative value;
6. low side turns off at the selected negative-current boundary;
7. stored negative-current energy commutates the next high-side capacitance;
8. the next high side is admitted only if its own `Vds=0` event occurs;
9. the admitted gate is latched until its own fixed `Ton` expires.

Paper-local labels such as `t1/t2/t3` are treated as aliases for these events,
because the two papers do not always attach the same label to the same physical
boundary.

## 6. Common numerical boundary

All present periodic-state, local-commutation and P24/P25 comparison runs use
the same ideal output-isolation condition:

`Vo(t) = 1 V`.

This freezes output regulation so that topology, switching, ZVS, capacitor
balance and periodic closure can be studied consistently. It is a
`NUMERICAL_IDEALIZATION`, not proof of output regulation or 250-W delivery.

The zero-start track is separate and cannot use this boundary: it must begin
with `Vo(0)=0` and stored energy equal to zero.

## 7. Results across the horizontal sequence and vertical model depth

### 7.1 Analytical layer

- Duty, `Ton`, phase-average and 125-A peak relationships were reproduced.
- The 1.4667-nH versus 2.68-nH P24 conflict was exposed and preserved.
- A40 showed that P25's Mode-5 commutation relation does not yield a unique
  capacitance limit without a stated available time/dead-time budget.

### 7.2 Local physical-event layer

- P24 1% and 2% negative-current cases do not reach high-side ZVS under the
  present GS61008T charge-equivalent capacitance plug-in.
- A41 ran 28 fixed-boundary snubber cases from 0 to 2 nF. No case reached ZVS;
  added passive capacitance monotonically increased residual `Vds` and delayed
  the voltage minimum.
- A42 kept zero snubber and changed only negative current. The local threshold
  was independently bracketed between 7.76% and 7.77% of 125 A. This is a
  P25-device-augmented sensitivity result, not a replacement for P24's 1-2%.

### 7.3 Four-phase coordination layer

A43 transplanted only 7.77% into A37's unchanged full four-phase event machine.
It deliberately retained all seven A37 `LOCAL_SOLVED_SEED` coordinates.

- H1 completed its fixed on-time;
- the next inductor reached the -9.7125-A cutoff;
- H2 `Vds` bottomed at 1.418 V rather than zero;
- H2 was correctly blocked from hard turn-on;
- H3 and H4 never started because they are downstream of this first failure.

Thus a negative-current percentage found in an isolated local state is not a
topology-independent control constant. It depends on the complete coupled
energy state and participating commutation paths.

### 7.4 Periodic-state layer

Earlier one-group-at-a-time iterations reduced the maximum current residual
from 80.468 A for an all-zero current seed to approximately 0.105 A. A37 then
tested the complete 15-condition problem (four peaks, four ZVS/slot conditions
and seven periodic residuals) on the 9% P25 extension. Only 3 of 15 residuals
met tolerance; the full periodic orbit did not close.

Therefore 36/24/12 V and the solved inductor currents remain
`LOCAL_SOLVED_SEED` coordinates, not a demonstrated startup result or a valid
complete periodic initial state.

## 8. Current conclusion

The actively developed executable line is
`P25_EXTENDED_ON_P24_TOPOLOGY`, because P25 provides the more complete mode
sequence, switch population and device information. The final target remains
P24, while `P24_PRIMARY_REPRODUCTION_AUDIT` is retained to expose precisely
which P24 claims cannot yet be reproduced using disclosed information.

The current failure is no longer described generically as “the SPICE waveform
does not work.” It is localised by hierarchy and event:

- P24 1-2% fails the current device-augmented local ZVS boundary;
- a local 7.77% pass does not transfer to the unchanged full four-phase state;
- the earliest A43 full-machine failure is H2 ZVS admission at `P1_M5`;
- no complete four-phase periodic state has yet been demonstrated.

## 9. Information to confirm with Mihai

1. For P24 Table I's four-phase/four-module 5-MHz row, is 2.68 nH the final
   inductance of each individual phase? Which voltage/current boundary produces
   it, and does the 125-A peak apply to the same row?
2. In P24, exactly which current, switch-off instant, capacitances and
   commutation paths define the reported 1-2% negative-current requirement?
3. What device model and effective high-/low-side commutation capacitances were
   used for the 48-to-1 V case? Was an external snubber included, and for what
   purpose?
4. Were the 36/24/12-V flying-capacitor coordinates directly initialised,
   obtained from a periodic-state solver, or established by an unpublished
   startup/equalisation controller?
5. Should the immediate milestone be a complete ideal periodic mechanism, or
   should a specific startup and output-regulation implementation be included?

## 10. Next work after clarification

1. Keep P24 1-2% as an independent audit branch.
2. On the P25-on-P24 executable branch, evaluate complete downstream effects
   rather than selecting a threshold from H2 alone.
3. Seek a state that jointly satisfies the physical event chain and periodic
   closure; never repair phases sequentially while freezing an invalid prior
   solution.
4. Remove the ideal 1-V output boundary only in a separately named power-
   balance/regulation layer.
5. Return to zero-start only after the target periodic orbit and its required
   state are defined.
