# D85 - the final design point's loss ledger, item by item

Script: `scripts/p24_loss_ledger.py` -> `diagnostics/D85_loss_ledger.json`. No new co-simulation. Written 2026-10-16
on the interview-prep session's request: the total looked stable, so look at each item first, then the sum.

Design point: the 2.5 MHz design (A124 / final configuration), nominal devices (N0), L0 = 2.93 nH, full load, per
250 W module. Every number names its source and conditions; "held" = no temperature law used.

## 1. The old numbers, reproduced bit for bit

- A124's middle budget (D62's terms on `A124 .../run_p125_n0.json`, L1 = 7.3333333e-9 / 2.5): 25.909 W, 90.61 %;
  every term equals `a124_summary.json` p125_n0.
- D83's efficiencies (D73's split + D83's copper + D83's core + D75 / D70's package): all 24 values equal
  `D83_hbs1_units.json` (84.01 % without core, 73.2-75.3 % at κ 1, 57.7-62.0 % at κ 3.074).
- The gate-level books (A206 `run_E_N0_steady_ls0p3.json`, recomputed with `a206_analyze.whole`) equal
  `a206_summary.json`.

## 2. The ledger (N0, W per module)

| item | 25 °C | 85 °C | source | conditions | how |
|---|---|---|---|---|---|
| conduction, high sides | 1.61 | 2.18 | A206 books | plant V6: EPC2067 vendor-model gates, 3.0 / 0.3 Ω high side, 0.3 Ω low sides, 50 pH loop with its damper, r_sw = 1.55 mΩ (datasheet max, 25 °C) / 2; last 10 µs settled | co-simulation waveforms; LTspice within 0.5-0.7 % (A206) |
| conduction, low sides | 14.04 | 18.97 | A206 books | as above, / 3; a low side also carries phase k+1's current during its on-time | same |
| edges, high sides | 2.44 | 2.44 | A206 books | channel edge energy at the final drive (36 / 72 A/ns) | same; held (D80: +0.41 W at 125 °C devices, +0.25 W at 85 °C, not summed) |
| edges, low sides | 1.41 | 1.41 | A206 books | reverse conduction while the low side's gate rises (0.3 Ω) | same; held |
| reverse conduction, dead time | 0.66 | 0.66 | A206 books | fitted reverse drop (A89) | same; held |
| gate drive | 3.35 | 3.35 | D62 formula | 20 devices x Q_G 17.1 nC (typ) x 5 V x 1.957 MHz (V6's period); 3.11 W if the low sides count Q_G − Q_GD (they turn on at zero voltage) | closed form; not in the books (driver) |
| series-capacitor ESR | 2.75 | 2.75 | D62 formula | A124's waveforms, ESR 1 mΩ per capacitor (assumed; P24 gives none) | closed form; held |
| loop damper, 50 pH | 1.81 | 1.81 | D80 (A145 harness) | the damper's ring energy at instantaneous turn-off: an upper bound | harness; held |
| inductor copper | 27.33 | 33.77 | D83 | IND048-HBS1, 2 x 41 per phase, R_DC x mean-square current ([10] Table II / VI); 34 % of it (9.4 W) is the ripple | closed form; x (1 + 0.393 %/K ΔT) |
| core, κ 1 / κ 3.074 | 34.5-44.1 / 106.0-135.6 | same | D83 | [10] Eq. (1), embedded r_acx band (Fig. 8: small signal, zero DC), κ from Table V | closed form; held (no temperature data) |
| package lateral copper | 1.25 (429 µm) / 6.24 (86 µm) | 1.55 / 7.71 | D75 | module over two P24 sites, 20 mm path | closed form; copper law |
| loop at 150 pH instead of 50 | +4.9 | +4.9 | D73 / D70 | 6.6 − 1.7 W (A145) | harness |

Not in the ledger: V7's r_core (15.5 W in its books; a damping resistor, D83 Section 3), output-capacitor ESR,
driver and controller quiescent power, Coss hysteresis, the core's temperature dependence.

Sum without core and package: 53.57 W at 25 °C, 65.52 W at 85 °C.

## 3. Each loss once: the overlaps checked

1. The budget's hard turn-on (0.66), turn-off overlap (0.28) and reverse conduction (0, A124's plant) are the same
   losses as the books' edges and reverse terms: replaced, not added (as D80 did with V5's 2.45 W).
2. The budget's conduction (13.17 W, one lumped resistance per phase) is replaced by the books' 15.65 W.
3. A205's +4.0 W (the low sides' zero-voltage turn-on through 0.3 Ω, missing from V5) is inside V6's books (V6 books
   20.15 W against V5's 15.75 W): not added.
4. A151 / A152's slow-turn-on edge increment (+0.12-0.36 W) is inside the books' high-side edges (V6 runs the final
   drive): not added.
5. D73's package loop at 50 pH (1.7 W = loop 1.6 + slow turn-on 0.1) is replaced by D80's damper (1.81 W): the edge
   part of the loop is already in the books (V6 has the 50 pH loop).
