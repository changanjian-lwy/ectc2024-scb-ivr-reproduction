# D71 - the module-to-load output path: does it need the plant?

2026-10-07. D70 named the per-module output path (R and L) as the next element for the dynamic plant. This note decides
from first principles whether it changes any conclusion, before any plant change. Inputs: P24 Fig. 5 (LOCKED: 10 mm
modules beside a central Vo / GND strip; the inductor outputs run in an ABF layer between the two glass substrates to
the central vias), D65 / D70 (lateral copper R), the plant (Co 4.672 mF per module, Vo sensed at the joined node).
MISSING in P24 and taken as scenarios: glass thickness, copper thickness, output-capacitor placement, the processor-side
connection and its decoupling.

## 1. The path inductance

A Vo layer over the GND layer, width w ≈ 10 mm (a module), lateral length l ≈ 5-10 mm (module to strip), separation
d ≈ 0.1-0.5 mm (glass 1 / ABF, MISSING): L = μ0 d l / w = **63-628 pH per module** (63 / 126 / 314 / 628 pH for
d, l = 0.1, 5 / 0.1, 10 / 0.5, 5 / 0.5, 10 mm). The path resistance is D70's 0.04-0.49 mΩ (429-35 µm). Vias and the
processor side are not included.

## 2. Two kinds of motion

**Differential (module against module).** Two module capacitors C ring through two paths: f = 1 / (2π√(L C)),
Q = √(L/C) / R:

| L per path | f | Z0 = √(L/C) | Q at R 0.04 / 0.2 / 0.49 mΩ |
|---|---|---|---|
| 63 pH | 294 kHz | 116 µΩ | 2.9 / 0.6 / 0.2 |
| 126 pH | 208 kHz | 164 µΩ | 4.1 / 0.8 / 0.3 |
| 314 pH | 131 kHz | 259 µΩ | 6.5 / 1.3 / 0.5 |
| 628 pH | 93 kHz | 367 µΩ | 9.2 / 1.8 / 0.7 |

With a common Ton every module is close to a current source (D58), so only a current difference between modules drives
this motion. A ±5 % inductor spread gives ~5 % of a 62.5 A step, ~3 A, i.e. Z0 × 3 A = 0.35-1.1 mV of ringing; the
16-phase switching ripple (~8 MHz per module) stays in each module's own capacitor (Z_C 4 µΩ against Z_L 3-32 mΩ).
A loop sensing the common node does not see the symmetric part. **Negligible: no plant change for it.**

**Common (all modules against the load).** If the output capacitance sits at the modules, the load sits behind the
four paths in parallel, L/4 = 16-157 pH. A load slew of di/dt drops L/4 · di/dt at the load before the module
capacitors can respond: 4-39 mV at 250 A/µs, 16-157 mV at 1 kA/µs (up to 16 % of Vo). This is faster than any 100 kHz
loop; the controller cannot remove it. To stay within 1 % (10 mV) a 250 A step needs ≥ 0.4-4 µs (L/4 · ΔI / ΔV), or
decoupling at the load that carries the step until the path current has ramped.

## 3. What follows

- **No plant change is needed now.** The differential motion is negligible; the common motion is an inductive drop in
  front of the load, set by two values P24 does not give (output-capacitor placement, processor-side decoupling) and
  by the load slew. A plant run would only sweep those unknowns.
- **Two interface requirements join the spec:** (1) sense Vo at the common strip (the plant's joined node), not at a
  module; (2) the processor-side decoupling and the load slew must cover L/4 · di/dt of the output path (16-157 pH
  here), as the bus-slew window covers the line steps.
- **The co-simulated load-step results (+15.3 / −11.9 mV) are at the modules' joined node**, not at the processor.
- If P24's capacitor placement or a measured path inductance becomes known and the common LC (L/4 with a load-side
  capacitance) falls near the loop's 100 kHz crossover, the plant step becomes worth doing: one registered run with the
  path and a load-side capacitor.
