# Consolidated findings A53-A66: does rated-load ZVS pay for itself? (2026-09-28, extended 2026-09-29)

(The file name keeps "A53_A64" so existing links still work.)

Scope: Track A, `SENSITIVITY_ONLY` throughout. The subject is one
four-phase EPC2067 module (48 V -> 1 V, 5 MHz, 250 W). Two designs are
compared:

- the **baseline**: P24's `L = 1.4667 nH`. It hard-switches its high side
  at ~12 V and has small negative current.
- the **large-ripple design**: `L = 0.6274 nH`. It reaches (near-)ZVS on all
  eight edges at rated load, with ~39% negative current.

None of this is a paper reproduction. It asks whether P24's design choice
leaves efficiency on the table.

## 1. The chain, and what each step changed

| step | what it fixed or added | large-ripple minus baseline at 250 W |
|---|---|---|
| A53/A54 | first L-vs-ZVS trade-off | "net negative" |
| A55 | branch-power metering, population-correct asymmetric Ron | found A53/A54's comparison was at unequal delivered power |
| A56 | equal power (Ton_cmd regulated to 250 W); adds hard-switch C energy the 62.5 ps meter missed | -3.18 W (ideal adaptive turn-on) |
| A57 | datasheet reverse conduction (Fig. 8, 2.3-2.5 V) under one symmetric fixed dead time | +7.06 W |
| A58 | two tuned fixed dead times (rise/fall) | -2.70 W |
| A59 | datasheet nonlinear Coss(V), dead times re-tuned | **-4.58 W** (reference) |
| A60 | typical RDS(on)(Tj): 25/60/100/125 C | -7.19 / -4.56 / -1.26 / **+0.98 W** |
| A61 | inductor-loss break-even | erased by ~185 uOhm (60 C) / **~50 uOhm (100 C)** of winding resistance |
| A62 | load sweep at fixed tuned timing | wins only above **~211 W (84%)**; +10.3 W at 100 W out |
| A63 | Cfly 1-6 uF | -6.13 ... -4.17 W (robust) |
| A64 | EPC's own EPC2067 SPICE model, finite gate drive, re-tuned timing | **+17.35 W** (R_drv 1 Ohm) / **+1.20 W** (0.3 Ohm) |
| A65 | A64 with a real driver: TI LMG1210's digitized output stage, one per device | **+11.68 W** (52.23 vs 40.55 W; between A64's two resistor cases) |
| A66 | phase-inductor loss with P24's own inductor (HBS1, P24 ref. [10]) | **+219 W** in the inductors (HBS1); +26 to +38 W with ref. [10]'s target material |

A53/A54's "net negative" conclusion was not reproduced for the reasons
they gave (unequal power, biased meter). It was wrong in its argument, not
necessarily in its final spirit.

## 2. Answer

**No: rated-load ZVS with a large ripple does not pay for itself in this
module.** The ideal-switch model (A56-A59) found an advantage of up to
4.6 W. That advantage needs all of the following at once:

- full load (>~84%);
- a device junction below ~114 C;
- a phase-inductor winding resistance below ~50-190 uOhm, depending on Tj;
- extra core loss below the same few-watt budget;
- dead times held within a few tenths of a nanosecond of the natural
  transitions.

EPC's own device model (A64) then removes the advantage at the reference
point (250 W, 60 C, zero inductor loss). (It is not the most favourable
point: at Tj 25 C the ideal-switch advantage is 2.6 W larger (A60). With
a 0.3 Ohm drive, where A64's gap is only +1.20 W, that could flip the
sign. A65 and A66 make that corner moot.) With a finite gate
drive, the large-ripple design must turn off ~189 A per high-side switch,
and the resulting V*I overlap costs 26.9 W vs the baseline's 7.7 W at
1 Ohm drive. The large-ripple design then loses by 17.35 W (1 Ohm) or
1.20 W (0.3 Ohm). At part load the baseline wins by a wide margin anyway:
the large-ripple design has a ~22 W circulating-current floor that does
not fall with load (A62).

The phase inductor settles it independently of the switches (A66). P24
names its inductor technology: embedded units of at most 5 A peak, on the
HBS1 composite core of its ref. [10].
- By ref. [10]'s own measured loss model, the large-ripple design's AC
  inductor loss is 2.33 times the baseline's, for any core material.
- With HBS1 at P24's 5 MHz, D = 1/12 point, that is +219 W per module.
- Even ref. [10]'s proposed future material leaves +26 to +38 W.
- The large-ripple design also needs 1.69 times as many embedded
  inductors.

This is consistent with P24's own choice: a larger inductor and a small
(1-2%) negative current, rather than full rated-load ZVS.

