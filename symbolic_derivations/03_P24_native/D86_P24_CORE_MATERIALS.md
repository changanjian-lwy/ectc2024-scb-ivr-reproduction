# D86 - the four core materials of Murali et al. (ECTC 2022) at the final design point

Script: `scripts/p24_core_materials.py` -> `diagnostics/D86_core_materials.json`. No co-simulation. Written 2026-10-22
on the interview-prep session's request: D83 judged the material by [10] alone (only HBS1 carries power current), while
the same group's Murali et al., ECTC 2022 (workspace PDF `Fabrication_and_Characterization_of_Package_Embedded_Inductors
_for_Integrated_Voltage_Regulators.pdf`) measured HBS1 and three Panasonic sheets (XVSZ2, XVSZ3, XVSZ4) in three new
windings. Nothing here had been evaluated before.

Design point as D83 / D85: N0, the 2.5 MHz design (record 1.98 MHz, D 0.075), A124's waveform, per 250 W module, 25 °C,
chip only; the rest of D85's ledger (switches, gate drive, Cs ESR) is 26.25 W. One phase is p identical units in
parallel (s = 1), so per-nH metrics carry over: copper = 4 × 62.5² × R_u / p (DC only, the load's current), core =
M × L × Σ(ΔI/2)² ([10] Eq. (1)), 74.2 W per mΩ/nH of the metric M. With a core term the ripple's copper is inside M
(D85 Section 3, item 6).

## 0. Result

- **Changing the material among the four does not fix the core loss.** At 2 MHz and D 0.075, per nH, the small-signal
  r_acx spans 0.35-0.44 mΩ/nH and Murali's large-signal metric 1.97-2.39 mΩ/nH (−7 to +13 % around HBS1's 2.11). Core
  per module: 26-32 W at κ 1, 146-177 W on Murali's own large-signal data.
- **XVSZ4 is the best measured option, by about 2 points:** 58.3 % on Murali's large-signal data (HBS1 56.5, XVSZ3 56.3,
  XVSZ2 54.0 %). Its permeability gives the most nH per mΩ (IND 1: 136 µΩ/nH), and its large-signal loss per nH is the
  lowest of the four. At κ 1 all four give 79.0-80.3 %.
- **Most of the gain over D85 comes from the windings, not the material.** Murali's windings reach 136-201 µΩ/nH; even
  HBS1 in IND 2 has 201, against 376 for [10]'s best HBS1 cell (IND048, D83). DC copper falls from 17.4 W to 6.3-9.3 W.
  The cost is area: a 350-391 nH unit needs 118-132 in parallel for 2.96 nH, i.e. 6.8-9.2 cm² per phase. That is
  1.6-7.4 × D83's IND048 array (1.2-4.2 cm²) and 11-37 × P24's phase column (0.25-0.63 cm²).
- **The two sources disagree on the same material.** Murali's large-signal factor at D 0.15 is κ 4.5-6.9 (±0.25 A,
  2 MHz, zero DC); [10]'s is 3.07 (IND037-HBS1, D 0.5, up to 584 mA). For HBS1 at D 0.075 the metric is 2.11 mΩ/nH
  here against 1.43-1.83 from [10] (15-47 % higher). Both say the large-signal loss is 3-7 × the small-signal one.
- **What 80 % needs:** a core term of at most 27-30 W per module with these windings' copper, i.e. M ≤ 0.36-0.40 mΩ/nH
  at 2 MHz, D 0.075. That is about the small-signal r_acx of these materials with κ ≈ 1, a 5-6 × cut of the measured
  large-signal loss. Murali concludes the same: "Magnetic cores with high permeability along with low magnetic loss
  tangent must be synthesized".

## 1. Inputs (Murali et al., ECTC 2022; conditions as printed)

| material | best winding (R_DC / L) | L at 2 MHz (Figs. 6-7) | R_DC (Table I) | R / L | footprint (p. 1-2) | r_acx at 2 MHz, D 0.075 / 0.15 (Fig. 8, IND 1) | Fig. 11 loss, D 0.15 (IND 1) | κ at D 0.15 |
|---|---|---|---|---|---|---|---|---|
| HBS1 | IND 2 | 350 nH | 70.5 mΩ | 201 µΩ/nH | 7.0 mm² | 0.369 / 0.267 mΩ/nH | 18.0 mW (IND 1, 189 nH) | 5.7 |
| XVSZ2 | IND 2 | 350 nH | 70.5 mΩ | 201 µΩ/nH | 7.0 mm² | 0.348 / 0.251 | 24.3 mW (226 nH) | 6.9 |
| XVSZ3 | IND 2 | 391 nH | 70.5 mΩ | 180 µΩ/nH | 7.0 mm² | 0.427 / 0.299 | 23.5 mW (250 nH) | 5.0 |
| XVSZ4 | IND 1 | 367 nH | 49.8 mΩ | 136 µΩ/nH | 5.44 mm² | 0.436 / 0.32 | 33.2 mW (367 nH) | 4.5 |

- Sheets 400 µm, 50 µm copper. Small signal: zero DC. Large signal (Fig. 11): 2 MHz, ripple ±0.25 A (Fig. 10), zero
  DC, D 0.15-0.5, IND 1 only; M = P / (L (0.25 A)²), κ = M / r_acx. DC bias (Fig. 9): no saturation up to 2.5 A for
  every material.
- Murali states r_acx is a material property independent of the winding for D 0.2-0.8 up to 5 MHz.
- Digitised at 420-1200 dpi from the PDF. HBS1's IND 2 inductance lies under IND 2 XVSZ2's line and is read as 350 nH.
  XVSZ4's IND 1 curve at 2 MHz, D 0.15 is not readable: 0.32 is taken from its D 0.1 value (0.390) with HBS1's shape.

## 2. On the design point (N0, 2.5 MHz, 25 °C, chip, per 250 W module)

| core | units / phase (area) | per unit: DC / peak / half p-p | copper DC | core κ 1 / Murali large signal | efficiency κ 1 / large signal | 80 % needs M ≤ |
|---|---|---|---|---|---|---|
| HBS1, IND 2 | 118 (8.3 cm²) | 0.53 / 1.22 / 0.68 A | 9.3 W | 27.4 / 156.5 W | 79.9 / 56.5 % | 0.36 mΩ/nH |
| XVSZ2, IND 2 | 118 (8.3 cm²) | 0.53 / 1.22 / 0.68 A | 9.3 W | 25.8 / 177.3 W | 80.3 / 54.0 % | 0.36 |
| XVSZ3, IND 2 | 132 (9.2 cm²) | 0.47 / 1.09 / 0.60 A | 8.4 W | 31.7 / 159.2 W | 79.0 / 56.3 % | 0.38 |
| XVSZ4, IND 1 | 124 (6.8 cm²) | 0.50 / 1.16 / 0.64 A | 6.3 W | 32.3 / 146.2 W | 79.4 / 58.3 % | 0.40 |
| D85: HBS1 IND048, [10] data | 82 (1.2-4.2 cm²) | 1.6 / 3.5 / 1.9 A | 17.4 W | 34.5-44.1 / 106-136 W ([10] κ 3.07) | 74.0-76.2 / 58.2-62.6 % | 0.25 |

The D85 row uses the load's DC (D85 Section 8); its κ 1 band is [10]'s r_acx band (0.465-0.595 mΩ/nH).

## 3. What is extrapolated

- **Duty:** 0.075 against Murali's measured 0.15-0.5 (large signal), carried by the small-signal shape
  r_acx(0.075) / r_acx(0.15) = 1.36-1.43. Fig. 11's own rise from D 0.5 to 0.15 (× 1.46 for HBS1) follows the
  small-signal one (× 1.38) within 6 %. The design's 1.98 MHz needs no frequency step.
- **Ripple per unit:** ±0.60-0.68 A against the measured ±0.25 A (2.4-2.7 ×). [10] Table IV has κ rising with ripple
  (5 MHz), so the large-signal core here is more likely low than high. This is still closer to the measurement than
  D83's IND048 array, which runs ±1.9 A per unit.
- **DC per unit 0.47-0.53 A, peak 1.1-1.2 A:** inside Murali's tested 2.5 A DC bias (no saturation, Fig. 9).
- **Large signal for IND 1 only:** the per-nH metric is applied to IND 2 (HBS1, XVSZ2, XVSZ3) as a material property,
  which Murali shows for the small signal only.
- **Arrays:** 118-132 units in parallel per phase. Current sharing between units, the interconnect's resistance and
  the layout are not modelled. All at 25 °C; neither paper gives temperature data.

## 4. What it changes

- T30 and D83 Section 2 stand with a refinement. "The material fails" now holds for all four materials this group
  measured (HBS1 and Panasonic XVSZ2-4), not only for HBS1. The best measured option is XVSZ4 in IND 1, about 2 points
  above HBS1 on the same data.
- Murali's windings show the copper can be about halved (136-201 against 376 µΩ/nH), but only with several times the
  area. A design built on them is a packaging question (layers, area), not a controller one.
- The number that matters is the large-signal loss per nH at our duty and ripple, and no source measures it there.
  It is the one measurement to ask for: M at 2-2.5 MHz, D 0.075, about ±2 A per unit, 1.5-2 A DC.
