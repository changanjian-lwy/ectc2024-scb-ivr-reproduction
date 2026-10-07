# D67 - the premise behind 2.5 MHz: the inductor's R/L, checked against P24's own inductor

2026-10-05. Method: math (no new co-simulation). Script: `scripts/p24_frequency_premise.py` (D64's script at
2.5 MHz and at Fig. 5's footprint) → `diagnostics/D67_frequency_premise.json`. Inputs: A124, D62, D64, P24 text.

## 1. Why
- The repo justified 2.5 MHz with D64 ("1 MHz does not pay in-package; the sweet spot is 2-3 MHz"). D64 models an
  air-core stripline and leaves magnetic cores out, while A124's 90.61 % uses D62's middle-case R/L (79 µΩ/nH, an
  MPC-class magnetic core). The two premises were mixed; this note separates them.

## 2. What P24 says about its inductor
- Two design points. Electrical analysis (Table 1, Eq. (4)): 4 phases, nM = 4, 250 W, 125 A peak, 5 MHz.
  Package section (Table 3, Figs. 5-6): 4 phases x 8 modules, 1 MHz, 62.5 A peak per phase.
- Package inductor: per phase 12 embedded MPC-core inductors (HBS1, ref. [10], saturation > 5 A each) in
  parallel, 183 nH each at 1 MHz (36.7 nH at 5 MHz); air-core inductors only "up to 100 MHz", as future work. P24
  asks to reassess these cores "considering the high ripple current".
- Inconsistent sizes: the text gives the inductor network as 2.5 cm x 10 cm x 1.5 cm and the package as
  "40 cm x 25 cm"; Figs. 5-6 give 25 x 40 mm inside a 97 x 84 mm processor package. This work keeps the figures.

## 3. This work's point against it
- Table 1's module (nM = 4, 250 W, 2 + 3 EPC2067) at 2.5 MHz, L = 2.933 nH (Eq. (4) scaled), 144 A steady peak.
- With HBS1-class units (> 5 A each) that is >= 29 in parallel per phase (P24: 12 at 62.5 A). At the project's
  200 A transient limit (scorecard Section 5) it is >= 40. Core loss and saturation are not modelled anywhere in
  this project.

## 4. The frequency follows the inductor's R/L
| premise | 1 MHz | 2.5 MHz | 5 MHz | best |
|---|---|---|---|---|
| A124, D62 middle R/L 79 µΩ/nH (MPC class), constant in L | 88.97 % | **90.61 %** | 90.17 % | 2.5 MHz |
| air-core stripline, 0.25 cm² per phase (one Fig. 5 column), 105-300 µm | 45.7-57.7 % | 76.0-80.4 % | **84.5-85.8 %** | 5 MHz |
| air-core, 0.625 cm² (25 x 40 mm over 16 phases) | 65.8-74.7 % | 84.7-86.8 % | **88.0-88.6 %** | 5 MHz |
| air-core, 1 cm² | 74.0-80.7 % | 87.4-88.8 % | 88.0-88.6 % | 3 MHz |
| air-core, 2 cm², 300 µm | 86.5 % | **89.27 %** | 88.6 % | 2.5 MHz |
(stripline rows: w = 5h, h <= 2 mm, best negative-current target with a valley margin >= 2 A, as D64.)
- Fixed copper (D64 table (a), rerun): 2-2.5 MHz wins at R/L <= ~65 µΩ/nH, 3 MHz at ~90-130, 5 MHz from ~200 up.
  D62's middle 79 µΩ/nH sits at the 2.5 / 3 MHz border (A124 compared 1, 2.5 and 5 MHz only).

## 5. What it means
1. **2.5 MHz rests on a magnetic premise:** an inductor reaching MPC-class R/L (<= ~80 µΩ/nH) at 2.9 nH and 144 A,
   i.e. P24's own inductor family scaled to this current. Under that premise A124 measured 2.5 MHz best (+0.44 points
   over 5 MHz, +1.6 over 1 MHz) with 3x the 1 MHz valley margin (7.9 A).
2. **With an air-core inside P24's footprint, 5 MHz is better by 2-9 points;** a 5 MHz design exists
   (A110 / A112 / A114: 20 % target, 90.17 % at D62 middle, matrix passed except at the line-step edges) on the
   controller before A128-A143, so a switch means rerunning the frozen controller's matrix at 5 MHz. "1 MHz does not
   pay in-package" (D64) stands for air-core; D64's "2-3 MHz sweet spot" needs >= 1-2 cm² per phase, which Fig. 5 does not give.
3. For Mihai: the inductor technology (MPC-type array or air-core) and the footprint per phase, with saturation at
   144 A. They decide 2.5 vs 5 MHz.

## 6. Limits
- A124 holds R/L constant as L scales with 1/f; D64's parallel plate (w = 5h, h <= 2 mm, no fringing, ripple
  harmonics left out); no core loss or saturation; 25 °C.
## 6. Update (D72, 2026-10-07)

79 µΩ/nH is the 500 nH HBS1 unit's R/L, i.e. ~170 units per phase at 2.5 MHz. With units sized for the current
(29-40 per phase) the R/L follows the unit size (power law through P24 Table 2's two HBS1 points), and on the design
records 2.5 MHz stays best by 0.2-0.6 points (86.6-87.7 %), against 86.4-87.1 % at 5 MHz and 85.7-87.1 % at 1 MHz.