**Why the papers can report ZVS with a small negative current (A67).**
There is no contradiction; the requirement depends on the operating point.
The negative current needed, as a fraction of the ripple, is about
`sqrt(L*C_node)/Ton`, i.e. the switch node's flip time over the on-time.
- **P25 (built, 12 V, 0.5 MHz).** The flip time is 7-9 ns against a
  500 ns on-time, so 1.5-2.0% suffices. P25 specifies 5-10%. Its measured
  ZVS is physically consistent.
- **P24 (48 V, 5 MHz, never built).** The flip time is ~4 ns against a
  16.7 ns on-time, so 22-26% is needed. P24's stated 1-2% lifts the node
  only to ~2 V of 12 V. The high side then hard-switches at ~10-12 V,
  which is what A56-A65 find.

The mathematical model now reproduces P25's control and orbit at P25
scale (D41/D42), and an independent circuit simulation confirms it (A69).
This is the regime where the papers' claim holds.

## 3. Robust intermediate results

- Hard-switch capacitive energy is badly under-metered at a 62.5 ps
  backward-Euler step (22-31% captured). It must be added from the
  `h -> 0` event-window re-integration. The meter-free `P_in - P_load`
  energy balance confirms this in A56, A58 and A59, to 0.01 W.
- EPC2067 reverse conduction at operating current (22-72 A/device) is
  2.3-2.5 V (Fig. 8, digitized from PDF vector paths). At the datasheet
  table's 1.2 V "typical" (0.5 A), the drop is irrelevant.
- EPC2067 Coss(V) falls steeply between 10 and 17 V, exactly where these
  switches block. Over 0-12 V it is +18.8% charge-equivalent vs Co(tr). A
  12 V hard turn-on then costs `Qoss*V - Eoss`, 28% more per device than
  `1/2 CV^2`.
- The tuned optimum is **near-ZVS**, not exact ZVS. Turning on at
  0.7-1.7 V residual costs a few tenths of a watt but avoids reverse
  conduction.
- The per-phase dead-time gain is bounded without a run. At the A59 optima,
  everything timing can recover is 0.32 + 0.19 W (large-ripple) and
  0.19 + 0.07 W (baseline). It shifts the difference by <0.3 W.
- Gate drive is ~8.6 W for the 20 devices (QG 17.1 nC * 5 V * 5 MHz), in
  neither proxy. It is nearly equal for both designs; ZVS saves ~0.4 W of
  Miller charge.

## 4. Data errors found in the project's device library (reported, not edited)

`src/scb_ivr/device_library.py` and
`paper_locked/04_component_models/EPC2067_typical_params.lib` label
EPC2067 max-column values as typical:

| value | recorded as typical | datasheet typical | datasheet max |
|---|---:|---:|---:|
| RDS(on), 25 C | 1.55 mOhm | 1.3 mOhm | 1.55 mOhm |
| Coss, 20 V | 1607 pF | 1071 pF | 1607 pF |
| Qoss, 20 V | 56 nC | 37 nC | 56 nC |

Only RDS(on) is used, by A55-A59. 1.55 mOhm equals the typical device at
Tj ~ 60 C, so those results are valid as "Tj ~ 60 C" results; A60 makes
temperature explicit. The library should be corrected by whoever owns
`src/scb_ivr/`.

## 5. Vendor-model SPICE cross-check (A64)

EPC's `EPC2067` LTspice subcircuit was taken from four byte-identical public
mirrors and hash-checked; it is not redistributed. Each high side is two
instances and each low side three. Floating 5 V gate drives through R_drv.
Each design's command timing was re-tuned in SPICE and regulated to 250 W
at 60 C. Full results: `A64_vendor_model_spice_crosscheck/RESULTS.md`.

| 250 W, 60 C, each at its SPICE-tuned timing | R_drv 1.0 Ohm | R_drv 0.3 Ohm |
|---|---:|---:|
| large-ripple P_in - P_out | 61.09 W | 36.95 W |
| baseline | 43.74 W | 35.75 W |
| large-ripple minus baseline | **+17.35 W** | **+1.20 W** |
| turn-off V*I overlap, large-ripple / baseline | 26.9 / 7.7 W | 5.9 / 1.05 W |

- Where the models should agree, they do:
  - vendor-model Rds(on) at 60 C is 1.51-1.61 mOhm/device vs 1.55;
  - Coss/Qoss/Ciss match the datasheet within 0.6%;
  - the baseline's hard turn-on loss is 19.7 W vs A59's ~18.9 W;
  - conduction at the vendor currents is 28.3 W vs A59's 28.2 W.
- The difference is turn-off overlap, which the ideal switch cannot have,
  plus conduction at partial gate enhancement.
- A59's tuned dead times used literally as gate commands shoot through
  (163.8 / 114.1 W). The vendor channel turns off 3.8-5.3 ns after its
  command at 1 Ohm, so the command timing had to be re-tuned.
