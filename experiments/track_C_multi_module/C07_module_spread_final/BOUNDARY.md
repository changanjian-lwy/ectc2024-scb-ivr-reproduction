# C07 - module spread on the final design (BOUNDARY)
Track C. Written and committed before any C07 run. Looked at beforehand: C04 RESULTS Section 3, C06 n0 valleys.
Decision it changes: whether slave_floor's 2 A is enough, and whether the multi-module summary may say "holds under component spread".
Cheaper check done first: C04 mechanism re-scaled by hand (below). Budget: 6 cosim runs, one batch, ~20 min.

## 1. What and why
- C04 (old A105 design): R +-30% moved slave valleys +-2.2 A; the floor is only 2 A below target (-15.625 A -> -17.625 A).
  If the final design shifts as much, the floor fires in steady state and can disturb the interleave (C06 step: gaps up to 65 ns).
- Rows (make_cfgs.py): C04's four (cs20_n0, r30_n0, all_n0, all_s_p62; module 1 +spread, module 3 -spread, 0/2 nominal;
  all = L +5%, Cs -20%, R +30%) on C06's cfg_n0 / cfg_s_p62; two controls r30_n0_nf, all_n0_nf with slave_floor 0.
- Nominals: L 2.9333 nH, Cs 6 uF, R 0.54 mOhm (checked: A79 init run params R = 0.00054; A124 scales only controller values).
- Not spread: Coss, per-module driver (as C04). Same load 250 A, module 62.5 A, phase 15.6 A as C04, so C04's current scaling applies.

## 2. Criteria (last 200 master periods; before the step for all_s_p62)
1. Every run: no overlap, peak <= 200 A, locked (0.1 ns), 16 gaps within T/16 +-0.1 ns.
2. Predictions below within their bands (current split, valleys).
3. New: floor not active in steady state: for r30_n0 and all_n0, floor-on vs floor-off rows agree in steady-state
   valleys within 0.05 A and gaps within 0.05 ns.

## 3. Predictions
Mechanism (C04): slaves run at the master's timing, so a module acts as a source of ~3.3 mOhm: dI = dR * I / 3.3 mOhm,
dR = 0.162 mOhm, I = 62.5 A -> dV 10 mV -> dI ~ 3 A module-level; C04 measured valley shifts +-1.7-2.2 A. The resistance
does not depend on L or period, current is unchanged, so the same size is expected here.
- r30_n0: module 1 (+R) valleys DEEPER by ~2 A (band 1.5-3), module 3 shallower by ~2 A; currents -1.2% / +1.3% (+-0.5%).
  Module 1 phase 1 nominal -16.35 A -> ~-18.4 A, i.e. BELOW the floor (-17.6 A): I expect the floor to fire in steady
  state, so criterion 3 is likely missed. This is the registered risk, not a hoped-for pass.
- cs20_n0: currents within +-0.5%, valleys within 0.35 A of C06 n0; no floor activity.
- all_n0: module 1 current -5% +-1.5%, module 3 +5% +-1.5% (L dominates, R adds ~1%); valleys within +-3 A of n0.
- all_s_p62: step extreme within +-10% of C06 s_p62; peak <= 200 A.

## 4. Decision rule
- Criterion 3 passes: summary Section 8 states "holds under C04's spread; floor inactive in steady state".
- Criterion 3 fails with floor-on gaps/valleys still within T/16 +-0.1 ns: floor works as a clamp; state that and the shift size.
- Gaps leave T/16 +-0.1 ns with floor on: report that 2 A is not enough; next step (floor depth) goes to the user.
