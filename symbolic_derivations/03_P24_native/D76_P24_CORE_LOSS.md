# D76 - the inductor array's core loss (HBS1-class MPC): efficiency and the frequency choice

2026-10-07. D70 / D72 left core loss "not modelled"; D67 named it a limit of the 2.5 MHz choice. This note prices it
with the metric P24's own inductor source uses. Code: `src/scb_ivr/p24_core_loss.py`; `scripts/p24_core_loss.py` →
`diagnostics/D76_core_loss.json`; `tests/test_p24_core_loss.py`. No new co-simulation.

## 0. Answer

- **Core loss is a first-order term.** On the 2.5 MHz design record (measured 1.98 MHz at full load, ripple 45.9 A rms
  per phase) an HBS1-class core costs **7.5 W per module at small signal, 15-30 W at the large-signal factor κ 2-4**,
  against 18.6 W of array copper. The converter's 86.6-87.7 % (D72, 25 °C) becomes **84.4-85.4 % at κ 1, 78.4-79.3 %
  at κ 4**; at 85 °C 81.9-83.1 % / 76.3-77.3 %, with the package (D75) 78.2-82.2 % / 73.1-76.6 %.
- **2.5 MHz no longer wins on efficiency.** Core loss per phase is R_acx · L · I_ac², with R_acx ∝ f^1.55 and L ∝ 1/f,
  so it grows ∝ f^0.55 at the same ripple: 5 MHz now loses to 2.5 MHz by 1.4-4.5 points; 1 MHz and 2.5 MHz are within
  ~1 point, and which leads depends on how R_acx falls below 2 MHz (the data stop there): 1 MHz leads by 0-2.7 points
  if f^1.55 continues, 2.5 MHz by 0.3-0.8 if it bends to f^1. D72's 0.2-0.6-point lead was a copper-only result.
- **The 2.5 MHz design stays the co-simulated one** (controller frozen; 3 × the 1 MHz valley margin, D67), now without
  an efficiency argument over 1 MHz, which is P24's own frequency with this very material. A lower-loss core (κ R_acx
  well below HBS1's) restores the copper-only ranking.
- **Heat:** the core loss sits in glass 2, in the layer D74 found binding; D74 is rerun with it (κ 1 and 4).

## 1. Data and model

- **Metric.** R_acx = R_AC / L (mΩ/nH) for a triangular ripple of duty D at frequency f; below ~5 MHz it is a material
  property (Murali et al., ECTC 2022, Fig. 8, from Alvarez Barros et al.'s metric). The AC loss of an inductance L with
  ripple rms I_ac is κ R_acx L I_ac². For N parallel units of N L carrying I / N each the loss is the same: **the core
  loss of a phase does not depend on the unit count**, only on L, the ripple and the material.
- **HBS1 values.** The black (HBS1) curves of Fig. 8(e) (discrete toroid, small signal) digitised at D 0.03-0.1 from the
  page rendered at 500 dpi, axes calibrated on the gridlines (±0.02 mΩ/nH): at D 0.077, 0.301 / 0.886 / 2.557 mΩ/nH at
  2 / 4 / 8 MHz, i.e. f^1.50-1.55. The metric rises at small D (more harmonic content); our D is 0.070-0.076.
- **Large signal κ.** Alvarez Barros et al. (TCPMT 2021, P24's ref. [10], where HBS1 is characterised): "in the
  megahertz range, the large-signal losses can be over four times larger than the small-signal ones". κ = 1 is the
  floor, 4 that source's figure. Murali et al.'s own large-signal points (12-18 mW for HBS1 at ±0.25 A, 2 MHz, Fig. 11)
  would imply ~60 × the small-signal value; we could not reconcile them with Fig. 8 and do not use them (if they held,
  an HBS1-class core would be unusable at these ripple currents).
- **Waveforms.** Each design record's measured valley, peak, Ton and period (p24_loss_budget.measure); I_ac² =
  (peak − valley)² / 12 per phase; the frequency is the measured one, not the nominal name.

## 2. Results

| design (record) | f measured | D | R_acx (mΩ/nH) | I_ac rms per phase | tan δ equiv. | core loss per module, κ 1 / 2 / 4 |
|---|---|---|---|---|---|---|
| 5 MHz (A112 p20_n0) | 3.52 MHz | 0.070 | 0.768 | 51.2 A | 0.035 | 11.8 / 23.6 / 47.2 W |
| 2.5 MHz (A124 p125_n0) | 1.98 MHz | 0.075 | 0.302 | 45.9 A | 0.024 | 7.5 / 14.9 / 29.9 W |
| 1 MHz (A118 f6_n0) | 0.83 MHz | 0.076 | 0.077 (extrapolated) | 44.4 A | 0.015 | 4.5 / 8.9 / 17.9 W |

Converter efficiency at 25 °C (D72 arrays; no package):

| design, units per phase | copper | no core | κ 1 | κ 2 | κ 4 |
|---|---|---|---|---|---|
| 5 MHz, 31 / 40 | 15.2 / 12.8 W | 86.38 / 87.10 % | 83.00 / 83.66 % | 79.87 / 80.48 % | 74.27 / 74.80 % |
| 2.5 MHz, 29 / 40 | 18.6 / 15.0 W | 86.56 / 87.65 % | 84.38 / 85.42 % | 82.30 / 83.29 % | 78.44 / 79.34 % |
| 1 MHz, 29 / 40 | 24.5 / 19.8 W | 85.71 / 87.13 % | 84.41 / 85.79 % | 83.16 / 84.49 % | 80.75 / 82.01 % |
| 1 MHz, f^1 below 2 MHz | | | 83.62 / 84.97 % | 81.62 / 82.91 % | 77.91 / 79.09 % |

At 85 °C (D73's laws, switch conduction and all copper hot, core loss held constant), 2.5 MHz, N 29 / 40:

| κ | converter | + package 429 µm / 50 pH | + package 86 µm / 150 pH | R_th max per module (86 µm), 25 / 45 °C coolant |
|---|---|---|---|---|
| 0 | 83.9 / 85.2 % | 83.0 / 84.3 % | 80.1 / 81.3 % | 0.97-1.04 / 0.64-0.69 K/W |
| 1 | 81.9 / 83.1 % | 81.0 / 82.2 % | 78.2 / 79.3 % | 0.86-0.92 / 0.57-0.61 K/W |
| 4 | 76.3 / 77.3 % | 75.5 / 76.6 % | 73.1 / 74.1 % | 0.65-0.69 / 0.43-0.46 K/W |

## 3. Limits

- κ is bounded, not measured for our waveform; HBS1 units here carry 2.2 A DC and up to ~5 A peak (saturation ~5 A,
  P24), and DC bias raises the loss further. The core loss is held constant with temperature.
- Winding AC resistance (skin, proximity) is not added: the copper term stays the D72 DC value.
- Below 2 MHz the metric is extrapolated (1 MHz design); Fig. 8(e) is a discrete toroid, not the embedded spiral.

## 4. For Mihai

Which core does the IVR's inductor use at 1-2.5 MHz, and is its large-signal loss known at ~5 A per unit with a
~5 A peak-to-peak ripple? It now sets both the efficiency (2-8 points at 2.5 MHz) and the frequency choice.
