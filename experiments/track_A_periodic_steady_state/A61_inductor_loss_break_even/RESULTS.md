# A61 - inductor-loss break-even for the tuned large-ripple advantage (RESULTS)

Track A, `SENSITIVITY_ONLY` break-even analysis. Boundary: `BOUNDARY.md`,
unmodified. No new solve. Records: `break_even_a59_reference.json` (A59
reference model, Tj ~ 60 C), `break_even_a60_T25C.json` and
`break_even_a60_T100C.json` (A60 points).

## 0. Verdict

**The tuned large-ripple advantage absorbs only a small inductor loss. At a
realistic hot junction (100 C), about 50 uOhm of winding resistance per
phase inductor erases it.** This is the most restrictive inductor
specification found so far, and it can be checked against any candidate
part.

Break-even values, above which the large-ripple design loses:

| reference | advantage | equal DCR in all 8 inductors | baseline DCR if R ~ sqrt(L) | equal ACR at 5 MHz, skin-scaled harmonics 1-4 |
|---|---:|---:|---:|---:|
| Tj 25 C (A60) | 7.19 W | 293 uOhm | 823 uOhm | 263 uOhm |
| Tj ~ 60 C (A59) | 4.58 W | **185 uOhm** | 516 uOhm | **166 uOhm** |
| Tj 100 C (A60) | 1.26 W | **50 uOhm** | 139 uOhm | **45 uOhm** |
| Tj 125 C (A60) | -0.98 W | already lost | - | - |

Core loss has the same budget: the four large-ripple inductors may lose at
most the advantage (4.58 W at 60 C, 1.26 W at 100 C) more than the
baseline's four.

## 1. Why the inductor counts against the large-ripple design

A59 reference model, per phase:

| | L | DC | rms | AC rms | peak | ripple p-p | 5 MHz harmonic rms |
|---|---:|---:|---:|---:|---:|---:|---:|
| large-ripple | 0.627 nH | ~62.5 A | 107.0-107.6 A | 86.8-87.2 A | 216-217 A | ~300 A | 73.1-73.4 A |
| baseline | 1.467 nH | ~62.5 A | 72.3-73.7 A | 37.2 A | 127-128 A | ~128 A | 31.3-31.4 A |

- Sum over phases of `Irms^2`: 45,950 vs 21,166 A^2. The difference,
  24,785 A^2, is what every micro-ohm of winding resistance multiplies.
- Harmonic `rms^2` differences (1st-4th): 17,576 / 4,102 / 1,600 / 752 A^2.
- Flux-linkage swing `L*dI_pp` is the same for both designs (ratio 0.998),
  as it must be for equal volt-seconds. The large-ripple inductor needs
  1.69x the saturation current (217 A vs 128 A).
- If resistance scales in proportion to inductance (`a = 1`), there is no
  break-even: the smaller inductor then loses less than the baseline's.
  That case needs a technology whose resistance per nH is constant, which
  the project cannot confirm.

## 2. Consequence

- The electrical-only advantages from A58-A60 hold only if the phase
  inductor's winding resistance stays well below ~50-190 uOhm (depending on
  junction temperature) and its extra core loss stays within the same
  budget.
- This turns the open inductor item into a concrete question for the
  advisor: what is P24's phase inductor's DCR, its AC resistance at
  5-20 MHz, and its core loss at ~300 A p-p ripple?

## 3. Method notes and limits

- Orbits are A59/A60's regulated periodic states. They are not re-solved
  with the added resistance; ~0.1 mOhm shifts the regulated point by <0.1%.
- The DFT is exact for the one-period orbit up to resampling (8192
  points).
- The skin-effect scaling `R(k f) = R1 sqrt(k)` is a textbook
  approximation. Proximity effects in a real winding make the AC resistance
  grow faster, which would lower the break-even further.
- Gate drive is excluded here, as everywhere in A56-A60. It is ~8.6 W for
  the 20 EPC2067 at 5 MHz (17.1 nC * 5 V * 5 MHz each). It is nearly equal
  for both designs; ZVS saves only the ~2 nC Miller charge on the eight
  high-side devices, ~0.4 W. It matters for absolute efficiency, not for
  the ranking.

## 4. Reproduction

```
python3 inductor_break_even.py ../A59_nonlinear_coss_epc2067/runs/zvs_r1.950_f0.650.json ../A59_nonlinear_coss_epc2067/runs/baseline_r2.150_f1.150.json --advantage-w 4.584417806318946 --out break_even_a59_reference.json
python3 inductor_break_even.py ../A60_temperature_ron_sensitivity/runs/zvs_r1.950_f0.650_T25C.json ../A60_temperature_ron_sensitivity/runs/baseline_r2.150_f1.150_T25C.json --advantage-w <A60 T25 advantage> --out break_even_a60_T25C.json
```
