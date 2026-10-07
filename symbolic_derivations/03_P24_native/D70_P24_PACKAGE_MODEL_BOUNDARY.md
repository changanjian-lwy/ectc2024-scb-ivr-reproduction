# D70 - the package model's boundary: what the plant holds, what only the budgets hold, what is missing

2026-10-07. An audit after an external review of the package layer (D65-D69, A144-A162); no new runs. It fixes what the
package conclusions may claim and checks the one-way loss estimates, the damper's physical meaning and double counting.

## 1. The ledger

| element | where it lives | value / range | conclusions resting on it |
|---|---|---|---|
| phase inductor | plant | 2.933 nH, R 0.54 mΩ per phase (DC only) | every co-simulated result |
| inductor core loss, saturation, AC resistance | **not modelled** | MPC-class R/L 79 µΩ/nH in D62 only | 2.5 MHz choice (D67), 200 A budget (≥ 40 HBS1-class units) |
| switches: on-state | plant: g_on 1e7 (no R_on); budget: R_on 1.55 mΩ (× 1.59 at 125 °C) | D62 | efficiency |
| switches: Coss(V), reverse conduction | plant (datasheet curves, 2 + 3 devices) | EPC2067 | ZVS, node charge (D68 Q₀), turn-on V_DS |
| switching edges | plant: linear current ramps (A145); **no gate model** | 6-144 A/ns | D68 laws, A151-A161; D69 resistors are an estimate |
| commutation loop | plant: series L on each high-side drain + **ideal parallel damper** rp | 50-300 pH, ring Q 7 (also 15-300, undamped) | all package V_DS, the turn-on window, Q ≤ 30 |
| series capacitors Cs | plant: ideal 6 µF; budget: ESR 1 mΩ (D62), ≤ 0.5 mΩ (D65) | | ladder dynamics |
| Cs ESL, Co ESR / ESL | **not modelled** | | ladder ringing, output ripple |
| output capacitor, load | plant: ideal Co 4.672 mF per module, 4 mΩ load | | load-step Vo |
| module-to-module and module-to-load path (R, L) | **not in the plant**: four modules joined at one ideal node each 4 ns window | budget: lateral copper (D65) | four-module sharing, load steps |
| lateral Vo / GND copper, vias, strip | budget only (D65, one-way) | 35 / 86 / 429 µm: 30.7 / 12.5 / 2.5 W | package efficiency |
| input source | plant: ideal 48 V with programmed steps | | line-step rows |
| temperature | assumed (25 °C; 125 °C in the budget only) | | hot efficiency (no thermal model) |
| Coss hysteresis, common-source and gate-loop inductance, EMI | **not modelled** | | |

## 2. Checks

**2.1 Is the one-way copper estimate valid?** The lateral copper of one module (Vo + GND) is R = 30.7 W / (250 A)² =
0.49 mΩ at 35 µm, a 123 mV drop at full load: 12 % of Vo. The converter would have to deliver ~1.12 V at its own
terminals, so the estimate made on 1.0 V waveforms is **not valid at 35 µm**. At 86 µm: 0.20 mΩ, 50 mV (5 %); at
429 µm: 0.04 mΩ, 10 mV (1 %). The one-way budget is self-consistent for a drop ≲ 2 %, i.e. ≳ 215 µm of copper.

**2.2 Does a path resistance change the four-module sharing?** With a common Ton a module is close to a current source
(D58: per phase (V_rail − Vo) Ton / (2L) − i_neg). A path resistance R raises that module's terminal voltage by I R and
lowers its current by about I R / (V_rail − Vo): 0.12 V / 11 V ≈ 1.1 % at 35 µm, 0.45 % at 86 µm, a weak droop that
helps sharing. A ±50 % path mismatch moves the shares by ~±0.5 %, small next to the ±5 % inductor matching that sets
200 A (D66). To first order the interconnect matters for loss and operating point, not for DC sharing; its inductance
(load steps, module interaction) is not covered by this argument.

