# D77 - a microchannel coolant in place of h: flow, pressure and the coolant's own temperature rise

2026-10-07. D74 cooled the spreader face with a uniform heat transfer coefficient. This note puts the team's cooler
behind it (substrate-embedded parallel microchannels next to the GaN layer, Choi et al. 2025; 1.6 g/s for a 1 kW DVPD
in Krishnakumar et al. 2026) and lets the coolant heat up along the channels. Code: `src/scb_ivr/p24_microchannel.py`,
`p24_thermal.coupled(coolant=...)`; `scripts/p24_coolant.py` → `diagnostics/D77_coolant.json`;
`tests/test_p24_microchannel.py`.

## 0. Answer

- **With channels in, the coolant's own temperature rise sets the flow; h matters only at the margin.** Copper channels
  of 50-200 µm give an effective h of 3.8·10⁴-2.6·10⁵ W/(m²K) on the face, yet the minimum flow at a 25 °C inlet moves
  only from 0.42 to 0.50 g/s between them (κ 1): ~63 W per module heat the coolant by 39 K at 0.4 g/s, 16 K at 1 g/s.
  At a 45 °C inlet, where the margin is thin, the cooler counts more (0.97-1.66 g/s).
- **Minimum flow per module (with its half of the strip, a quarter of the package) for 85 °C,** baseline channels
  (Cu 100 / 400 µm, walls 100 µm), glass-1 fill 2 %: **κ 1: 0.44 g/s at a 25 °C inlet, 1.12 g/s at 45 °C;**
  **κ 4: 1.15 g/s at 25 °C; at 45 °C not reached within 4 g/s** (19.6 % fill: 2.3 g/s). For the package ×4: κ 1 1.8 /
  4.5 g/s. The framework's 1.6 g/s for the whole system is the edge for this IVR: 88 °C at κ 1 with a 25 °C inlet.
- **Pumping is free:** 7.5 kPa and 7.6 mW per module at 1 g/s, 30 kPa and 0.12 W at 4 g/s (laminar, Re 40-400), so
  the package needs < 0.5 W, as the team reported (< 0.1 % of the load). The flow, not the pressure, is the requirement.
- **A cold plate through a TIM** (0.05 K·cm²/W) instead of channels in the spreader costs 5-13 % more flow at κ 1;
  silicon instead of copper walls 2-3 %.

## 1. Model

- **Cooler** (fully developed laminar flow; Shah and London 1978): Nu_H1 and f Re as polynomials in the aspect ratio
  (limits 8.235 / 3.61 and 24 / 14.23 reproduced); walls as straight fins (adiabatic tip); h_eff = h_ch (w_c + 2ηH) /
  (w_c + w_w) per footprint; Δp = 2 (f Re) μ u L / D_h²; water at ~40 °C. Channels along the 20 mm columns. The Graetz
  number x* = 0.04-1.9 (mostly developed; entry enhancement left out, conservative).
- **Coupling.** The module's full length (D74's stack, no mirror plane); each column of face cells is a channel group
  with m_dot dx / width; the fluid temperatures join the linear system (first-order upwind, m cp ΔT_f = G (T_w − T_f) per
  cell), solved by GMRES with the solid's z-line solve and an exact downstream sweep as preconditioner; the electrothermal
  loop (per-die, per-column losses, D75 / D76 terms) iterates around it. An explicit fluid update diverged at NTU ~ 40
  (50 µm channels, 0.4 g/s) and was replaced.

## 2. Checks

| check | result |
|---|---|
| Shah-London limits (parallel plates / square) | Nu 8.235 / 3.610, f Re 24.00 / 14.23 |
| 2D finite-volume fin vs tanh(mH) / mH | −0.08 % |
| full module = half module (uniform h); coolant at m_dot → ∞ = uniform h | 48.8710 / 48.8710 / 48.8710 °C |
| coolant energy balance (all 200 runs) | ≤ 8·10⁻⁹ |
| cells along the flow halved (0.25 → 0.125 mm), 1 g/s | 64.14 → 64.09 °C |

