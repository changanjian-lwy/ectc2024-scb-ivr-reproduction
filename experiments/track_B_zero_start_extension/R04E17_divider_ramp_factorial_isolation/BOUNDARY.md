# R04E17 - factorial isolation of "divider removed" vs. "Vin ramped" (BOUNDARY)

## 1. Parent and why this experiment exists

**R04E16** (`experiments/track_B_zero_start_extension/
R04E16_roberts_softstart_fixed_timing/`) tested Roberts' soft-start
mechanism by making TWO changes simultaneously relative to R03A: (a)
removing R02B's passive-divider precharge network entirely, and (b)
ramping `Vin` slowly instead of stepping it instantly, while running
P24's ordinary fixed-timing PWM from `t=0` in both cases. Its own control
cell (fast ramp, divider removed) ALSO avoided R03A's catastrophic
runaway, exactly matching every slow-ramp cell -- meaning **R04E16's own
design cannot tell whether removing the divider or ramping `Vin` is
responsible for avoiding the runaway, because both were changed at once**
(R04E16 `RESULTS.md` Section 6 states this explicitly as an open
question for "a future experiment isolating each change").

Per explicit user direction 2026-09-17, this experiment is that isolation
experiment: a `2x2` factorial design crossing `{divider present, divider
absent}` x `{fast ramp, slow ramp}`, reusing R04E16's own two already-
completed divider-ABSENT cells as two of the four factorial cells, and
adding the two divider-PRESENT cells that do not yet exist anywhere in
this project.

## 2. The 2x2 design

| | Fast ramp (`Tramp=1 us`) | Slow ramp (`Tramp=68.61 us`, `30x` margin) |
|---|---|---|
| **Divider ABSENT** | R04E16's own `e16_ctrl_f3_t1` (already complete: no runaway, `IL1_max=150.07 A`) | R04E16's own `e16_g1_f3_t68p61` (already complete: no runaway, `IL1_max=86.94 A`) |
| **Divider PRESENT** | **NEW cell, this experiment** | **NEW cell, this experiment** |

Both new cells reuse R04E16's own netlist (four-phase power stage,
`TSTART=0` fixed-timing gate B-sources copied from R03A, `LPHASE=
1.4666667 nH`, `CFLY=3 uF`, true-zero-energy IC, `solver=alt cshunt=1e-15
plotwinsize=0`/`TMAX=50 ps` per R04E16's own forensically-justified fix)
with ONE addition: R03A's own passive-divider-plus-diode network
(`CIN1-4`/`RLEAK1-4`/`DPC1-3`, connecting to the SAME real `a1`/`a2`/`a3`
power-stage nodes R03A itself used -- R03A already demonstrates this
exact wiring pattern, so no new topology is invented here), with `CDIV`
set to `300 uF` (R04E15's own well-characterized best-`(CDIV,Tramp)`
divider value at this project's corrected `CFLY=3 uF`, NOT R02B/R03A's
own cross-topology-suspect `1.076 mF`/`53.8 uF` combination -- reusing
the OLD divider value here would reintroduce a second, unrelated
confound this experiment is not designed to test).

`Tramp` values (`1 us` and `68.61 us`) are copied EXACTLY from R04E16's
own already-tested control and `30x`-margin cells, for direct,
apples-to-apples comparability -- not re-derived or re-chosen.

## 3. What changed relative to R04E16, exactly

- R03A's own passive-divider-plus-diode network (`CIN1-4`/`RLEAK1-4`/
  `DPC1-3`) is ADDED BACK into R04E16's own netlist, unchanged in
  topology from how R03A itself wires it (diodes feeding the real
  `a1`/`a2`/`a3` power-stage nodes, not a separate ground-referenced
  approximation).
- `CDIV=300 uF` (R04E15's own corrected, well-characterized value) is
  used, NOT R02B/R03A's own `1.076 mF` (which was sized for the
  cross-topology-suspect `Cfly=53.8 uF`, no longer this project's active
  value).
