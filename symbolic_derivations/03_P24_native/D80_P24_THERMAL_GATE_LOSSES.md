# D80 - the thermal model with the final gate-level losses

Script: `scripts/p24_thermal_gate.py` -> `diagnostics/D80_thermal_gate.json`. Records: release records-a171.
Written 2026-10-08 after an external review. The review found that the thermal model (D74 / D77) still took its die
losses from D73 and its loop at 150 pH, not from the final gate-level plant (A171 / A172, 50 pH).

## 1. What replaces what

| D74 / D77 input | from | D80 replaces it with |
|---|---|---|
| high-side die switching | D62 ideal edges: hard turn-on at the energy-balance minimum + turn-off overlap at t_f 0.75 ns (0.94 W per module with reverse conduction) | each switch's channel edge + reverse-conduction energy in the final plant (record `edge_energy_j` / `rev_energy_j`, steady 600-950 µs, A171 S50 l_p48_1us); per die = switch / devices (2 high, 3 low) |
| loop | D70: A145's edge-power increase + damper; 6.6 W at 150 pH, 1.7 W at 50 pH | the damper only, 1.81 W at 50 pH (A145 harness at instantaneous turn-off, an upper bound for the ≤ 0.3 Ω sink). The edge part is in the channel energy now, so it is not counted twice |
| gate drive, conduction, inductor copper, core (D76), caps, lateral copper (86 µm, D75) | D73 / D74 | unchanged; the gate power stays wholly in the die layer (includes R_G's share) |

Edge + reverse power per module (W): nominal 2.45, 125 °C 2.86, slow corner 4.57. Per high-side switch
0.60-0.65 / 0.70-0.75 / 1.12-1.19 W; low sides ≤ 0.001 W (ZVS turn-on, strong-sink turn-off).

## 2. Results

h 2·10⁴ W/m²K, κ 1, no vias, 25 °C coolant (D74's headline). f* = the via fill for 85 °C at h 2·10⁴, by the same
linear interpolation for every variant (D74's `f_star_interp`; its refined values are ~10-20 % lower). Flow =
cu_100_400 cooler, 2 % fill (D77).

| variant | loss / dies (W) | T_max (°C) | junction | f* κ1 25 / 45 °C, κ4 25 °C | flow g/s κ1 25 / 45 °C, κ4 25 °C |
|---|---|---|---|---|---|
| published (150 pH, D73 dies) | 65.7 / 15.4 | 96.6 | 42.9 | 0.16 / 1.51 / 1.66 % | 0.44 / 1.12 / 1.15 |
| loop at 50 pH | 60.5 / 15.3 | 94.9 | 41.8 | 0.13 / 1.13 / 1.43 % | 0.40 / 0.97 / 1.02 |
| + gate-level edges, nominal | 62.2 / 16.8 | 95.3 | 42.0 | 0.14 / 1.22 / 1.48 % | 0.41 / 1.00 / 1.06 |
| + gate-level edges, 125 °C devices | 62.6 / 17.2 | 95.4 | 42.1 | 0.14 / 1.24 / 1.49 % | 0.41 / 1.01 / 1.07 |
| + gate-level edges, slow corner | 64.4 / 19.0 | 95.9 | 42.3 | 0.15 / 1.33 / 1.54 % | 0.43 / 1.06 / 1.10 |

κ 4 at 45 °C fails at h 2·10⁴ in every variant, as in D74. The energy balance closes to 8·10⁻⁹.

## 3. What it changes

- **The thermal conclusions stand for the final spec, and the published numbers are conservative.** The gate-level
  edges add 1.4-3.6 W per module at the dies, which sit ~53 K below the inductor hot spot: +0.4 to +1.0 K at
  T_max. The 50 pH loop removes 4.9 W of loop loss against the 150 pH case the published runs used (5.2 W with the
  temperature feedback): −1.7 K. Net: T_max −0.7 to −1.3 K, fill for 85 °C −6 to −19 %, coolant flow −3 to −11 %.
- **Efficiency.** Against D73 at 50 pH the module loses 1.7 W more at nominal devices (0.7 point at 250 W), 2.1 W at
  125 °C devices, 3.9 W at the slow corner (1.6 points). The summary's "about 0.5 point" is ~0.7 point at nominal devices
  and up to 1.6 at the slow corner.

## 4. Limits

- The edge loss is held constant in temperature; the 125 °C-device variant bounds its own rise.
- The edges come from single-module runs. Four modules give the same per module (A172: 2.44-2.46 W).
- The damper heats the lower ABF copper over the columns (D74's placement); where a real damper heats is open (D70 2.4).
