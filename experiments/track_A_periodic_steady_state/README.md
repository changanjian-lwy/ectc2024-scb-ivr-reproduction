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

`A27-A39` develop and diagnose the device-capacitance/event-controlled 9%
cross-paper branch. Their local ZVS results and failures do not constitute a
P24 1%-2% periodic reproduction. `A40_analytical_peak_and_commutation_feasibility`
then separates the P24 lossless peak-current target from the P25
device-augmented ramp and audits the P25 Mode-5 time law without inventing an
unpublished time budget. `A41_p24_snubber_local_sensitivity` runs the resulting
fixed 1%-2%, 0-2-nF local screen. No positive passive snubber case reaches ZVS;
added capacitance monotonically worsens the post-release minimum high-side
`Vds`. `A42_zero_snubber_negative_current_threshold` then changes only the
negative-current target and independently brackets the local device-augmented
ZVS threshold at 7.76%-7.77%. This is a mechanism result, not a P24 periodic or
hardware conclusion, and it must not replace the P24 1%-2% branch.
`A43_p25_device_augmented_7p77_full_event_machine` then transplants only 7.77%
into A37's unchanged full-machine seed. It stops at `P1_M5`: H2's Vds bottoms
at 1.418 V and H2 remains blocked. This proves the A42 local threshold is not
portable without its complete local energy state.

No result may be promoted to the four-module assembly until the complete
single-module periodic orbit and its paper-defined event alignment are closed.

`A49_math_model_affine_periodic_seed_crosscheck` is a separate cross-check,
not part of the A00-A43 narrative chain above: it imports the parallel
`src/scb_ivr/` ideal-switch effort's own already-published periodic-orbit
state into `A37`'s own unmodified real-device, event-driven four-phase
construct (`CFLY` corrected to `3 uF` to match the orbit's own frozen
boundary; seven initial conditions replaced). The rotation stalls one
transition earlier than A37's own best candidate -- H1-to-H2 itself is
missed (`Vds(H2)` bottoms at `0.252 V`, never crosses zero) because the
imported phase-2 seed is a period-average current, not an instantaneous
snapshot at A37's own `t=0` reference instant. `1/15` residuals converge
(vs. A37's `3/15`), `0/4` phase transitions achieve ZVS admission (vs.
A37's `1/4`) -- worse than A37 on both of BOUNDARY.md's own named metrics.
See `A49_math_model_affine_periodic_seed_crosscheck/RESULTS.md`.

`A50_zvs_capable_solver_prototype` builds, on a byte-for-byte COPY of the
parallel `src/scb_ivr/` fast affine-periodic solver (never modifying the
original), a real-device extension: switch capacitance and genuine
event-driven dead time added to the same linear MNA descriptor framework.
Validated against two independent gates: (1) exact regression at
`dead_time_s=0`/no capacitance, reproducing the original ideal periodic
orbit bit-for-bit; (2) reproducing `A42`'s own already-SPICE-verified
single-phase local ZVS threshold (no crossing at `7.76%`, crossing at
`7.77%` within `1.9%` of A42's own timing, against a pre-declared `20%`
tolerance), cross-checked further against a closed-form lossless-LC
solution fitted to all 28 of A42's own published rows. Both gates passed.
See `A50_zvs_capable_solver_prototype/RESULTS.md`.

`A51_four_phase_joint_zvs_solve` uses A50's own validated solver to
search for a genuine four-phase joint periodic fixed point (`z*=F(z*)`,
now non-affine since dead-time crossings depend on the state) -- the
first attempt to do this search with a fast (seconds, not SPICE's
20-100+ minute) evaluator, seeded from A37's own best SPICE candidate.
At P24's own rated `250 W`, a genuine fixed point is found (residual
`2.26e-11`) but ALL FOUR phases hard-switch. A load sweep (an engineering
diagnostic, not a P24 claim) locates a sharp boundary: below `~190-225 W`
(phase-dependent), the same ripple/load-balance mechanism that starves
ZVS at `250 W` reverses, and at `190 W` a converged state (residual
`4.78e-07`) exists at which ALL FOUR phases achieve natural ZVS --
the first self-consistent four-phase joint ZVS periodic state found by
any method in this project's history. Extensive robustness checks
(dead-time, sub-step, `Rds(on)`, divider admissibility, local stability)
support the finding; the result rests on a Python solver validated only
against A42's own single-phase case, so a SPICE cross-check was flagged
as the required next step. See
`A51_four_phase_joint_zvs_solve/RESULTS.md`.

