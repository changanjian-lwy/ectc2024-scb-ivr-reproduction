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