- Two cells only, at `Tramp` in `{1 us, 68.61 us}`, both at `Cfly=3 uF`
  (matching R04E16's own control and `30x`-margin cells exactly).

## 4. What did not change

- Everything else in R04E16's own netlist: the four-phase power-stage
  connectivity, `TSTART=0` fixed-timing gate B-sources (`D=1/12`,
  `TON=D*T`, non-overlapping, complementary), `LPHASE=1.4666667 nH`,
  `CFLY=3 uF`, `COUT=4.672 mF`, `RLOAD=Vout^2/Pout`, ideal `SWI` switch
  model, `RLDAMP=1u`, true-zero-energy IC (`UIC`), `TMAX=50 ps`,
  `solver=alt cshunt=1e-15 plotwinsize=0` (R04E16's own forensically-
  justified fix, required at this `TMAX` for this netlist family --
  reused unchanged, not re-derived).
- `TSTOP = Tramp + 300 us` per cell (`301 us` and `368.61 us`),
  identical to R04E16's own corresponding cells.
- `IPEC2018 LPAR=5n`/`RPAR=10m` source parasitics for the divider network
  itself, `RLEAK=1G`, ideal diode model (`Ron=1m Roff=1T Vfwd=0`) --
  unchanged from R02A/R03A.

## 5. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| R03A's own divider-network topology, reused unchanged | `paper_locked/02_ectc2024_main/spice/R03A_passive_precharge_to_fixed_pwm_takeover.cir` | inherited, unchanged |
| `CDIV=300 uF` | R04E15's own well-characterized best-point value at `Cfly=3 uF` | `SENSITIVITY_ONLY`, inherited |
| `Cfly=3 uF`, `LPHASE=1.4666667 nH` | R04E8's own corrected value / Eq.-4 branch | `SENSITIVITY_ONLY`/`P24_EXPLICIT`, inherited |
| `Tramp={1, 68.61} us` | R04E16's own already-tested control and `30x`-margin values | inherited, unchanged, chosen for direct comparability |
| `solver=alt cshunt=1e-15 plotwinsize=0` | R04E16's own forensically-diagnosed and justified fix for this netlist family at `TMAX=50 ps` | `NUMERICAL_IDEALIZATION`/`TOOLING_NECESSITY`, inherited |

No new paper-sourced, cross-paper, or external-device data is
introduced. This experiment recombines two already-existing, already-
justified circuit elements (R03A's divider wiring, R04E16's fixed-timing
power stage) at already-established parameter values; the only thing
"new" is the combination itself, which has never been built or tested.

## 6. What question this experiment is meant to answer

With the divider REINTRODUCED (at corrected component values) into an
otherwise-unchanged R04E16 netlist: does the `Vin` ramp NOW matter -- i.e.
does the fast-ramp/divider-present cell show runaway (matching R03A's
own diagnosed mechanism) while the slow-ramp/divider-present cell avoids
it (confirming the ramp CAN rescue a system with the divider's mismatch
present)? Or does even the fast-ramp/divider-present cell avoid runaway
(meaning `TSTART=0`, i.e. starting PWM immediately rather than delaying
it the way R03A did, is what actually matters, independent of both the
divider and the ramp)? The four cells of the completed `2x2` table
(Section 2) will show exactly one of these patterns (or a more complex
one), resolving the ambiguity R04E16 could not.

## 7. Success/failure conditions and what counts as informative

Every outcome is informative and none should be treated as a "failure"
requiring rework, per Ground Rule 7:

- If BOTH new cells avoid runaway: the divider's presence/absence is not
  the deciding factor either -- `TSTART=0` itself (PWM active from the
  very start, never delayed the way R03A delayed it to `150 us`) is
  likely the dominant factor, and neither the ramp nor the divider
  removal is doing the work R04E16 attributed to them.
- If BOTH new cells show runaway (or runaway-scale current, i.e.
  approaching `+/-250 A` or R03A's own `563-884 A` range): the divider's
  presence is the dominant hazard regardless of ramp speed, and R04E16's
  own removal of it (not its ramp) is what mattered.
- If the fast-ramp/divider-present cell shows runaway but the slow-ramp/
  divider-present cell does NOT: this is the clean confirmation of
  Roberts' own mechanism -- the ramp specifically rescues a system that
  would otherwise fail, cleanly separated from the divider-removal
  confound.
- If the fast-ramp/divider-present cell does NOT show runaway but the
  slow-ramp/divider-present cell DOES: a genuinely surprising, separately
  reportable finding with no assumed explanation -- report the raw result
  and investigate rather than forcing an interpretation.

Report the actual pattern found; do not select which explanation to
believe before running the cells.

## 8. What this experiment cannot prove

- It does not test any `Cfly` value other than `3 uF`, nor any `Tramp`
  value other than the two already used in R04E16 -- if the observed
  pattern is `Cfly`- or `Tramp`-magnitude-dependent, this 2-cell addition
  cannot show that; a further, separately-scoped sweep would be needed.
- It does not validate the divider's own precharge quality (`LADDER_ERR`
  at the moment PWM starts) as a mediating variable -- it treats "divider
  present/absent" as a binary factor, not a graded one.
- It does not address `Vout`/handoff bootstrap beyond what R04E16 itself
  already reports.
- It does not modify, overwrite, or invalidate R04E16's own committed
  results -- its own two divider-absent cells are reused by reference
  (their already-published numbers), not re-run.
- A P24 reproduction claim of any kind remains out of scope, same
  standing Track-B limitation as every other experiment in this lineage.
