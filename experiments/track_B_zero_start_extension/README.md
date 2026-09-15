# Track B - zero-start engineering extension

Canonical records remain at `paper_locked/02_ectc2024_main/STEP_27` through
`STEP_31`; their netlists remain beside those records to preserve links.

## Boundary-provenance gap found 2026-09-15 -- read before trusting `Cfly=53.8 uF` or `Cout=4.672 mF`

Every experiment in this track (`R00` through `R04E7`) uses `Cfly=53.8 uF`
(and the `R03A`/`R03D`/`R04E3` family also uses `Cout=4.672 mF`), logged
everywhere only as "EPE2019 cross-source candidates." Re-checked against
the primary source: both numbers are literal component sums from EPE2019's
Table I (`Cfly`: `4x10uF+2x4.7uF+2x2.2uF=53.8uF`; `Cout`:
`8x220uF+32x47uF+64x22uF=4672uF`), but that table is the parts list for
EPE2019's own **CSC buck prototype** (their proposed topological
modification), not the conventional 4-phase SC buck this project's P24
model actually is. The same paper states its conventional SC buck's `C1`
must block the *full* `Vin`, while the CSC buck's whole redesign purpose is
to avoid exactly that stress -- and Table I's individual flying capacitors
are rated only `35 V`/`50 V`, not enough to block P24's `48 V Vin` at all.
See `paper_locked/00_boundaries/CURRENT_ASSUMPTION_CROSSCHECK.md`'s "Flying
capacitor" and "Output capacitor value" rows for the full citation and
reasoning. This does not invalidate any of this track's *qualitative*
findings (e.g. R04E7's ratio-gating fix, R04E6's blind-cycling failure mode)
-- those are mechanism-level results that would likely hold at a different
capacitance
-- but every *numeric* result quoted from this track (charge budgets,
inrush currents, `LADDER_ERR` values, convergence times) should be read as
conditioned on this specific, now-suspect capacitance choice, not as a
validated P24 number.

## Lesson from R04E5 -- do not repeat this specific combination

R03D's only successful `Vout` bootstrap (Section 5 history) depended on
firing gate pulses at a fixed time regardless of whether any physical exit
condition had been met -- exactly the practice this project's own control
principle prohibits everywhere else. R04E5 confirmed directly that grafting
R03D's ramped on-time ceiling onto R04E3's correctly-event-gated latched
controller cannot inherit R03D's success: once physical-event gating is
enforced (the right thing to do), the controller permanently stalls at its
very first unmet event and the ramp mechanism never gets a second chance to
act, because the machine never returns to a state where a new on-time can be
issued. This was true across a 12-cell sensitivity grid (`TSOFT` from 50 to
500 us, per-phase current limit from 10 to 150 A) and held for windows up to
600 us -- it is not a "wait longer" or "try more grid points" problem.
**Do not re-attempt "keep the strict full P24 admission chain, just add a
ramp/timeout on top of it" as a zero-start fix -- this has now been tried
and it cannot work by construction, not by bad luck.** Any future attempt
needs a genuinely different, deliberately looser admission rule for the
bootstrap phase itself (not the steady-state P24 event chain), with an
explicit handoff into the existing, already-validated strict event-gated
controller only once `Vout`/the capacitor ladder is already close to target.
See `R04E5_ramped_duty_event_gated_zero_start/RESULTS.md` for the full
causal account.

