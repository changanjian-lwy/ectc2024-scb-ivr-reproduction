# D87 - an air-core parallel-plate inductor for the three designs

Script: `scripts/p24_air_core.py` -> `diagnostics/D87_air_core.json`. No co-simulation. Written 2026-10-22 after D86
showed that no measured magnetic core fixes the core loss. D64 (2026-10-03) had already modelled an air-core
stripline, but with the ideal-switch losses and the ripple at its fundamental only. Here the semiconductor block is
tied to the gate-level books, the ripple's harmonics are summed with their own skin depths, and the result is compared
with D85 / D86's magnetic cores.

## 0. Result

- **Which air-core inductor: one single-turn parallel-plate (stripline) loop per phase.** P24 Table 2's air-core
  entries are 1.2-2.5 nH, 0.6-8 A units for 90-140 MHz, with 4.8-16 mΩ/nH, i.e. 13-43 × [10]'s IND048. A phase
  of 62.5 A DC and 150 A peak would need hundreds of them, and over 200 W of copper. The parallel plate is the one
  form that carries tens of amperes at a few nH and keeps its field between the plates. Its loss depends on two
  numbers only: the gap h and the copper thickness t.
- **The gap decides.** DC: R/L = 2ρ/(μ0 h t); ripple: R/L = 2ρ/(μ0 h δ) per harmonic. Copper thicker than about three
  skin depths (δ = 42 µm at 2 MHz) helps only the DC part. The ripple's AC copper dominates, from the same 154-177 A
  peak-to-peak ripple that drives the magnetic cores' loss.
- **80 % needs a gap of about 0.6 mm (300 µm copper) or 0.75-0.8 mm (105 µm).** The 2.5 MHz design and the 5 MHz design
  (3.52 MHz in its record) need the same gap, but the 5 MHz one needs half the plate area: 0.18-0.22 against
  0.35-0.47 cm² per phase. The 1 MHz design needs 0.94-1.43 mm and 1.4-2.1 cm².
- **Against the magnetic cores:** with a 1 mm gap and 300 µm copper, the 2.5 MHz design reaches 83.9 % and the 5 MHz
  design 82.9-84.2 %. The best measured core is 54-62 % on large-signal data (D85 HBS1 IND048 58.2-62.5 %, D86 XVSZ4
  58.3 %). Only κ 1, a lower bound that no measurement supports, reaches 74-80 %.
- **Within P24's own column (0.25 cm² per phase) the 5 MHz design wins:** 81.4-82.7 % (gap 0.75 mm) against 75.7 % for
  2.5 MHz, whose gap the area limits to 0.43 mm.
- **The 2.5 MHz design keeps its controller.** The phase L stays 2.93 nH, so A124's controller and every co-simulation
  carry over; only the plant loses its core. The 5 MHz design would need its controller rebuilt on the final
  configuration, as A124 did for 2.5 MHz.

## 1. Model (D64's, extended)

- Per phase: plates of width w and length l, copper t, gap h. L = μ0 l h / w. At the design's L the smallest plate area
  is at w = 5 h (D64's fringing limit): A = 25 L h / μ0.
- DC: 4 × 62.5² × 2ρ L / (μ0 h t), with the load's 62.5 A per phase. Ripple: the record's triangle (rise D, fall 1 − D,
  D83's per-phase ΔI) as harmonics a_n = ΔI |sin(π n D)| / (π² n² D (1 − D)), n ≤ 400 (an FFT agrees within 3e-8).
  Each flows within δ_n = √(ρ / (π n f μ0)): R_n = 2ρ L / (μ0 h min(t, δ_n)).
- Semiconductor block (N0, chip, 25 °C): D83's ideal-switch budget of each record plus the gate-level excess measured
  at 2.5 MHz (D85 26.25 W against D83 20.24 W, +6.0 W). Only 2.5 MHz has gate-level books, so the excess is taken
  either constant or ∝ f, which gives a band: 30.2-34.9 W at 3.52 MHz, 19.7-23.2 W at 0.83 MHz. The 80 % gaps use
  the higher end.

## 2. Numbers (per 250 W module)

| design (record f, L) | gap / copper | plate area per phase | copper DC + AC | efficiency |
|---|---|---|---|---|
| 5 MHz (3.52 MHz, 1.47 nH) | 0.5 mm / 105 µm | 0.15 cm² | 11.9 + 29.1 W | 76.7-77.8 % |
| | 1 mm / 300 µm | 0.29 cm² | 2.1 + 14.5 W | 82.9-84.2 % |
| | 2 mm / 300 µm | 0.58 cm² | 1.0 + 7.3 W | 85.3-86.7 % |
| 2.5 MHz (1.98 MHz, 2.93 nH) | 0.5 mm / 105 µm | 0.29 cm² | 23.9 + 34.8 W | 74.6 % |
| | 1 mm / 300 µm | 0.58 cm² | 4.2 + 17.4 W | 83.9 % |
| | 2 mm / 300 µm | 1.17 cm² | 2.1 + 8.7 W | 87.1 % |
| 1 MHz (0.83 MHz, 7.33 nH) | 1 mm / 300 µm | 1.46 cm² | 10.5 + 26.3 W | 80.7-81.6 % |

Gap for 80 % (higher semiconductor estimate): 5 MHz 0.60 / 0.74 / 1.18 mm, 2.5 MHz 0.60 / 0.81 / 1.56 mm, 1 MHz
0.94 / 1.43 / 3.44 mm, for 300 / 105 / 35 µm copper.

## 3. What is not covered

- **No source has built this.** P24 Table 2 lists no package air-core inductor at tens of amperes and a few MHz; its
  one stripline ([18]) has a composite core, 3 nH / 12 mΩ at 100 MHz. The R/L here (91 µΩ/nH DC at 1 mm / 300 µm)
  is 50-180 × lower than those units', from a far larger copper and gap cross-section. That is plausible physics,
  but it is unbuilt.
- **The package's gap and copper are unknown.** Built in P24's glass package, the plates would be the copper on the
  two sides of a glass core, closed by through-glass vias, so the gap is the glass thickness. P24 gives neither the
  thickness nor the copper (Figs. 5-6). The via resistance, fringing, current crowding at the plate edges and coupling
  between neighbouring phases are not modelled, so the AC loss is a lower bound (D64).
- **Light load loses its damping.** V7's r_core models the core's damping of an idle phase's ring, and A220 / A221
  showed the skipping mode needs it: V6, without it, left the ring undecayed and the valleys out of band. An air core
  damps only through its copper. So the 2.5 MHz light-load results would need rechecking.
- **The semiconductor block off 2.5 MHz is an estimate.** At 3.52 MHz the band is 4.7 W wide (about 1.3 points), and
  the 5 MHz design's valley target (20 %) and controller come from A112's older configuration.

## 4. What it changes

- T30's open item has a candidate outside the material: an air-core parallel plate with a gap of at least about
  0.6-0.8 mm reaches 80 %+ on the 2.5 MHz design with the current controller. Within P24's 0.25 cm² per phase, the
  5 MHz design is the better host.
- The deciding numbers are package facts: the glass or substrate thickness available as a gap, and the plateable
  copper. They are worth asking Mihai for, alongside the large-signal core measurement D86 asks for.
