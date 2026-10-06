# D68 - the slow hard turn-on, from the node charge

2026-10-07. Code: `scripts/p24_slow_turn_on.py` → `diagnostics/D68_slow_turn_on.json` (A145's single-edge harness,
plus the records of A145, A151 and A152). Tested prospectively by A153.

## 1. Why

A151 / A152 set the package's drive spec in co-simulation: a slow hard turn-on (36 A/ns at 50 pH, 18 A/ns at 100 pH)
with the 72 A/ns turn-off, and a start-up on-time of 35.5 ns + 36 A ÷ (turn-on di/dt). Both numbers were found by
runs, not derived. With them the spec holds only at the tested points; Mihai's loop inductance or driver would need
new runs. This note derives both from one quantity, the charge of the switch node, and gives laws for any L and
di/dt.

## 2. A hard turn-on with a current ramp

The plant's turn-on (A145) is a channel current rising at di/dt while V_DS > 0. Before the switch node can rise, the
channel must take over the phase current i1; then the excess charges the node. In series sits the loop L, which
takes L·di/dt of the voltage while the current ramps. The ramp ends when V_DS reaches 0:

  Q(t_r) / C-part + L·di/dt = V_on,   with  Q(t_r) = ½·di/dt·t_r² − i1·t_r .

**Harness** (A145's single-edge plant, SH1 on at 12 V, 2 + 3 EPC2067, Q 7 damping), 63 edges:
- For small x = L·di/dt the ramp moves the whole node charge, **Q₀ ≈ 162 nC** (2 + 3 EPC2067 swung by 12 V),
  so **t_r = √(2 Q₀ / (di/dt))**: 7.4 ns at 6 A/ns, 4.2 ns at 18, 2.0 ns at 72.
- **Q / Q₀ and η depend on x only**, not on L and di/dt separately (x = 1.8 V: 0.97 and 0.60 at 50 / 100 / 150 pH):

| x = L·di/dt | ≤ 0.6 V | 0.9-1.35 V | 1.8 V | 2.4-2.7 V | 3.6 V | 5.4 V | 7.2 V | 10.8 V |
|---|---|---|---|---|---|---|---|---|
| Q / Q₀ moved by the ramp | 0.98-1.00 | 0.93-0.95 | 0.97 | 0.97-0.98 | 0.89-0.90 | 0.65 | 0.53 | 0.44 |
| η (lost volt-seconds / V_on t_r) | 0.64 | 0.62-0.64 | 0.60 | 0.55-0.57 | 0.53 | 0.55 | 0.58 | 0.60 |

What the ramp does not move, the loop's LC ring moves. That is the overshoot (Section 4).

## 3. The start-up on-time (the 36 A term)

Mode S is open loop at a fixed 400 ns period, so it is a voltage source: Vo ≈ V_rail (Ton − t_lost) / T0 − IR.
Every hard turn-on loses t_lost ≈ η·t_r ∝ (di/dt)^-½ of the on-time. Co-simulated, Vo before the handover
falls by 0.0283 V per ns lost (A152's calibration; 12 V / 400 ns = 0.030 ideal).

**Law:** t_lost(d) − t_lost(72) = K (d^-½ − 72^-½).
- Harness, from the node charge: K = 10-15 ns·(A/ns)^½ (more with the phase current at turn-on, i1 0 → 5 A).
- Co-simulation (A151's seven n0 runs against A145's 72 A/ns run at the same L, ton 35.5): **K = 15.6**
  (by L: 15.3 / 16.7 / 14.6 at 50 / 100 / 150 pH). Residuals ±0.23 ns, rms 0.15 ns (Vo ±0.007 V).
- A152's rule, 36 A / di/dt, has rms 0.35 ns on the same points (best 1/di/dt fit 37 A: 0.34 ns). Its 36 A is
  not a current in the circuit; it is a 1/di/dt fit to a √ law over 18-36 A/ns.
- The harness is ~30 % below the co-simulation at 100-150 pH. The records point at the ladder: with the slow
  turn-on rail 1 rises to 12.66 V and rail 4 falls to 11.29 V, so the phases lose different on-times, which one
  edge cannot show.

**Compensation:** ton_S(d) = 35.5 ns + 15.6 (d^-½ − 72^-½), referred to the 72 A/ns start-up that A145 found clean
(141-147 A at the handover).

| turn-on di/dt (A/ns) | 72 | 48 | 36 | 24 | 18 | 12 | 9 |
|---|---|---|---|---|---|---|---|
| D68 ton_S (ns) | 35.5 | 35.9 | 36.1 | 36.85 | 37.3 | 38.2 | 38.9 |
| A152's rule (ns) | 36.0 | 36.25 | 36.5 | 37.0 | 37.5 | 38.5 | 39.5 |

Within 0.6 ns down to 9 A/ns. A152's rule over-compensates slightly, which is the safe side (at 100 pH / 18 A/ns
the handover peak goes 174 → 148 → 141 A for ton 36.5 → 37.5 → 38.5).

## 4. The line-step overshoot

The binding overshoot is mechanism B (A144): after a rising line step phase k−1 turns on hard at 17-19 V and rings
SH_k. The ramp's share of the swing (Section 2) and its time against the ring's period, t_r / T ∝
√(Q / (di/dt · C)) / √(L C), depend on **x = L·di/dt only**. The co-simulation collapses on x too (whole-run max V_DS,
l_p48_1us, turn-off 72 A/ns, Q 7):

| x (V) | 0.9 | 1.35 | 1.8 | 2.7 | 3.6 | 7.2 | 10.8 |
|---|---|---|---|---|---|---|---|
| max V_DS (V) | 34.3 (33.9 / 34.6) | 36.5 | 36.8 (36.4-37.1) | 38.0 | 41.5 (41.2 / 41.8) | 51.0 | 54.7 |
| from | 100×9, 50×18 | 150×9 | 50×36, 100×18 | 150×18 | 50×72, 100×36 | 100×72 | 150×72 |

- **Rule: L · di/dt_on ≤ x* = 3.2 V keeps every switch ≤ 40 V**, i.e. di/dt_on ≤ 64 / 43 / 32 / 26 / 21 A/ns at
  50 / 75 / 100 / 125 / 150 pH. x* is about a quarter of the 12 V rail: the loop may take a quarter of the swing.
- The harness collapses on x as well but sits 4-14 V below the co-simulation (its rails are 12 V; after the step
  rail 1 is ~16 V), so the rule is calibrated on the co-simulation, not the harness.
- **Valid to 150 pH.** Above it the 72 A/ns turn-off ring (mechanism A) binds on its own: steady 31.1 V at 150 pH,
  48.8 V at 300 pH whatever the turn-on (A152). Between 150 and 300 pH it is not measured.
- The spec points have margin: S50 (36 A/ns, x 1.8 V) and S100 (18 A/ns, 1.8 V) sit at 36.4-37.6 V.

## 5. Limits

- One edge model: a linear current ramp, no gate charge or Miller plateau. Which gate resistor gives a given
  di/dt is the driver's question (Mihai).
- K and x* are calibrated on 7 and 12 co-simulated runs at Q 7, 25 °C, nominal L and Cs; A152's corners (L × 0.7 /
  1.3) stayed ≤ 37.6 V at x = 1.8 V.
- The overshoot rule covers the +4.8 V / 1 µs line step, the binding row; load steps and start-up were lower in
  every run so far (A151, A152).