6. Copper against core: D83's copper counts the ripple at R_DC (9.4 W). [10]'s r_acx near 2 MHz (0.465-0.595 mΩ/nH)
   lies below R_DC / L of three of the six HBS1 windings (IND034 / 046 / 035: 0.69-0.76 mΩ/nH), so it cannot
   contain R_DC: read as the AC excess, no double count. [10] does not say so; this is an inference.
7. Gate drive is outside the books (driver supply): counted once.

## 4. Efficiency (P_out 250 W; κ band = r_acx band lo-hi)

| N0 | no core | κ 1 | κ 3.074 ([10] Table V) |
|---|---|---|---|
| 25 °C, chip (no package) | 82.35 % | 71.90-73.95 % | 56.92-61.04 % |
| 25 °C, 429 µm / 50 pH | 81.53 % | 71.27-73.29 % | 56.53-60.59 % |
| 25 °C, 86 µm / 150 pH | 78.98 % | 69.32-71.23 % | 55.29-59.17 % |
| 85 °C, chip | 79.24 % | 69.51-71.43 % | 55.41-59.31 % |
| 85 °C, 429 µm / 50 pH | 78.40 % | 68.87-70.75 % | 55.00-58.84 % |
| 85 °C, 86 µm / 150 pH | 75.77 % | 66.83-68.60 % | 53.70-57.35 % |

85 °C is an isothermal point at the DVPD threshold. D84 found no tested cooling that holds the module there, so a
real module runs hotter and lower. The 85 °C column applies only the D73 laws: conduction +0.586 %/K and copper
+0.393 %/K; everything else is held.

Other boards (their own L 0.75 L0, 2.58-2.60 MHz; semiconductor block only, the passives belong to their own L):
N75 at 25 °C: books 22.32 W, gate drive 4.41 W. S75 (slow devices, drive x 1.2) at 25 °C: books 31.91 W, gate
drive 4.44 W, i.e. **+12.9 W against N0's 23.50 W** (edges +9.6, reverse +1.4, conduction +0.8, gate +1.1). S0 (slow at
L0) has no gate-level books (A235's S0 runs log no edges); one steady run with the edge log would give it.

## 5. Old against new: where the items moved

| item (N0, 25 °C, W) | A124 budget | D83 | D85 |
|---|---|---|---|
| conduction | 13.17 | 13.17 | 15.65 |
| edges + reverse | 0.94 | 0.94 | 4.50 |
| gate drive | 3.38 | 3.38 | 3.35 |
| series-capacitor ESR | 2.75 | 2.75 | 2.75 |
| loop | (package 1.7) | (package 1.7) | damper 1.81 |
| inductor copper | 5.66 (HPE1 R/L) | 27.33 | 27.33 |
| **sum without core and package** | **25.91** | **47.57** | **53.57** |

- **No offset hides behind D83's total.** D83 kept A124's ideal-switch semiconductor block. The gate-level books
  raise conduction (+2.48 W) and edges plus reverse (+3.56 W); both rise and nothing falls. The no-core, no-package
  efficiency goes from 84.01 to 82.35 %.
- **Two places where the total moved little while items moved a lot:**
  - The loop: it leaves the package column (−1.7 W) and enters the die column (+1.81 W). Net +0.11 W, but the heat
    moves into the die layer (D80 already did this).
  - D80's 50 pH change: the loop fell by 5.2 W while the edges rose by 1.7 W, so the total moved only −3.5 W.
- **The rest rose item by item:**
  - V5 -> V6: conduction +2.33 W, low-side edges and reverse +2.07 W.
  - D72 -> D83: copper +8.8 W, core κ 1 7.5 -> 34.5-44.1 W.
  - 25 -> 85 °C: conduction +5.5 W, array copper +6.4 W (+0.3 W lateral at 429 µm).
  - N0 -> S75: every semiconductor item.
- A64 / A65 / A110's offsets were between candidate designs, not inside the final design's ledger.

## 6. What it changes
- The final design point at 25 °C (nominal, no package): 82.4 % without core, 71.9-74.0 % at κ 1, 56.9-61.0 % at
  [10]'s κ (D83: 84.0 / 73.2-75.3 / 57.7-62.0 %). The order of the items is unchanged: core, then inductor copper,
  then switch conduction, then edges. D83's conclusion stands: the material decides.
- D84's die-layer heat used D80's dies (V5 edges). The books add ~4.5 W at the dies (conduction +2.5 W, low-side
  edges + reverse +2.1 W). That is small against the inductor's 62-163 W; noted, not rerun.

## 7. Limits
- One operating point (full load). The 85 °C column comes from the D73 laws, with edges and core held. S75 / N75 are
  at 0.75 L0, and only their semiconductor block is reported.
- Assumed or unknown: Cs ESR (1 mΩ), core temperature dependence, r_acx's content (Section 3, item 6), output
  capacitor, quiescent power.
