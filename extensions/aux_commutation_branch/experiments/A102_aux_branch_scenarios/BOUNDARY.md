# A102 / D57 - the auxiliary commutation branch over its assumed values (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Follows A101 / D56.

**Written before any A102 co-simulation run.** The code change (branch
enable time, per-branch precharge) is a7b5e23; the D57 results in
Section 3 and the predictions in `d57_predictions.json` are committed
with this file, before the runs.

## 1. Question

A101 ended with a verdict that rested on values I had assumed. I had
planned to ask Mihai for them. Instead, this experiment builds the cases
itself, so that Mihai can evaluate them:

1. **Is the branch worth it?** A101's sign depended on the hard turn-on
   loss model. Here the net is computed under three loss models, four
   Lr technologies, three gate-supply efficiencies and three residual
   currents at the opening.
2. **Does it fit?** The added die, inductor and capacitor area, against
   the main stage of the same technology.
3. **Why does P24 say 1-2% is enough?** The negative current a phase
   needs for zero voltage without a branch, over P24's own inductor
   values and node compositions.
4. **The cases A101 did not run:**
   - enabling after the handover, with three precharges;
   - load steps of ±62.5 A;
   - the 2% target;
   - Lr's resistance from an embedded-inductor technology;
   - a smaller Cm.

## 2. What A101's verdict rested on

| assumed value | A101 | spanned here |
|---|---|---|
| hard turn-on loss | D56 central (own Eoss + the other node capacitances' charge through the channel) | A91 lower (own Eoss), central, A91 upper (Qoss(V) V of five devices) |
| Lr's resistance | 0.2 mΩ whatever Lr | the main inductor's R/L (0.37 mΩ/nH); P24 Table 2: CoaxMIL (4.8 mΩ/nH), substrate air core (5.8 mΩ/nH) |
| BDS gate supply | lossless | efficiency 1, 0.7, 0.5 |
| zero-current opening | ideal | residual 0, 2, 5 A (0.5 Lr i² lost; ring into the open pair) |
| start | branch active from t = 0, Cm at 0 V | enabled at 200 µs; Cm at D56's balance, 5 V, 0 V |
| operating point | 5%, ~250 A | ±62.5 A steps; the 2% target |
| Cm | 1 µF | 0.22 µF |

## 3. D57 - the mathematical model and its results

`src/scb_ivr/p24_aux_scenarios.py`, `scripts/p24_aux_scenarios.py`,
`symbolic_derivations/03_P24_native/diagnostics/D57_aux_scenarios.json`.
The model is D56's single-phase edge and cycle model (phase 1 of the 5%
orbit, retuned dead time, ×4 phases), unless stated.

### 3.1 P24's 1-2%

The negative current for the high side to reach zero voltage, no branch
(% of P24's 125 A peak):

| Lf | this model's node (2 HS, 3 LS, next HS) | the high side alone (P24's text) | P24 Section IV (1 HS, 2 LS, next HS) |
|---|---|---|---|
| 13.44 nH (Table I, 1 MHz) | 8.8% | **5.3%** | 6.7% |
| 2.68 nH (Table I, 5 MHz) | 19.7% | 11.8% | 15.0% |
| 1.34 nH (Table I, 10 MHz) | 27.9% | 16.7% | 21.2% |
| 1.4667 nH (Eq. (4), this model) | 26.7% | 15.9% | 20.3% |

- **No case reaches 1-2%.** The smallest is 5.3%.
- For 2% to suffice, the node's equivalent capacitance would have to be
  6.5-180 times smaller than any composition above.

### 3.2 Loss scenarios (W, four phases; negative = saving)

