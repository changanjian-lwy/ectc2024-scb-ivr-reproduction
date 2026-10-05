# D65 - P24's package layer: copper, via and loop parasitics from first principles

2026-10-05. Method: math. Code: `src/scb_ivr/p24_package_parasitics.py`. Map: `scripts/p24_package_budget.py` →
`diagnostics/D65_package_budget.json`. Tests: `tests/test_p24_package_parasitics.py`.
Geometry: `paper_locked/02_ectc2024_main/P24_FIG5_FIG6_PACKAGE_TRANSCRIPTION.md` (Figs. 5-6).

## 1. Why
- First step of the package layer (user decision 2026-10-05, after C13 froze both controller levels). P24 names the
  open item itself: "the interconnection losses of copper and via inside the package".
- Decision it changes: which parasitic enters the co-simulation plant first, and over what range. Cheapest model first:
  closed forms with the converter's own waveforms; no plant change.

## 2. Inputs
- Currents: A143's four-module steady record (master, last 50 us): T 505.5 ns, Ton 37.8 ns, peak 143 A, valley
  -16.0 A, resonant interval 10.7 ns, rails 11.9-12.3 V. SCB branches: phase rms 77.9 A (dc 62.6), high side 22.6,
  low side 84.7 (74.5 on phase 4: QLk also returns phase k+1's Ton current), Cs 32.0, input 22.6 A rms.
- Fig. 5 layout: 10 mm module, four 2.5 mm phase columns, L1 next to the central Vo / GND strip; inductor outputs
  and low-side sources reach the strip laterally in the ABF build-up.
- Scenarios (none printed by P24): copper 35-400 um per stack, Cu 17 nOhm m (VPD framework, Table III); via arrays at
  pitch 2 d (R x A = 5.1 rho h, independent of d; matches Table III's TSV within 3 %); glass 0.3 / 0.5 mm; Cs ESR
  0.2-2 mOhm; commutation loop 25-500 pH (published embedded-GaN power loops: 0.23-0.32 nH PCB-embedded, 1.03 nH DBC).
- Reference: 250 W module, measured 90.61 % -> 25.9 W loss; EPC2067 rating 40 V.

## 3. Results
| path | scenario | loss per module |
|---|---|---|
| lateral Vo + GND | 35 / 105 / 210 / 400 um Cu | 30.7 / 10.3 / 5.1 / 2.7 W (12.3 / 4.1 / 2.0 / 1.1 %) |
| switch-node vias (4 phases) | 0.5-5 mm^2, glass 0.3-0.5 mm | 0.13-2.1 W |
| central strip vias (Vo + GND) | 12 mm^2 each, 0.5-1 mm | 0.45-0.91 W |
| Cs ESR (3 Cs) | 0.2 / 0.5 / 1 / 2 mOhm | 0.6 / 1.5 / 3.1 / 6.2 W |

1. **The lateral output and ground copper dominates.** Fig. 5 brings every phase sideways to one central strip, so
   the inner segment carries the module's 250 A. 1 / 2 / 5 % of Pout needs 429 / 215 / 86 um of copper per stack
   (Vo and GND each). One 35 um layer costs more than the whole converter (118 % of 25.9 W). Vias, strip and Cs ESR
   (at <= 0.5 mOhm) stay below ~1 % together. A vertical output (Vo / GND straight up from each phase column) or
   thick copper is the package requirement; this needs no co-simulation.
2. **The commutation loop limits the high-side voltage.** Energy bound (instantaneous turn-off, 0.5 L I^2 into the
   turning-off switch's nonlinear Coss above its rail):

| turn-off | allowed loop for <= 40 V / <= 32 V |
|---|---|
| high side, steady 143 A at 12.3 V | 141 / 91 pH |
| high side, 200 A spec limit | 72 / 46 pH |
| high side, C13's 260 A falling ramp at 16.4 V | 37 / 22 pH |
| low side, C13's +173 A positive valley | 127 / 75 pH |

   The published embedded-GaN loops (230-320 pH) exceed every row. The bound is pessimistic (a finite turn-off
   lets part of the energy return), so the loop is the parasitic that needs the plant.

## 4. Decision
- Next experiment: the commutation-loop inductance in the co-simulation plant (one parasitic: a series L in each
  phase's switching loop, instantaneous switching first, so the plant must reproduce this bound), swept 25-300 pH on
  the frozen design. It answers what the bound cannot: the real V_DS overshoot and ringing, and whether the
  controller's V_DS comparators (valley detection, czh / czl) and timing survive the ringing.
- Copper: reported as a P24 layout requirement; enters the loss budget, not the plant (DC drop is inside the
  voltage loop if Vo is sensed at the strip).
- For Mihai (real values decide these numbers): the copper thickness and layer count of the ABF build-ups; whether
  Vo / GND leave each module laterally (Fig. 5) or vertically; the placement of a module's QH and QL dies and the
  expected loop inductance in the glass stack; the series-capacitor technology and its ESR.

## 5. Limits
- Lateral copper: DC resistance; the ripple share is included in the rms but skin / proximity effects (skin depth
  41 um at 2.5 MHz) are not, so thick-copper numbers are optimistic for the ripple part.
- Waveforms are piecewise linear from one steady record; transients only enter the loop rows.
- Loop bound: no damping, no finite di/dt, no Cs / Cin ESL split; geometry of the loop itself not modelled.
