# Track B - zero-start engineering extension

Canonical records remain at `paper_locked/02_ectc2024_main/STEP_27` through
`STEP_31`; their netlists remain beside those records to preserve links.

**Start here for a synthesized view of `R04E9`-`R04E14` and the
2026-09-16 literature review**: `CONSOLIDATED_FINDINGS_2026-09-16.md`.
It does not replace the individual experiments' own `BOUNDARY.md`/
`RESULTS.md` files, which remain the authoritative per-experiment record.

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
| R04E13 | single conceptual change from R04E12: stack a SECOND, analogous precharge admission gate after phase 1's own (fixed at `N1_PRECHARGE=3`, R04E12's own clean best value), gating phase 2 the same way R04E12 gated phase 1 -- a naive first attempt (hanging the phase-2 mirror chain directly off the real, round-robin-shared `FREE2` state) FAILED its own required pilot check (re-triggered every rotation, not just once) and was corrected to a dedicated one-time-only "ADMIT" duplicate of `CHARGE1`/`FREE1`/`CHARGE2`/`FREE2` positioned strictly upstream of the closed loop, mirroring why R04E12's own phase-1 gate never had this problem; `I_LIMIT=60A`, `T_CHARGE_MAX=T_FREEWHEEL_MAX=50ns` fixed, sweep `N2_PRECHARGE` in {1,3,5,10} (4 cells) plus a separate `N1=1,N2=1` identity cell | Both required identities confirmed to full printed precision (`N1=1,N2=1` vs. R04E10; `N1=3,N2=1` vs. R04E12's own `N_PRECHARGE=3`); the corrected construct was proven correct two ways -- an independent, run-independent static rule-graph/walk-simulation check (all 5 cells PASS) and direct raw-trace pilot verification (clean PASS at `N2_PRECHARGE=3`); `N2_PRECHARGE=5`/`10` FAIL the strict admission-order pattern-match, but precisely-timed cross-cell evidence (the same stiff-solver episode recurring at `t=6.1843-6.1844e-7s` in every cell regardless of `N2_PRECHARGE`) attributes this to the already-diagnosed R04E10/R04E11 retry/chatter artifact landing, for the first time in this lineage, inside the admission window itself rather than a new construct defect; stacking the phase-2 gate does NOT further improve `Vout`/`VC1`/`VC3` (WORSE than the `N2_PRECHARGE=1` baseline at every tested value, `-10.6%` to `-35.7%`), and only marginally improves `VC2` (~+4%) at `N2_PRECHARGE in {5,10}`, paired with a larger `VC3` cost -- directly traced to a fixed rotation-count cost (12->10) any phase-2 gate incurs within the fixed 20us window; no cell reaches handoff; all `IL1-4` stay safely bounded (worst case 24% of the +/-250A limit) |
| R04E14 | replay of R02A/R02B's own passive-divider-plus-diode precharge module (NOT the R04E9-R04E13 inductor-mediated/ratio-gating lineage), byte-level-faithful except CFLY and the CDIV sweep range: CFLY=3uF fixed (R04E8's corrected value, vs R02B's cross-topology-suspect 53.8uF) x CDIV in {10,30,100,300}uF (re-scaled around R02A's own found 10:1 CDIV:CFLY ratio) x TRAMP in {1,10,100}us unchanged from R02B (12 cells), plus a secondary 2-cell grid at the primary grid's own best (CDIV,TRAMP) point (CDIV=300uF/TRAMP=10us) re-run at CFLY=0.6uF and 8.7uF (the first-principles range extremes) | 2 of the 12 primary cells (CDIV=100uF and CDIV=300uF, both at TRAMP=100us) simultaneously beat R02A's own best passive LADDER_ERR (~0.236, Step 1) AND R02B's own best peak source current (150.15A) -- LADDER_ERR 0.157/0.054 at 16.45A/39.18A respectively -- graded PASS_TOPOLOGY_PRINCIPLE/NOT_P24_REPRODUCTION, reusing R02A's own Step-1 language; 9/12 primary cells beat R02B's own best LADDER_ERR (0.260), the exception being the three CDIV=10uF cells (0.963-1.106, still better than R02B's own worst, 2.732); peak current is NOT uniformly improved by the CFLY correction alone (12-cell span 3.31-2497.83A, overlapping R02B's own 6.01-3429.57A) -- three TRAMP=1us cells exceed the 500A flag threshold (up to 2497.83A), confirming R02B's own CDIV/TRAMP separability finding still holds; at the fixed best (CDIV,TRAMP) point, LADDER_ERR is sensitive to which point in the 0.6-8.7uF CFLY range is used (13x spread, 0.0107 to 0.1389, monotonic with CFLY) while peak current is nearly flat (8% spread) -- consistent with R04E8's own V/Ron-dominated peak-current finding; a reproducible LTspice-runner tooling failure (full .cir path length >=~250-259 characters silently drops all .meas output with no error) was found and worked around with short case filenames, unrelated to the circuit itself |
| R04E15 | fine-grid refinement of R04E14's own two PASS cells, same unmodified circuit: Grid A, CFLY=3uF/TRAMP=100us fixed x CDIV in {150,200,250,350,400,500}uF (6 cells, fills the 100-300uF gap and extends beyond 300uF); Grid B, CFLY=3uF/CDIV=300uF fixed x TRAMP in {20,50,75,150,200}us (5 cells, fills the 10-100us gap); Grid C, at the winning (CDIV,TRAMP) point identified from Grids A/B plus R04E14's own CDIV=300/TRAMP=100 cell (CDIV=500uF/TRAMP=100us, the lowest LADDER_ERR still under the 150.15A current bar), re-run at CFLY=0.6uF and 8.7uF (2 cells) -- 13 cells total | No cell beats R04E14's own best PASS cell (CDIV=300uF/TRAMP=100us, LADDER_ERR=0.0536, IIN_PK=39.18A) on BOTH axes simultaneously -- R04E14's coarse-grid optimum sits at a genuine local LADDER_ERR-vs-IIN_PK trade-off frontier; every cell tested either improves one axis at the other's expense; LADDER_ERR decreases monotonically with CDIV through 500uF (no plateau yet) and IIN_PK rises monotonically but stays well under the 150.15A bar throughout; this experiment's own best-LADDER_ERR-while-passing cell is CDIV=500uF/TRAMP=100us (LADDER_ERR=0.0335, a 37.6% improvement over R04E14's best, at IIN_PK=61.44A, 1.57x higher but still 2.4x below the bar); 12 of 13 cells (all except CDIV=300uF/TRAMP=20us, which fails only the current half at 195.90A) simultaneously satisfy both halves of the PASS_TOPOLOGY_PRINCIPLE bar; Grid C's own Cfly-robustness check at the ACTUAL winning (CDIV=500uF/TRAMP=100us) point -- unlike R04E14's own secondary grid, run at a different TRAMP=10us point where all three Cfly values failed the current bar outright (382-412A) -- passes BOTH halves of the bar at all three Cfly values (0.6/3/8.7uF), LADDER_ERR 0.0066-0.0956 (still far under 0.236) and IIN_PK a nearly flat 60.48-63.68A (far under 150.15A), showing the PASS verdict is genuinely robust across the full Cfly range at this operating point; graded PASS_TOPOLOGY_PRINCIPLE/NOT_P24_REPRODUCTION, same category as R04E14, not a new one |
| R04E16 | Roberts' PhD dissertation Sec. 3.5 soft-start mechanism (Vin ramped slowly through an eFuse while P24's ORDINARY fixed-timing four-phase PWM, R03A's own gate formulas, runs unchanged from t=0) -- genuinely different from R04E5's already-falsified "ramp grafted onto the strict event-gated controller" combination; base netlist copied from R03A with TSTART=0, LPHASE=1.4666667nH (was R03A's 2.68nH), CFLY swept, and R02B's passive-divider precharge network removed entirely (true zero-energy start, no auxiliary precharge circuit); sweep Cfly in {0.6,3,8.7}uF x Tramp at Roberts' own 30x margin (3 cells), plus Cfly=3uF x Tramp at 10x/100x margin (2 cells), plus a Cfly=3uF/Tramp=1us control cell (near-instant ramp) -- 6 cells total, TSTOP=Tramp+300us each | **GRID COMPLETE (6/6).** Pilot confirmed TSTART=0 gating works correctly (correct Ton/T/phase-spacing, one negligible ~5e-17s floating-point boundary artifact at t=0 reported transparently); EVERY cell first attempted at R03A's own default solver options hit a reproducible, forensically-confirmed solver breakdown (an independent PWL source reading physically impossible values after classic retry-chatter, at varying times unrelated to actual circuit stress) -- fixed by adopting solver=alt/cshunt=1e-15/plotwinsize=0, the exact convention R04E5-R04E10 already use at this TMAX=50ps; a second, independent tooling finding -- severe, TSTOP-disproportionate runtime variance (1302.6/1932.1/7937.0/11842.4/2165.2/2525.2s wall-clock across the 6 cells, an 8.3x spread in simulated-ns-per-wall-second that does not scale monotonically with TSTOP: the two LARGEST-TSTOP cells finished FASTER than two smaller-TSTOP ones) -- meant the grid was completed across multiple sessions, all 6 cells run strictly one at a time (never concurrently, since concurrent runs cause ~20x throughput collapse on this 10-core machine); ALL 6 completed cells avoid R03A's own catastrophic runaway (max phase current 75.1-150.1A, 3.75x-7.51x below R03A's own smallest peak of 563A, all within the +/-250A bound) with NO Vout overshoot -- but the control cell (near-instant ramp) equally avoids it, directly undermining a clean "the ramp specifically is responsible" causal claim; most likely explanation is that removing R02B's passive-divider precharge network (which is what let R03A's ladder pre-charge to 34/22/11V before a cold-Vout PWM hit it) eliminates R03A's own diagnosed mismatch independent of ramp speed; all four Cfly=3uF cells (control/10x/30x/100x margin) converge to nearly identical Vout~0.559V/LADDER_ERR~1.34-1.35 despite a 229x Tramp range, while peak IL1 now shows a clean MONOTONIC decrease with margin factor (150.1/111.6/86.9/75.1A at Tramp=1/22.87/68.61/228.71us, diminishing returns at each step) -- so the ramp does not determine WHETHER runaway occurs but does measurably shape the transient's magnitude; the completed 3-point Cfly trend (0.6/3/8.7uF, all at 30x margin) shows LADDER_ERR/Vout_final decreasing modestly but monotonically with Cfly (LADDER_ERR 1.399->1.348->1.333) while IL1_max is small and non-monotonic (92.2/86.9/90.2A) |
| R04E17 | 2x2 factorial isolation of R04E16's own two simultaneous changes (divider removed vs. Vin ramped), per explicit user direction: reuses R04E16's own two already-completed divider-ABSENT cells (e16_ctrl_f3_t1, e16_g1_f3_t68p61) by reference, and adds R03A's own divider-plus-diode network (CDIV=300uF, R04E15's corrected value, NOT R03A's own 1.076mF) back onto R04E16's netlist at the SAME two Tramp values (1us, 68.61us) -- 2 new cells, run strictly one at a time | Clean third pattern of BOUNDARY.md Section 7: fast-ramp/divider-present (e17_div_f3_t1) shows genuine runaway (IL1-4 813-1046A, all four phases over the +/-250A bound, same order as R03A's own 563-884A), slow-ramp/divider-present (e17_div_f3_t68p61) does NOT (IL1-4 140.8-154.7A) -- directly resolving R04E16's own open question: WITH the divider present, the Vin ramp speed is causally decisive, confirming Roberts' own soft-start mechanism specifically protects against the divider's precharge-vs-cold-Vout mismatch; both divider-present cells also reach Vout_final within 0.6% of the 1V target and LADDER_ERR 0.024-0.029 (46-56x better than either divider-ABSENT cell's ~1.34-1.35), so reintroducing the divider is beneficial for ladder accuracy at either ramp speed, not merely "safe if slow"; both new cells' raw .raw traces were directly parsed and confirmed free of R04E16's own documented solver-corruption fingerprint (zero non-monotonic timestamps, V(vin) never deviates from its commanded PWL value in either 6.7M- or 8.2M-point trace); does not modify or re-run R04E16's own committed cells |

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

## R04E13 -- stacking a second (phase-2) precharge gate on phase-1's own
   costs more rotations than it gains, and a naive generalization of
   R04E12's own construct failed its own pilot check first

R04E13 stacks a SECOND, analogous precharge admission gate after phase 1's
own (fixed at R04E12's own clean best `N1_PRECHARGE=3`), gating phase 2 the
same way R04E12 gated phase 1: repeat `CHARGE2`/`FREE2` `N2_PRECHARGE-1`
extra times before ever advancing to the real `CHARGE3`. A naive first
implementation attempt -- hanging the phase-2 mirror chain directly off the
real, round-robin-shared `FREE2` state's own single rule, the most direct
generalization of R04E12's own phase-1 pattern -- FAILED its own required
pilot verification immediately: because `CHARGE2`/`FREE2` are themselves
part of the closed round-robin cycle (a `.machine` where every state has
exactly one outgoing rule is a deterministic functional graph, and anything
reachable from a cyclic state is also on that cycle forever), the mirror
chain re-triggered on EVERY subsequent rotation, not just once. The fix
(a dedicated, one-time-only "ADMIT" duplicate of `CHARGE1`/`FREE1`/
`CHARGE2`/`FREE2`, positioned strictly upstream of the closed loop, exactly
mirroring the structural position R04E12's own phase-1 mirror chain already
occupies) was verified two independent ways: a run-independent static
rule-graph/walk-simulation check (all 5 cells PASS, proving the `.rule`
graph itself converges correctly with no revisits) and direct raw-trace
pilot verification against real LTspice runs.

Both required baseline identities (`N1=1,N2=1` vs. R04E10's own committed
cell; `N1=3,N2=1` vs. R04E12's own committed `N_PRECHARGE=3` cell) matched
to full printed precision. Pilot verification at `N2_PRECHARGE=3` passed
all six checks cleanly; at `N2_PRECHARGE=5`/`10` the strict admission-order
pattern-match FAILED, but precisely-timed cross-cell evidence (the SAME
stiff-solver episode recurring at `t=6.1843-6.1844e-7 s`, agreeing to 6
significant figures, in all four `N1=3` cells regardless of
`N2_PRECHARGE`) attributes this directly to the already-diagnosed
R04E10/R04E11 retry/chatter artifact landing, for the first time in this
project's lineage, transiently inside the admission window itself (because
longer admission chains are still running when that fixed-timing episode
occurs) rather than a new construct defect -- corroborated by the
static-analysis proof above and by every cell still completing its
expected rotations cleanly with `IL1-4` safely bounded.

**Stacking the phase-2 gate does NOT further improve `Vout`, `VC1`, or
`VC3` at any tested `N2_PRECHARGE` -- all three are WORSE than the
`N2_PRECHARGE=1` baseline** (`Vout`: `-10.6%` to `-11.9%`; `VC1`: `-6.1%`
to `-22.2%`; `VC3`: `-18.9%` to `-35.7%`). `VC2` shows only a small
(`~4%`) improvement at `N2_PRECHARGE in {5,10}`, far smaller than R04E12's
own phase-1-gate `VC2` gains, and paired with a substantially larger `VC3`
cost at those same values. The directly-identified root cause: adding ANY
phase-2 gate costs exactly 2 completed rotations within the fixed
`TSTOP=20 us` window (`12->10`, regardless of `N2_PRECHARGE`'s exact
value) -- the one-time admission chain's own wall-clock cost eats into the
window that would otherwise fund additional round-robin rotations, and
losing those rotations costs more progress than the extra phase-2
front-loading gains at nearly every state variable. This directly answers
the question this experiment was designed to test: the bottleneck does NOT
"relay" cleanly to `VC3`/phase 3 in an improved sense when phase 2 is
gated on top of phase 1's own -- `VC3` is in fact the variable that
worsens most. See
`R04E13_phase2_precharge_admission_gate/BOUNDARY.md` and `RESULTS.md` for
the full construct-design-correction narrative, the pilot-verification
evidence, and the complete 4-cell grid.

## R04E14 -- the corrected `Cfly` also rescues R02A/B's own, much older
   passive-divider module, not just the R04E7-E13 lineage

R04E14 goes back to R02A/R02B's own original passive-divider-plus-diode
precharge module (the literature-transferred IPEC 2018 circuit, structurally
unrelated to R04E9-R04E13's inductor-mediated `CHARGE_k`/`FREE_k` machine)
and asks the same corrected-`Cfly` question R04E8 already asked of the
newer ratio-gating lineage: does R02A/B's own `FAILED_CAPACITANCE_TRANSFER`
verdict survive once `Cfly=53.8 uF` is replaced by this project's own
first-principles `0.6-8.7 uF` range? The circuit is copied byte-level from
R02B's own `.cir` file with only `CFLY` (fixed at `3 uF`) and `CDIV`'s
swept range (`{10,30,100,300} uF`, re-scaled around R02A's own found
`10:1` ratio) changed; `TRAMP` (`{1,10,100} us`) is unchanged from R02B.

**Yes, the verdict changes -- 2 of the 12 primary cells (`CDIV=100 uF` and
`CDIV=300 uF`, both at `TRAMP=100 us`) simultaneously beat R02A's own best
passive `LADDER_ERR` (`~0.236`, its Step-1 `CFLY=1 uF` case) AND R02B's own
best peak source current (`150.15 A`)** -- `LADDER_ERR` `0.157`/`0.054` at
only `16.45 A`/`39.18 A` peak. This is graded `PASS_TOPOLOGY_PRINCIPLE /
NOT_P24_REPRODUCTION`, reusing R02A's own Step-1 language rather than
inventing a new category. `9` of the `12` primary cells beat R02B's own
best `LADDER_ERR` (`0.260`); only the three `CDIV=10 uF` cells do not
(`0.963-1.106`), though even those remain better than R02B's own worst
(`2.732`). **Peak current is NOT uniformly rescued by the `Cfly` correction
alone**: the 12-cell peak-current span (`3.31-2497.83 A`) overlaps R02B's
own old-`Cfly` span (`6.01-3429.57 A`), and the three `TRAMP=1 us` cells
exceed the `500 A` flag (up to `2497.83 A`) -- confirming R02B's own
`CDIV`/`TRAMP` separability finding (final charge set by `CDIV`, peak
current separately controllable by `TRAMP`) still holds at the corrected
`Cfly`. A secondary 2-cell check at the primary grid's own best `(CDIV,
TRAMP)` point, sweeping `CFLY` across the full `0.6-8.7 uF` range, found
`LADDER_ERR` genuinely sensitive to which point is used (`13x` spread,
monotonic with `Cfly`) while peak current stayed nearly flat (`8%`
spread) -- the same `V/Ron`-dominated peak-current pattern R04E8 already
found in the structurally different ratio-gating mechanism, now confirmed
in this older, purely passive one too. A reproducible LTspice-runner
tooling failure was also found and is flagged for future experiments in
this worktree: a full `.cir` absolute path length at or above roughly
`250-259` characters silently drops ALL `.meas` output with no error
(`unable to open database file` in the `.log`, otherwise a normal fast
run) -- paths at or below `~239` characters were confirmed clean. Keep
generated case filenames short. See
`R04E14_corrected_cfly_passive_precharge_replay/BOUNDARY.md` and
`RESULTS.md` for the full 14-cell grid, the direct R02A/R02B comparison,
and the path-length failure-mode isolation test.

## R04E15 -- mapping R04E14's own two PASS gaps more finely: a real
   trade-off frontier, not a further improvement, plus a genuinely
   Cfly-robust operating point

R04E14 left three explicit gaps in its own coarse 12-point grid: no `CDIV`
tested between `100` and `300 uF` or above `300 uF`; only three `TRAMP`
points (`1, 10, 100 us`), leaving the ladder-error-vs-peak-current
trade-off curve unmapped between `10` and `100 us`; and its own `Cfly`
sensitivity check run at `(CDIV=300uF, TRAMP=10us)`, not at the actual
winning `TRAMP=100us` point. R04E15 fills all three gaps with the SAME
unmodified circuit (no mechanism, topology, or parameter-model change):
Grid A sweeps `CDIV` in `{150,200,250,350,400,500} uF` at fixed
`CFLY=3uF/TRAMP=100us` (6 cells); Grid B sweeps `TRAMP` in
`{20,50,75,150,200} us` at fixed `CFLY=3uF/CDIV=300uF` (5 cells); Grid C
re-runs the winning `(CDIV,TRAMP)` point at `CFLY=0.6uF` and `8.7uF` (2
cells).

**The headline finding is a negative-but-informative one, per Ground Rule
7: no cell in the fine grid beats R04E14's own best PASS cell
(`CDIV=300uF/TRAMP=100us`, `LADDER_ERR=0.0536`, `IIN_PK=39.18A`) on BOTH
axes simultaneously.** `LADDER_ERR` decreases monotonically as `CDIV`
increases all the way to `500 uF` (no plateau yet, `0.1055` at `150uF`
down to `0.0335` at `500uF`), but `IIN_PK` rises right along with it
(`22.47A` to `61.44A`) -- confirming R04E14's own coarse-grid optimum
sits at, or very near, a genuine local trade-off frontier between the two
axes, not an accident of under-sampling. The best-`LADDER_ERR`-while-
still-under-the-`150.15A`-bar cell found here, `CDIV=500uF/TRAMP=100us`
(`LADDER_ERR=0.0335`, a `37.6%` improvement, at `IIN_PK=61.44A`, still
`2.4x` under the bar), is a legitimate alternative operating point, not a
strict improvement -- it trades away peak-current margin for ladder
accuracy. `12` of `13` cells pass the full bar (the lone exception,
`CDIV=300uF/TRAMP=20us`, fails only the current half at `195.90A`),
because this grid was deliberately centered on territory R04E14 already
found good, not because the underlying physics changed.

**The genuinely new, positive result is Grid C's `Cfly`-robustness
check.** Run at the ACTUAL winning point (`CDIV=500uF/TRAMP=100us`) this
time, all three `Cfly` values across the full `0.6-8.7 uF` first-
principles range pass BOTH halves of the bar comfortably (`LADDER_ERR`
`0.0066-0.0956`, `IIN_PK` a nearly flat `60.48-63.68A`) -- a materially
more robust result than R04E14's own secondary grid, which was run at a
different, `TRAMP=10us` point where all three `Cfly` values FAILED the
current bar outright (`382-412A`, regardless of `Cfly`). The lesson: a
`Cfly`-sensitivity check is only as informative as the operating point it
is run at -- `TRAMP`, not `Cfly`, is what determines whether the current
axis is cleared at all in this circuit, exactly as R02B's own
`CDIV`/`TRAMP`-separability finding predicts. Graded
`PASS_TOPOLOGY_PRINCIPLE/NOT_P24_REPRODUCTION`, the same category R04E14
used, not a new one; this does not change or supersede R04E14's own
committed grid or numbers. See
`R04E15_passive_precharge_fine_grid_refinement/BOUNDARY.md` and
`RESULTS.md` for the full 13-cell grid and the explicit before/after
comparison against R04E14's own best cell.

## R04E16 -- extending Roberts' own dissertation soft-start method into
   this project's model: it avoids R03A's runaway, but the control-cell
   counterfactual shows the ramp itself is probably not why (GRID
   COMPLETE, 6/6 cells)

R04E16 is the first experiment in this project to build and run Roberts'
PhD dissertation Section 3.5 soft-start idea (ramp `Vin` slowly through
an eFuse while the converter's ORDINARY, non-event-gated switching
pattern runs unchanged) -- explicitly NOT a repeat of R04E5's own
already-falsified "graft a ramp onto the strict event-gated controller"
combination (see the "Lesson from R04E5" section above): R04E16 reuses
R03A's own fixed-timing, `T/4`-shifted gate-generation B-sources
verbatim (`TSTART=0` is the only change to those formulas), on R03A's
own four-phase power stage, with `LPHASE` corrected to this project's
`1.4666667 nH` standing value, `CFLY` swept across the `0.6-8.7 uF`
first-principles range, and R02B's passive-divider precharge network
removed entirely (true zero-energy start, no auxiliary precharge
circuit of any kind).

**Before any grid cell could be trusted, R03A's own default LTspice
solver options were found to corrupt every single cell** -- direct
byte-level inspection of the raw `.raw` trace showed the classic
near-duplicate-timestamp retry-chatter fingerprint this project already
documented for R04E10/R04E11's unrelated `.machine` construct, followed
by the INDEPENDENT `Vin` PWL source itself reading physically impossible
voltages (`-20885 V`, then `5.33e24 V`) -- unambiguous proof of solver
corruption, not a physical result, occurring while real circuit state
was still completely benign. The fix was to adopt `solver=alt
cshunt=1e-15 plotwinsize=0`, the exact numerical-stabilization
convention R04E5 through R04E10 already use at this project's own
`TMAX=50 ps` resolution -- `TMAX` itself was never coarsened, at any
point across all 6 cells.

**A second, independent tooling finding**: even with the corruption
fixed, this netlist class showed severe, `TSTOP`-disproportionate
runtime variance (`1302.6/1932.1/7937.0/11842.4/2165.2/2525.2 s` of real
LTspice compute time across the final 6 cells, an `8.3x` spread in
simulated-ns-per-wall-second that does NOT scale monotonically with
`TSTOP` at all -- the two LARGEST-`TSTOP` cells actually finished FASTER
than two smaller-`TSTOP` ones), and running cells concurrently made this
roughly `20x` worse (this machine's `10` physical cores get
oversubscribed by each LTspice process's own `10`-thread request). This
meant the grid could not be completed in a single session; all `6` cells
were eventually completed across multiple sessions, each run strictly
one at a time (the next cell was only ever launched after the previous
one's own `.log` confirmed a `Total elapsed time` line), never
concurrently, per this same finding.

**All 6 completed cells avoid R03A's own catastrophic runaway**
(max phase current `75.1-150.1 A`, `3.75x-7.51x` below R03A's own
smallest peak of `563 A`, comfortably inside the `+/-250 A` safety
bound) with no `Vout` overshoot at all (the opposite of R03A's own
`54%` overshoot). **But the control cell (`Tramp=1 us`, a
near-instantaneous ramp) equally avoids the runaway** -- exactly the
possibility BOUNDARY.md's own Section 10 flagged as a separately
-reportable finding if it happened, and it did: this directly undermines
a clean "the `Vin` ramp specifically is responsible" causal claim, and
this conclusion is UNCHANGED by completing the grid. All four
`Cfly=3 uF` cells (control, `10x`, `30x`, and `100x` margin) converge to
nearly identical final state (`Vout~=0.559 V`, `LADDER_ERR~=1.34-1.35`)
despite a `229x` range in `Tramp`, strongly suggesting the dominant
effect is removing R02B's passive-divider precharge network itself
(which is what let R03A's own ladder pre-charge to `34/22/11 V` before
full-strength PWM hit a still-cold `Vout` -- R03A's own diagnosed
failure mechanism), not the ramp speed. **New with the completed grid**:
peak inductor current now shows a clean, MONOTONIC decrease with margin
factor (`150.1/111.6/86.9/75.1 A` at `Tramp=1/22.87/68.61/228.71 us`,
with diminishing returns at each step) -- so while the ramp does not
determine WHETHER runaway occurs, it does have a real, measurable,
secondary effect on HOW LARGE the benign transient current is. The
completed 3-point `Cfly` sensitivity trend (`0.6/3/8.7 uF`, all at `30x`
margin) shows `LADDER_ERR`/`Vout_final` decreasing modestly but
monotonically with `Cfly` (`LADDER_ERR` `1.399->1.348->1.333`) while
`IL1_max` is small and non-monotonic (`92.2/86.9/90.2 A`). See
`R04E16_roberts_softstart_fixed_timing/BOUNDARY.md` and `RESULTS.md` for
the full forensic evidence, the complete 6-cell results table, and the
final classification.

## R04E17 -- isolating R04E16's own two simultaneous changes: with the
   divider present, the Vin ramp speed is what decides runaway or not

R04E16 could not tell whether removing R02B's own passive-divider
precharge network, or ramping `Vin` slowly, was responsible for avoiding
R03A's own runaway, because both were changed at once (its own control
cell, fast ramp with the divider already removed, ALSO avoided runaway).
R04E17 is the factorial isolation experiment R04E16's own `RESULTS.md`
Section 6 called for: a `2x2` design crossing `{divider present,
absent}` x `{fast ramp (`Tramp=1 us`), slow ramp (`Tramp=68.61 us`)}`,
reusing R04E16's own two already-completed divider-ABSENT cells
(`e16_ctrl_f3_t1`, `e16_g1_f3_t68p61`) by reference and adding two NEW
divider-PRESENT cells built by grafting R03A's own divider-plus-diode
network (`CIN1-4`/`RLEAK1-4`/`DPC1-3`, connecting into the SAME real
`a1`/`a2`/`a3` power-stage nodes) onto R04E16's own unmodified netlist,
with `CDIV=300 uF` (R04E15's own corrected best-point value at
`Cfly=3 uF`, not R03A's own cross-topology-suspect `1.076 mF`).

**The result is the clean, unambiguous third pattern BOUNDARY.md Section
7 anticipated: the fast-ramp/divider-present cell shows genuine
runaway, and the slow-ramp/divider-present cell does not.**
`e17_div_f3_t1` (`Tramp=1 us`) reaches phase currents of `813-1046 A`
across all four inductors -- every phase individually exceeds the
`+/-250 A` safety bound, in the same order of magnitude as R03A's own
originally diagnosed runaway (`563-884 A`). `e17_div_f3_t68p61`
(`Tramp=68.61 us`, the same `30x`-margin value R04E16 itself used) stays
at `140.8-154.7 A`, comfortably inside the bound and close to
`e16_g1_f3_t68p61`'s own `86.94 A` at the same `Tramp`. **This directly
answers R04E16's own open question: with the divider physically
present, the `Vin` ramp speed is the causally decisive factor** -- it is
not merely "PWM active from `t=0`" or "the divider happens to be
removed" that determines runaway, but Roberts' own dissertation
mechanism doing genuine protective work against the specific mismatch
(a precharged capacitor ladder suddenly exposed to full-strength PWM
while `Vout` is still cold) R03A originally diagnosed. R04E16's own
control-cell surprise is not contradicted by this -- it is explained: an
experiment where the mismatch has already been removed some other way
(deleting the divider entirely, as R04E16 did) gives the ramp nothing
left to protect against, so ramp speed had no effect there.

A second, independent finding: **both divider-present cells reach
`Vout_final` within `0.6%` of the `1 V` target and `LADDER_ERR`
`0.024-0.029`** -- roughly `46-56x` better than either of R04E16's own
divider-ABSENT cells (`LADDER_ERR~=1.34-1.35`, `Vout_final~=0.559 V`).
Reintroducing the divider is not merely "safe if the ramp is slow
enough" -- it substantially improves ladder and output accuracy at
EITHER tested ramp speed, a genuine benefit R04E16's own divider-removal
approach gives up entirely. Both new cells' raw `.raw` binary traces
(`6.7` million and `8.2` million points respectively) were directly,
byte-level parsed and confirmed free of R04E16's own documented
solver-corruption fingerprint (zero non-monotonic or duplicate
timestamps; the independent `V(vin)` PWL source never deviates from its
own commanded ramp value at any point in either trace) -- the large
currents reported for `e17_div_f3_t1` are a confirmed real result, not a
numerical artifact. Both cells were run strictly one at a time (never
concurrently), and R04E16's own two divider-ABSENT cells are reused
here purely by reference, not re-run or modified. See
`R04E17_divider_ramp_factorial_isolation/BOUNDARY.md` and `RESULTS.md`
for the complete 2x2 table, the full forensic corruption-check detail,
and the discussion of what this experiment does and does not establish
beyond these two exact `(Cfly, Tramp)` points.

## R04E18 -- localizing R04E17's own untested runaway/safe `Tramp`
   boundary to a `5-22.87 us` sub-interval, with a gradual (not sharp)
   underlying transient trend

R04E17 isolated the ramp-vs-divider confound but tested only two `Tramp`
points (`1 us`, runaway; `68.61 us`, safe), leaving the actual transition
between them completely unmapped (its own `RESULTS.md` Section 7). R04E18
adds three new intermediate `Tramp` points -- `5 us` (new, near the fast
end), `22.87 us` (R04E16's own already-derived `10x`-margin value at
`Cfly=3 uF`, now tested divider-PRESENT for the first time), and `40 us`
(new, filling the gap between R04E16's own `10x`/`30x` margin values) --
to the SAME unmodified R04E17 netlist (divider present, `Cfly=3 uF`,
`CDIV=300 uF`, `solver=alt cshunt=1e-15 plotwinsize=0`/`TMAX=50 ps`,
nothing else changed), giving a 5-point picture together with R04E17's
own two already-completed endpoints, reused here strictly by reference.

**Result: the fast new cell (`Tramp=5 us`) still shows runaway-scale
current (`max{|IL1-4|}=651.55 A`, all four phases over the `+/-250 A`
bound); both slower new cells (`22.87 us`, `40 us`) are safe
(`205.07 A`/`170.41 A`).** This localizes the runaway/safe crossing
(against this project's own `+/-250 A` engineering bound) to the
`5-22.87 us` sub-interval -- narrower than, and entirely inside, R04E17's
own previously-untested `1-68.61 us` gap. The complete 5-point
`max{|IL1-4|}` sequence (`1046.42/651.55/205.07/170.41/154.73 A` at
`Tramp=1/5/22.87/40/68.61 us`) is smoothly monotonic-decreasing across
the full range, with no discontinuous jump anywhere -- so while the
specific `+/-250 A` bound happens to be crossed within the `5-22.87 us`
sub-interval, the underlying transient-current relaxation with `Tramp`
is better described as gradual than as a sharp cliff. `Vout_overshoot`
and `IIN_PK` show the same gradual, monotonic pattern across all 5
points, while `LADDER_ERR`/`Vout_final`/`VC1-3_final` stay essentially
flat (`Tramp`-insensitive) throughout -- confirming, as R04E17 itself
found, that ramp speed affects the transient's peak magnitude, not the
divider's own end-state charging accuracy. All three new cells' raw
`.raw` traces (`6.8`/`7.2`/`7.6` million points) were directly,
byte-level parsed and confirmed free of the documented solver-corruption
fingerprint (zero non-monotonic/duplicate timestamps; `V(vin)` stayed
within `0-48.36 V` throughout, well inside any physically-impossible
range, across all three cells). All three cells were run strictly one at
a time, never concurrently, and R04E17's own two endpoint cells are
reused here purely by reference, not re-run or modified. See
`R04E18_divider_present_tramp_boundary/BOUNDARY.md` and `RESULTS.md` for
the complete 5-point table, the full forensic corruption-check detail
(including a methodological note on why the tight tolerance R04E17 used
flags physically-plausible small-signal ringing at these particular
`Tramp` values, distinct from genuine corruption), and the discussion of
what this experiment does and does not establish.

## R04E19 -- testing whether the divider-present runaway/safe boundary
   R04E18 localized at `Cfly=3 uF` scales with `Cfly` the way the
   underlying `1/√Cfly` resonance-frequency law predicts

**The picture is genuinely more complex than a clean scaling law at
`Cfly=0.6/8.7 uF`, and reported honestly as such rather than forced into
either "confirmed" or "refuted."** Four cells reused R04E17/R04E18's own
`Tramp` values at the two untested `Cfly` extremes: `Tramp=5 us`
(unsafe at `Cfly=3uF`) at `Cfly=0.6uF` remains unsafe on ALL FOUR phases
(`max(|IL_min|,IL_max)` = `412/321/398/1022 A` -- phase 4 actually WORSE
than the `Cfly=3uF` reference, `1022A` vs `652A`), contradicting the
simple "smaller `Cfly` = safer" direction of the prediction; `Tramp=
22.87 us` (safe at `Cfly=3uF`) at `Cfly=8.7uF` becomes unsafe on 2 of 4
phases (`372/225/167/300 A`), consistent with the "larger `Cfly` needs
more margin" direction. Unlike `Cfly=3uF`'s own phase-symmetric pattern
(all four phases moving together), both new `Cfly` values show genuine
PER-PHASE asymmetry (e.g. a `2.2x` spread across phases at the same
`Cfly`/`Tramp` for the `8.7uF` cell) -- an unexplained new finding, not
diagnosed further here. Neither `Cfly`'s own `30x`-margin
model-recommended `Tramp` is comfortably safe across the board: only
`Cfly=8.7uF`'s (`116.84 us`) is uniformly safe (`170/141/132/158 A`);
`Cfly=0.6uF`'s (`30.68 us`) has one phase marginally OVER the `250A`
bound (`251.0A`, phase 4). A first analysis pass that checked only each
phase's own `IL_max` (not the correct `max(|IL_min|,IL_max)`) understated
the `Cfly=0.6uF`/`Tramp=5us` cell's own hazard -- caught and corrected
before this document was finalized (see `RESULTS.md` Section 3). Separate
from the current-safety question, `Cfly=8.7uF` reaches substantially
better `LADDER_ERR` (`0.009-0.019`) than `Cfly=0.6uF` (`0.134-0.138`) at
comparable `Tramp` fractions; `e19_f8p7_t116p84`'s own `LADDER_ERR=
0.00947` is the best value reached anywhere in this project's Track-B
lineage to date. All four cells' raw traces were confirmed free of the
documented solver-corruption fingerprint. Because `CDIV=300 uF` was
deliberately held fixed while `Cfly` varied (per this experiment's own
single-conceptual-change scope), the results cannot cleanly isolate the
pure resonance law from the simultaneously-changing `CDIV/Cfly`
charge-sharing ratio -- this is reported as this experiment's own
explicit attribution limit, not resolved here. Cells were run across two
sessions with an explicit user-directed pause between the third and
fourth cell (not a technical failure); the fourth cell was later run to
completion in the same already-existing worktree, reusing the first
three cells' already-invested compute rather than restarting from
scratch. See `R04E19_divider_present_cfly_sensitivity/BOUNDARY.md` and
`RESULTS.md` for the complete 4-cell table, the corrected per-phase
hazard analysis, and full discussion of what this does and does not
establish.

## R04E20 -- testing a parallel math-model effort's own charge-
   conservation law across `CDIV`: directionally useful, but not a
   precise predictor, a genuinely mixed result

A parallel, independently-developed hybrid-DAE math-model effort in this
same repository (`results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md`)
derived a simple charge-conservation law from first principles: the four
equal `CDIV` divider capacitors present a `CDIV/4` series equivalent to
`Vin`, so a linear `0-Vin` ramp of duration `Tramp` demands an
unavoidable base charging current `Idiv=(CDIV/4)*Vin/Tramp`, giving a
predicted runaway/safe threshold `Tramp_threshold=CDIV*Vin/(4*250A)`
against this project's own `+/-250A` engineering bound. At
`CDIV=300uF` this predicts `14.4us`, already consistent with R04E18's
own independently-observed `5-22.87us` transition bracket -- but that
was retrospective corroboration, not a prospective test. R04E20 tests
the law prospectively at two OTHER `CDIV` values (`100uF`, `500uF`) it
was not fitted to, holding `Cfly=3uF` fixed throughout (the reverse of
R04E19's own design, directly addressing R04E19's own attribution
limit), with four new cells at `0.5x`/`2x` each `CDIV`'s own predicted
threshold, plus R04E18's own two `CDIV=300uF` cells reused by reference.

**The result is genuinely mixed, not a clean confirmation or refutation.**
`e20_c100_t2p4` (`CDIV=100uF`, `Tramp=2.4us`, `0.5x` threshold, predicted
unsafe) confirms dramatically (`851/884/855/942A`, all four phases). But
`e20_c100_t9p6` (`CDIV=100uF`, `Tramp=9.6us`, `2x` threshold, predicted
safe) does NOT confirm -- still unsafe on all four phases (`332/288/261/
309A`), a clear quantitative failure of the law at this `CDIV`.
`e20_c500_t12` (`CDIV=500uF`, `Tramp=12us`, `0.5x` threshold, predicted
unsafe) matches only marginally -- just one of four phases (`IL4=
318.07A`) exceeds `250A`, far weaker than either `CDIV=100uF`'s own
unsafe cell or R04E18's own `CDIV=300uF` unsafe cell. `e20_c500_t48`
(`CDIV=500uF`, `Tramp=48us`, `2x` threshold, predicted safe) confirms
cleanly (`149/155/144/143A`, all four phases comfortably safe). The
law's qualitative DIRECTION (larger `CDIV` needs more `Tramp` margin)
holds at both new `CDIV` values -- the `0.5x` cell is always worse than
the `2x` cell at the same `CDIV` -- but the SPECIFIC threshold formula
is not an accurate quantitative predictor away from `CDIV=300uF`,
increasingly so at the smaller `CDIV`. A plausible but NOT independently
verified explanation is offered (a roughly `CDIV`-independent
switching-stage current contribution would become proportionally more
significant relative to the shrinking divider term as `CDIV` drops,
explaining why the law under-predicts danger more severely at smaller
`CDIV`) -- flagged as a hypothesis for the parallel math-model effort's
own next steps, not an established finding. All six rows (new and
reused) show the SAME phase-symmetric pattern R04E17/R04E18 already
found at `CDIV=300uF` (when unsafe, usually unsafe on most/all phases
together), unlike R04E19's own `Cfly`-sweep result -- supporting, though
not proving, that the divider's own charge demand is a more
phase-uniform driver than the flying-capacitor resonance mechanism
R04E19 tested. All four new cells' raw `.raw` traces were directly,
byte-level parsed and confirmed free of the documented solver-corruption
fingerprint. All four cells were run strictly one at a time, never
concurrently, and R04E18's own two reused cells are not re-run or
modified. See
`R04E20_divider_charge_conservation_law/BOUNDARY.md` and `RESULTS.md`
for the complete 6-row table, the full per-`CDIV` discussion, and what
this does and does not establish.

## R04E21 -- does a Track-B-bootstrapped phase-1 state avoid R04E3's own
   documented zero-energy stall? A narrow negative result: the same
   stall recurs

**This experiment does NOT test P24 periodicity** (a 2026-09-18 research
pass, recorded in `R04E21_phase1_handoff_into_r04e3_stall/BOUNDARY.md`
Section 0, established that no genuinely closed periodic orbit has ever
been found anywhere in this project by either SPICE or symbolic methods
-- that question remains independently unresolved regardless of this
experiment's own outcome). It asks one narrow question instead: does
R04E3's own event-gated phase-1 local commutation controller
(`paper_locked/02_ectc2024_main/spice/
R04E3_P24_minimal_zero_start_event_cycle.cir`, unmodified except `Cfly`
corrected `53.8uF->3uF`) avoid its own documented permanent stall at
state `COMMUTATE_HIGH_TO_ZVS` (waiting forever for `V(vin,a1)<=0`) when
phase 1 is started from R04E17's own real bootstrapped state (`e17_div_
f3_t68p61`'s own `VC1`/`IL1` at `TSTOP=368.61us`) instead of true zero
energy? Step 1 re-ran R04E17's own unmodified cell with one added
`.meas` line to extract the missing instantaneous `IL1_AT_TSTOP=
75.96527862548828 A` (the re-run's own `.log` failed to print `.meas`
results due to a benign post-processing hiccup, so all values were
independently re-extracted from the `.raw` trace and cross-checked --
all 18 of R04E17's own already-published values reproduced exactly).
Step 2 built the new handoff cell with `VC1_IC=35.85894624845418V`,
`IL1_IC=75.96527862548828A` on phase 1 only; phases 2-4 deliberately
kept R04E3's own hardcoded zero-energy, single-phase-isolation
configuration (an explicit, stated scope limit, not an oversight --
their own real R04E17-bootstrapped currents were discarded). **RESULT:
the same stall recurs.** `STATE_FINAL=4` (`COMMUTATE_HIGH_TO_ZVS`) at
`TSTOP=20us`; `T_HIGH_SIDE_ZVS` `FAIL`s to trigger, exactly as in
R04E3's own zero-start cell. The bootstrapped state reaches this same
parked state far faster (`~1.69us`, vs. needing to first build current
from zero) but does not avoid it -- bootstrapped current/voltage
magnitude alone is not sufficient to unblock the high-side ZVS event.
Phase 1's own current stayed well within the `+/-250A` bound throughout
(`max|IL1|=75.97A`), and the `.raw` trace was confirmed free of the
documented solver-corruption fingerprint (zero non-monotonic timestamps,
`V(vin)` exactly within its commanded `0-48V` step). See
`R04E21_phase1_handoff_into_r04e3_stall/BOUNDARY.md` and `RESULTS.md`
for the complete Step-1 verification table, state-transition timeline,
and full discussion of what this narrow negative result does and does
not establish.

## R04E22 -- rescaling I_LIMIT/I_NEG to P24's own real current scale: an
   inconclusive result, neither confirming nor refuting R04E21's own
   diagnosed hypothesis

Direct, narrowly-scoped follow-up to R04E21's own negative result,
testing one specific diagnosed hypothesis (`R04E22_phase1_handoff_
rescaled_ilimit/BOUNDARY.md` Section 1): R04E21's own `I_LIMIT=10A`/
`I_NEG=0.2A` are leftover values sized for true-zero-energy startup's
tiny first-pulse scale, not P24's own real current scale -- did rescaling
`I_LIMIT` to P24's own `LOCKED` Table-1 peak current (`125A`,
`SOURCE_COVERAGE_MATRIX.md`) let the state-4 high-side ZVS event
(`V(vin,a1)<=0`) actually occur, when phase 1 starts from the SAME
R04E21 bootstrapped state (`VC1_IC=35.85894624845418V`, `IL1_IC=
75.96527862548828A`)? Two cells were built, both from R04E21's own
netlist as the literal template with ONLY the `I_LIMIT`/`NEG_FRAC`
`.param` line changed: `r04e22_neg2pct` (`NEG_FRAC=.02`, `I_NEG=2.5A`,
"main P24 branch" convention) and `r04e22_neg7p77pct` (`NEG_FRAC=.0777`,
`I_NEG=9.7125A`, A42's own found local natural-ZVS threshold). **RESULT:
neither cell reaches state 4 or state 5 -- both park one state EARLIER
than R04E21's own stall, at state 3 (`LOW_BUILD_NEGATIVE`), at
`TSTOP=20us` (unchanged from R04E3/R04E21).** `STATE_FINAL=3` in both
cells; `t_neg_target` (the `3->4` transition) `FAIL`s in both, since
`IL1` only reaches `-2.21509122849A` by `TSTOP` -- less negative than
EITHER swept `I_NEG` target. Because this rule never fires in either
cell, `NEG_FRAC` never actually enters the simulated physics before
`TSTOP`, so both cells' entire measured state (all `.meas` values) is
numerically IDENTICAL. Correcting `I_LIMIT` to `125A` does what
BOUNDARY.md Section 2 predicted to state 0 (genuine dwell/charging,
`t_energy_end=6.37ns` vs R04E21's near-instant `~0.3ps`), and the
zero-crossing timing is close to R04E21's own (`~1.63us` in both) -- but
a previously-unexamined knock-on effect is that the POST-zero-crossing
negative-current-build rate (state 3) is far slower under this
larger-`I_LIMIT` trajectory than under R04E21's (`-2.215A` over
`~18.37us` here, vs. R04E21's own `-0.2A` reached in just `~56ns`).
`TSTOP=20us`, inherited byte-identical from R04E3/R04E21 (sized for the
OLD `I_LIMIT=10A` regime, not re-derived for this new one), is
consequently not long enough for either swept `I_NEG` target to be
reached. **This means R04E21's own diagnosed hypothesis is UNTESTED by
this run -- not confirmed and not refuted**: the mechanism the
hypothesis is about (does a larger `I_NEG` unblock the state-4 ZVS
event) is never exercised, because state 4 itself is never entered in
either cell. Phase 1's own current stayed well within the `+/-250A`
bound throughout both cells (`max|IL1|=125.390A`, `0` points over
bound), and both `.raw` traces were confirmed free of the documented
solver-corruption fingerprint (zero non-monotonic timestamps in either,
`V(vin)` exactly within its commanded `0-48V` step in both). Per this
project's own Ground Rule 7, this inconclusive result is reported as
exactly that -- not forced into a false positive or negative -- and a
follow-up would need either a longer `TSTOP` or an explicit accounting
of how the corrected `I_LIMIT` reshapes the entire downstream timescale
before the state-4 ZVS question this experiment set out to answer can
actually be exercised. See `R04E22_phase1_handoff_rescaled_ilimit/
BOUNDARY.md` and `RESULTS.md` for the complete state-transition
timeline, current-safety and fingerprint checks for both cells, and full
discussion of what this inconclusive result does and does not establish.

## R04E23 -- extending TSTOP so R04E22's own question can actually be
   tested: still inconclusive, I_NEG not reached even at 100us

Direct, minimal, one-parameter follow-up to R04E22's own inconclusive
result (`R04E23_phase1_handoff_extended_tstop/BOUNDARY.md`): R04E22
found neither swept `NEG_FRAC` cell's own `I_NEG` target was reached by
`TSTOP=20us` (inherited byte-identical from R04E3/R04E21, sized for the
OLD `I_LIMIT=10A` regime), so R04E21/R04E22's own actual question (does
a correctly-scaled `I_NEG` avoid R04E3's own documented ZVS stall) was
never actually tested. This experiment extends `TSTOP` from `20us` to
`100us` (a `5x` margin over a naive linear extrapolation of R04E22's own
observed rate) and updates the five `AT 20u` `.meas` lines to `AT 100u`
to match -- the ONLY changes; everything else is byte-identical to
R04E22's own two netlists (`r04e22_neg2pct.cir`, `r04e22_neg7p77pct.cir`).
**RESULT: `I_NEG` is STILL not reached in EITHER cell, even at the
extended `100us` -- both remain parked at state `3` (`LOW_BUILD_
NEGATIVE`), `t_neg_target` `FAIL`s in both.** Direct byte-level parsing
of both full `100,356`-point `.raw` traces reveals WHY the naive linear
extrapolation reasoning was wrong: `IL1` reaches its own GLOBAL minimum
of `-2.2150912284851074A` at `t~=2.82us` (well inside the ORIGINAL
`20us` window, essentially the same value R04E22's own `20us`-window
`IL1_MIN` already captured), then **relaxes back toward zero** for the
entire remainder of the window (`IL1=-0.098A` at `20us`, `-0.0024A` at
`40us`, `-0.0000236A` at the final point, `t=100us`) instead of
continuing to build more negative. Extending the observation window did
not help because the trajectory itself was never still ramping past
`20us` -- it had already peaked and begun relaxing back by `~2.82us`.
Neither swept `I_NEG` target (`-2.5A`, `-9.7125A`) is reached, and both
cells remain confirmed numerically AND physically identical (`0` of
`100,356` differing rows in either `time` or `I(xmod:L1)` between the two
`.raw` files, same reason as R04E22: the `3->4` rule never fires in
either cell, so `NEG_FRAC` never enters the simulated physics). Phase 1's
own current stayed well within the `+/-250A` bound throughout both cells
(`max|IL1|=125.390A`, `0` points over bound across all `100,356` scanned
points per cell), and both `.raw` traces were confirmed free of the
documented solver-corruption fingerprint. **R04E21's own diagnosed
hypothesis remains UNTESTED by this run too** -- state 4 is never reached
in either cell at either tested `TSTOP`, so whether a rescaled `I_NEG`
would unblock the state-4 ZVS event still cannot be determined. Per
BOUNDARY.md Section 6's own explicit instruction, this is reported
plainly as the third anticipated outcome ("`I_NEG` still not reached even
at `100us`") with NO further `TSTOP` extension attempted or recommended
here -- a future attempt would need either a circuit-level intervention
that changes state 3's own negative-current trajectory, or a `NEG_FRAC`
target within the trajectory's own observed `~-2.215A` reach. See
`R04E23_phase1_handoff_extended_tstop/BOUNDARY.md` and `RESULTS.md` for
the complete state-transition timeline, full-trace relaxation-curve
evidence, current-safety and fingerprint checks for both cells, and full
discussion of what this still-inconclusive result does and does not
establish.

## R04E24 -- a reachable I_NEG target: state 4 finally entered, but the
   same ZVS stall recurs (R04E21's hypothesis REFUTED)

Direct, single-cell follow-up to R04E23's own inconclusive result
(`R04E24_phase1_handoff_reachable_ineg/BOUNDARY.md`): R04E23 found `IL1`
peaks negative at `-2.2150912284851074A` (`~2.82us`) then relaxes back
toward zero, so BOTH swept `I_NEG` targets (`2.5A`, `9.7125A`) sat above
this natural ceiling and state 3 (`LOW_BUILD_NEGATIVE`) never exited in
either R04E22 or R04E23 cell. This experiment picks `NEG_FRAC=.016`
(`I_NEG=2.0A`), `~10%` below that observed ceiling, and changes NOTHING
else relative to R04E23's own `r04e23_neg2pct_t100us.cir` (`diff`
confirms only the `NEG_FRAC` line differs). **RESULT: `t_neg_target`
PASSES for the first time in the R04E21-R04E24 chain, at `t=2.289us` --
state 3 exits and state 4 (`COMMUTATE_HIGH_TO_ZVS`) IS entered.** But
`t_high_side_zvs` `FAIL`s: `STATE_FINAL=4` at `t=100us`, the SAME
documented stall recurs one state further in. Direct byte-level parsing
of the full `465,821`-point `.raw` trace (`4.6x` more points than
R04E23's own `100,356` -- state 4's own resonant ring forces a much finer
solver step) shows why: immediately after state-4 entry, `V(vin,xmod:a1)`
(the `4->5` rule's own quantity, needing `<=0V`) rings down to only
`9.662612915039062V` at its CLOSEST approach to the threshold
(`t=2.291us`), then damps to a `~11.92V` steady state for the rest of the
run -- nowhere near `0V`. **This is a clean REFUTATION of R04E21's own
diagnosed hypothesis** (that too-small `I_NEG` under the old
`I_LIMIT=10A` regime was the blocker): a directly reachable,
correctly-`125A`-scaled, nonzero `I_NEG=2.0A` IS enough to exit state 3,
but the resulting state-4 ring is roughly `9.66V` short of what the ZVS
condition needs -- reaching state 4 at all is not sufficient. Phase 1's
own current stayed within the `+/-250A` bound throughout
(`max|IL1|=125.390A`, `min IL1=-2.000A`, `0` of `465,821` points over
bound), and the `.raw` trace was confirmed free of the documented
solver-corruption fingerprint (zero non-monotonic timestamps, `V(vin)`
exactly within its commanded `0-48V` step). This result does not
establish what WOULD unblock the ZVS event, nor characterize the full
reachable `I_NEG` range (`0` to `~2.2A`) -- a follow-up sweep or a
circuit-level intervention is a natural next step, not performed here.
See `R04E24_phase1_handoff_reachable_ineg/BOUNDARY.md` and `RESULTS.md`
for the complete state-transition timeline, state-4 ring dynamics,
current-safety and fingerprint checks, and full discussion of what this
negative result does and does not establish.
