# How far P24 and P25 are reproduced

Written 2026-10-09 at the close of the work. Every item of the two papers, against what this work found and where.
P24 = Khorasani et al., ECTC 2024 (48 V → 1 V, 1 kW, the target system). P25 = Khorasani et al., APEC 2025
(12 V → 1 V, 0.5 MHz, 200 W prototype, 3 phases × 3 modules). Source status per equation and figure:
`paper_locked/00_boundaries/SOURCE_COVERAGE_MATRIX.md`. Plant versions (V0 ideal switches ... V5 final gate-level
plant): `reports/FINAL_SPEC_COVERAGE.md`.

Marks: **✓** agrees · **≠** reproduced, different number at this design point · **✗** does not hold, with evidence ·
**+** not in the paper, added here · **–** not done.

## 1. P24 (ECTC 2024)

P24 is analytical and conceptual: equations, Table I-III calculations, Fig. 4's theoretical waveforms and the
Fig. 5-6 package concept. It has no measurement, controller, start-up, loss or efficiency figure (losses, copper,
vias and thermal are named future work).

| # | P24 item | This work | |
|---|---|---|---|
| 1 | Fig. 3 topology: multi-phase series-capacitor buck at the CCM/DCM boundary | circuit model + Verilog controller in co-simulation, one module and four modules (16 phases) | ✓ |
| 2 | Eqs. (1)-(3): D = 8.33 %, Ton, I_L,pk = 125 A | recomputed (`TABLE1_PRIMARY_SOURCE_EXTRACT.md`) | ✓ |
| 3 | Fig. 4 / Sec. II-B: three intervals per phase (QH1 + QL2, then the Coss commutation, then the negative current) | the event model (D63) and the co-simulation run this sequence | ✓ |
| 4 | series capacitors balance by the adjacent phases' amp-seconds | rails self-balance; after a ±10 % line step they re-divide within 25 µs (V0) | ✓ |
| 5 | Table 3 switches, nM = 4: 2 × EPC2067 high side, 3 × low side per phase | adopted | ✓ |
| 6 | Table I L_crit (4 phases, 5 MHz: 2.68 nH) | Eq. (4) gives 1.47 nH; the ratio is 1.83 / 2 / 2 / 1 for nP 4 / 6 / 8 / 16 - a table error, not one formula. This work uses Eq. (4) | ≠ (paper inconsistent) |
| 7 | "1-2 % negative current gives ZVS for all phases" | with P24's own inductances and node, full high-side ZVS needs ≥ 5.3 % (any Table I value) and ~27 % at 1.47 nH (D57, A67, A78-A86); at 2 % the high side turns on at ~9.9 V. Chosen 12.5 %: low sides ZVS, high sides at their valley, 3.3-3.9 V of the 12 V rail (V0) | ✗ |
| 8 | "zero switching loss, so the frequency is limited only by the minimum on-time (25 MHz for 4 phases at 48 V)" | the 25 MHz arithmetic holds; the loss does not vanish: 16.8 W at 5 MHz against 1.6 W at 1 MHz per module (A115), while inductor copper rises as L ∝ 1/f. Optimum 2.5 MHz with an MPC-class inductor, 5 MHz with an air-core stripline (D64, D72). Above 5 MHz not simulated | ✗ (as a design rule) |
| 9 | Eqs. (5)-(6) / Table 3: embedded inductor count (nM = 4: 25 units of 5 A) | formula reproduced; 29-40 HBS1-class units per phase for the 144 A steady peak and the 200 A transient budget (D72) | ≠ |
| 10 | Figs. 5-6 package (8 modules of 10 × 10 mm, 12 dies each) | geometry transcribed; a 250 W module's 20 dies (185 mm²) do not fit 10 × 10 mm → 10 × 20 mm (D75). The conclusion's "40 cm × 25 cm" is Fig. 6's 40 × 25 mm | ≠ |
| + | controller, start-up, load / line transients | frozen RTL controller; zero start; ±62.5 A load step +15.3 / −11.9 mV (V0) | + |
| + | current sharing ("the primary challenge", no method in P24) | one common on-time; sharing is an inductor-matching spec (±5 %, C14 / D66) | + |
| + | losses and efficiency | 86.6-87.7 % before core loss, 78-85 % with it, ~73-82 % at 85 °C with the package (loss model on V0 waveforms; D62, D72, D73, D76) | + |
| + | package parasitics, gate drive, thermal | loop ≤ 50 pH, 3.0 / 0.3 Ω ±20 % drive, driver interlock (V5, FINAL_SPEC_COVERAGE); thermal D73-D80 | + |
| – | 6 / 8 / 16 phases, 10-100 MHz, the 8-module Fig. 5 system, 12 V → 1 V, mechanics / CTE / EMI | Table I recomputed only; four modules simulated | – |