| design | central | hard turn-on: A91 lower / upper | Lr: P24 air core | gate supply 50% | residual 5 A | pessimistic corner | optimistic corner |
|---|---|---|---|---|---|---|---|
| Lr 0.75 nH, α 0.3 | −4.45 | +1.76 / −11.05 | −3.68 | −3.57 | −4.29 | +3.58 | −11.51 |
| Lr 1.0 nH, α 0.25 | −5.08 | +1.08 / −11.57 | −4.28 | −4.34 | −4.86 | +2.81 | −11.97 |
| Lr 1.25 nH, α 0.25 | −5.20 | +0.71 / −11.34 | −4.39 | −4.46 | −4.93 | +2.50 | −11.70 |

- Values at a 1 ns turn-off fall.
- **72 of 108 grid cases save power for every design: exactly those
  with the central or upper hard turn-on model.** All 36 with A91's
  lower bound lose.
- Every other assumption moves the net by at most 0.9 W.

### 3.3 Area (against the main stage of the same technology)

| design | BDS dies | Lr by peak stored energy | Lr by L I_rms² | Cm (1 µF) by C V² |
|---|---|---|---|---|
| 0.75 nH | 5.6 mm², 12% of the main dies | 3.8% of Lf | 0.5% | 5.5% of the series capacitors |
| 1.25 nH | 4.6 mm², 10% | 3.6% | 0.5% | 4.6% (0.22 µF: 1.0%) |

- An array of identical elements needs L I² / (L_e I_e²) of them, and
  its R is L R_e / L_e, whatever the element (D57 docstring).
- The main dies are P24 Table 3's per phase: 5 × EPC2067, 46.3 mm².
- **Not counted:** four more floating gate drivers per module. The
  module already has eight, and P24's own area estimate leaves drivers
  out.

### 3.4 Enable: the first cycle (Cm 1 µF)

| design | Cm at the balance | Cm at 5 V | Cm at 0 V |
|---|---|---|---|
| 0.75 nH | +32.9 / −36.6 A | +16.0 / −137 A, about 2 cycles to the balance | −277 A; the current does not return to zero |
| 1.25 nH | +22.1 / −27.7 A | +11.5 / −82 A, about 2 cycles | −173 A; does not return to zero |

### 3.5 Load and the 2% target

**Load** (phase 1; the turn-off current scaled with the phase's average;
the low side turning on where the controller keeps it):

| design | −62.5 A | 0 | +62.5 A |
|---|---|---|---|
| 0.75 nH: Vm, high-side V_DS | 8.21 V, +0.52 V | 9.06 V, 0 | 9.62 V, 0 |
| 1.25 nH: Vm, high-side V_DS | 7.40 V, +3.07 V | 8.28 V, +2.14 V | 8.92 V, +1.44 V |

**The 2% target** (D51's 2% orbit, solved for this experiment: soft,
high-side turn-on at 9.86-10.21 V without a branch):

| design | Vm (V), phases 1-4 | high-side V_DS | branch current | net against the 2% design without a branch |
|---|---|---|---|---|
| 0.75 nH | 8.69 / 8.85 / 8.86 / 9.07 | 0 | +34.4 / −39.3 A (phase 1) | −6.1 to −6.6 W |
| 1.25 nH | 7.80 / 7.97 / 7.98 / 8.18 | 2.7-2.8 V | +23.5 / −29.9 A | −6.6 to −7.0 W |

- At 2% the branch saves more than at 5%, because the high side would
  otherwise turn on 1 V higher.
- **Whether 2% with a branch beats 5% with a branch** is read from
  ref_2pct against A101's ref (the main conduction) and these nets.

## 4. Co-simulation

**Physical model:** Verilog RTL (unchanged) with A88's plant (kernel2)
and the adopted design (A92's correctors, A97's slots), 25 C, ~250 A
resistive load.

**Branch:**
- `valley_zero` 0 in every run;
- enabled at 200 µs (the handover is at 88.6 µs);
- each branch starts at its next low-side turn-off.