| Experiment | Changed variable | Status |
|---|---|---|
| R04E0 | add observer-only voltage-difference detector | static pass only |
| R04E1 | add one calculated QH1+QS2 narrow pulse | local current increment pass |
| R04E2 | repeat period 10/4/2/1 ns | unsafe negative current; no full ladder |
| R04E3 | add event controller to zero-energy P24 local cycle | stops before t3 |
| R04E4 | sweep QH1 gate-off current | first hard turn-on dominates |
| R04E5 | ramped on-time ceiling (R03D) grafted onto the event-gated latched controller (R04E3), sweep TSOFT x I_LIMIT | reproduces R04E3's stuck-at-state-4 point (9/12 cells) or an earlier stuck-at-state-3 point (3/12 cells); never returns to ENERGY a second time in any of the 12 cells, so TSOFT has no observed effect and Vout never approaches 1 V; current stays inside the +/-250 A bound in all 12 |
| R04E6 | replace the P24 admission chain entirely with EPE2019's borrowed 3-state charge-redistribution sequence (open-loop, sweep hold time TH x cycle count NCYC), ladder-bootstrap-only scope | best single cell (TH=20us, NCYC=1) reaches VC1~24/VC2~12/VC3~12 V (LADDER_ERR=0.836); every additional cycle beyond the first makes it worse at every TH>=1us, converging toward ~45-46 V on all three (equalization, not the 3:2:1 target) by NCYC=10; does not outperform R02B's passive divider (0.260) |
| R04E7 | replace R04E6's blind fixed-hold-time/fixed-cycle-count gating with voltage-RATIO gating (state (a) exits at V(C1)>=36V, state (b) at 2V(C1)<=3V(C2), state (c) at V(C2)<=2V(C3), cycle repeats until all three voltages are within a swept tolerance band or a fixed 50us safety cap is hit), same EPE2019 truth table/power stage otherwise unchanged, sweep TOL in {2%,5%,10%} | all 3/3 cells reach DONE well inside the cap (5-8 cycles, t=3.90-4.24us) with LADDER_ERR decreasing monotonically on every single cycle (the opposite of R04E6's own finding); final LADDER_ERR 0.207/0.124/0.045 at TOL=10%/5%/2%, all beating both R02B (0.260) and R04E6 (0.836); no cell hit the safety cap without converging; no comparator chatter observed |
| R04E8 | module swap inside R04E7's unchanged ratio-gating framework: replace R04E7's Cfly=53.8uF (found to have a cross-topology provenance problem -- EPE2019's own CSC-buck Table I sum, parts rated only 35V/50V, not enough for P24's 48V Vin) with a first-principles-derived corrected range, sweep CFLY in {1,3,8.7 uF} with TOL fixed at 2% (R04E7's own best cell) | all 3/3 cells reach DONE in exactly 8 cycles each (matching R04E7's own TOL=2% cycle count), LADDER_ERR 0.0442-0.0448 (essentially matching R04E7's 0.045) -- the ratio-gating comparators are scale-invariant in Cfly; convergence time scales close to linearly with Cfly and is 5.7x-49.5x FASTER than R04E7's 53.8uF case (85.60/256.72/741.62 ns at 1/3/8.7 uF vs 4239.5 ns at 53.8uF); peak ICS1/ICS2/ICS3 MAX currents stay roughly flat (~4.2-4.6 kA for ICS1_MAX) across the whole 1-53.8uF range, confirming peak current does NOT shrink with smaller Cfly (V/Ron-dominated) -- so the Cfly correction does not resolve the multi-kilo-amp current-plausibility concern already flagged in R04E6/R04E7; some minimum/reverse currents (ICS3_MIN, IL1) do scale up with Cfly; no cell hit the safety cap without converging |
| R04E9 | genuinely new synthesis: a single unified rotating `CHARGE_k`/`FREE_k` machine drives ALL FOUR phases (not one phase held statically), replacing BOTH R04E3/R04E5's strict single-phase admission chain AND R04E6/E7/E8's switch-only ladder mechanism -- every phase's own series inductor `Lk` is the charging/current-limiting element (P24's own Interval-1 mechanism), `CHARGE_k` exits at R04E3/R04E4's own current-limit rule, `FREE_k` exits at the earlier of the natural zero-crossing or an A48-style `T_FREEWHEEL_MAX` timeout; `CFLY=3uF` (R04E8's corrected value); sweep `I_LIMIT` in {10,30,60}A x `T_FREEWHEEL_MAX` in {50,200,1000}ns (9 cells) | all 9/9 cells advance CHARGE1->FREE1->CHARGE2 within ~1us then permanently stall in CHARGE2 (I(L2) never reaches its own I_LIMIT, best case 67% of the way) because phase 2 has no direct Vin path, only C1's limited relayed charge from phase 1's single ~0.93ns pulse; zero full rotations complete, handoff condition never reached in any cell; both swept axes have real, monotonic, opposite-direction effects on how close IL2 gets to I_LIMIT (unlike R04E5's TSOFT, which had no effect at all); peak currents stay under 61A everywhere in the grid, roughly two orders of magnitude below R04E6/E7/E8's 4.2-4.6kA figures, directly confirming inductor-mediated charging is far more physically plausible even though it does not reach handoff here; two construct bugs (missing timer capacitor, inverted B-source current sign) were found and fixed during piloting, and are flagged as a latent, never-exercised risk in R04E5's own analogous timer construct (not fixed there, out of scope) |
| R04E10 | single conceptual change from R04E9: add a timeout fallback `T_CHARGE_MAX` to `CHARGE_k` too (OR'd with the existing `I(Lk)>=I_LIMIT` rule), symmetric with `FREE_k`'s own event-OR-timeout pattern, via an exact mirror of R04E9's own validated `FREE_k` timer construct; `T_FREEWHEEL_MAX` fixed at R04E9's own best value (50ns); an isolated pilot found `T_CHARGE_MAX` near R04E9's own ~1ns pulse width breaks the construct, so the swept range is restricted to the pilot-verified-safe `{5,20,50}ns`; sweep `I_LIMIT` in {10,30,60}A x `T_CHARGE_MAX` in {5,20,50}ns (9 cells), `TSTOP=20us` (extended from R04E9's 3us for multi-rotation observation) | 6/9 cells (`T_CHARGE_MAX in {20,50}ns`) complete 4-17 full rotations with `Vout` rising monotonically across every completed rotation -- a genuine unlock of the R04E9 stall; but the other 3/9 cells (`T_CHARGE_MAX=5ns`, all three `I_LIMIT` values) complete ZERO rotations, reproducing R04E9's own total stall exactly despite this value passing isolated verification -- isolated single-branch pilot verification does not guarantee clean full-machine behavior; no cell reaches handoff, best cell reaches only 1.4-5.5% of target across Vout/VC1-3 (3x-20x further than R04E9's own best cell, still 95-99% short); VC2 specifically regresses (wrong direction) at T_CHARGE_MAX=20ns but progresses correctly at 50ns, a reproducible axis-dependent split; inductor currents stay bounded (max 60.17A, same order as R04E9), but a NEW pervasive numerical artifact contaminates flying-capacitor current (ICS1-3) reporting in every one of the 9 cells (hundreds of A up to ~500kA), traced directly to a newly-found retry/chatter dynamic where the machine repeatedly makes partial forward progress then reverses before eventually completing a rotation (first rotation in a representative cell took 18.86us, 70x longer than a naive estimate, vs 273-347ns for later clean rotations); compared to R04E7/R04E8's switch-only ladder (98.9% of target in 5-8 cycles), R04E10 needs more cycles (11-17) to reach far less (3-5.5%), confirming the inductor-mediated approach trades convergence speed for physical plausibility |
| R04E11 | diagnostic-only (no mechanism change): fine-time-resolution raw-trace instrumentation of R04E10's own `I_LIMIT=30A/T_CHARGE_MAX={20,5}ns` cells, adding `V(reset_gate)`, `V(reset_gate_chg)`, `V(timer)`, `V(timer_chg)` to `.save` (measurement only); tests two hypotheses for the R04E10-documented CHARGE/FREE reversal directly against the raw trace, then tests one candidate fix (reset-switch `Vh=0->1` hysteresis) in a controlled isolation re-run | the "two reset gates disagree" race hypothesis is REFUTED (0/231 conflicts sampled across two independent reversal episodes in two cells); the reversal is instead a genuine, continuous, monotonic multi-integer sweep of the raw `.machine` state variable itself (e.g. `3.9999995->3.4999995->2.4999998->1.4999998` in ~16 ps), occurring during the same stiff sub-picosecond-timestep solver episodes that separately produce the `ICS1-3` artifact; exact, reproducible retry periods measured directly (143.14ns and 214.71ns, refining R04E10's own "~143ns" estimate); the hysteresis fix-test produced a BIT-IDENTICAL trace to the unmodified baseline (same row, same 15-sig-fig timestamp, same state_mon value), refuting that candidate fix; R04E10's own cited `t=19.275us` "reversal event" is directly shown to actually be a clean forward transition coincident with the ICS artifact, not a reversal (a correction to that specific characterization; the ICS/non-integer-state_mon finding itself is fully reproduced); no working fix found, so per Ground Rule 7 none is forced and the 9-cell grid is not re-run -- R04E10's own grid/results.csv remain the authoritative record |
| R04E12 | single conceptual change from R04E10: insert a phase-1 precharge admission gate before the machine's normal round-robin rotation begins -- a counter (implemented as a compile-time-unrolled chain of `N_PRECHARGE-1` extra state pairs electrically mirroring `CHARGE1`/`FREE1`, since this project's own `.machine` convention never uses more than one `.rule` per state) routes `FREE1`'s exit back to `CHARGE1` while below `N_PRECHARGE`, then joins R04E10's own unchanged round-robin permanently; `I_LIMIT=60A`, `T_CHARGE_MAX=T_FREEWHEEL_MAX=50ns` fixed (R04E10's own best cell), sweep `N_PRECHARGE` in {1,3,5,10,20} (5 cells) | `N_PRECHARGE=1` confirmed IDENTICAL to R04E10's own committed `I_LIMIT=60A/T_CHARGE_MAX=50ns` cell to full printed precision on every measured quantity (by construction and directly verified); the new construct was pilot-verified directly against the raw state trace at `N_PRECHARGE=3` and `=10` (exact admission order, one-time gating, correct dwell count -- all PASS); `Vout` improves monotonically and substantially with `N_PRECHARGE` (`0.0141->0.0197V`, +40% at `N_PRECHARGE=20`); `VC2` (the axis this experiment targeted) improves at `N_PRECHARGE in {3,20}` but REGRESSES at `N_PRECHARGE=5` and is flat at `10` -- a non-monotonic, mixed result, not a clean "precharge helps" verdict; the single best-`VC2` cell (`N_PRECHARGE=20`) has the only negative `VC3_final` in the whole grid, a new trade-off; the R04E10/R04E11-diagnosed retry/chatter dynamic and `ICS1-3` artifact recur in all 5 cells at essentially uniform severity (19-22% reversal rate, matching R04E10's own ~19% figure), confirming it is a property of the reused construct, not caused or fixed by the precharge stage; no cell reaches handoff; all `IL1-4` stay safely bounded (worst case 24% of the +/-250A limit) |

These results are retained but are not Track-A periodic reproduction evidence.

See `R04E5_ramped_duty_event_gated_zero_start/BOUNDARY.md` and `RESULTS.md`
for the full two-parent synthesis provenance and sensitivity grid, and
`R04E6_epe2019_charge_redistribution_startup/BOUNDARY.md` and `RESULTS.md`
for R04E6's borrowed-fact table, independent truth-table derivation, and
full sensitivity grid.

## Lesson from R04E6 -- blind repetition of this mechanism hurts, don't just rerun it with more cycles

The EPE2019 3-state charge-redistribution sequence, applied open-loop with
a fixed cycle count, drifts the ladder toward all three capacitors
converging to a common voltage rather than the required `3:2:1` ratio --
more cycles make this worse, monotonically, at every tested hold time. Any
future attempt at this same mechanism needs a voltage-monitored/gated stop
condition per state (matching what the source paper's own wording implies
but does not detail), not a larger or finer `(TH, NCYC)` grid search over
the blind version already tested here.

## R04E7 -- the voltage-monitored/gated fix works

R04E7 built exactly the fix R04E6 called for: state (a) exits at
`V(C1)>=36V`, state (b) exits at the measured ratio `2*V(C1)<=3*V(C2)`,
state (c) exits at `V(C2)<=2*V(C3)`, with the full cycle repeating until
all three voltages are simultaneously within a swept tolerance band. All
three tested tolerances (`2%`, `5%`, `10%`) converge, with `LADDER_ERR`
decreasing on every single cycle (the direct opposite of R04E6's own
result), reaching final `LADDER_ERR` of `0.045-0.207` -- beating both
R02B's `0.260` and R04E6's `0.836`. See
`R04E7_ratio_gated_charge_redistribution_startup/BOUNDARY.md` and
`RESULTS.md` for the charge-conservation check, the full per-tolerance and
per-cycle results, and the chatter check.

## R04E8 -- the mechanism survives a corrected, physically-appropriate `Cfly`

R04E7's own `Cfly=53.8 uF` was later found to have a cross-topology
provenance problem (see the "Boundary-provenance gap found 2026-09-15"
section above): it is EPE2019's own CSC-buck prototype Table I sum, whose
parts are rated only `35 V`/`50 V`, not enough for P24's `48 V Vin`. R04E8
reruns R04E7's ratio-gating mechanism unchanged, swapping only `Cfly` to a
first-principles-derived range (`{1, 3, 8.7} uF`, `TOL` fixed at `2%`). All
three cells converge in exactly the same 8 cycles as R04E7's own `TOL=2%`
cell, with essentially the same final `LADDER_ERR` (`0.0442-0.0448` vs
`0.045`) -- the mechanism's voltage-ratio comparators are scale-invariant
in `Cfly`, so convergence *quality* is unaffected by the correction.
Convergence *speed*, however, is dramatically faster (`5.7x`-`49.5x`,
scaling close to linearly with `Cfly`), confirming the task's physical
expectation directly. Peak flying-capacitor-to-flying-capacitor currents
(`ICS1`/`ICS2`/`ICS3` MAX) do **not** shrink with the smaller, corrected
`Cfly` -- they stay in essentially the same multi-kilo-amp range as
R04E7's own `53.8 uF` result, confirming the `V/Ron`-dominated peak-current
hypothesis and showing that the `Cfly` correction does **not** by itself
resolve the current-plausibility concern already flagged in R04E6/R04E7 --
that concern is attributable to the zero-dead-time/`Ron`-only idealized
switch model, not to the (now-corrected) `Cfly` value. See
`R04E8_corrected_cfly_ratio_gated_startup/BOUNDARY.md` and `RESULTS.md`
for the pilot-run derivation of the safety cap, the full per-`Cfly`
results, and the detailed current-scaling breakdown (including the
asymmetry between flat MAX currents and growing MIN/inductor currents).

## R04E9 -- a unified, inductor-mediated four-phase bootstrap, genuinely new but still stuck

R04E9 replaces BOTH R04E3/R04E5's strict single-phase admission chain AND
R04E6/E7/E8's switch-only EPE2019 ladder mechanism with one synthesis: a
rotating `CHARGE_k`/`FREE_k` machine that actively drives all FOUR
phases (not one phase held statically, unlike every prior R04E
experiment), routing each phase's own charging current through its own
series inductor `Lk` -- P24's own Interval-1 mechanism -- instead of a
bare switch-to-switch capacitor path. `CHARGE_k` reuses R04E3/R04E4's own
validated current-limit turn-off rule; `FREE_k` exits at the earlier of
the natural zero-crossing or an A48-style `T_FREEWHEEL_MAX` timeout.
Swept `I_LIMIT` in `{10,30,60} A` x `T_FREEWHEEL_MAX` in
`{50,200,1000} ns` (9 cells), `CFLY=3 uF` (R04E8's own corrected value).

**All 9 cells stall permanently in `CHARGE2`** -- phase 1 completes its
own charge/freewheel cycle cleanly, but phase 2 never reaches its own
current limit (`I(L2)` gets to at most `67%` of the commanded `I_LIMIT`)
because phase 2 has no direct `Vin` connection, only whatever limited
charge phase 1's single `~0.93 ns` pulse deposited on `C1`. Zero full
four-phase rotations complete in any cell; the handoff condition
(`Vout` within `5%` of `1 V` and `VC1-3` within `2%` of `36/24/12 V`) is
never reached. Unlike R04E5's own `TSOFT` axis (which had NO observed
effect because the machine never returned to a state where it mattered),
**both of R04E9's swept axes have real, monotonic, opposite-direction
effects** on how close `IL2` gets to unsticking the machine (`I_LIMIT`
up -> `IL2_max` up; `T_FREEWHEEL_MAX` up -> `IL2_max` DOWN, because a
longer freewheel lets phase 1's residual current decay more before
coupling into phase 2). Peak currents everywhere in the grid stay under
`61 A` -- roughly two orders of magnitude below R04E6/E7/E8's
`4.2-4.6 kA` figures, directly confirming that inductor-mediated
charging is far more physically plausible than the switch-only
mechanism, even though (in this tested grid) it does not reach the
handoff condition either. Two construct bugs (a missing timer storage
capacitor, and an inverted B-source current sign that silently defeated
the timeout branch in a first, discarded pilot) were found and fixed
before any grid cell was committed; both are flagged as a latent risk in
R04E5's own analogous, never-exercised timer construct (R04E5's own
results never actually exercised the affected branch, so they are not
directly impacted, but the risk is unverified there). See
`R04E9_unified_inductor_mediated_bootstrap/BOUNDARY.md` and `RESULTS.md`
for the full parentage, the exact state machine, the bug-diagnosis trail,
and the complete 9-cell grid.

## R04E10 -- adding a CHARGE_k timeout unlocks multi-rotation operation,
   but reveals two new problems

R04E10 makes the single change R04E9's own "next module" note (Section
11 of its `RESULTS.md`) implicitly called for: `CHARGE_k` now exits at
`(I(Lk)>=I_LIMIT) | (V(timer_chg)>=T_CHARGE_MAX)`, symmetric with
`FREE_k`'s existing event-OR-timeout pattern, via an exact mirror of
R04E9's own validated `FREE_k` timer construct (charge/reset roles
swapped). Everything else -- node topology, `CFLY=3 uF`, `COUT=4.672 mF`,
the current-limit mechanism, the `FREE_k` timer -- is reused unchanged.
`T_FREEWHEEL_MAX` is fixed at R04E9's own best-performing value (`50 ns`)
rather than re-swept. A pilot, run before committing to any grid cell
(same discipline R04E9 used for its own timer), found `T_CHARGE_MAX`
values at or near R04E9's own `~0.93 ns` phase-1 pulse width (`100 ps`,
`1 ns`) break the construct -- a spurious backward state transition,
confirmed by direct raw-trace inspection -- so the swept grid is
restricted to the pilot-verified-clean range `{5, 20, 50} ns`.

