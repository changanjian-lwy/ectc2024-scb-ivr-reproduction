# A86 - the adopted P24 module controller with EPC2067's nonlinear Coss(V) (RESULTS)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-6 were written before any run.
- Section 7 was added after runs n0-n5, before n6-n8.
- Section 8 was added after D44 and the step check, before e1, e2 and n0b.

**Records:**
- `run_*.json`;
- `a86_summary.json`;
- `gate_pairs.json`;
- `a86_verify_step.json`.

**Model: the physical model** (A84's simulator plus a charge-based nonlinear
Coss step). Two mathematical-model studies accompany it:
- D44: equivalent-linear capacitance in D43's exact map;
- D45: a nonlinear-Coss event map built for this check.

Both are in `symbolic_derivations/03_P24_native/`.

## 0. Verdict

1. **With the datasheet Coss(V), P24's 2% target works.**
   - Every phase turns on predictively once per cycle, with no restart,
     and Vo is regulated to 1.0000 V.
   - Phase 4 carries -1.85 A at its turn-off and turns on at 10.24 V.
   - With the linear 1860 pF, the same 2% is restart-driven: +6.82 A at
     phase 4's turn-off (A82 run 5).
   - Criterion 2's dither at 2% is 1.04 A (n1) and 0.97 A (n8), at the
     1 A `PROJECT_DECISION` threshold. This is a margin statement.
2. **The lower bound moves from 2.5-3% (linear, A82) to 1.5-2%.**
   - 1%: phase 4 restart-driven (+5.74 A).
   - 1.5%: the edge. Soft on average but not periodic; the turn-off
     current swings between -4.3 and +2.6 A.
   - 2% and above: soft.
3. **At 2% the soft state is the only attractor.** Kicking phase 4's
   `dt_pred` to 20.2 ns at 250 us gives exactly one restart turn-on. From
   the next cycle phase 4 is predictive and soft again (n8), as A84 found
   for the linear model.
4. **The mathematical model confirms it independently.**
   - D45 is an event map with the same datasheet curve. It has ideal
     switches and ODE integration between events, and shares no numerics
     with this simulator.
   - At 2, 2.5, 3, 5 and 7.5% its regulated, valley-consistent orbits are
     all soft and stable.
   - They match these runs within 0.05 A for phase 4's turn-off current and
     0.03 V for its turn-on voltage.
5. **This is not an equivalent-capacitance effect. It is the shape of the
   high-side curve.**
   - No single linear capacitance reproduces the result (D44). The best
     swing-matched one, L2, gives -2.30 A at 3% and a restart at 2%.
   - This simulator at L2 agrees with D44 at L2 (runs e1 and e2). So the
     two models agree at equal linear capacitance, and differ from the
     nonlinear case only through the curve.
   - With the datasheet curve on the high sides only, D45 reproduces the
     full result. On the low sides only, it does not (D45 part E).
6. **Other quantities barely move.**
   - Peak Vds 25.0-25.5 V (EPC2067: 40 V).
   - Conduction loss 12.1-12.7 W at 250 W out.
   - Vo enters the 1% band 67-70 us after the handover.

## 1. Runs (last 50 cycles)

All runs use A82's adopted controller:
- predictive valley turn-on, with the corrector also learning at restart
  turn-ons;
- trim 0.5, no reactive ZVS, 10 ns latency;
- fixed shifts, restart 20 / 400 ns;
- loop ki 0.25 ns/V;
- zero start, 388.61 us.

