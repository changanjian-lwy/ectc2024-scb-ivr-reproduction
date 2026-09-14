# Four-phase gate truth tables: P24 minimal and P25 extension

Legend: `1` commanded ON, `0` commanded OFF, `E` physical-event controlled,
`?` not reported by the selected source.

## P24 minimal branch, active phase 1

| State | H1 H2 H3 H4 | L1 L2 L3 L4 | End condition | Compile status |
|---|---|---|---|---|
| I1 energy | 1 0 0 0 | 0 1 ? ? | high-side on-time ends | blocked by P24 silence |
| I2 Coss/low-ZVS/current decay | 0 0 0 0 | E ? ? ? | `iL1=0` | blocked by P24 silence |
| I3 negative/high-ZVS | E 0 0 0 | E ? ? ? | `Vds(H1)=0` | blocked by P24 silence |

Rows for phases 2-4 are exact index rotations. Visual inspection of P24 Fig. 3
establishes `Ska -> Hk` and `Skb -> Lk`; therefore the first row's adjacent
support device is the physical `S2b`, canonically `L2`.

The P24-minimal table passes the no-commanded-shoot-through check but is
intentionally **not compile-ready** because unreported gates remain unknown.

## P25 all-inactive-low extension, active phase 1 to phase 2

| Mode | H1 H2 H3 H4 | L1 L2 L3 L4 | End condition |
|---|---|---|---|
| M1 active H1 | 1 0 0 0 | 0 1 1 1 | H1 turns off |
| M2 H1/L1 commutation | 0 0 0 0 | 0 1 1 1 | `Vds(L1)=0` |
| M3 all-low freewheel | 0 0 0 0 | 1 1 1 1 | `iL2=0` |
| M4 build negative `iL2` | 0 0 0 0 | 1 1 1 1 | `iL2=-Ineg` |
| M5 H2 commutation | 0 0 0 0 | 1 0 1 1 | `Vds(H2)=0` |
| M6 active H2 | 0 1 0 0 | 1 0 1 1 | `iL2` reaches peak |

This table passes completeness and no-commanded-shoot-through checks. It is
labelled `P25_NP4_EXTENSION`: P25 prints the rule for three phases; rotating it
to four phases is an explicit cross-paper extension, not P24 text.

## Compilation decision

- Do not compile the P24-minimal branch by filling `?` with guesses.
- The P25 extension may be compiled as a separate experiment because all gate
  commands and physical end events are explicit after the labelled rotation.
- Both branches reuse the same topology, device, event and measurement modules;
  only the sequence slot changes.
