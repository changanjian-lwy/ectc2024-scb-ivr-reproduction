# D88 - known air-core inductors on the design point

Script: `scripts/p24_air_core_units.py` -> `diagnostics/D88_air_core_units.json`. No co-simulation. Written 2026-10-22
on the user's question "can't you try the air-core inductors that already exist?". D87's parallel plate is a
first-principles design; here the units are ones somebody built or sells, placed on the designs the way D83 placed
[10]'s HBS1 cells.

Method: each unit is arranged s in series × p in parallel to give the design's phase L within 2 % (D83's tolerance),
with the per-unit rms current (the phase's 77.5 A rms / p) at most its rating. An air core does not saturate, so the
ratings are thermal. Copper: DC from R_DC. Ripple from the record's triangle as harmonics (D87), through
R_AC(nf) = max(R_DC, R_Q √(nf / f_Q)) with R_Q = 2π f_Q L / Q from the catalogue's Q. That is skin-effect scaling,
assumed; units without a Q are taken at R_DC, a lower bound. Semiconductor block as D87. N0, chip, 25 °C, per 250 W
module.

## 0. Result

- **Every published package-embedded air-core inductor is far worse than the magnetic cores.** The Intel FIVR and TSMC
  InFO units in P24 Table 2 (1.2-2.5 nH, 0.6-8 A, built for 90-140 MHz) have 4.8-16 mΩ/nH, i.e. 13-43 × [10]'s
  IND048. On the 2.5 MHz design they give 220-755 W of DC copper alone and 17-41 % efficiency; on the 5 MHz design 27-54 %.
  They suit a FIVR phase of a few amperes at ~100 MHz, not 62.5 A at a few MHz.
- **Board-level catalogue air coils reach 82-87 % (2.5 MHz design), but outside the package.** Würth WE-ACHC (flat wire, 22-90 nH,
  30-40 A, 0.55-1.2 mΩ) and Coilcraft SQ (47-500 nH, 4-6 A) have 13-135 µΩ/nH. The copper is set by the ripple: their
  catalogue Q puts R_AC at 6-39 × R_DC at 2-3.5 MHz, and the ripple's copper is 8-23 W against a DC part of 0.3-6 W.
  The most compact, WE-ACHC 7449150023 (23 nH, 30 A, 10 × 10 × 4 mm), gives 85.6 % with 8 units per phase: 8 cm² per
  phase, 32 cm² per module, against P24's 0.25-0.63 cm² per phase. That is a board-level regulator beside the
  processor, i.e. the routing loss that an in-package regulator exists to avoid.
- **So no existing air-core inductor fits P24's package.** The air-core route stays where D87 put it: a purpose-built
  parallel plate, with a gap of about 0.6-0.8 mm and a plate of 0.2-0.5 cm² per phase. Nobody has built it at these
  currents.

## 1. Units and results

| unit (source, conditions) | L / R_DC / rating | R/L | 2.5 MHz design: units (area per phase), copper DC + ripple, efficiency | 5 MHz design (3.52 MHz): units, efficiency |
|---|---|---|---|---|
| FIVR package, Burton 2014 [17] (P24 Table 2, 140 MHz) | 1.2 nH / 7 mΩ / 8 A | 5833 µΩ/nH | 24 × 10 = 240, 263 + 142 W, 36.7 % | 208, 49.0-49.5 % |
| FIVR package, Lambert 2016 [11] (P24 Table 2*) | 2.5 nH / 40.7 mΩ / 5 A | 16280 | 304, 755 + 408 W, 17.4 % | 170, 27.5 % |
| InFO 3D, Chen 2016 [15] (P24 Table 2, 90 MHz) | 2.5 nH / 12 mΩ / 8 A | 4800 | 143, 222 + 120 W, 40.5 % | 84, 53.5-54.0 % |
| InFO, Yu 2015 [16] (P24 Table 2) | 1.2 nH / 7.1 mΩ / 0.6 A | 5917 | 40 560, 266 + 144 W, 36.4 % | 21 870, 49.3-49.7 % |
| PCB embedded, Dou 2018 [13] (P24 Table 2*) | 685 nH / 40.7 mΩ / 1 A | 59 | 234 (area unknown), 2.7 + 1.5 W (R_DC only), 89.1 % | 467, 87.1-88.5 % |
| Coilcraft 1515SQ-47N (Doc 720-1, Irms 20 K) | 47 nH / 6.35 mΩ / 4.9 A | 135 | 16 (2.3 cm²), 6.2 + 23.0 W, 81.9 % | 32 (4.6 cm²), 81.4-82.7 % |
| Coilcraft 2222SQ-111 | 110 nH / 6.5 mΩ / 5.7 A | 59 | 38 (11.9 cm²), 2.7 + 13.2 W, 85.6 % | 75 (23.5 cm²), 84.1-85.4 % |
| Coilcraft 2929SQ-501 | 500 nH / 16.5 mΩ / 4.3 A | 33 | 170 (92 cm²), 1.5 + 10.4 W, 86.8 % | 341 (185 cm²), 85.0-86.3 % |
| Würth WE-ACHC 7449150023 (40 K rise; 10 × 10 × 4 mm) | 23 nH / 1.2 mΩ / 30 A | 52 | 8 (8.0 cm²), 2.3 + 13.5 W, 85.6 % | 16 (16 cm²), 84.1-85.4 % |
| Würth WE-ACHC 7449152022 (12 × 11.5 × 6.6 mm) | 22 nH / 0.55 mΩ / 40 A | 25 | 2 × 15 = 30 (41 cm²), 1.1 + 9.4 W, 87.2 % | 15 (21 cm²), 85.2-86.6 % |
| Würth WE-ACHC 7449152066 (12 × 11.5 × 8.8 mm) | 66 nH / 0.99 mΩ / 32 A | 15 | 90 (124 cm²), 0.7 + 10.8 W, 86.9 % | 45 (62 cm²), 85.0-86.4 % |
| Würth WE-ACHC 7449152090 | 90 nH / 1.21 mΩ / 30 A | 13 | 31 (43 cm²), 0.6 + 11.6 W, 86.7 % | 61 (84 cm²), 84.8-86.1 % |

\* P24 Table 2 gives [11] and [13] both 40.7 mΩ, and [13]'s PCB-air row repeats its MPC-spiral row (685 nH /
40.7 mΩ). The original papers were not available, so these two rows are unverified. Neither changes the result: [11]
is the worst row, and [13] is rated 1 A.

For comparison (same conditions): D85's HBS1 IND048 array 58.2-62.5 % on [10]'s κ (74-76 % at κ 1); D86's best
measured core (XVSZ4) 58.3 %; D87's parallel plate 80 % at a gap of about 0.6 mm (300 µm copper), 83.9 % at 1 mm.

## 2. Limits

- Discrete parts: R_AC is scaled from one catalogue Q (50-400 MHz) by √f. The proximity between turns and between
  closely packed units is not modelled, and neither is the board's copper to and between the units.
- Package parts: no AC data, so the ripple is taken at R_DC, a lower bound; they fail on DC copper alone.
- The 2 % inductance tolerance can force s = 2. A 6-7 % mismatch would halve some arrays: 7449152022 at 1 × 8 gives
  2.75 nH.
- The semiconductor block is D87's: gate-level at 2.5 MHz, a band at 3.52 MHz.

Sources: P24 Table 2 (refs [11], [13], [15], [16], [17]); Coilcraft Document 720-1, rev. 12/01/21 (1515SQ / 2222SQ /
2929SQ); Würth Elektronik WE-ACHC product page (we-online.com, read 2026-10-22).
