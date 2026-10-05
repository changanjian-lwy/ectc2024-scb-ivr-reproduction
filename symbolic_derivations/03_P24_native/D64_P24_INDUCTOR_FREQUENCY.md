# D64 - the filter inductor from first principles, and the frequency it implies

2026-10-03. Code: `src/scb_ivr/p24_inductor_model.py`. Map:
`scripts/p24_frequency_choice.py` → `diagnostics/D64_frequency_choice.json`.
Tests: `tests/test_p24_inductor_model.py`.

## 1. Why

**The trade-off map's open lever (T14):** whether a lower switching
frequency pays rests on the inductor's resistance per henry, R/L.
- D62 carried R/L as an assumed technology constant.
- A115 found the break-even at 1 MHz against 5 MHz: ~51-103 µΩ/nH.

D64 derives R/L for a buildable inductor instead of asking for one.

## 2. The model

**Inductor:** a parallel-plate (stripline) air-core loop, per phase.
- Geometry: plates of width w, length l, copper thickness t, gap h.
- P24 Table 2's "stripline" and "substrate air core" are this class.

**Formulas:**
- L = μ0 l h / w (field between the plates; w ≫ h);
- **DC:** R_dc = 2ρl / (w t), so **R_dc/L = 2ρ / (μ0 h t)**;
- **ripple:** on the facing surfaces within the skin depth δ = √(ρ / (π f
  μ0)) (66 µm at 1 MHz), so **R_ac/L = 2ρ / (μ0 h min(t, δ))**;
- **loss:** I_dc² R_dc + (ripple/√12)² R_ac per phase.

**What sets R/L:** only the height h and the copper (t or δ). The
footprint sets l/w = L / (μ0 h).

**Converter side at each f (0.5-5 MHz):**
- Eq. (4)'s L = 7.333 nH × (1 MHz / f);
- for each negative-current target, D57's turn-on, the charge-balance
  orbit and D62's middle-case losses with an ideal inductor
  (`a115_predict.row`);
- D57's threshold. The target is limited to a valley margin ≥ 2 A, the
  margin A118's floor design runs at.

**What it leaves out:**
- the ripple's harmonics (more AC loss, so the AC term is a lower bound);
- fringing;
- magnetic cores (higher L per copper, plus core loss);
- the controller's feasibility at other frequencies (validated at 1 and
  5 MHz only).

## 3. Results

**Loss with an ideal inductor falls with frequency.**
- 16.1 W at 0.5 MHz (best target 5%), 17.4 W at 1 MHz (7.5-10%), 24.8 W
  at 5 MHz (25%).
- Switching losses scale with f, and zero voltage needs more negative
  current at higher f.

**Copper loss rises with L ∝ 1/f.** The balance depends on the inductor.

**(a) Fixed height and copper:**

| h, t | R_dc/L | best f | efficiency there | 1 MHz | 5 MHz |
|---|---|---|---|---|---|
| 0.5 mm, 105 µm (package-like) | 521 µΩ/nH | 5 MHz | 80.7% | 68.7% | 80.7% |
| 1 mm, 300 µm | 91 | 3 MHz | 86.6% | 84.2% | 86.5% |
| 2 mm, 300 µm | 46 | 2 MHz | 89.3% | 88.5% | 88.6% |
| 4 mm, 300 µm | 23 | 1.5 MHz | 91.0% | 90.9% | 89.8% |

**(b) Fixed footprint per phase** (w = 5h, h ≤ 2 mm), which is P24's
in-package setting. A smaller L (a higher f) leaves room for a taller
gap, so the copper loss falls ~1/f².

| footprint per phase, copper | best f | efficiency there | 1 MHz |
|---|---|---|---|
| 0.25-0.5 cm², 105-300 µm | **5 MHz** | 84.5-88.3% | 46-71% |
| 1 cm², 105-300 µm | **3 MHz** | 88.2-89.2% | 74-81% |
| 2 cm², 105 µm | **3 MHz** | 88.2% | 82.4% |
| 2 cm², 300 µm | **2 MHz** | 89.3% | 86.5% |

## 4. What it means

**Scope note (D67, 2026-10-05).** These conclusions are for an air-core stripline. P24's package itself uses MPC
magnetic cores at 1 MHz (8 modules); its 5 MHz is the electrical analysis. Fig. 5 gives 0.25-0.63 cm² per phase,
where this model picks 5 MHz, so the 2-3 MHz sweet spot below needs >= 1-2 cm² per phase. The project's 2.5 MHz
rests on A124 with an MPC-class R/L (D62 middle); see D67.

1. **At P24's in-package scale, 1 MHz does not pay.** With a stripline
   inductor of ≤ 2 cm² per phase, the best frequency is 2-5 MHz.
   - **1 MHz needs a bulky, off-package inductor:** ~6 cm² × 4 mm per
     phase with 300 µm copper, about 93 cm² for 16 phases.
   - **P24's own choice of 5 MHz is right** for its integration target.
   - The project's 1 MHz work (A115-A123) answered the high-side
     zero-voltage question the user asked. **D64 says it is not the
     efficiency optimum** unless the inductor can be large.
2. **The likely sweet spot is 2-3 MHz with a 10-15% target.**
   - D57's threshold there is 21-26 A, so 10-15% (12.5-18.75 A) leaves a
     5-10 A margin. That is more than A118's 2.4 A, and the transients
     are easier.
   - The loop samples 2-3× faster than at 1 MHz.
   - **Not yet co-simulated.**
3. **The break-even of A115** (51-103 µΩ/nH at 7.33 nH) is now a
   geometry.
   - The DC term alone needs a copper-gap product h·t ≳ 0.27-0.54 mm²
     (2ρ / (μ0 · R/L)). The ripple's skin-depth term needs more.
   - Package-integrated inductors (h ~ 0.2-0.5 mm, t ~ 35-105 µm, h·t ≤
     0.05 mm²) are an order of magnitude away.
