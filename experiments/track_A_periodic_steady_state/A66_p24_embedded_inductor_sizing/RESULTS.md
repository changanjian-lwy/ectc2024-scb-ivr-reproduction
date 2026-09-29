# A66 - phase-inductor loss under P24's own inductor technology (RESULTS)

Track A, `SENSITIVITY_ONLY`. This is a closed-form evaluation with no solve
and no tuning, so there is no separate BOUNDARY; every choice is listed in
Section 3. Records:
- `results.json` (`p24_inductor_sizing.py`);
- `ref10_hbs1_digitized.json` (`digitize_ref10_hbs1.py`).

## 0. Verdict

**With the inductor technology P24 itself names, the large-ripple design
loses about 220 W more per 250 W module in its phase inductors than the
baseline.** That is fifty times the best switch-level advantage found
(4.58 W, A59). Even a hypothetical future material, the target that P24's
inductor reference proposes, leaves it 26-38 W behind. The inductor question
(A61; advisor question 2 in the A53-A64 consolidation) is therefore settled
from public sources.

| inductor loss per module (DC + AC), 5 MHz, D = 1/12 | large-ripple | baseline | difference |
|---|---:|---:|---:|
| HBS1, the material P24 names (ref. [10]) | 403.9 W | 184.9 W | **+219.0 W** (range +199 ... +240) |
| ref. [10]'s target material for 12-1 V at 5 MHz (Table VII), face value | 64.9 W | 39.1 W | +25.7 W |
| same, scaled to D = 1/12 | 86.5 W | 48.5 W | +38.1 W |

Break-even: the large-ripple design keeps A59's 4.58 W only if the core's
large-signal loss factor `kappa*racx` is below **0.37 mOhm/nH**. HBS1 has
7.05 mOhm/nH at P24's operating point, 19 times more. Ref. [10]'s own
target material has 1.03-1.41 mOhm/nH.

## 1. Why the result does not depend on the material

Ref. [10]'s loss model (its Eqs. 1 and 11) is

`P_L = I_dc^2 * R_dc + delta_i^2 * L * kappa * racx(D, f)`,

where `delta_i` is half the peak-to-peak ripple. Its Table IV reproduces
this to the printed digit: 0.5844^2 * 76.22 nH * 4.043 mOhm/nH = 105.2 mW.

- **The AC term does not depend on paralleling.** With n embedded units per
  phase, each unit has ripple `delta_i/n` and inductance `n*L`. The n units
  together lose `delta_i^2 * L_phase * kappa * racx`.
- **The two designs have the same D and f.** They therefore see the same
  `kappa*racx`. Their AC losses scale as `sum(delta_i^2 * L)`. Both designs
  have the same volt-seconds, so this is proportional to the ripple.
- **The ratio is fixed: 2.33.** The large-ripple design's AC inductor loss
  is 2.33 times the baseline's for any core material (ripple 300 A vs
  128 A p-p).
- **The DC term favours the large-ripple design, but only slightly.** It
  needs more parallel units, so it has more copper: 7.0 vs 14.3 W with HBS1
  units.

## 2. P24's sizing rule applied to both designs

P24 (Sec. IV-A, Eqs. 5-6) builds each phase inductor from embedded units of
at most 5 A peak (HBS1 saturation). P24's own numbers give 25 units of
36.7 nH for the 4-module, 250 W configuration: `L_phase = 1.4667 nH`.

| | orbit peak | units per phase | unit L | unit R_dc (HBS1 designs, interpolated) | R_phase | unit half-ripple |
|---|---:|---:|---:|---:|---:|---:|
| large-ripple | 217.1 A | 43.4 | 27.2 nH | 19.4 mOhm | 0.446 mOhm | 3.45 A |
| baseline | 128.3 A | 25.7 | 37.6 nH | 23.4 mOhm | 0.912 mOhm | 2.50 A |

The large-ripple design needs **1.69 times as many embedded inductors**.
This is inductor area and volume in a package whose size is P24's central
constraint. Both unit inductances lie inside the range of ref. [10]'s HBS1
designs (18.8-70.7 nH).

## 3. Data and declared choices

From ref. [10] (C. Alvarez Barros et al., IEEE TCPMT 11(12):2183-2192,
2021, doi:10.1109/TCPMT.2021.3116946; `EXTERNAL_DEVICE_DATA`, not
redistributed):

- **DC resistance per design**, Table II (13.6-39.3 mOhm).
- **HBS1 inductance per design**, digitized from Fig. 7's vector paths.
  IND037 reads 69.8 nH at 5 MHz, equal to Table IV's 69.8 nH.
- **Small-signal `racx(D, f)`**, digitized from Fig. 8 (six designs per
  frequency). At 5 MHz and D = 1/12 it is 1.390 mOhm/nH (1.344-1.435).
  At D = 0.5 it is 0.78, against Table IV's 0.753 for IND037.
  Grid-fit residuals are below 1e-3 of a division.
- **`kappa`** = 5.069 at 5 MHz (Table V). Table IV spans 4.79-5.37.
- **Target material** (Table VII): racx 0.257 mOhm/nH, kappa 4, "for
  12-1 V at 5 MHz". The text's example uses D = 0.19.

PROJECT_DECISIONs:

- P24's 5 A-per-unit rule is applied to each orbit's actual peak.
- Unit R_dc is interpolated linearly in L over the six HBS1 designs.
- The SCB phase duty is `D = nP*Vo/Vin = 1/12`.
- The target-material racx is also shown scaled from D = 0.19 to D = 1/12
  with HBS1's 5 MHz curve (factor 1.37).

Phase currents are from A61 (A59's tuned orbits). The phase DC currents are
~62.5 A; the ripples are 300 A (large-ripple) and 128.5 A (baseline) p-p.

## 4. Limits

- **Extrapolation in ripple amplitude.** `kappa` was measured up to
  0.584 A half-ripple. Here a unit carries 2.50 A (baseline) or 3.45 A
  (large-ripple), 4.3-5.9 times more. HBS1 does not saturate below 5 A DC
  (ref. [10] Fig. 10), and `kappa` rose slightly with ripple in Table IV.
  Core loss usually grows faster than `delta_i^2` at higher flux, so the
  constant-`kappa` model is more likely optimistic than pessimistic.
- **Extrapolation in duty cycle.** The large-signal loss was measured at
  D >= 0.15. At D = 1/12 the model uses the small-signal racx (from the
  measured spectra, Eq. 2) times `kappa`, as ref. [10] prescribes.
- **Joule heating ignored.** Ref. [10] reports that R_dc rises above 2 A
  from Joule heating. That would add to both designs.
- **Loss-only comparison.** The switch-level comparison (A59-A65) is
  separate: this adds to it, it does not replace it.

## 5. What this also says about P24 itself (context, not this track's question)

With HBS1 at P24's 5 MHz point, even the baseline's inductors would
dissipate ~185 W per 250 W module, an inductor efficiency of ~58%. This is
consistent with ref. [10]'s own conclusions:

- For 92.5-97% inductor efficiency, HBS1 suits only ~1.3-2.3 V -> 1 V
  conversion at 10 MHz (its Fig. 16).
- 12-1 V at 5 MHz needs a new material (its Section IX, Table VII).

It is also consistent with P24's own caveat that the cores must be
"reassess[ed] ... considering the high ripple current". The 5 MHz embedded
design in P24's Table 3 is therefore not efficiency-viable with the named
material. P24 is a sizing/packaging study, and this project already treats
its 48 V point as unbuilt.

## 6. Reproduction

```
python3 digitize_ref10_hbs1.py <ref10 IEEE PDF>
python3 p24_inductor_sizing.py
```