## 3. Results (hottest point, °C, at 0.4 / 0.6 / 1 / 2 / 4 g/s per module; fill 2 %)

| cooler (h on the face) | κ 1, 25 °C inlet | κ 1, 45 °C | κ 4, 25 °C | κ 4, 45 °C |
|---|---|---|---|---|
| Cu 100 / 400 µm (9.0·10⁴) | 88 / 75 / 64 / 56 / 53 | 112 / 98 / 86 / 78 / 74 | 121 / 102 / 87 / 76 / 71 | 145 / 125 / 109 / 98 / 93 |
| Cu 50 / 300 µm (2.6·10⁵) | 87 / 73 / 62 / 54 / 50 | 110 / 96 / 84 / 76 / 72 | 119 / 100 / 85 / 73 / 68 | 142 / 122 / 107 / 95 / 89 |
| Cu 200 / 500 µm (3.8·10⁴) | 92 / 79 / 68 / 61 / 57 | 116 / 102 / 91 / 83 / 79 | 126 / 108 / 93 / 83 / 77 | 150 / 131 / 116 / 105 / 99 |
| Si 100 / 400 µm (8.4·10⁴) | 89 / 75 / 64 / 57 / 53 | 112 / 98 / 87 / 78 / 74 | 121 / 102 / 88 / 77 / 71 | 145 / 125 / 110 / 99 / 93 |
| Cu 100 / 400 + TIM (6.2·10⁴) | 90 / 76 / 66 / 58 / 54 | 113 / 99 / 88 / 80 / 76 | 123 / 104 / 89 / 78 / 73 | 147 / 127 / 111 / 100 / 95 |

Minimum flow per module for 85 °C (g/s), fill 2 % | 19.6 %:

| cooler | κ 1, 25 °C | κ 1, 45 °C | κ 4, 25 °C | κ 4, 45 °C |
|---|---|---|---|---|
| Cu 100 / 400 | 0.44 \| ≤ 0.40 | 1.12 \| 0.78 | 1.15 \| 0.73 | none \| 2.28 |
| Cu 50 / 300 | 0.42 \| ≤ 0.40 | 0.97 \| 0.72 | 0.98 \| 0.67 | none \| 1.78 |
| Cu 200 / 500 | 0.50 \| 0.41 | 1.66 \| 0.95 | 1.70 \| 0.88 | none \| none |
| Si 100 / 400 | 0.45 \| ≤ 0.40 | 1.15 \| 0.79 | 1.18 \| 0.73 | none \| 2.38 |
| Cu 100 / 400 + TIM | 0.46 \| ≤ 0.40 | 1.27 \| 0.83 | 1.31 \| 0.77 | none \| 2.97 |

Coolant outlet (mean) at 0.4 / 1 / 4 g/s: 64 / 40 / 29 °C from a 25 °C inlet (κ 1); 102 / 67 / 50 °C from 45 °C (κ 4).

## 4. What follows

- **Cooling requirement for the IVR, per 250 W module:** substrate or spreader microchannels (any of these copper
  geometries) at ≥ ~0.5 g/s with a 25 °C inlet, ≥ ~1.1 g/s at 45 °C (κ 1, 2 % glass-1 fill); at κ 4 ≥ ~1.2 g/s at
  25 °C and a warm inlet only with the full 19.6 % fill. For four modules: 2-5 g/s, ~0.1-0.5 W of pumping.
- **The coolant temperature, not the cooler, is the lever:** inlet temperature and flow rate. A 45 °C inlet (typical
  warm-water cooling) needs 2.5 × the flow of a 25 °C one at κ 1.
- D74's uniform-h answers hold with h ≈ 6·10⁴-2.6·10⁵ plus the coolant rise added on top.

## 5. Limits

Fully developed laminar correlations (entry enhancement and flow maldistribution between channels not modelled), the
four-wall Nu_H1 (the lid side of a real channel is less effective: a few per cent of h, which matters little here),
constant water properties, no manifold pressure loss. The processor face is adiabatic (D78 opens it).
