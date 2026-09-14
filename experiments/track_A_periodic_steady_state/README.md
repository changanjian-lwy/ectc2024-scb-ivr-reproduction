# Track A - P24 periodic steady-state reproduction

Order:

1. `A00_boundary__split_tracks_no_electrical_change`
2. `A01_p24_2pct__first_periodic_seed_all_iL_zero`
3. `A02_p24_8pct__change_negative_target_only` (after A01)
4. `A03_p25_handoff__change_sequence_branch_only` (after the P24 pair)

Later retained steps continue through the periodic shooting/tightening sequence
`A06-A16`. `A17_p24_interval1_observation` re-runs the unchanged A16 electrical
case and extracts only the P24 `t0-t1` event window; it is an observation step,
not another state update. `A18_p24_interval2_coss_commutation` then observes the
unchanged `t1` high-side turn-off and Coss commutation window. `A19` continues
from that zero-voltage opportunity until the first `iL1` zero crossing. `A20`
then audits whether the P24 2% negative-current event is compatible with the
simultaneous phase-4 adjacent-low-side conduction obligation.

`A21-A24` are a separate P25-derived, all-inactive-low four-phase extension.
They compare 5%, 8%, 9% and 10% negative-current targets with identical
electrical state; see `P25_THRESHOLD_SENSITIVITY_A21_A24.md`.

`A25_p25_four_phase_low_latches_09pct` applies event memory to all four low
sides for one rotation and reports the earliest failed boundary. It retains
the fixed high-side schedule so scheduler incompatibility is visible.

`A26_h2_zvs_readiness_guard` inserts the paper-defined `Vds(SH2)=0` permission
check at the first A25 failure. It prevents hard turn-on but exposes an
unresolved choice between shortened on-time and shifted interleaving timing.

No result may be promoted to the four-module assembly until the complete
single-module periodic orbit and its paper-defined event alignment are closed.
