# Step 02 - Single-module four-phase topology and mode lock

## Decision

The smallest primary reproduction unit is one 2024 module with four phases.
The two-module/eight-phase case must be produced later by copying this module
and applying the inter-module phase shift. It must not be implemented as a
separate hand-drawn topology.

This step does not yet authorize a publication-locked SPICE netlist. It locks
what the papers support and lists what is still unknown.

## Source hierarchy

1. The 2024 ECTC paper is the primary source for the four-phase topology,
   three main intervals per phase, and the 48 V/1 V target.
2. The 2025 APEC paper is auxiliary evidence for terminal connectivity,
   capacitance commutation and the expanded interval sequence.
3. A statement shown only in 2025 is never silently relabelled as a 2024 fact.
4. A four-phase extension of a three-phase 2025 statement is explicitly tagged
   `CROSS_PAPER_INFERENCE`.

## Canonical node map

The executable list is in `ectc2024_mode_spec.py`.

| Part | Proposed connection | Evidence status |
|---|---|---|
| Vin | R0 to module reference 0 | 2024 explicit |
| S1a | R0 to R1 | 2024 Fig. 3 |
| C1, L1 | R1-C1-X1-L1-OUT | 2024 Fig. 3/text |
| S2a | R1 to R2 | 2024 Fig. 3 |
| C2, L2 | R2-C2-X2-L2-OUT | 2024 Fig. 3/text |
| S3a | R2 to R3 | 2024 Fig. 3 |
| C3, L3 | R3-C3-X3-L3-OUT | 2024 Fig. 3/text |
| S4a, L4 | R3-S4a-X4-L4-OUT | read from 2024 Fig. 3; terminal dots absent |
| S1b-S4b | X1-X4 to reference 0 | SL1-SL3 explicit in 2025 Fig. 1; fourth phase accepted as the scalable extension |
| Co | OUT to reference 0 | 2024 explicit |

`X1` to `X4` are the four switching nodes. `R0` to `R3` name the
high-side ladder nodes so that the SPICE netlist cannot confuse a ladder node
with a switching node.

## Phase-1 to phase-2 hand-off

The 2024 paper compresses each phase into three intervals. The 2025 paper
separates capacitor commutation and the negative-current interval. The working
state machine therefore uses six intervals per hand-off:

| Mode | Start cause | Commanded conducting switches | Main physical result | End cause |
|---|---|---|---|---|
| M1 | S1a is turned on after ZVS | S1a and adjacent S2b are explicit in P24; P25 explicitly keeps all other low sides ON in its three-phase case, so S3b/S4b ON is a labelled four-phase extension rather than a P24-printed fact | iL1 rises while the other phase currents freewheel/fall and adjacent phases transfer capacitor charge | fixed on-time reaches t1 |
| M2 | S1a gate removed | exact simultaneous four-phase command set unresolved | iL1 commutates output capacitances toward S1b ZVS | Vds(S1b)=0 at t2 |
| M3 | S1b gated on at zero Vds | S1b plus only those other switches supported by the rotating state table | applicable phase currents fall | adjacent monitored phase current crosses zero at t3 |
| M4 | monitored current crosses zero | its low-side path remains on | monitored current becomes slightly negative | negative-current target reached at t4 |
| M5 | corresponding low side gate removed | exact simultaneous command set resolved by adjacent-pair rotation, not ordinary complementary PWM | negative current commutates next high/low capacitances | next high-side Vds reaches zero at t5 |
| M6 | next high side gated on at zero Vds | next high side and its explicit adjacent partner | transfer advances to the next phase | next high-side on-time ends at t6 |

The same state pattern rotates 2->3, 3->4 and 4->1. This rotation is a model
construction rule, not a claim that the 2024 paper printed all expanded modes.

R04B rejected ordinary fixed complementary PWM, not the physical possibility
that other low sides conduct while an active high side is ON. P25 explicitly
supports those freewheel paths in its three-phase interval description. The
error was generating each low-side command solely as the complement of its own
high-side clock, instead of retaining it according to the cross-phase state and
zero/negative-current transition conditions.

## Resolved project decisions

| ID | Decision | Basis |
|---|---|---|
| U01 | S1b-S4b Sources are tied to module reference 0 | 2025 Fig. 1 explicitly grounds SL1-SL3; the project accepts the same scalable rule for phase 4 |
| U02 | Use a negative-current target range of 5%-10% of phase peak current | 2025 Interval 4; do not silently select one fitted value inside the range |

## Remaining missing information

| ID | Status | Question/issue | Why it blocks a locked SPICE run |
|---|---|---|---|
| U03 | partially specified | 2025 gives commutation equations, GS61008T and driver type, but not CH/CL values, complete capacitor suffixes, or a numeric dead time | Determines commutation time and whether ZVS completes |
| U04 | principle only | 2025 says one inductor current can provide ZCD, points to reference [22], and lists adjustable on/off-time or constant-off-time control; it does not give the implemented detector, threshold, blanking or delay | Determines t3 and t4 rather than merely replaying them |
| U05 | absent | Neither paper defines zero-state startup, precharge, active series-capacitor balancing or startup current limiting | Prevents a justified zero-state startup simulation |

## Boundary decision

An exploratory ideal netlist may be generated later only if every inferred or
assumed item appears in its header and experiment record. It may be called a
`topology exploration`, not a `2024 reproduction`.

The publication-locked SPICE gate currently returns **false**.