**The core question is answered YES, conditionally**: 6 of the 9 cells
(`T_CHARGE_MAX in {20, 50} ns`, all three `I_LIMIT` values) complete `4`
to `17` full four-phase rotations -- a genuine unlock of R04E9's own
permanent `CHARGE2` stall -- and `Vout` rises **monotonically** across
every single completed rotation in every one of those 6 cells. The best
cell (`I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, 12 rotations) reaches `1.4%`
of the `Vout` target and `5.5%` of the `VC1` target -- `3x` to `20x`
further than R04E9's own best single-pass cell, though still `95-99%`
short of handoff in every variable, and `T_HANDOFF` never fires in any of
the 9 cells.

**Two genuinely new problems were found, not present in R04E9:**

1. **`T_CHARGE_MAX=5 ns` -- the value closest to the task's own suggested
   `~1 ns` starting point that survived isolated verification -- is
   uniformly the WORST value tested: all 3 cells using it (every
   `I_LIMIT`) complete ZERO rotations within the full `20 us` window,
   reproducing R04E9's own total stall exactly. This despite `5 ns`
   passing a dedicated isolated pilot check beforehand. Direct raw-trace
   inspection of a representative full-machine cell explains why: the
   machine does not advance cleanly through the 8 states; it repeatedly
   makes partial forward progress (as far as `CHARGE3`/`CHARGE4`) and then
   reverses back to `FREE1`, retrying with a ~143 ns period, for many
   cycles, before eventually escaping. At `T_CHARGE_MAX=5 ns` this retry
   loop apparently never resolves in `20 us`. **Isolated single-branch
   pilot verification does not guarantee clean behavior once both
   OR-branches are live and circuit-coupled in the full machine** -- a
   methodological lesson for this whole family of dual-timer constructs.
2. **A pervasive numerical artifact contaminates the flying-capacitor
   branch current (`ICS1-3`) `.meas` reporting in EVERY ONE of the 9
   cells** -- from several hundred amps up to `~500 kA` (`I_LIMIT=60 A`,
   `T_CHARGE_MAX=20 ns`). Diagnosed directly (not assumed): the spike
   coincides with several raw-trace rows sharing an identical timestamp,
   an unchanging `VC1-3`/`IL1-4` state, and a non-integer "state" value
   (e.g. `3.217`) -- a solver-convergence retry artifact at a difficult
   transition, the same general class R04E6/R04E8/R04E9 already
   documented finding at `t=0` in their own constructs, but here occurring
   later in the run and roughly `100x` larger. `IL1-4` (inductor
   currents) show no such contamination and stay bounded (max `60.17 A`,
   same order as R04E9) -- the artifact is confined to the capacitor
   branches, tied to the same retry dynamic as finding 1.

Compared against R04E7/R04E8's switch-only ladder mechanism (`VC1~=35.6 V`,
`98.9%` of target, in `5-8` cycles), R04E10 needs MORE cycles (`11-17`)
to reach FAR LESS (`3-5.5%` of target) -- confirming, quantitatively, the
trade-off R04E9 already identified qualitatively: routing charge through
a genuinely current-limited series inductor is far more physically
plausible on the inductor branches, but far less effective per cycle at
actually moving charge onto the flying capacitors, than a comparatively
unconstrained switch-only path. `VC2` also shows a real, reproducible,
axis-dependent split: it regresses (wrong direction, away from its `24 V`
target) in 3 of the 6 multi-rotation cells at `T_CHARGE_MAX=20 ns`, but
progresses correctly at `T_CHARGE_MAX=50 ns` in all three `I_LIMIT`
values. See `R04E10_timeout_gated_multi_rotation_bootstrap/BOUNDARY.md`
and `RESULTS.md` for the full pilot-diagnosis trail, the complete 9-cell
grid, and the per-rotation trend tables.

## R04E11 -- the reversal is a `.machine` state-variable excursion, not a
   race in this project's own gate logic; the obvious fix does not work

R04E11 is diagnostic-only: it instruments (via `.save` additions alone,
no circuit/parameter change) two of R04E10's own already-committed cells
with the four internal nodes R04E10 never recorded
(`reset_gate`/`reset_gate_chg`/`timer`/`timer_chg`), then directly tests
two hypotheses for the CHARGE/FREE reversal R04E10 documented but did not
root-cause. **The "two reset gates briefly disagree" race hypothesis is
refuted**: across 231 sampled rows spanning two independent reversal
episodes in two different cells, `reset_gate`/`reset_gate_chg` are
perfect complements at every single row (0 conflicts) -- this project's
own B-source gate logic behaves exactly as designed throughout. **What
actually happens**: the raw `.machine` state variable itself (exposed via
`V(state_mon)`) sweeps continuously and monotonically backward through
several half-integer bucket boundaries within picoseconds (e.g.
`3.9999995 -> 3.4999995 -> 2.4999998 -> 1.4999998` in ~16 ps), during the
same class of genuinely stiff, sub-picosecond-timestep solver-retry
episode that separately produces the `ICS1-3` current artifact -- both
are manifestations of the same underlying solver difficulty. Exact,
reproducible retry periods were measured directly (`143.14 ns` and
`214.71 ns`, refining R04E10's own "~143 ns" estimate to 4+ significant
figures). A well-motivated, minimal candidate fix -- giving the
zero-hysteresis reset-switch comparators (`Vt=2.5 V, Vh=0`, sitting
exactly on the same boundaries the `.machine` itself uses) an explicit
`Vh=1` dead band -- was built and run as a controlled isolation test.
**The result was bit-identical to the unmodified baseline** (same row,
same 15-significant-figure timestamp, same state value), directly
refuting that candidate. A secondary cross-check on the permanently-
stalled `T_CHARGE_MAX=5 ns` cell confirms the same phenomena, more
severely (273 reversals across the full non-escaping `20 us` run vs. 113
in the escaping `T_CHARGE_MAX=20 ns` cell) and the same zero-conflict
gate consistency. One further correction: R04E10's own cited
`t=19.275 us` "reversal event" is, on direct inspection, actually a
**clean forward transition** coincident with the `ICS` artifact, not a
reversal -- the `ICS`/non-integer-`state_mon` finding itself is fully
reproduced and confirmed, only the "reversal" label at that specific
instant is corrected. **No working fix was found**, so per Ground Rule 7
none is forced onto the construct, and the 9-cell grid is not re-run --
R04E10's own grid and `results.csv`/`results.json` remain the
authoritative record for all 9 cells. The reversal is attributed to
LTspice's own `.machine`/`.rule` event-resolution behavior in this stiff
regime, not to any defect in this project's own constructed B-source/
switch logic that a further netlist-level change could be expected to
fix. See
`R04E11_charge_free_reversal_root_cause/BOUNDARY.md` and `RESULTS.md`
for the full row-by-row trace evidence, both fix-test comparisons, and
the exact scripts used.

## R04E12 -- precharging phase 1 helps `Vout` cleanly but `VC2` only
   improves non-monotonically, with a new trade-off

R04E12 implements R04E9's own Section 11 option (c) (per explicit user
direction): insert a precharge admission gate before R04E10's normal
round-robin rotation, so `FREE1`'s exit routes back to `CHARGE1` (repeat
phase 1 alone, building up `C1`'s charge) `N_PRECHARGE-1` times before the
machine is permanently admitted into the unchanged round robin. Because
this project's own `.machine` convention never uses more than one `.rule`
per state anywhere in R04E5-R04E11, the "counter" was implemented as a
compile-time-unrolled chain of extra state pairs (one per netlist, since
this project already generates one file per grid cell) rather than a
runtime SPICE counter node -- a documented implementation-detail choice,
not a deviation from the requested mechanism. `N_PRECHARGE=1` was
confirmed, both by construction and by direct LTspice re-run, IDENTICAL
to R04E10's own committed `I_LIMIT=60A/T_CHARGE_MAX=50ns` cell to full
printed precision on every measured quantity -- the required baseline
sanity check. The construct itself was pilot-verified by direct raw-trace
inspection at `N_PRECHARGE=3` and `=10` (BOUNDARY.md Section 5's
requirement): the machine visits every precharge pair exactly once, in
order, before ever reaching the real `CHARGE1`, and never re-enters the
precharge chain afterward -- confirmed, not assumed.

**`Vout` improves monotonically and substantially** with `N_PRECHARGE`
(`0.0141 V` at `N_PRECHARGE=1` to `0.0197 V` at `N_PRECHARGE=20`, `+40%`)
-- the cleanest result in this experiment. **`VC2`, the axis this
experiment specifically targeted, does NOT improve monotonically**: it is
better than baseline at `N_PRECHARGE=3` (`+16%`) and best of the whole
grid at `N_PRECHARGE=20` (`+38%`), but WORSE than baseline at
`N_PRECHARGE=5` (`-18%`) and essentially flat at `N_PRECHARGE=10`
(`+0.5%`) -- reported plainly as a mixed, non-monotonic result, not forced
into a clean verdict either way. A new trade-off was found: the single
best-`VC2` cell (`N_PRECHARGE=20`) has the ONLY negative `VC3_final` value
in the entire grid (`-0.170 V`), where every other cell (including
baseline) stays positive. The R04E10/R04E11-diagnosed retry/chatter
dynamic and its coincident `ICS1-3` numerical artifact recur in every one
of the 5 cells, at essentially uniform severity regardless of
`N_PRECHARGE` (`19-22%` of settled-state dwell transitions are reversals
in every cell, matching R04E10's own `~19%` figure) -- confirming this is
a property of the reused `CHARGE_k`/`FREE_k` construct itself, neither
caused nor fixed by the precharge stage. No cell reaches handoff; `IL1-4`
stay safely bounded in every cell (worst case `24%` of the `+/-250 A`
limit). See
`R04E12_phase1_precharge_admission_gate/BOUNDARY.md` and `RESULTS.md` for
the full construct-design rationale, the pilot-verification evidence, and
the complete 5-cell grid.
