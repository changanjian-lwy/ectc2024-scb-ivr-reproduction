# D69 - which gate resistors give the drive spec (estimate from EPC2067's datasheet)

2026-10-07. Status: **estimate**, not simulated (the plant's edges are current ramps; it has no gate model). Inputs:
EPC2067 datasheet (typical, 25 °C): C_ISS 2178 pF, R_G 0.4 Ω, Q_G(TH) 4.2 nC, Q_GS 5.3 nC (37 A), plateau 2.3 V at
37 A (Fig. 7), transfer curve ~0 A at 1.9 V, 50 A at 2.4 V, 200 A at 3.0 V (Fig. 2), Q_OSS(12 V) ≈ 27 nC (Fig. 6).

## 1. Why

D68 / A153-A155 state the package drive as di/dt values: turn-on ≤ 3.2 V / L, turn-off 72 A/ns (≤ 10 V / L above
150 pH). Mihai's first question is whether P24's driver can do that. This note turns the di/dt values into gate
resistances, so the question can be answered from a schematic.

## 2. The current rise is set by the gate current

While the drain current rises, the gate sits between threshold and plateau, and the channel current follows the gate
charge: from Q_G(TH) to Q_GS the current goes 0 → 37 A on 1.1 nC, i.e. **33.6 A of drain current per nC**
(C_ISS × 0.5 V; the transfer curve's 100-200 A/V agrees). So per device di/dt ≈ 33.6 A/ns per ampere of gate current.

- **Turn-on** (5 V drive, gate at ~2.1 V during the rise): I_G ≈ 2.9 V / R_tot.
- **Turn-off** (0 V drive, gate falling from ~2.4 V through the rise region): I_G ≈ 2.2 V / R_tot.
- R_tot = R_G (0.4 Ω) + driver output (~0.5 Ω assumed) + the external resistor; the high side has two devices in
  parallel, each with its own resistor, so the switch's di/dt is twice the device's.

| target (switch, 2 devices) | R_tot per device | external resistor |
|---|---|---|
| turn-on 36 A/ns (50 pH, x 1.8 V) | 5.4 Ω | ~4.5 Ω |
| turn-on 24 A/ns (125-133 pH at x 3.0-3.2 V) | 8.1 Ω | ~7 Ω |
| turn-on 18 A/ns (100-150 pH) | 10.8 Ω | ~10 Ω |
| turn-off 72 A/ns | 2.1 Ω | ~1.2 Ω |
| turn-off with no external resistor | 0.9 Ω | 0 → ~160 A/ns |

A driver with separate source and sink outputs (one resistor each) gives both at once. The usual default of a small
or zero sink resistor would turn off at ~150-170 A/ns; with A154's rule (L·di/dt_off ≤ ~10 V) that alone limits the
loop to ~60-65 pH. **So the spec must name the turn-off di/dt (or the sink resistor), not leave it "as fast as
possible".**

## 3. Check of D68's node charge

The hard turn-on swings 3 low sides up and 2 high sides down by 12 V: 5 × Q_OSS(12 V) ≈ 135 nC. D68's harness
measured Q0 ≈ 162 nC (+20 %; the plant's node also holds the loop and flying-capacitor parasitics). Same order: the
ramp time √(2 Q0 / di/dt) rests on the datasheet's charge.

## 4. Limits

- Typical values at 25 °C; the threshold and transconductance spread and drift with temperature (Fig. 2: 125 °C
  shifts the curve).
- No common-source or gate-loop inductance: both slow the edge at high di/dt, so the fast cases (≥ 72 A/ns) are
  upper bounds on the speed.
- The gate charge figures are at 37 A, 20 V; the hard turn-ons here are 12-19 V and 40-160 A.
- Validating it needs a gate-level device model (EPC's SPICE model) or a measurement; both are outside this repo.