`A52_spice_crosscheck_reduced_load_zvs` performs that SPICE cross-check.
First, A51's own headline state (idealized `1 uOhm` switch resistance)
was corrected to GS61008T's real `7 mOhm` (uniform on both sides,
matching A51's own model simplification, not A37/A42's more detailed
asymmetric `RHS`/`RLS`) and re-solved -- still ZVS on all four phases, at
`89.9 W` actual delivered power. A real LTspice netlist was then built
with an exact, independently-piloted event-gated switching sequence
(natural zero-voltage crossing OR commanded dead-time timeout, whichever
comes first -- confirmed correct on 8 isolated pilot runs before the full
build), seeded from that corrected state, with every timing window
derived programmatically from the solver's own code (no hand arithmetic).
**Result: SPICE independently confirms natural ZVS on all four phases**,
at crossing times agreeing with the Python solver's own predictions to
within `0.107%-0.242%` (against a pre-declared `20%` tolerance) -- the
first SPICE-confirmed four-phase joint ZVS periodic state in this
project's history. This remains `SENSITIVITY_ONLY` (a `76%`-of-rated-load
finding, not a P24 operating point) and does not by itself constitute a
P24/P25 reproduction claim. See
`A52_spice_crosscheck_reduced_load_zvs/RESULTS.md`.

`A53_lphase_zvs_load_tradeoff` asks the complementary question: instead of
reducing LOAD (A51/A52's own lever), can P24's own RATED `250 W` load be
kept fixed and `LPHASE` reduced instead to unlock ZVS, and is that actually
a net efficiency win? A local wrapper exposes `phase_inductance_h` as an
overridable parameter on A51's own boundary construction, and A51's own
Newton+Picard search (embedded in that script's `main()`) is re-expressed
as an importable function, reproducing A51's own published nominal residual
bit-for-bit as a fidelity check. Because a raw, un-converged evaluation of
A37's own fixed seed state turns out to exceed the `+/-250 A` safety bound
once `LPHASE` drops much below nominal, every candidate is instead solved
by continuation (warm-started from the previous, nearby candidate's own
converged fixed point) rather than re-seeded from A37's own values.
**Result: a critical `LPHASE` of `1.19625 nH` (`18.44%` below the paper's
own nominal `1.4667 nH`) is found, at which all four phases achieve natural
ZVS at the FULL rated load** -- confirmed converged and step-size-consistent.
But the net Watts comparison does not favor it: RMS current (integrated from
the actual solved waveform) rises enough that the conduction-loss increase
(`+40.5 W` at critical, `+58.5 W` at a `10%`-further margin point) is
`18x`-`27x` LARGER than the capacitive switching loss eliminated (`2.09 W`,
computed from A51's own already-published measured capacitances and
hard-switch residual voltages). **Achieving ZVS at rated load by shrinking
`LPHASE` alone is therefore not shown to be a net efficiency win** under
this project's own conduction/switching loss model -- a genuine, quantified
negative finding, distinct from and not superseding A51/A52's own positive
load-reduction result. Every phase current stayed at or below `150.13 A`
(`60%` of the `+/-250 A` bound) throughout the entire search. See
`A53_lphase_zvs_load_tradeoff/RESULTS.md`.

`A54_epc2067_lphase_joint_tradeoff` asks whether a JOINT change -- swapping
GS61008T for EPC2067 (P24's own printed Table 3, `nP=4`/`nM=4` row's own
specified device and population, `NHS=2`/`NLS=3`, already present in this
repository since `A45` but never before fed into the A50-A53 ZVS-search
chain) AND re-bisecting `LPHASE` -- can find a genuinely better net-Watts
balance than A53's own GS61008T result. EPC2067 offers `4.5x` lower per-
device resistance (`1.55 mOhm` vs `7 mOhm`) but `~7-9x` higher total switch
capacitance (`CH=3720 pF`/`CL=5580 pF` vs `385/770 pF`), so the outcome was
genuinely uncertain, not assumed. A sibling local wrapper reuses A51's own
boundary-construction functions and A53's own generic Newton+Picard search
machinery (`a53_solve.py`, verified device-agnostic), both imported
read-only, with only the device parameters changed. **Result: confirmed
first (not assumed) that EPC2067 at nominal `LPHASE` still hard-switches all
four phases at `250 W`**, exactly like GS61008T. The critical `LPHASE` was
found much deeper than A53's: `0.62741 nH`, a `57.22%` reduction from
nominal -- more than `3x` A53's own `18.44%`, directly confirming
`BOUNDARY.md`'s own `~3x`-higher-threshold estimate from the capacitance
increase. The net Watts comparison remains negative (`-20.75 W` at critical,
`-32.17 W` at a `10%` margin point) but is a genuine, quantified IMPROVEMENT
over A53's own GS61008T result (`-38.43 W`/`-56.45 W`) -- roughly HALVING
the net loss at both points, because EPC2067's lower resistance cuts
conduction loss sharply while its higher capacitance (measured fresh at this
run's own nominal point, since A51's own published capacitance numbers are
GS61008T-specific and do not transfer) raises the switching-loss "prize"
eliminated (`17.98 W` vs `2.09 W`). The improvement does not flip the sign of
the tradeoff, however: EPC2067 is a genuine improvement on this lever, but
"less bad," not "good." Safety held throughout (`+/-250 A` bound never
violated by any accepted candidate) but with much less margin than A53's own
search: maximum observed `232.54 A`, `93%` of the limit, only `7%` headroom
-- a direct, quantified cost of the much deeper `LPHASE` cut this device
requires. See `A54_epc2067_lphase_joint_tradeoff/RESULTS.md`.
