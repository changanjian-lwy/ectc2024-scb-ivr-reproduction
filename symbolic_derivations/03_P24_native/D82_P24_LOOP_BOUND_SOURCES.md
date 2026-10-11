# D82 - the 50 pH loop bound against published loops: sources, their conditions, and the geometry it asks for

2026-10-11. Method: literature check plus one formula. No simulation.

## 1. Why
- D65 wrote "published embedded-GaN power loops: 0.23-0.32 nH PCB-embedded, 1.03 nH DBC" without naming a paper.
  A144, A151, A152, A154, the scorecard (T20) and the Mihai summary repeated it as "230-320 pH", and the final
  specification's consequence ("this drive cannot hold published loops") rests on it. An unsourced number is not a
  basis (reports/LITERATURE_BASIS.md, open points).

## 2. The sources, with the conditions each figure was obtained under
| figure | source | its conditions | how the figure was obtained |
|---|---|---|---|
| 1.03 nH | Tian, Jia, DeVoto et al., "PCB-on-DBC GaN power module design with high-density integration and double-sided cooling," IEEE TPEL 39(1), 2024, DOI 10.1109/TPEL.2023.3311440 | one 650 V lateral GaN die per switch (GS66508T), half-bridge module 27 x 18 mm, PCB on a ceramic substrate | extracted from the ringing period (2.3 ns, C_oss 127 pF) in a 400 V / 25 A double-pulse test. **Read in the paper.** |
| 0.4 nH | D. Reusch, "Optimizing PCB layout," EPC white paper WP010 | EPC2015 (40 V eGaN FET), one device per switch, 12 V to 1.2 V buck, 1 MHz, up to 20 A; board 31 mil thick, 4 mil between the loop's two layers | the paper's "optimal" layout; its other eGaN layouts are shown at about 1.0, 1.6 and 2.9 nH. **Read in the paper.** |
| 0.23 nH | Moench, Reiner, Waltereit et al., "PCB-embedded GaN-on-Si half-bridge and driver ICs with on-package gate and DC-link capacitors," IEEE TPEL 36(1), 2021 | 600 V-class GaN-on-Si ICs embedded in a PCB | reported as an estimate for the stacked package. **From search summaries only; the paper was not read.** |
| 0.32 nH | Heydari et al., "Ultra-fast and ultra-compact driver-integrated GaN half-bridge module with insulated top-side cooling," Electronics Letters, 2025, DOI 10.1049/ell2.70323 | two 200 V, 22 mOhm GaN devices, module 15 x 15 x 2.6 mm | **From search summaries only; the paper was not read.** |

D65's three numbers match the first, third and fourth rows. D65 did not record which papers it used, so this is a
reconstruction: the 1.03 nH row is confirmed in the paper, the other two only by title and abstract-level summaries.

## 3. What the comparison can and cannot carry
- **Not the same case.** Three of the four are 200-650 V modules with one die per switch at tens of amperes. A 650 V
  layout needs creepage that a 40 V layout does not. P24's phase is 2 + 3 paralleled 40 V devices at 143-200 A.
- **The closest case is EPC's own:** 0.4 nH with a 40 V device of the same family on a board with 4 mil (100 um) between
  the loop's two layers. Our bound of 50 pH (A168) is 8 x below it.
- So the statement "published embedded-GaN loops are 230-320 pH" should not be used. What can be said: the best
  published board-level loop for this device family is 0.4 nH (EPC, 12 V, 20 A, 100 um dielectric); published
  module-level loops of higher voltage classes are 0.23-1.03 nH; none is a 40 V in-package loop at 143-200 A.

## 4. What 50 pH asks of the geometry
- A loop made of two facing planes (the supply plane and its return, length l along the current, width w, separated
  by h) has L = mu0 h l / w: mu0 h per square. It is the formula D64 uses for the stripline inductor.

  | h between the planes | L per square | squares allowed for 50 pH |
  |---|---|---|
  | 100 um (EPC's 4 mil) | 126 pH | 0.40 |
  | 50 um | 63 pH | 0.80 |
  | 30 um | 38 pH | 1.33 |
  | 20 um | 25 pH | 1.99 |

- EPC's 0.4 nH at 100 um is about 3 squares. Reaching 50 pH therefore needs h x (l / w) <= 40 um-squares: a build-up
  dielectric of 20-30 um with the decoupling capacitor within about 1.3-2 squares of the die pair, or several
  loops in parallel (N equal loops give L / N: the 2 high-side devices with their own capacitors halve it).
- Not included: the inductance inside the devices and the capacitors (ESL), and the vertical vias. They add to the
  plane term, so the allowance above is an upper bound on the plane part.
- For P24: its Fig. 5 places C1-C3 with the GaN under glass 1, in an ABF build-up; no thickness is printed. Whether
  the series capacitors can sit within ~1-2 squares at 20-30 um is a layout question for the package designers. It
  joins question 5 of the Mihai summary (the prototype's loop inductance).

## 5. Also corrected here
- TI LMG1210 propagation delay: 10 ns typical / 18 ns maximum is the independent-input mode (A75, A91); 11 ns typical /
  21 ns maximum is the PWM-input mode. A88 wrote "10 ns (21 ns max)", mixing the two. No result used a maximum: the
  runs use 10 ns and the 1 / 3.4 ns mismatch (tMTCH).
