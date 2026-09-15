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
