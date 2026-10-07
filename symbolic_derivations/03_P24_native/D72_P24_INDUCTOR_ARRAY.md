# D72 - the inductor as a buildable array: unit count, R/L and the frequency choice

2026-10-07. Closes the external review's point on the inductor (D70 Section 1: core loss, saturation and fit were
open). No new runs: D62's budget on the existing design records (A112 p20_n0 at 5 MHz, A124 p125_n0 at 2.5 MHz,
A118 f6_n0 at 1 MHz) with the inductor R/L each array implies.

## 1. What 79 µΩ/nH means

D62's middle case (and A124's 90.61 %) uses R/L = 39.3 mΩ / 500 nH = 79 µΩ/nH: the largest HBS1 unit of P24 Table 2. An
array of N identical units keeps the unit's R/L (D62) but has L = L_unit / N, so 2.933 nH from 500 nH units takes
**~170 units per phase** (68 at 1 MHz, 341 at 5 MHz). P24 places 12 per phase. The 90.61 % therefore assumes an inductor
that does not fit Fig. 5.

## 2. Units sized for the current

Each HBS1 unit saturates above ~5 A (P24), so a phase needs N ≥ I_peak / 5 A: 29-31 at the steady peaks (141-153 A),
40 at the 200 A budget. The unit is then L_unit = N L_phase. P24 Table 2 gives HBS1 only at its ends (20 nH / 13.6 mΩ,
500 nH / 39.3 mΩ); between them R = 13.6 mΩ (L / 20 nH)^0.33 (a power law through both, an assumption). Smaller units
have a higher R/L, and lower frequencies need larger units:

| design (record) | N per phase | unit | R/L | efficiency (D62 middle otherwise) | inductor copper |
|---|---|---|---|---|---|
| 5 MHz, 20 % (A112 p20_n0) | 31 / 40 | 45 / 59 nH | 392 / 331 µΩ/nH | 86.38 / 87.10 % | 15.2 / 12.8 W |
| 2.5 MHz, 12.5 % (A124 p125_n0) | 29 / 40 | 85 / 117 nH | 258 / 208 µΩ/nH | **86.56 / 87.65 %** | 18.6 / 15.0 W |
| 1 MHz, 10 %, floor (A118 f6_n0) | 29 / 40 | 213 / 293 nH | 139 / 112 µΩ/nH | 85.71 / 87.13 % | 24.5 / 19.8 W |

For comparison, at one fixed R/L for all three (the method of A124 / D67): 2.5 MHz leads at 79 µΩ/nH (90.60 against
90.17 / 88.95 %) and 5 MHz from ~120 µΩ/nH up (210: 88.54 against 87.60 %). A fixed R/L is the wrong comparison for an
array technology, because the unit size follows the frequency.

## 3. What follows

- **2.5 MHz stays the choice, but by efficiency only narrowly:** 0.2-0.6 points over 5 and 1 MHz with buildable
  arrays. Its other reasons stand: 3× the 1 MHz valley margin (7.9 against 2.4 A), and the frozen controller exists at
  2.5 MHz (5 MHz would need a rerun of its matrix).
- **The converter's estimated efficiency is ~86.6-87.7 % with a buildable HBS1-class array, not 90.6 %;** 90.6 %
  stands for ~170 units per phase. Package-inclusive (D70 Section 2.5's copper 86-429 µm and loop 50-150 pH added) that is ~81-86 %.
- **Fit:** 29-40 units per phase against P24's 12 per phase column; whether they fit is open (unit sizes are not in
  P24). Core loss at 2.5 MHz with ~4-5.5 A peak-to-peak per unit (on 1.6-2.2 A DC) is not in any number here; it
  would lower all three, the high frequencies more.
- **Heat (a requirement, not a result):** the converter, copper and loop losses come to ~39-58 W per 10 × 10 mm module
  (35-39 W converter at 87.65-86.56 %, 2.5-12.5 W copper, 1.6-6.4 W loop). The 125 °C used for the hot estimate holds only if the
  package removes that from ~1 cm² per module; P24 gives no thermal path (the IVR sits on the back of the processor
  package, Fig. 6). **D73** closes it to first order in the team's electrothermal form: at the 85 °C threshold of
  Choi et al. 2025, ≤ 0.8-1.0 K·cm²/W per module to a 25 °C coolant, converter ~84-86 %.

## 4. Limits

- Two HBS1 points and a power law; the real family may not follow it.
- Waveforms from the 25 °C ideal-inductor co-simulations; a lossy inductor changes them little at these R values.
