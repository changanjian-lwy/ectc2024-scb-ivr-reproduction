# R04E6 - EPE2019 charge-redistribution ladder bootstrap (BOUNDARY)

## 1. Parent

**PARENT: R04E3** (`paper_locked/02_ectc2024_main/spice/R04E3_P24_minimal_zero_start_event_cycle.cir`,
`paper_locked/02_ectc2024_main/STEP_30_R04E3_ZERO_START_EVENT_CONTROLLER.md`).
R04E6 reuses R04E3's `SCB4P_P24_EVENT` power-stage subcircuit connectivity
**unchanged**: the `vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4` series high-side chain,
flying capacitors `CSk` bridging `ak` to `xk` (`k=1,2,3`), low-side
switches `SLk` grounding `xk`, inductors `Lk` from `xk` to the common `out`
node, the GS61008T `RHS`/`RLS`/`CH`/`CL` device values, `CFLY=53.8 uF`,
`COUT=4.672 mF`, and true zero initial energy (`ic=0` throughout, `UIC`).

R04E6 is **not** a one-variable perturbation of R04E3. It replaces R04E3's
event-driven `.machine`/`.state`/`.rule` P24-admission controller entirely
with a different, source-borrowed mechanism (see Section 9): a fixed
hold-time, 3-state charge-redistribution sequencer, driving only phases 1-3
(H1-H3/L1-L3) with H4/L4 permanently off. It also narrows scope: R04E3
attempted (and stopped before completing) one full P24 t0-t3 admission
cycle; R04E6 does not attempt P24 admission or `Vout` regulation at all --
it targets only the flying-capacitor ladder bootstrap.

## 2. What changed relative to the parent

- Controller mechanism: R04E3's event-driven `.machine` (turns off at a
  current limit, waits for physical zero-crossing/negative-current events)
  is replaced by an **open-loop, fixed-hold-time PWL gate sequencer**
  implementing EPE2019 Fig. 5's 3-state cycle (Section 3below).
- Phases driven: R04E3 drives only phase 1's H/L pair (phases 2-4 held at a
  fixed pattern). R04E6 actively drives phases 1, 2, **and** 3's H/L pairs
  (the three states touch `H1/L1`, `H2/L1/L2`, `H3/L2/L3` respectively);
  phase 4 (`H4`/`L4`) is never asserted in any state, matching Fig. 5 where
  the phase-4 switch pair is black (off) in all three panels.
- Free sensitivity axes: `TH` (hold time, applied equally to states a, b,
  c each cycle) in `{200 ns, 1 us, 5 us, 20 us}` and `NCYC` (number of full
  a-b-c cycles) in `{1, 3, 5, 10}`. R04E3 had no such axes (single fixed
  10 A current-off limit, single pulse).
- No PWM, no `Ton`/`fsw`/`D` P24 timing parameters are used at all -- this
  mechanism does not touch the P24 200 ns switching period.

## 3. What did not change

- Power-stage node names, topology, and component values (Section 1).
- `Vin=48 V`.
- GS61008T device data (`RHS`, `RLS`, `CH`, `CL`), unchanged from
  R04E3/R04E4/R04E5.
- `Cfly=53.8 uF`, `Cout=4.672 mF` (EPE2019 Table 1 cross-source values,
  unchanged from every prior R02-R04E5 experiment in this project).
- True zero initial energy on every capacitor and inductor.
- `.options` numerical tolerances (`reltol=1e-5 abstol=1e-9 chgtol=1e-16
  solver=alt cshunt=1e-15`), unchanged from R04E3/R04E5.
- `RLDAMP=1u` series damping on every inductor branch, unchanged from
  R04E3/R04E5 (a `NUMERICAL_IDEALIZATION` present in the reused subcircuit,
  not added by this experiment).

## 4. Borrowed-fact table (per-item, per the user's explicit requirement)

Each row states exactly what is borrowed, its exact source citation, and an
explicit confirmed-transferable vs. assumption-only verdict. Nothing here is
silently promoted from one status to another.

