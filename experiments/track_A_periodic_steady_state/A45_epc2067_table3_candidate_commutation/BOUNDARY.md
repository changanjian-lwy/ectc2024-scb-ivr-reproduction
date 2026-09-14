# A45 EPC2067 Table-3 candidate commutation boundary

Track: A, local P24 `t1->t2->t3` mechanism experiment (interval 1 -> interval
2 -> interval 3 chain). This is not a periodic-orbit or startup experiment.

## Parent and fixed quantities

Electrical parents (the full chain, re-run stage by stage, not just the
final stage):

- Stage 0: `paper_locked/02_ectc2024_main/spice/R04D0_p24_first_interval_shared_ladder.cir`
- Stage 1: `paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir`
- Stage 2: `paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir`

`R04D3A` is also A42's own parent
(`A42_zero_snubber_negative_current_threshold/BOUNDARY.md`), whose
methodology (coarse 1%-10% grid with the same `P24_EXPLICIT` /
`DIAGNOSTIC_BRIDGE` / `P25_SUPPLEMENT` row labelling, then a bracket-search
refinement) A45 reuses directly.

The following remain identical to the R04D0/R04D2A/R04D3A chain and to
A42's zero-snubber baseline:

- P24 topology, local state sequence and event-latch/control-machine
  structure (`.machine`/`.state`/`.rule`/`.output` blocks, unchanged);
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `nM=4` configuration context (the local
  subnetwork itself models `nM=1`, matching R04D0/R04D2A/R04D3A), `Ipk=125 A`
  (P24 Eq. 2), `Ton=16.667 ns`;
- locked Eq.-(4) `L=1.4666667 nH` (NOT the 2.68 nH Table-I value);
- no added snubber, delay, dead time, nonlinear `Coss(V)` or retuning;
- the same negative-current sweep convention as A42 (coarse 1%-10% grid in
  1-percentage-point steps, extended only because it did not bracket the
  threshold -- see "Only changed variable" below);
- `CFLY=53.8 uF` flying-capacitor placeholder (EPE2019-derived, unchanged,
  not fitted in this experiment either).

## Only changed variable

The commutation-capacitance `.include` is swapped from
`GS61008T_commutation_capacitance.lib` (`CH_TOTAL=385 pF`, `CL_TOTAL=770 pF`,
NHS=1/NLS=2) to `EPC2067_commutation_capacitance.lib` (`CH_TOTAL=3720 pF`,
`CL_TOTAL=5580 pF`, NHS=2/NLS=3), the device 2024's own Table 3 names for
this project's `nP=4`/`nM=4` row (2 parallel high-side + 3 parallel low-side
EPC2067). Values come from the EPC2067 datasheet, revised 2021-10-21 (see
`paper_locked/04_component_models/EPC2067_typical_params.lib` and
`EPC2067_commutation_capacitance.lib` for the full scope caveat: this is
2024's Sec. IV embedded/3-D package device selection, NOT yet confirmed to
be the device Sec. II-B's ZVS mechanism -- the circuit actually simulated
here -- assumes).

**Scope limitation -- Ron is intentionally not swapped.** Table 3 does not
give a validated `RDS(on)` model for EPC2067 at this operating point, so
switch on-resistance is frozen at the exact GS61008T 1-HS/2-LS literal
values every downstream stage already used (`RHS=GS61008T_RDS_TYP_25C/1`,
`RLS=GS61008T_RDS_TYP_25C/2`), independent of which capacitance library's own
`NHS`/`NLS` happens to be in scope. (`EPC2067_commutation_capacitance.lib`
defines its own `NHS=2 NLS=3`; if the stage-1/stage-2 `RHS`/`RLS` formula had
kept referencing `.../NHS` it would have silently picked up the new parallel
count and changed Ron too, which the task's single-variable requirement
forbids. Both stage netlists therefore hardcode the divisor instead.) This
means A45 tests only a capacitance/parallel-count-for-capacitance swap; it
does **not** test an EPC2067 Ron/conduction-loss model.

**Chained-state consequence, not a second independent variable.** Because
`CL_TOTAL` participates in interval 2's low-side Coss discharge as `iL1`
falls to zero, the state handed off to interval 3 (`VC1_T2`, `VX1_T2`,
`VA1_T2`) is itself a function of which commutation-capacitance library is
in use. Reusing R04D3A/A42's GS61008T-chain handoff state
(`VC1_T2=36.0193959392 VX1_T2=-9.6476751536u VA1_T2=36.0193862915`) would
have been physically wrong. A45 therefore re-runs interval 1 (stage 0,
unchanged, see below) and interval 2 (stage 1, EPC2067-substituted) and uses
stage 1's own measured handoff state
(`VC1_T2=36.0201391787 VX1_T2=-7.76858225411e-05 VA1_T2=36.0200614929`) as
stage 2's initial condition, replicating exactly the
measure-in-one-stage/`.param`-into-the-next mechanism R04D0->R04D2A->R04D3A
already used.

**Stage 0 (interval 1) is mathematically device-invariant.** R04D0 contains
no `CH1`/`CL1` element at all -- only the switches, flying capacitor and
inductor -- so its result cannot depend on the GS61008T-vs-EPC2067 choice.
Stage 0 is still rebuilt and rerun (not silently reused) for full-chain
provenance, and its output is checked to reproduce R04D0's committed
`IL1_MAX=124.932723999`, `VC1_END=36.0193109995`,
`IL2_AT_TON=-11.3505529996` exactly, which it does.

**.tran observation window widened for the larger negative-current
percentages, event-driven, not a physics change.** At the larger negative
percentages the wide bracket search required, the pre-release ramp itself
(time to reach `-NEG_FRAC*125 A`) grows to ~1.9-2.0 ns per percentage point
and can consume most or all of R04D3A's original fixed 50 ns window,
truncating the post-release commutation event before `Vds(QH1)=0` is
observed. Per `EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` Section VI ("a
fixed time may never substitute for a physical event"), the window is
widened (never shortened, never used to force an early cutoff) so the same
declared physical events are actually observed. No `.meas` measurement point
or control-latch rule changes.

## Success and extraction

A row passes the local event only when the low side releases at its exact
target and high-side `Vds` subsequently reaches zero naturally within the
observed window. The high side may turn on only after that voltage event.
Extract release time/current, ZVS time, commutation duration and current at
ZVS, exactly as A42 did.

The 1%-10% coarse grid is intended to bracket the threshold, matching A42's
convention. If it does not bracket a transition (as happened here), a wider
sensitivity search is run and reported honestly as a wider bracket, not
forced into the original grid. A later refinement searches only inside the
found bracket and remains a sensitivity result, not a paper value.

## Prohibited claims

1. A local pass here cannot establish that EPC2067 is the real Sec. II-B
   device; it only reproduces 2024's own Table-3 candidate-device population
   under the stated scope caveats.
2. Cannot establish or replace the P24 1%-2% claim.
3. Cannot establish four-phase closure, a periodic orbit, or startup
   behavior (this is a single-phase local `t2->t3` subnetwork, same as
   R04D3A/A42).
4. Cannot validate an EPC2067 Ron/conduction-loss model (Ron was frozen at
   the GS61008T value throughout; see scope limitation above).
5. Cannot claim hardware behavior, loss, or the authors' actual unpublished
   device selection for the Sec. II-B mechanism.
6. A comparison against A42's 7.76%-7.77% GS61008T-based bracket is a
   same-mechanism, different-device-assumption sensitivity comparison only;
   it does not by itself validate either device assumption against hardware.
