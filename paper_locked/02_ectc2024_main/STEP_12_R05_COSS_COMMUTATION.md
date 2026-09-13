# Step 12 — R05 source-branch Coss commutation

> **Post-audit classification:** `QUARANTINED_CROSS_PAPER_EXPLORATION`.
> P25 Modes 3-6 are a cross-phase handoff, whereas P24 interval three follows
> the same phase (`iL1`, `QL1`, then `QH1`). Therefore this run is not a P24
> sequence reproduction and cannot be cited as testing P24's 1%-2% claim.

## Purpose

Test one local P24 phase-1-to-phase-2 handoff before attempting the complete
four-phase cycle. The state begins at P25 Mode 5 and ends at Mode 6 when
`Vds(S2a)=0`.

## Fixed boundary

- Power topology: P24 Fig. 3, one four-phase module.
- Switching sequence: P25 Mode 5 to Mode 6, extended only by the fourth
  grounded low-side leg already recorded in the topology specification.
- `Vin=48 V`, `Vo=1 V`, phase peak `125 A`.
- Flying capacitors: `53.8 uF`, copied from the EPE 2019 auxiliary source and
  used only as an explicitly cross-source placeholder; this run makes no P24
  capacitor-value claim.
- Device: GS61008T named by P25; `Co(tr)=385 pF/device` from its manufacturer
  datasheet. One high-side and two parallel low-side devices follow P25.
- Added snubber/output capacitance: zero because P24/P25 give no value.
- No startup, nonlinear Coss, driver delay, parasitic interconnect, thermal or
  loss claim.

The `36/24/12 V` quantities are capacitor initial voltages, not independent
node-voltage sources. The nodes are allowed to move under the complete ladder
connections.

## Variable

Only the negative-current branch changes:

- `10%`: user-selected P25 Mode-4 bring-up endpoint;
- `5%`: lower P25 endpoint and Eq. (20) design endpoint;
- `2%`: upper P24 endpoint.

For each branch, `L=(1-alpha)*Lcrit`, where `Lcrit=1.4666667 nH` is the
user-selected recalculation from the printed P24 equation. This is a declared
cross-paper generalization of the factor printed as `0.95` in P25 Eq. (20).

## Initial 10% result

- `L=1.32 nH`, `iL2(0)=-12.5 A`.
- `Vds(S2a)` started at `11.9529 V` and crossed zero at `1.90134 ns`.
- `S2a` was latched on at `1.90151 ns`.
- `iL2` at turn-on was `-3.9745 A`.
- The local handoff passed. This does not yet establish periodic operation.

## Source-range sweep result

All other inputs were held fixed. The sweep first tested the source endpoints
`2%`, `5%`, and `10%`, then refined only within P25's explicit `5%-10%` range.

| Negative branch | Minimum `Vds(S2a)` | ZVS event |
|---:|---:|---|
| 2% | 8.3942 V | no |
| 5% | 4.9821 V | no |
| 6% | 3.8451 V | no |
| 7% | 2.7172 V | no |
| 8% | 1.5998 V | no |
| 9% | 0.4938 V | no |
| 9.4% | 0.0548 V | no |
| 9.5% | -0.0062 V | yes, 2.2322 ns |
| 9.6% | -0.0118 V | yes, 2.1267 ns |
| 10% | -0.0247 V | yes, 1.9013 ns |

Under this **device-Coss-only placeholder**, the simulated boundary is between
9.4% and 9.5%. This result does not refute P24's 1%-2% statement: the 2024
design's actual device arrangement, nonlinear Coss, added CH/CL, parasitics and
driver timing are unpublished. Instead, the failure identifies those values as
the next hardware-specific parameter request.

## Safety and model checks

- The commanded Mode-5 state has `S1b/S3b/S4b` on and both phase-2 switches
  off; Mode 6 turns on `S2a` while `S2b` remains off. No same-leg shoot-through
  command exists.
- `S2a` is event-triggered only after `Vds(S2a)<=0`; it is not switched at a
  fitted fixed time.
- Automated analytical/topology tests: 24/24 pass.

## Next experiment

R05B will prepend Mode 4, let `iL2` evolve through zero to the selected negative
threshold, and then enter this validated Mode-5/Mode-6 commutation block. The
10% branch remains the bring-up choice; 5% and 2% remain recorded margin
failures under the current placeholder rather than being tuned away.
