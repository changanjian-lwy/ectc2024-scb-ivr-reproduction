# D78 - the IVR's processor-side face: a heat source or a second path

2026-10-07. D74 kept the face above glass 2 adiabatic. In P24 Fig. 6 the IVR sits on the back of the processor
package, under the processor; that face is joined through the package substrate to whatever temperature the processor's
own cooling holds. Script: `scripts/p24_processor_side.py` → `diagnostics/D78_processor_side.json` (D74's model).

## 1. Model

Top face: h_top = 1 / R''_sub to T_proc. R''_sub = 12 / 3.3 / 1.2 K·cm²/W (a ~1.2 mm substrate with through-plane
conductivity ~1 / 3.6 / 10 W/(m K), from bare laminate to dense power vias); T_proc = 45 / 65 / 85 / 95 °C (a cool to a
hot processor). Bottom: h on the spreader, 2·10⁴ or 9·10⁴ (D77's copper microchannels), coolant 25 / 45 °C. Losses as
D74 (D75 lateral copper 86 µm, D76 core loss κ 1 / 4), glass-1 fill 2 %. 104 solves, energy balance ≤ 2·10⁻¹¹.

## 2. Results (hottest point, °C; heat through the top face, + out of the IVR)

| case (κ, h_bot, coolant) | adiabatic top: T_max (top face) | R'' 1.2, T_proc 45 / 65 / 85 / 95 °C | warmest T_proc for 85 °C (R'' 12 / 3.3 / 1.2) |
|---|---|---|---|
| κ 1, 2·10⁴, 25 °C | 60.8 (55.9) | 51.4 / 64.2 / 78.4 / 85.5 (+6.7 … −27.1 W) | all / all / 94 |
| κ 1, 2·10⁴, 45 °C | 82.9 (77.7) | 62.1 / 72.2 / 84.9 / 92.0 (+21.4 … −12.4 W) | 93 / 87 / 85 |
| κ 1, 9·10⁴, 25 °C | 48.9 (45.0) | 46.9 / 59.9 / 73.3 / 79.9 (−0.6 … −39.3 W) | all / all / all |
| κ 1, 9·10⁴, 45 °C | 70.2 (66.1) | 57.1 / 67.4 / 80.4 / 87.1 (+15.7 … −23.0 W) | all / all / 92 |
| κ 4, 2·10⁴, 25 °C | 82.5 (73.6) | 60.1 / 71.8 / 84.9 / 92.0 (+18.2 … −15.6 W) | 94 / 87 / 85 |
| κ 4, 2·10⁴, 45 °C | **104.5 (95.4)** | 70.8 / 81.0 / 92.6 / 99.0 (+32.9 … −0.9 W) | none / 55 / 72 |
| κ 4, 9·10⁴, 25 °C | 65.8 (58.5) | 54.0 / 65.8 / 79.0 / 85.6 (+9.3 … −29.4 W) | all / all / 94 |
| κ 4, 9·10⁴, 45 °C | **87.1 (79.6)** | 64.6 / 74.6 / 86.3 / 92.8 (+25.6 … −13.1 W) | 72 / 81 / 83 |

("all": 85 °C holds up to 95 °C; "none": not even at 45 °C.)

## 3. What follows

- **The processor side is a second path when it is cooler than the IVR's own top face, and a source when warmer.** The
  crossover is the adiabatic top-face temperature (45-95 °C here). The link matters in proportion to 1 / R''_sub: with
  dense power vias (1.2 K·cm²/W) up to ~33 W per module leaves upwards or ~39 W comes in; through bare laminate
  (12 K·cm²/W) a few watts either way.
- **At κ 1 the processor side does not bind:** with h ≥ 2·10⁴ the module holds 85 °C for any processor-side temperature
  up to 85-95 °C. **At κ 4 with a 45 °C coolant it decides:** the adiabatic module is over 85 °C, and only a processor
  side at ≤ 55-83 °C (by R'' and h) brings it back.
- **Interface requirement:** the processor-side temperature under the IVR should stay ≲ 85 °C, and the heat the IVR
  passes up (up to ~130 W for four modules at the cool end) belongs in the processor cooler's budget.

## 4. Limits

The processor side is a fixed temperature behind a uniform resistance; the processor's own heat map, the substrate's
lateral spreading and the coupling of both coolers are not modelled. R''_sub and T_proc are scenarios (P24 gives neither).
