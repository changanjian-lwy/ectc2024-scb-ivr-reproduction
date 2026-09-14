# A19 - P24 Interval 2 low-side conduction to iL1 zero

## Parent and source order

- Electrical parent: unchanged A16 periodic candidate.
- Prior physical event: A18 first `Vds(QL1)<=0` event after `QH1` turns off.
- P24 event under test: `QL1` conducts after the Coss commutation opportunity,
  and `iL1` falls to its first zero crossing.
- The first `iL1<=0` event after A18 defines the observed `t2`. This follows the
  physical event wording rather than assuming a fixed paper timestamp.

## Only change

Observation window and measurements only. No topology, initial state, device,
capacitance, gate expression, interleaving, output clamp or timestep is changed.

## Important interleaving boundary

P24's phase-1 Interval 2 overlaps the rotated activity of the other phases. The
other phases therefore remain active in this full four-phase run; A19 is not a
single-inductor isolated decay test.

## Acceptance checks

1. `iL1` remains positive immediately after the A18 low-side ZVS opportunity.
2. It subsequently decreases and reaches zero.
3. `Vds(QL1)` remains near its conducting-state value before the zero crossing.
4. No parameter may be changed to force a particular zero-crossing time.