| # | Borrowed fact | Source citation | Status |
|---|---|---|---|
| 1 | The 3-state switching TOPOLOGY itself (a "conventional 4-phase SC buck" with a series high-side chain and shunt flying caps, identical in structure to this project's own `SCB4P_P24_EVENT`) | Roberts/McRae/Prodic, EPE'19 ECCE Europe, Fig. 5 (p.5), rendered at dpi=500 and read directly by this session (not taken on trust from a prior description) | **CONFIRMED TRANSFERABLE at the node/switch level.** Independently re-derived from this project's own already-validated `R04A`/`R04C`/`R04E3` connectivity (Section 5), then cross-checked pixel-for-pixel against the rendered figure. They match exactly: state (a) = `H1+L1` only; state (b) = `H2+L1+L2`; state (c) = `H3+L2+L3`. This is a stronger confirmation than "same topology family" -- it is switch-for-switch identical. |
| 2 | The `36/24/12 V` target ratio (`3Vin/4, Vin/2, Vin/4` for `C1,C2,C3`) | EPE2019 body text, p.5 (steady-state conventional-SC-buck FC voltages), read directly from the source PDF | **CONFIRMED TRANSFERABLE as a target number.** At `Vin=48 V` this is exactly `36/24/12 V`, matching P24's own target ladder. This is an already-noted match (see task framing); re-confirmed here by reading the source text directly rather than trusting a restated value. It is a STEADY-STATE target, not a claim about this bootstrap sequence's own convergence rate or shape -- see item 4. |
| 3 | The claim that the sequence "can be repeatedly cycled through until the desired voltages ... are obtained" | EPE2019 p.5, body text immediately preceding Fig. 5's description: "a similar approach to start-up for the conventional 4-phase SC buck can be implemented as shown in the various stages of Fig. 5, which can be repeatedly cycled through until the desired voltages across the FCs are obtained." | **ASSUMPTION ONLY beyond the qualitative claim.** The paper gives **no cycle count, no hold time, no numeric convergence rate, and no threshold/event to detect "desired voltage reached."** It is a qualitative existence claim about a hardware benchtop procedure, not a quantified control law. `TH` and `NCYC` are free `SENSITIVITY_ONLY` axes swept by this experiment specifically because the source is silent on both. |
| 4 | Any numeric inrush-current limit | Not present anywhere in EPE2019. The paper's only quantitative inrush statement is qualitative-comparative: "the inrush current of Fig. 5(a) is potentially higher [than the paper's own proposed CSC buck] as the effective capacitance is C1 itself ... the peak voltage on C1 of Fig. 5(a) is the full `Vin`" (p.5) | **ABSENT FROM SOURCE, explicitly not invented here.** No pass/fail current threshold is adopted. Section 7 reports the actual peak currents found and flags implausibility qualitatively, per the task's explicit instruction not to invent a threshold the source doesn't give. |
| 5 | The source's own switch truth table | EPE2019 Fig. 5 (p.5), all three panels, blue = "activated" per the figure's own caption | Re-derived **independently** in Section 5 below from this project's own already-validated P24 connectivity, **then** cross-checked against the rendered raster. A prior informal description of this figure (available only as a secondhand paraphrase before this session) claimed state (a) closes "only the outermost high-side and low-side switches" to put "C1, C2, C3 in series directly across Vin." **That paraphrase is WRONG** and is explicitly rejected here -- see Section 6. |
| 6 | `Cfly=53.8 uF`, `Cout=4.672 mF` | EPE2019 Table 1 | Already an approved cross-source candidate value, used unchanged in R02-R04E5. **Not re-derived or re-justified here** -- this experiment borrows only the startup MECHANISM (items 1-4 above), not a second, independent capacitance justification. |

## 5. Independent truth-table derivation (done first, from this project's own topology)

This project's own `SCB4P_P24_EVENT` subcircuit (copied unchanged into this
experiment's cases) has this connectivity:

