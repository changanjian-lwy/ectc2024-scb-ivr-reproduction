# Consolidated findings A53-A64: does rated-load ZVS pay for itself? (2026-09-28)

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

EPC's own device model (A64) then removes the advantage even at the most
favourable point (250 W, 60 C, zero inductor loss). With a finite gate
drive, the large-ripple design must turn off ~189 A per high-side switch,
and the resulting V*I overlap costs 26.9 W vs the baseline's 7.7 W at
1 Ohm drive. The large-ripple design then loses by 17.35 W (1 Ohm) or
1.20 W (0.3 Ohm). At part load the baseline wins by a wide margin anyway:
the large-ripple design has a ~22 W circulating-current floor that does
not fall with load (A62).

This is consistent with P24's own choice: a larger inductor and a small
(1-2%) negative current, rather than full rated-load ZVS.

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

## 6. What still needs the advisor

After A57-A64, these items remain that public data and modeling cannot
settle. Each names the conclusion it unblocks.

1. **Gate driver (pull-up/pull-down strength or turn-off speed) and
   dead-time implementation (fixed or adaptive, timing accuracy).** A64:
   the answer swings by 16 W between 1 Ohm and 0.3 Ohm drive. A57/A58: it
   swings by ~10 W between one symmetric window and tuned timing.
2. **Phase-inductor DCR, AC resistance at 5-20 MHz and core loss at
   ~300 A p-p (or the part/structure).** The A61 break-even is
   ~50-190 uOhm. After A64 this matters only if a very strong driver is
   used.
3. **Typical full-load junction temperature or the board's thermal path.**
   The ideal-switch ranking reverses at ~114 C (A60).
4. **P24's load profile or efficiency weighting.** Below ~84% load the
   baseline wins outright (A62).

No longer needed for this question:
- the exact Cfly (A63, robust over 1-6 uF);
- nonlinear Coss (A59, public);
- the reverse-conduction drop (A57, public);
- a switching device model (A64, EPC's own);
- per-phase timing (bounded, <0.3 W).