| run | target | Coss | phase 4: turn-on; current at its turn-off, mean [min, max]; Vds at turn-on | phases 1-3 Vds at turn-on | phase-4 `dt_pred` | period | Ton | dither | P_cond | criterion 2 | linear counterpart (1860 pF) |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---|---|
| n0 (gate) | 3% | linear | predictive; -2.26 [-2.63, -1.88] A; 10.16 V | 9.54-9.56 V | 8.62 ns | 224.65 ns | 17.465 ns | 0.79 A | 12.18 W | pass | = A82 run 3 |
| n6 | 1% | datasheet | **restart**; +5.74 [+5.57, +5.90] A; 10.51 V | 10.03-10.07 V | 34.81 ns (cap) | 223.06 ns | 17.405 ns | 1.05 A | 12.12 W | fail | restart, +7.95 A (D45 part D) |
| n7 | 1.5% | datasheet | predictive, **not periodic**; -0.18 [-4.32, +2.63] A; 10.38 V (max 11.12) | 9.97-10.01 V | 10.00 ns | 223.75 ns | 17.417 ns | 4.61 A | 12.14 W | fail | restart, +7.57 A (D45 part D) |
| **n1** | **2%** | datasheet | **predictive; -1.85 [-2.35, -1.36] A; 10.24 V** | 9.87-9.90 V | 9.81 ns | 224.41 ns | 17.442 ns | 1.04 A | 12.17 W | soft, no restart; dither 1.04 A | **restart, +6.82 A, 10.68 V (A82 run 5)** |
| n8 | 2%, kick at 250 us | datasheet | predictive; -1.85 [-2.32, -1.39] A; 10.23 V | 9.87-9.90 V | 10.01 ns | 224.40 ns | 17.442 ns | 0.97 A | 12.16 W | pass | - |
| n2 | 2.5% | datasheet | predictive; -2.53 [-2.89, -2.18] A; 10.07 V | 9.75-9.77 V | 9.57 ns | 225.33 ns | 17.476 ns | 0.83 A | 12.20 W | pass | soft on average, not periodic (A82 run 4) |
| n3 | 3% | datasheet | predictive; -3.19 [-3.61, -2.76] A; 9.90 V | 9.61-9.63 V | 8.93 ns | 226.38 ns | 17.518 ns | 0.90 A | 12.23 W | pass | -2.26 A, 10.16 V (A82 run 3) |
| n4 | 5% | datasheet | predictive; -5.74 [-6.21, -5.27] A; 9.11 V | 8.95-8.96 V | 8.20 ns | 231.67 ns | 17.741 ns | 1.002 A | 12.41 W | soft, no restart; dither 1.002 A | -5.10 A, 9.24 V (A82 run 1, ki 1.0) |
| n5 | 7.5% | datasheet | predictive; -8.96 [-9.21, -8.73] A; 8.02 V | 7.99-8.04 V | 7.70 ns | 239.69 ns | 18.071 ns | 0.49 A | 12.69 W | pass | -8.43 A, 7.99 V (A79 run 3) |