```
vin --SH1-- a1 --SH2-- a2 --SH3-- a3 --SH4-- x4
            |CS1                |CS2       |CS3
            x1                  x2         x3
            |SL1,L1              |SL2,L2    |SL3,L3
            g,out               g,out      g,out
```

Basic charge-conservation/loop reasoning on this exact topology, done
**before** looking at the figure:

- To charge `C1` alone directly from `Vin`, the only complete low-impedance
  loop not touching `C2`/`C3` is `vin-SH1-a1-CS1-x1-SL1-g`: close **`H1`
  and `L1`** only.
- To redistribute charge between `C1` and `C2` (and nothing else) without
  drawing from `Vin`, the loop must close through the shared ground return
  on both ends and through the switch bridging `a1`-`a2`:
  `g-SL1-x1-CS1-a1-SH2-a2-CS2-x2-SL2-g`: close **`H2`, `L1`, and `L2`**
  only (`H1` OFF, so `Vin` is not in this loop).
- Symmetrically for `C2`-`C3`: `g-SL2-x2-CS2-a2-SH3-a3-CS3-x3-SL3-g`: close
  **`H3`, `L2`, and `L3`** only.
- No combination of switches in this topology can place `C1`, `C2`, and
  `C3` literally in series across `Vin` to ground, because `x1` (the
  bottom plate of `C1`) has no switch to `a2` (the top plate of `C2`) --
  only `CS1` itself, `SL1`, and `L1` touch `x1`. A true 3-capacitor series
  stack is not realizable in this connectivity by switches alone.

## 6. Cross-check against the rendered figure -- and an explicit disagreement resolved

The independently-derived table in Section 5 was checked against
`epe2019_page5_hires.png` (this PDF's page 5 rendered at `dpi=500` via
`pymupdf`, `page.get_pixmap(dpi=500)`, read directly by this session). Fig.
5's blue ("activated") switches are:

- **(a) Charging**: the top-left switch (`vin`-to-`a1`, i.e. `H1`) is blue,
  and the switch to the right of `C1` going to ground (i.e. `L1`) is blue.
  All other switches (including the switch below `H1` on the left column,
  i.e. `H2`) are black (off).
- **(b) Charge Redistribution I**: the left-column switch between `C1`'s
  row and `C2`'s row (`H2`) is blue; the switches to the right of `C1` and
  `C2` (`L1`, `L2`) are blue. `H1`, `H3`, `H4`, `L3`, `L4` are black.
- **(c) Charge Redistribution II**: the left-column switch between `C2`'s
  row and `C3`'s row (`H3`) is blue; the switches to the right of `C2` and
  `C3` (`L2`, `L3`) are blue. `H1`, `H2`, `H4`, `L1`, `L4` are black.

**This matches Section 5's independent derivation exactly, switch for
switch, in all three panels.** It also matches the source's own body text
verbatim: "the inrush current of Fig. 5(a) is potentially higher as the
effective capacitance is **C1 itself**" (p.5) -- consistent with state (a)
charging `C1` alone via its own `H1`/`L1` pair, not a 3-capacitor series
stack.

**Explicit disagreement, stated per the task's own instruction:** this
task's own a-priori framing paraphrased state (a) as putting "`C1`, `C2`,
`C3` in series directly across `Vin`" using "only the outermost high-side
and low-side switches" (implying `H1`+`L4`). **Both the independent
topology-based derivation (Section 5) and the rendered figure (this
section) contradict that paraphrase.** State (a) uses `H1`+`L1` (phase-1's
own pair, not the outermost pair across all three capacitors) and charges
`C1` alone, leaving `C2` and `C3` untouched at `0 V`. The netlists and all
of Section 4's table use the figure-verified derivation (`H1+L1`,
`H2+L1+L2`, `H3+L2+L3`), not the rejected paraphrase. `H1+L4` (true
"outermost only") is never used anywhere in this experiment.

## 7. Question this experiment answers

