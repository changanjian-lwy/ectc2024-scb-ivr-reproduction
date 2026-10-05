# D66: the cost of passive current sharing, and what an i_neg trim would leave (four-module final design)

Method: math (no new co-simulation; calibrated on existing four-module records). Script:
`scripts/p24_sharing_loss.py` → `diagnostics/D66_sharing_loss.json`.

## 1. Why

The four modules share by their inductance (common Ton, D61 scheme A). C03 called this sufficient up to ±10 % L,
judged on peak current and soft switching, but C03 only ran a module with *larger* L, which carries *less* current.
The heavy direction (smaller L) and its loss and temperature were never assessed. Active sharing (D61 scheme B, a
per-module i_neg trim) was analysed but not built.

## 2. Method

- Common Ton and period; a module at L0 (1 + e) has its per-phase swing scaled by 1 / (1 + e); the shared loop scales
  Ton so that the total current is unchanged.
- Valley against e, two bounds: (a) fixed at the nominal module's (D61's law); (b) the slave law measured on C12 ls_p5 /
  ls_p10 (valley shift +20.7…+21.4 A per unit e).
- High-side turn-on V_DS: the nominal module's measured value plus the edge model's change (datasheet Coss(V)).
- Loss: D62 middle scenario on the constructed phases. Nominal module: 25.9 W (90.6 %).
- Temperature: ΔT = ΔP × Rth, Rth 0.5 / 1 / 2 K/W per module (assumed; P24 gives no thermal path).
- Peak through transients: steady peak + 45 A (the worst registered four-module row: 189 A against a 144 A steady
  peak).

**Calibration** (measured / bound (a) / bound (b)):
- C12 ls_p10, slave at +10 % L: current −6.64 % / −8.73 % / −6.19 %; loss 23.12 / 22.27 / 23.29 W. Bound (b) is fitted
  on this row.
- C07 all_n0, module 3 at −5 % L (also Cs / R spread; independent): current +5.87 % / +6.42 % / +4.76 %; loss
  28.41 / 28.68 / 28.00 W; V_on 3.57-4.21 / 3.46-4.11 / 2.93-3.64 V. The measured heavy module lies between the
  bounds, nearer (a).

## 3. Results: passive sharing (the heavy module, bound (b) … (a))

"One low": one module at −t, three nominal. "Worst": one at −t, three at +t.

| L tolerance | spread | heavy module current | extra loss | ΔT at 0.5 / 1 / 2 K/W | steady peak | + transient |
|---|---|---|---|---|---|---|
| ±5 % | one low | +3.7 … +4.9 % | +1.7 … 2.2 W (+6 … 8 %) | 1 / 2 / 4 K | 150 A | 195 A |
| ±5 % | worst | +7.1 … +9.6 % | +3.0 … 4.1 W (+12 … 16 %) | 2 / 3-4 / 6-8 K | 154-156 A | **199-201 A** |
| ±10 % | one low | +7.7 … +10.2 % | +3.6 … 4.6 W (+14 … 18 %) | 2 / 4-5 / 7-9 K | 156-157 A | **201-202 A** |
| ±10 % | worst | +14.5 … +19.8 % | +6.5 … 8.8 W (+25 … 34 %) | 3-4 / 7-9 / 13-18 K | 165-169 A | **210-214 A** |
| ±20 % | one low | +17.4 … +22.1 % | +8.5 … 10.6 W (+33 … 41 %) | 4-5 / 9-11 / 17-21 K | 170-172 A | **215-217 A** |
| ±20 % | worst | +30.7 … +41.7 % | +14.8 … 20.3 W (+57 … 79 %) | 7-10 / 15-20 / 30-41 K | 187-197 A | **232-242 A** |

- **The binding limit is the peak current, not the temperature.** The heavy module reaches 200 A through transients
  at about ±5 % worst-case spread, or one module at −10 %. Its loss there is +12-18 % (2-5 K at 1 K/W).
- **It switches harder as well:** smaller L raises its zero-voltage threshold (I_th ∝ 1/√L), so its V_on rises by
  ~0.2 V per −5 % of L under bound (a).
- **No thermal self-balancing:** a hotter module's higher R_on hardly moves the sharing (C04: R ±30 % → ±1.3 %),
  because the split is set by L and the common Ton.

## 4. Results: an i_neg trim (D61 scheme B), currents equalised, mean valley kept

To shed its extra current at the common Ton, the heavy module's valley must deepen; that is its valley margin
I_th − |valley| (nominal: 8.1 A phase 1, 5.3 A phase 4; scorecard T12: every design at ≤ 2.5 A failed a transient).

| L tolerance | spread | heavy valley | heavy margin, min over phases (48 V / 43.2 V input) | other modules' V_on, max |
|---|---|---|---|---|
| ±5 % | one low | −19.5 A | 2.7 / 0.5 A | 4.4 V |
| ±5 % | worst | −22.5 A | −0.3 / −2.5 A | 4.7 V |
| ±10 % | one low | −22.8 A | −0.05 / −2.3 A | 4.9 V |
| ±10 % | worst | −28.9 A | −6.2 / −8.4 A | 5.6 V |
| ±20 % | worst | −42.8 A | −18.8 / −21.2 A | 7.7 V |

- **The trim does not rescue sharing.** Already at ±5 % it puts the heavy module on or past the margin line where
  the predictive timing breaks in transients; beyond that the margin is negative.
- Shifting every valley shallower to make room moves the cost to the light modules' hard turn-on (toward the 5 %
  design's ~9 V, 8.9 W per module).

## 5. Decision

- **Current sharing in this architecture is an inductor-matching specification.** Both handles are taken: Ton by the
  interleave (the period does not depend on L, D61), i_neg by the ZVS / transient margin (T12). With the frozen design,
  passive sharing holds the 200 A limit for about ±5 % worst-case L spread (or about −9 % on one module); the heavy
  module then carries +12-16 % loss.
- **Correction to C03:** "scheme A sufficient up to ±10 % L" holds only for a module with larger L; a module with
  10 % smaller L reaches 201-202 A through transients.
- For Mihai (scenarios, not a request): the embedded inductors' matching across modules decides this; matched
  elements from one substrate favour ±5 %, discrete parts with ±10-20 % tolerance need either a larger peak budget
  (more devices) or a sharing handle that does not consume the valley margin.

## 6. Limits

- Steady state at 25 C, D62 middle; the +45 A transient increment is the nominal modules' (C07 measured 193 A on its
  rows with one module at −5 %, the model 195 A). Checked by C14 (co-simulation, frozen design, module 2
  heavy): shares and steady peaks inside this table; transient peaks 2-7 A below it (194.4 / 195.4 / 207.9 A for
  ±5 % worst / −10 % one low / ±10 % worst), because the frozen design's nominal increment is 40.7 A, not 45 A.
- If the heavy module is the master, its phase 1 valley is regulated (bound (a) for that phase).
- Rth is assumed; ΔT scales with it.
