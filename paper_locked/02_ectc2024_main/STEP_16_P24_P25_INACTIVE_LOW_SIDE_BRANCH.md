# Step 16 - P24/P25 inactive-low-side branch

## Source distinction

P24 explicitly says `QH1` and adjacent-phase `QS2` conduct in the first
interval. It does not enumerate the commanded state of every remaining low
side, so their OFF state cannot be inferred merely from omission.

P25 Mode 1 explicitly commands `SH1`, `SL2` and `SL3` in its three-phase
prototype. For the current four-phase target, adding `SL4` follows the same
all-inactive-low freewheel rule but is labelled `CROSS_PAPER_EXTENSION`.

## Two retained branches

### P24-minimal branch - R04D0

- Explicit switch set: `QH1 + QS2`.
- Unspecified phases are omitted from the local subnetwork rather than silently
  forced OFF in a full converter.
- Result: phase-1 current reaches 124.933 A and C1 receives charge.

### P25-expanded branch - R04D0E

- Commanded switch set: `SH1 + SL2 + SL3 + SL4`.
- `SL2+SL3` follow P25 Mode 1; `SL4` is the labelled four-phase extension.
- All electrical values and initial conditions remain identical to R04D0.

## Measurements and decision rule

Compare phase-1 current, inactive-phase currents and C1-C3 transferred charge.
Do not choose a branch because its numbers look more balanced. The P24-minimal
branch remains the primary evidence branch; the P25-expanded branch may fill
the unspecified gate states only if it remains explicitly provenance-labelled.

## Result

Status: **PASSED_AS_SEPARATE_PROVENANCE_BRANCH**.

| Quantity | P24-minimal R04D0 | P25-expanded R04D0E |
|---|---:|---:|
| `iL1(Ton)` | 124.783 A | 124.783 A |
| charge into C1 | 1.03898 uC | 1.03898 uC |
| `iL2(Ton)` | -11.351 A | -11.351 A |
| `iL3(Ton)` | not assigned by local branch | -11.351 A |
| `iL4(Ton)` | not assigned by local branch | -11.351 A |
| charge into C2 | approximately zero | approximately zero |
| charge into C3 | not represented | approximately zero |

The extra low-side commands do not change phase-1 current or C1 charge during
this isolated first interval. They do determine the current trajectories of
the other phases: every grounded inactive switching node places approximately
`-Vo` across its inductor, so L2-L4 decrease together.

Therefore the branches are not globally equivalent. Their difference becomes
important at the later zero-crossing and phase-handoff boundaries. The
P25-expanded result cannot be used to retroactively claim that P24 explicitly
commands every inactive low side.