**2.3 What the damper stands for.** A ring of quality Q in a loop L at ω = 2π / T needs a series-equivalent resistance
R_s = ωL / Q. With the harness's ring periods (2.40 / 3.43 ns at 50 / 100 pH; ~4.2 ns at 150 pH by √L):

| | 50 pH (~420 MHz) | 100 pH (~290 MHz) | 150 pH (~240 MHz) |
|---|---|---|---|
| Q 7 | 19 mΩ | 26 mΩ | 32 mΩ |
| Q 30 | 4.4 mΩ | 6.1 mΩ | 7.6 mΩ |

Q 30 asks for a few mΩ at a few hundred MHz, the order of capacitor ESR plus skin-effect copper; Q 7 asks for
20-30 mΩ, which a tight layout may not have without a deliberate damping element (e.g. an RC snubber, whose own C V² f
loss is in no budget). **The Q 7 baseline is an assumption, possibly a generous one; Q ≤ 30 is the tested requirement;
the real Q needs a layout or a measurement (A146's capture gives it).**

**2.4 Double counting.** The damper dissipates each switching event's ring energy (A145's loop-dependent loss: the edge
power increase plus the damper). D62's Cs ESR term uses the switching-frequency phase currents, D65's copper the output
current: different currents and frequency bands, so the terms add without overlap. Whatever damps the real loop
dissipates the same ring energy; only where it heats is open.

**2.5 Package-inclusive efficiency, first-order sum** (each term on the nominal waveforms, uncoupled; converter 25.9 W
= 90.61 %; loop-dependent loss 1.6 / 6.4 W at 50 / 150 pH; slow turn-on +0.1 / +0.2 W):

| lateral copper | loop 50 pH | loop 150 pH |
|---|---|---|
| 35 µm | 81 % (estimate not valid, 2.1) | 80 % (idem) |
| 86 µm | 86.2 % | 84.8 % |
| 429 µm | 89.3 % | 87.7 % |

At 125 °C the switch conduction adds 7.7 W (D62): about −2 points on each entry.

## 3. What the package conclusions may claim

- **Loop bound:** "In the tested model (ring Q 7 with an ideal damper, 25 °C, nominal Cs, linear current-ramp edges;
  A152's matrix and four modules) the turn-on window ~20 A/ns ≤ di/dt_on ≤ 3.0 V / L closes near 150 pH, where the
  worst switch reached 39.4 V (0.6 V margin). A candidate, not a hardware limit: above it the drive can still hold
  40 V at an efficiency cost (A154), and the regulation side rests on four turn-on rates."
- **Damping:** "With an ideal parallel damper, ring Q 15 and 30 hold and Q ≥ 100 or none loses the valley tracking.
  The physical damping and its loss location are open."
- **Efficiency:** "estimated (loss model on simulated waveforms)", never "measured"; package-inclusive figures as in
  2.5, with their copper condition.
- **Late fires:** "no consequence observed in the tested rows; they fall 2-17 µs after the −8 V ramp; which timed edge
  is late is not identified; A161's criterion 3 stays failed."
- **Temperature:** "assumed junction temperature; no thermal model."

## 4. The next dynamic element

The per-module output path (R and L) between each module and the shared output node: the largest unmodelled element
and the only coupling between modules. Its DC effects are bounded above (2.1-2.2); the plant is needed for its
inductance (load steps, module interaction), whose value needs Fig. 5's strip geometry, not yet estimated. Before
that, the copper requirement should keep the one-way estimate valid (drop ≲ 2 %).
**Decided by D71:** the path does not need the plant now. Its module-to-module motion is negligible (≤ ~1 mV); its
common motion is an inductive drop in front of the load (L/4 · di/dt, 16-157 pH), set by the output-capacitor
placement, the processor-side decoupling and the load slew, which P24 does not give. They become interface requirements.
**D72 (inductor array):** 90.61 % uses the 500 nH HBS1 unit's R/L (~170 units per phase). With 29-40 current-rated
units per phase the converter is 86.6-87.7 %, and Section 2.5's package-inclusive figures become ~81-86 %.