**Amendment 8** (linear, D44's swing-matched L2: per device 1796.9 pF high, 2424.5 pF low):

| run | target | phase 4 | D44 L2 prediction |
|---|---:|---|---|
| e1 | 3% | predictive; -2.22 [-2.72, -1.73] A; 10.21 V | soft, -2.30 A, 10.16 V |
| e2 | 2% | restart; +6.25 [+6.11, +6.40] A; 10.67 V | restart, +6.25 A |

Both are inside D44 Section 5's tolerance (+/-0.3 A, +/-0.15 V).

**Notes.**
- **n8.**
  - The kick at 250.07 us gave one phase-4 restart, at 250.24 us.
  - n1 and n8 both pass through 275 phase-4 restarts during the zero
    start; the last is at 172.2 us, 83 us after the handover.
- **n7** is the edge: the corrector keeps phase 4 predictive on average,
  but the orbit does not settle (compare A82 run 4 at 2.5% with linear
  Coss).
- **`P_cond`** is R times each phase's integral of i^2 dt per cycle (A78),
  at P_out = 250 W. Peak current is 170-176 A.
- **Timing.** Vo is 1.0000 V in every run, and settles into the 1% band
  66.9-69.9 us after the handover.

## 2. Checks

**Regression gates.**
- n0 (option off, run before the CLI change) and n0b (after it) each
  replay A82 run 3 bit-identically: 1791 sections, difference 0.0, equal
  end state.

**The curve** (BOUNDARY Section 2):
- Coss at 20 V: 1063 pF against the printed 1071 pF;
- Co(tr): 1864 pF against 1860 pF;
- Co(er): 1598 pF against 1597 pF.

**The nonlinear step against an independent integrator** (`a86_verify_step.py`).
- **Setup.**
  - Phase 4's node x4 is a 1-D nonlinear LC while phases 1-3 are low.
  - The reference is solve_ivp (DOP853, rtol 1e-12) on the PCHIP curve
    itself, not this simulator's 1 mV table.
  - The full-circuit step starts from the same state.
- **Result.**

  | case | valley time, full / ODE | valley Vds, full / ODE | max \|dx4\| |
  |---|---|---|---:|
  | -1.85 A, linear | 9.258 / 9.262 ns | 9.7511 / 9.7482 V | 2.2 mV |
  | -1.85 A, nonlinear | 10.286 / 10.290 ns | 9.7930 / 9.7900 V | 2.1 mV |
  | -3.19 A, linear | 8.265 / 8.268 ns | 9.3788 / 9.3756 V | 2.5 mV |
  | -3.19 A, nonlinear | 9.212 / 9.215 ns | 9.4691 / 9.4659 V | 2.4 mV |
  | -5.74 A, linear | 7.324 / 7.326 ns | 8.5053 / 8.5014 V | 3.3 mV |
  | -5.74 A, nonlinear | 8.152 / 8.155 ns | 8.6939 / 8.6900 V | 3.1 mV |
  | fall a3 -> 0 at +120 A, linear | 0.9121 / 0.9125 ns | - | - |
  | fall a3 -> 0 at +120 A, nonlinear | 1.0806 / 1.0811 ns | - | - |

- **Reading.** The differences are the same with and without the
  nonlinear curve. They come from the full circuit's a3 and out motion,
  which the 1-D reduction omits, not from the nonlinear step.

**Solver statistics** (n1-n8).
- 38.9 M steps per run, 1.75-1.95 chord iterations per step.
- Full Newton was needed in 1.0% of the steps (at most 10 iterations in
  total).

## 3. Cross-check in the mathematical model

**D45's method.**
- Regulated (Vo = 1 V by Ton) orbits with a 20 ns restart.
- Each soft phase's delay equals its natural valley time, measured from
  the low-side turn-off itself (D45 Section 7).
- Floquet multipliers are from the section map.

| target | A86 (physical, datasheet) | D45 (mathematical, datasheet) | D45 linear 1860 pF |
|---:|---|---|---|
| 1% | restart, +5.74 A, 10.51 V | restart, +5.77 A, 10.53 V (valley at 21.07 ns, after the 20 ns restart) | restart, +7.95 A |
| 1.5% | edge: not periodic | soft fixed point, -0.81 A, 10.37 V; \|mu\|max 0.9957 (see below) | restart, +7.57 A |
| 2% | soft, -1.85 A, 10.24 V | **soft, -1.82 A, 10.21 V; \|mu\|max 0.9927** | restart, +6.81 A |
| 2.5% | soft, -2.53 A, 10.07 V | soft, -2.55 A, 10.05 V | soft, -1.23 A |
| 3% | soft, -3.19 A, 9.90 V | soft, -3.22 A, 9.87 V | soft, -2.29 A |
| 5% | soft, -5.74 A, 9.11 V | soft, -5.79 A, 9.09 V | soft, -5.16 A |
| 7.5% | soft, -8.96 A, 8.02 V | soft, -8.97 A, 8.01 V | soft, -8.45 A |

**The one disagreement: 1.5%.**
- D45 has a self-consistent, stable soft fixed point at 1.5%. This
  simulator's corrector does not settle on it.
- The linear model shows the same at its edge, 2.5%: a D43/D45 soft fixed
  point, while A82 run 4 is not periodic.
- In both cases phase 4's current at that fixed point is small: -0.81 A
  (nonlinear, 1.5%) and -1.23 A (linear, 2.5%).
- Why the physical corrector does not converge there is open. Its 0.2 ns
  steps, 10 ns latency, trim and loop are not in the fixed-point model.
- So the models agree on the practical bound (2%), and the mathematical
  fixed point reaches slightly lower.

**The restart branch at 2%** (D45 part C).
- The phase-4 restart orbit exists: +1.99 A at phase 4's turn-off.
- Its natural valley is at 15.59 ns, before the 20 ns restart. Letting the
  delay follow it returns to the soft orbit.
- With linear Coss the valley is at 21.57 ns, so there is no escape.
- This is the mathematical counterpart of n8.

**Delays and period at 3%.**

| | phase delays | period |
|---|---|---:|
| D45 | 10.42 / 10.01 / 10.01 / 9.15 ns | 226.49 ns |
| A86 (`dt_pred`) | 10.43 / 10.06 / 9.85 / 8.93 ns | 226.38 ns |

**Which side's curve matters** (D45 part E, 3%). The other side is held at
L2's constant.

| curve on | phase 4 at turn-off | at 2% |
|---|---:|---|
| high sides only | -3.24 A | soft, -1.86 A |
| low sides only | -2.20 A (close to L2's -2.30 A) | restart, +6.37 A |

## 4. Consequences for earlier results

- **A78 and A82: "P24's stated 1-2% is not enough".** This is qualified.
  - With EPC2067's typical datasheet Coss(V), the top of P24's range (2%)
    works.
  - 1% and 1.5% still do not.
  - The linear-model lower bound (2.5-3%) becomes 1.5-2%.
  - The margin is thin: 1.5% is already the edge.
- **D43 and D44's valley times were one 0.25 ns grid step early** (D45
  Section 7). With the correction, phase 4's current changes by at most
  0.13 A, and no D43 conclusion changes.
- **A candidate question for the advisor.** Did P24 choose 1-2% with the
  high-side Coss(V) in mind? In our models only 2% works, and it works
  because of the high-side curve's shape.

## 5. Limits

- **The circuit.** A79's idealised module otherwise:
  - ideal diodes (no reverse-conduction drop; datasheet Fig. 8 is the
    next step);
  - lumped R, no package or PCB parasitics;
  - Cout 4.672 mF (inherited, suspect);
  - one module.
- **The curve.** The typical curve at 25 C and VGS = 0. Device-to-device
  spread and temperature are not covered. The digitisation matches the
  printed values within 0.06-0.7%.
- **The mechanism is only located, not isolated.** Part E locates it in
  the high-side curve; which transition carries it is not isolated.
  - **Hypothesis:** the high sides' small capacitance over 12-24 V
    (charge-equivalent 1240 pF), which every hard turn-on and turn-off
    sweeps. No single constant can represent both it and the 10-14 V range
    of the valley ring.
- **Statistics.**
  - One kick per run.
  - The 1.5% edge was run once.
  - The dither threshold (1 A) is a `PROJECT_DECISION`. At 2% and 5% the
    dither sits at it: 0.97-1.04 A and 1.00 A.

## 5a. Reproduction

```
zsh run_a86.sh      # n0-n5
zsh run_a86b.sh     # n6-n8 (BOUNDARY Section 7)
zsh run_a86c.sh     # e1, e2, n0b (BOUNDARY Section 8)
python3 a86_analyze.py
python3 a86_verify_step.py
```

The mathematical-model side:

```
python3 -m scripts.audit_p24_ceq_orbits
python3 -m scripts.audit_p24_nonlinear_orbits --part A   # and B, C, D, E
```

The datasheet and paper PDFs are not in this repository.