- Gate-drive energy is 8.29-8.35 W per module in every case.
- Independent replay (parent session): the four optima were re-run from
  their recorded states for 20 plain periods, with no acceleration. The
  .raw was read with an independently written reader and integrated
  separately. Last-4-period means: 61.087 / 43.733 W (1 Ohm) and
  36.917 (still rising towards the recorded 36.950) / 35.738 W (0.3 Ohm).
  All agree with the records to within 0.04 W.
- Limits: no layout loop inductance; a symmetric driver (a stronger
  pull-down than pull-up would narrow the gap); 60 C only.

## 5a. Boundary audit (2026-09-29): scope limits common to A53-A66

None of these can reverse the answer. They mark where the numbers apply.

1. **Module row.** The chain uses P24's 4-module row: 250 W per module,
   2 high / 3 low EPC2067 per switch (P24 Table 3; Table I's analytical
   case). P24's featured design (Fig. 5) is the 8-module row: 1 high /
   2 low per switch.
   - A66's per-module inductor losses scale with module power, so its
     ratio (2.33) and its inductor efficiencies carry over.
   - A64/A65's switch-level watts are specific to the 4-module row.
   - Side finding: Table 3's 4-module row lists 25 parallel 36.7 nH units
     per phase, i.e. 1.468 nH. That independently supports the project's
     Eq. (4) value (1.4667 nH) over Table I's printed 2.68 nH.
2. **Device count held fixed.** P24 sizes the switch count from the peak
   current: 62.5 A per high-side device in this row. By that rule, the
   large-ripple design's 217 A high-side peak would need ~4 devices, not 2.
   This is not modelled. More devices cut conduction but add gate charge,
   Coss and area. They cannot close A66's inductor gap.
3. **Gate-drive supplies.** The sources of high sides 1-3 sit on the
   flying-capacitor nodes (36-48 V, 24-36 V, 12-24 V) and never return to
   ground. They need isolated or cascaded-bootstrap supplies. A64/A65 use
   ideal floating 5 V supplies.
4. **Not modelled, all against the large-ripple design:**
   - power-loop and common-source inductance (turn-off at 1.7x the
     current);
   - the output ripple and output-capacitor cost of 300 A p-p phase
     ripple;
   - the 1.69x embedded-inductor area (A66).
5. **Operating point.** The SPICE lines (A64/A65) cover 250 W at 60 C
   only. A60 (temperature) and A62 (load) exist only for the ideal-switch
   model.

## 6. What still needs the advisor: nothing blocks the answer

The 48 V / 1 kW converter was never built (Mihai, 2026-09-15). Questions
of the form "what did P24 use" therefore have no hardware answer. Public
sources settled every item that A57-A64 had left open:

1. **Gate driver and timing: public datasheets (A65).**
   - P25's own driver (Infineon 1EDBx275F) suppresses input pulses shorter
     than 15/19/23 ns (min/typ/max). P24's high-side on-time at 5 MHz is
     16.7 ns.
   - One TI LMG1210 per 2-device switch cannot charge the high-side gate
     within the on-time: Vgs reaches 3.2 V.
   - With one LMG1210 output per device, the strongest commercial
     arrangement, the large-ripple design still loses by **+11.68 W**
     (52.23 vs 40.55 W). That lies between A64's 0.3 Ohm (+1.20 W) and
     1.0 Ohm (+17.35 W) cases, closer to the 1 Ohm end.
     - The turn-off overlap penalty is +11.3 W.
     - The driver's weak pull-up adds ~1.1 ns of reverse conduction at
       ~160 A: +3.3 W that a resistor driver does not have.
     - A60's 2.6 W cold-device margin cannot close that gap.
   - Timing: LMG1210's minimum dead time spreads -0.55 to 3.1 ns part to
     part, and its high-/low-side mismatch is up to 3.4 ns. The tuned
     optima need ~0.1-0.3 ns. Only closed-loop adaptive timing reaches
     that.
2. **Phase inductor: P24 names it (A66).** Ref. [10]'s measured loss model
   puts the large-ripple design +219 W per module behind with HBS1, and
   +26 to +38 W behind with ref. [10]'s future target material.
3. **Junction temperature and load profile** mattered only for the
   ideal-switch margin of at most 4.6 W. A66's inductor term alone
   exceeds that margin 5-50 times, so neither can change the answer.

Findings to report to the advisor (not questions):

- **P24's 5 MHz point with its named inductor.** With HBS1 inductors, even
  the baseline's inductors would lose ~185 W per 250 W module, an inductor
  efficiency of ~58% (A66 Section 5). This agrees with ref. [10]'s own
  conclusion that 12-1 V at 5 MHz needs a new material.
- **Gate drive at P24's 5 MHz point.** The point needs at least one
  fast-GaN driver output per device. The group's own P25 driver cannot
  pass the pulse.

Also no longer needed for this question:
- the exact Cfly (A63, robust over 1-6 uF);
- nonlinear Coss (A59, public);
- the reverse-conduction drop (A57, public);
- a switching device model (A64, EPC's own);
- per-phase timing (bounded, <0.3 W).
