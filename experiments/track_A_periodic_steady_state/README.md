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
project's history. This remains `SENSITIVITY_ONLY`: the SPICE-confirmed
uniform-`7 mOhm` corrected state delivers `89.92 W`, not A51's nominal
`190 W` (`76%`) load-setting value, and is not a P24 operating point. It does
not by itself constitute a P24/P25 reproduction claim. See
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

`A55_joint_lphase_deadtime_total_loss_optimization` corrects two limitations
that prevent A54's numbers from serving as a rigorous next-stage baseline.
It applies P24 Table 3's EPC2067 population to resistance as well as
capacitance (`RHS=1.55mOhm/2`, `RLS=1.55mOhm/3`), resolves each periodic state
with those unequal resistances in the dynamics, and integrates high-side,
low-side and dead-time current exposure separately. Re-solving A54's three
saved comparison points gives channel-loss proxies of `8.592/21.404/25.259 W`
at nominal/old-critical/old-margin. More importantly, the old critical point
is no longer all-phase ZVS (`F/F/F/T`); the deeper margin remains `T/T/T/T`.
This is a baseline correction, not an optimization result. A55's eventual
objective is explicitly a partial electrical-loss proxy, not total system
loss, because third-quadrant dead-time loss and magnetic loss remain
unmodelled. See `A55_joint_lphase_deadtime_total_loss_optimization/BOUNDARY.md`.

2026-09-26 continuation: the corrected four-phase transition is locally
bracketed at 0.621524–0.622014 nH with dead time fixed at 2.15 ns; halving
both time steps retains the ZVS classifications. The passing point delivers
219.97 W, not 250 W, and has negative valleys around 39% of positive peaks.
Independent actual-branch metering exposes a further loss-accounting issue:
phase inductor current is not always channel current in this flying-capacitor
network. At the passing point actual model channel dissipation is 24.955 W
versus the old proxy's 21.718 W. Joint ranking must use the corrected metering.
See A55 `RESULTS_2026-09-26.md`; this remains a sensitivity result.

2026-09-27: A55's 3x3 local L/dead-time grid is complete. Only those two
boundary fields vary; each power-metering replay is checked against its solve.
All nine points converge, but none meets both rated output and the paper's
small-negative-current condition. Full matrix and refinement evidence are in
`A55_joint_lphase_deadtime_total_loss_optimization/JOINT_GRID_RESULTS.md`.
This is not an equal-output-power loss optimization or a native P24 controller.

`A56_equal_power_regulated_loss_comparison` re-compares A55's nine L/dead-time
points at EQUAL delivered power. Each is regulated to mean(Vout^2/R)=250 W by
an openly declared command on-interval `Ton_cmd`; the 4 mOhm load is never
retuned, and a test proves every scheduler path reads the override. A55's
`metered_orbit` rebuilds its own boundary and so is used through a documented
scoped rebinding. The required capacitive-accounting check found that A55's
branch meter captures only 18-31% of each hard-switch node-capacitance
discharge at the 62.5 ps step. The rest is backward-Euler numerical damping,
confirmed by the exact energy identity. The measured missing energy is
therefore added. At 250 W, the regulated nominal baseline (`Ton_cmd` +13.3%)
has a partial-loss proxy of 31.38 W (18.41 W metered + 12.97 W missed). The
best all-eight-ZVS point (0.627406 nH, 2.15 ns, `Ton_cmd` +6.2%) has 28.21 W,
a 3.18 W advantage. The proxy is step-converged, and a source-side energy
balance confirms it. The margin is narrow: a constant reverse-conduction drop
of only ~0.9 V under the fixed symmetric dead time would erase it. Coss
nonlinearity and magnetic loss are unresolved, and negative currents remain
~39% of peak. This is a partial electrical-loss proxy result, not a hardware
efficiency or native-P24 claim. See `A56_equal_power_regulated_loss_comparison/RESULTS.md`.

`A57_datasheet_reverse_conduction_pricing` prices A56's dead-time conduction
with the EPC2067 datasheet's Fig. 8 reverse characteristic (`VGS=0`, digitized
from the PDF vector paths; 2.27-2.52 V at the 22-72 A per-device operating
currents, far above A56's 0.9 V break-even). A56's model turns each gate on at
the natural zero crossing, so its numbers are the ideal adaptive-dead-time
limit and stand unchanged there (ZVS -3.18 W). Under the fixed symmetric dead
time of the A51 scheduler, the best ZVS point becomes 44.47 W vs the baseline's
37.41 W (+7.06 W). Even the table's 1.2 V floor leaves ZVS +1.23 W. The ZVS
advantage survives only if every edge's residual reverse conduction stays
below ~0.44 ns. This is first-order post-processing (orbits not re-solved with
the clamp), and 8 tests tie it to A56's accounting. See
`A57_datasheet_reverse_conduction_pricing/RESULTS.md`.