Starting from true zero energy on every flying capacitor, does open-loop
cycling of EPE2019's own 3-state charge-redistribution sequence (Section 5
truth table) move `VC1/VC2/VC3` toward P24's `36/24/12 V` target ladder,
and over what (hold-time, cycle-count) combination -- and what peak currents
does this fixed-time, zero-dead-time, zero-added-impedance implementation
actually produce on this project's own component values?

## 8. Success condition

For a given `(TH, NCYC)` cell: `VC1`, `VC2`, `VC3` at the end of the run are
all closer to `36/24/12 V` (smaller `|VCk - target_k|/target_k`) than at
`t=0` (trivially true from zero) **and** than at the end of cycle 1, i.e.
the ladder is monotonically improving with more cycles at fixed `TH`, or
with longer `TH` at fixed `NCYC` (a `SENSITIVITY_ONLY` trend, not a P24
value). No numeric current threshold is adopted as pass/fail (Section 4,
item 4); peak currents are reported and qualitatively flagged only.

## 9. Failure conditions

- The ladder does not monotonically approach `36/24/12 V` with more
  cycles/longer hold time (e.g. it plateaus far short, oscillates, or one
  capacitor's voltage moves away from its target) -- reported as a
  `SENSITIVITY_ONLY` trend showing the mechanism's actual limit, not
  forced into a pass.
- A solver non-convergence before `TSTOP` -- reported as such, not silently
  retried with a loosened power-stage boundary.
- Peak currents that are implausible for real hardware (no invented
  threshold; qualitative flag only, per Section 4 item 4).

## 10. What this experiment cannot prove

- It cannot establish a P24-reported or EPE2019-reported numeric startup
  timing law. `TH` and `NCYC` are free sensitivity axes; the source paper
  gives neither a hold time nor a cycle count.
- It does **not** attempt, and its result says nothing about, handing off
  into P24 steady-state switching, ZVS admission, or `Vout` regulation --
  explicitly out of scope (see the task framing and R04E5's own documented
  lesson in `experiments/track_B_zero_start_extension/README.md`: this is
  not another "ramp + strict event chain" attempt, and does not graft onto
  R04E3/R04E5's admission machinery at all).
- It cannot claim four-phase interleaving; phase 4 is never driven.
- It cannot claim hardware-level switching loss, dead-time, or
  device-level ZVS accuracy -- the power stage uses the same ideal-switch,
  scalar-`Coss` model as R04E3/R04E4/R04E5, and this experiment adds
  **zero dead time** between adjacent-phase high-side handoffs (state a to
  b, and b to c), which is itself a reportable finding (Section 11), not a
  validated hardware timing.
- A pass in one `(TH, NCYC)` cell does not imply neighboring untested
  cells would also pass.

## 11. Zero-dead-time handoff -- a known idealization, reported not hidden

Every state transition in this experiment's PWL gate sequencer is a
100 ps edge with **no interlock/dead-time gap** between one high-side
switch's turn-off and the next high-side switch's turn-on (e.g. `H1` falls
and `H2` rises at the same commanded instant, `a1`). The source paper gives
no dead-time guidance for this sequence. Section 4 (`RESULTS.md`) reports
whether this produces an observable handoff-instant current transient
distinct from the steady within-state redistribution current, and flags it
qualitatively; no dead time is added to "fix" it, per protocol Section
I.7 (a boundary must never be changed merely to produce an attractive
number).

## 12. Honesty about mechanism provenance (`CROSS_PAPER_EXTENSION`)

The 3-state charge-redistribution sequence is a `CROSS_PAPER_EXTENSION` in
this project's own taxonomy: EPE2019 demonstrates it for the paper's own
"conventional 4-phase SC buck" comparison topology (not P24, and not
EPE2019's own proposed CSC-buck main contribution). It is grafted onto
P24's own four-phase connectivity here because Section 5/6 confirm the two
topologies are switch-for-switch identical for this purpose. This is
**not** a P24-stated mechanism and must never be reported as one. The
already-approved `Cfly`/`Cout` cross-source values (item 6, Section 4) are
a separate, previously-approved borrowing and are not re-litigated by this
experiment.