## 2. P25 (APEC 2025)

P25 is the circuit-level companion with a measured prototype. Here it supplied circuit detail P24 lacks and its own
operating point tested the mathematical model (D10-D42, closed 2026-10-06 when the mathematical model moved to P24's
module) and the physical model (A67-A69).

| # | P25 item | This work | |
|---|---|---|---|
| 1 | Figs. 1-2: topology and the 15-mode order (Fig. 3 shows 9, the text explains 6) | all 15 modes from node equations (D15); M1-M15 complete at P25 scale (D40) | ✓ |
| 2 | ZVS of every switch with 5-10 % negative current (Mode 4; "up to 5 %" in Sec. III), measured in Fig. 4 | P25's point needs 1.5-2.0 % (A67); the periodic orbit has ZVS on all three high sides (D41) | ✓ |
| 3 | Sec. III: one current sensor per module suffices | D41: phase 1 sensed, phases 2-3 at fixed shifts → a periodic ZVS orbit (1.946 µs); weakly unstable lossless, stable at P25's estimated 4.9 mΩ (\|λ\| 0.926). A69, an independent circuit simulation, reproduces period (3.5 ps), growth (1.059 / 1.060) and decay (0.929 / 0.926) | ✓ |
| + | (not in P25) | started far from the orbit, the fixed-shift control deadlocks (timed low sides turn off without enough negative current, nothing forces a turn-on): hardware needs a timeout (A69) | + |
| 4 | Eq. (17) conversion ratio; Eqs. (18)-(19) D ≤ 1/nP | adopted; P24's 4 phases at 48 V give 8.33 % | ✓ |
| 5 | Table II "D = 0.26 %" | Eq. (17) gives 0.25 | ≠ (typo) |
| 6 | Table III 22 nH at 0.5 MHz; Fig. 5 50 A phase peak | Eq. (20) gives ~32 nH at this point; 22 nH and 500 ns give a 66 A ideal ramp, 59-61 A in the event model, against Eq. (2)'s 44.4 A and the measured 50 A (captured at 100 kHz, not 500 kHz) (`02_P25_native/31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md`) | ≠ (operating point inconsistent) |
| 7 | closed-form mode equations (5)-(16), ripple (21)-(22), stress Table I | not checked one by one; the node equations were solved instead | – |
| 8 | the measured prototype (Figs. 4-5), 3 × 3 modules at 200 W | no hardware; one module, three phases, open loop (Ton and load held, Vo 0.844 V) | – |
| 9 | efficiency | P25 reports none | |

## 3. The link between the two papers

The negative current that ZVS needs, as a fraction of the peak, is about √(L·C_node) / Ton (A67):

| | P25 (12 V, 0.5 MHz, GS61008T) | P24 (48 V, 5 MHz, EPC2067) |
|---|---|---|
| flip time √(L·C_node) | 6.7-9.0 ns | 3.7-4.4 ns |
| on-time | 500 ns | 16.7 ns |
| needed | 1.5-2.0 % | 22-26 % |
| the paper's value | 5-10 % (ample) | 1-2 % (an order short) |

The ZVS mechanism is real and P25's measurement is consistent with it; the percentage does not carry from 12 V /
0.5 MHz to 48 V / MHz. That is why P24 item 7 fails.

## 4. In one paragraph

Of P24's ten checkable items, five agree (topology, equations, the interval sequence, capacitor balance, device
choice), two give different numbers at this design point (inductor count, package size), and three do not hold as
printed: the two performance claims (1-2 % negative current gives full ZVS; zero switching loss leaves the frequency
free) and Table I's inductance against its own Eq. (4). P25's two central claims (ZVS at a small negative current,
one sensor per module) hold at P25's own operating point in two independent models; its data carry a duty-cycle typo
and an inductance / peak-current inconsistency; its hardware and the three-module closed loop were not reproduced.
What neither paper describes - controller, start-up, multi-module operation, losses, package parasitics, gate drive,
thermal - is this work's.