| run | design | case | to |
|---|---|---|---|
| e125_5v, e075_5v | 1.25 nH α 0.25; 0.75 nH α 0.3 | Cm precharged to 5 V | 500 µs |
| e125_pc, e075_pc | as above | Cm precharged per phase to D56's balance | 500 µs |
| e125_0v, e075_0v | as above | Cm at 0 V | 500 µs |
| s125_m62, s125_p62, s075_m62, s075_p62 | as above, Cm at 5 V | −62.5 / +62.5 A at 400 µs (A100's steps) | 600 µs |
| ref_2pct | no branch | 2% target (−2.5 A) | 500 µs |
| n125_2pct, n075_2pct | Cm at 5 V | 2% target | 500 µs |
| r125_lrair | 1.25 nH, Lr 7.29 mΩ (P24 Table 2 air core) | Cm at 5 V | 500 µs |
| c125_cm022 | 1.25 nH, Cm 0.22 µF | Cm at 5 V | 500 µs |

**Comparisons:**
- A101's ref, p125 and dz_vz0 (5%, no step);
- A100's ref_m62 and ref_p62 (the same adopted design without a branch,
  under the same steps).

## 5. Registered criteria

**Statistics:** over the last 200 phase-1 periods unless stated. The
"final state" of the design is A101's stable run: p125 for 1.25 nH,
dz_vz0 for 0.75 nH.

### 5.1 Enable (e*)

1. **No overlap.** After the enable, every section's Vo is within
   1.000 ± 0.050 V.
2. **Peak branch current** over the sections after the enable:
   - `_pc`: ≤ 1.3 × the final state's |i_r| extreme;
   - `_5v`: within ±30% of D57's first cycle at 5 V;
   - `_0v`: ≥ 0.7 × D57's first cycle at 0 V.
3. **Settling.** Vm within 2% of its final value, and the high side's
   turn-on V_DS within 0.3 V of its final value, by 50 µs after the
   enable (`_pc`, `_5v`).
4. **The same final state as A101** (one attractor):
   - Vm ±0.1 V;
   - high-side V_DS ±0.2 V;
   - branch current extremes ±5%;
   - low-side turn-on V_DS ≤ 0;
   - Vo ±1 mV.

### 5.2 Load steps (s*)

1. **No overlap.**
2. **Vo extreme** within ±15% of A100's reference for the same step
   (−62.5 A: +122 mV; +62.5 A: −127 mV).
3. **Peak branch current** after the step ≤ 1.5 × its value before the
   step.
4. **After the step** (last 200 periods):
   - Vm within ±0.5 V of D57's `load` prediction;
   - high-side turn-on V_DS within ±0.7 V of it (1.25 nH) or ≤ 1.0 V
     (0.75 nH);
   - low-side turn-on V_DS ≤ 0.
   - **Reported as not settled if Vo is not within 5 mV of 1.0 V.**

### 5.3 The 2% target (ref_2pct, n*)

1. **ref_2pct** is soft: high-side turn-on V_DS within ±0.3 V of D51's
   2% orbit, per phase.
2. **The branch runs**, per phase against D57's 2% predictions:
   - Vm ±0.4 V;
   - V_DS ≤ 0.5 V (0.75 nH) or within ±0.5 V (1.25 nH);
   - branch extremes ±20%;
   - low-side turn-on V_DS ≤ 0;
   - no overlap;
   - ripple within ±3% of ref_2pct.

### 5.4 Realism (r125_lrair, c125_cm022)

1. **r125_lrair**, per phase against D57's `p125_lr_air`:
   - Vm ±0.4 V;
   - V_DS ±0.5 V;
   - branch extremes ±20%.
2. **c125_cm022:**
   - stable, no overlap;
   - Vm and V_DS within ±0.4 / ±0.5 V of A101's p125.

## 6. What stays assumed

- The bidirectional switch: α × EPC2067 dies (40 V; a ~12 V die would
  be smaller), its floating gate drive, and its zero-current detection
  (ideal in the co-simulation, spanned only in D57's bookkeeping).
- Lr's and Cm's parasitics beyond their series resistance.
- Temperature: 25 C only.
- The hard turn-on loss itself: three models, no measurement. Section
  3.2 shows that this is the one value the sign depends on.