`A58_asymmetric_fixed_deadtime_tuning` splits the single dead time into two
fixed values, `d_rise` (high-side edge) and `d_fall` (low-side edge), common
to all phases. It does not edit the scheduler files: the four schedule
functions are swapped by object identity. Tests prove bit-identity with A56
when the two values are equal, and that no path reads the old scalar. A
67-point grid was regulated to 250 W (no failures, inside the 250 A
screen). The tuned large-ripple design (0.6274 nH, 1.9/0.6 ns) reaches a
29.11 W fixed-dead-time proxy with the datasheet VSD, against 31.81 W for
the tuned baseline (1.4667 nH, 2.15/1.1 ns). The -2.70 W difference is 85%
of A56's adaptive -3.18 W and reverses A57's symmetric +7.06 W. It is
step-converged (62.5/31.25/15.625 ps) and confirmed by an extrapolated
source-side balance to 0.01 W. The optimum is near-ZVS: it turns on at
0.7-1.7 V residual on six of eight edges, trading 0.26 W of capacitive loss
for most of the reverse conduction. The advantage holds for falling-edge
errors from -0.1 to about +0.35 ns. Magnetic loss, nonlinear Coss and other
loads remain open. See `A58_asymmetric_fixed_deadtime_tuning/RESULTS.md`.

`A59_nonlinear_coss_epc2067` replaces the constant Co(tr) with EPC2067's
datasheet Coss(V), digitized from Fig. 5a. The digitized curve reproduces
the printed Q(20 V), Co(tr), Co(er) and Coss(20 V) within 1%. The stepper is
charge-based backward Euler with a per-step Newton solve. It is installed by
object identity without editing the solver files, and it reproduces the
linear solver to 5.8e-12 when given a linear charge model. The dead times
were re-tuned on a 52-point grid centered on the new transition times. The
tuned large-ripple design (1.95/0.65 ns) reaches 28.67 W and the tuned
baseline (2.15/1.15 ns) 33.26 W, a -4.58 W difference (A58: -2.70 W). The
real curve makes the baseline's 12 V hard turn-on 28% costlier per device
(Qoss*V - Eoss vs 1/2 CV^2). The result is step-converged and confirmed by
an extrapolated source-side balance to 0.01 W. Reading the datasheet also
showed that the project's EPC2067 "typical" RDS(on) (1.55 mOhm), Coss (1607
pF) and Qoss (56 nC) are the MAX column; typical values are 1.3 mOhm,
1071 pF and 37 nC. Only RDS(on) is used, and 1.55 mOhm equals the typical
device at Tj ~ 60 C (A60). See `A59_nonlinear_coss_epc2067/RESULTS.md`.

A60-A63 stress-test A59's tuned comparison with public data only, before
any request to the advisor:

- `A60_temperature_ron_sensitivity`: typical RDS(on)(Tj) = 1.3 mOhm times the
  EPC2067 Fig. 9 factor. The advantage is -7.19 / -4.56 / -1.26 / +0.98 W
  at Tj 25 / 60 / 100 / 125 C, reversing at ~114 C, because the
  large-ripple design's loss is almost all conduction. The optima do not
  move with temperature.
- `A61_inductor_loss_break_even`: all solves have ~zero inductor
  resistance. The advantage is erased by an equal winding DCR of 293 / 185
  / 50 uOhm (skin-scaled 5 MHz ACR 263 / 166 / 45 uOhm) at Tj 25 / 60 /
  100 C.
- `A62_load_sweep_fixed_deadtime`: with 250 W-tuned fixed dead times, the
  large-ripple design wins only above ~211 W (84% load). Its ~22 W
  circulating-current floor stays at light load: 22.1 vs 11.8 W at 100 W
  out. With ideal adaptive turn-on the crossover is still between 200 and
  225 W.
- `A63_flying_capacitor_sensitivity`: the advantage is -6.13 / -4.97 /
  -4.58 / -4.17 W for Cfly = 1 / 2 / 3 / 6 uF, so the exact Cfly is not
  blocking for this comparison.

Together these say that A56-A59's rated-load advantage is a narrow,
warm-device, full-load, low-inductor-loss result, not a design win.

`A64_vendor_model_spice_crosscheck` (verification line) repeats the tuned
comparison in LTspice with EPC's own EPC2067 subcircuit. The model was
hash-checked from public mirrors and is not redistributed. The run uses
floating 5 V gate drives and SPICE-retuned timing, at 250 W and 60 C. The
ranking reverses: the large-ripple design loses by +17.35 W at R_drv =
1 Ohm and +1.20 W at 0.3 Ohm. The cause is turn-off V*I overlap at ~189 A
per high-side switch, which an ideal switch cannot have: 26.9 vs 7.7 W at
1 Ohm. Where the two models should agree, they do: Rds(on), Coss, the
baseline's hard turn-on and the conduction loss. The parent session
independently replayed all four optima to within 0.04 W. See
`CONSOLIDATED_FINDINGS_A53_A64_2026-09-28.md` for the whole A53-A64 chain
and the remaining advisor questions.
