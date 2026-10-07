# D75 - the module footprint: a 250 W module takes two of P24's sites

2026-10-07. Found while building D74's thermal model. Script: `scripts/p24_footprint.py` →
`diagnostics/D75_footprint.json` (no new runs; D65's currents, D73's converter losses).

## 1. The dies do not fit one site

| | dies per module | die area | site | package (25 × 40 mm) |
|---|---|---|---|---|
| this work: 4 × 250 W, QH 2 / QL 3 per phase | 20 EPC2067 | 185 mm² | 100 mm² | 80 dies, 74 % covered |
| P24 Fig. 5: 8 × 125 W, QH 1 / QL 2 per phase | 12 | 111 mm² | 100 mm² | 96 dies, 89 % covered |

EPC2067 is 2.85 × 3.25 mm (datasheet). Neither layout fits its dies flat under a 10 × 10 mm module; P24 prints no die
placement. The package as a whole holds them. **Here a 250 W module takes two sites, 10 × 20 mm, with the phase
columns 20 mm long along the central strip** (die cover 93 %): four modules on P24's eight sites, 1.25 A/mm² (P24's own
density). D73's "2.5 A/mm²" and its per-cm² reading assumed 1 cm² modules, which cannot hold the dies.

## 2. What changes

- **Lateral Vo + GND copper (D65, D70).** Its resistance scales as 1 / (thickness × depth); D65 used a 10 mm deep
  module. At 20 mm the loss halves:

| copper per stack | loss, 10 mm (D65) | loss, 20 mm | one-way drop at 250 A |
|---|---|---|---|
| 86 µm | 12.5 W | 6.2 W | 2.5 % |
| 215 µm | 5.0 W | 2.5 W | 1.0 % |
| 429 µm | 2.5 W | 1.25 W | 0.5 % |

  D70's validity condition for the one-way estimate (drop ≲ 2 %) moves from ≳ 215 µm to ≳ 107 µm of copper.
- **Package-inclusive efficiency at 25 °C, no core loss** (D72 arrays, N = 29 / 40; loop 1.7 / 6.6 W at 50 / 150 pH):

| | converter | 429 µm, 50 pH | 429 µm, 150 pH | 86 µm, 50 pH | 86 µm, 150 pH |
|---|---|---|---|---|---|
| 10 mm (D70 / D72) | 86.6-87.7 % | 85.3-86.4 % | 83.9-84.9 % | 82.5-83.5 % | 81.2-82.2 % |
| **20 mm** | 86.6-87.7 % | **85.7-86.8 %** | 84.3-85.3 % | 84.2-85.3 % | **82.9-83.9 %** |

  "Package-inclusive ~81-86 %" becomes **~83-87 %** before core loss (D76 adds it).
- **Output path (D71).** The lateral Vo path's inductance also scales as 1 / width: Fig. 5's 63-628 pH per module
  becomes ~32-314 pH, and the load-side drop L/4 · di/dt halves with it (not recomputed; D71's requirements stand, with
  more margin).
- **Thermal (D73, D74).** D73's requirement per module in K/W is unchanged; per area it doubles (a 2 cm² module may
  have 1.6-2.0 K·cm²/W where D73 read 0.8-1.0). D74 is built on this footprint.
- **Not changed:** the commutation loop (inside a phase column), the controller, the co-simulations.

## 3. For Mihai

How do P24's 12 EPC2067 (111 mm²) sit under a 10 × 10 mm module: dies under the strip, on both faces, or a larger site?
