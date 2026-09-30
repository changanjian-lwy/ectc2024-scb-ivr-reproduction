# A87 - the EPC2067 reverse-conduction drop in the P24 module (RESULTS)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`.

**Boundary:** `BOUNDARY.md`, written before any run and unmodified.

**Records:**
- `run_*.json`;
- `a87_summary.json`;
- `gate_pairs.json`;
- `a87_fig8_vs_epc_model.json`.

**Model: the physical model** (A86's simulator plus a constant-drop-plus-
resistance reverse path), with A86's datasheet Coss(V).

**The mathematical-model counterpart is D46**
(`symbolic_derivations/03_P24_native/D46_P24_REVERSE_DROP_EVENT_MAP.md`):
D45's nonlinear-Coss event map with the same reverse-path model.

## 0. Verdict

1. **Soft switching survives the datasheet reverse drop.**
   - At 2%, 3%, 5% and 7.5% every phase turns on predictively once per
     cycle, with no restart.
   - Criterion 2 passes in all four, including P24's 2% (dither 0.99 A).
   - Phase 4's current at its turn-off moves slightly negative: 3% gives
     -3.36 A, against -3.19 A with ideal diodes (A86 n3).
2. **The reverse-conduction loss is large: 55-57 W at 250 W out**, 4.5
   times the conduction loss (12.3-12.8 W).
   - The low side conducts in reverse for 9.8 ns per edge at 49-52 A per
     device (2.39-2.40 V) before its channel turns on.
   - The electrical loss proxy becomes:

     | | loss | proxy efficiency |
     |---|---:|---:|
     | ideal diodes (A86) | ~22 W | ~92% |
     | with the drop | ~79 W | ~76% |

     The loss is conduction + reverse + the turn-on proxy.
3. **The cause is the controller's 10 ns comparator-to-gate latency (A75,
   `PROJECT_DECISION`), not the power stage.** With 2 ns (r5, sensitivity
   only):
   - the reverse time falls to 1.8 ns per edge;
   - P_rev falls to 10.0 W;
   - Ton, the phase-4 current and the turn-on voltages are nearly those
     of the ideal-diode case.

   This is A57's lesson, now in the closed-loop switching model: keep
   reverse conduction short.
4. **The loop absorbs the drop.**
   - Ton rises by 1.8 ns (17.5 to 19.4 ns at 3%). Each edge's -2.4 V
     node costs about 16 A of extra current decay per phase (2.4 V for
     9.8 ns across 1.4667 nH).
   - Vo still regulates to 1.0000 V, but settles later: 104-111 us after
     the handover, against 67-70 us.
   - Peak Vds rises from 25.2 to 26.7-26.9 V: the node now swings to
     -2.4 V. EPC2067 is rated 40 V.
5. **The two models agree** (D46 against A87, at matched settings):

   | quantity | difference |
   |---|---:|
   | Ton | within 0.02 ns |
   | period | within 0.2 ns |
   | phase-4 current at its turn-off | within 0.05 A |
   | phase-4 turn-on voltage | within 0.03 V |
   | P_rev | within 0.03 W |

   All D46 orbits are stable (|mu|max 0.986-0.990).

## 1. Runs (last 50 cycles)

All runs use A86's adopted controller with the datasheet Coss(V):
- predictive valley turn-on, with the corrector also learning at restart
  turn-ons;
- trim 0.5, no reactive ZVS;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- zero start, 388.61 us.

Reverse drop: per device Vf = 2.0894 V, R = 6.013 mOhm. The fit is to Fig.
8 at 25 C over 10-100 A, with a maximum error of 44 mV.

| run | target | drop | t_d | phase 4: current at turn-off, mean [min, max]; Vds at turn-on | phases 1-3 Vds at turn-on | Ton | period | dither | reverse time per low-side edge | P_cond | **P_rev** | P_on proxy | peak Vds | criterion 2 |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r0 (gate) | 3% | off | 10 ns | -3.19 [-3.61, -2.76] A; 9.90 V | 9.61-9.63 V | 17.518 ns | 226.38 ns | 0.90 A | - | 12.23 W | 0 | 9.99 W | 25.19 V | pass (= A86 n3) |
| r2 | 2% | on | 10 ns | -2.12 [-2.59, -1.65] A; 10.21 V | 9.87-9.96 V | 19.278 ns | 223.22 ns | 0.99 A | 9.79-9.85 ns | 12.28 W | **56.78 W** | 10.60 W | 26.66 V | pass |
| r1 | 3% | on | 10 ns | -3.36 [-3.74, -3.00] A; 9.88 V | 9.61-9.69 V | 19.356 ns | 225.21 ns | 0.79 A | 9.79-9.85 ns | 12.34 W | **56.58 W** | 10.02 W | 26.66 V | pass |
| r3 | 5% | on | 10 ns | -5.89 [-6.15, -5.64] A; 9.10 V | 8.95-9.03 V | 19.580 ns | 230.61 ns | 0.55 A | 9.79-9.85 ns | 12.53 W | **56.08 W** | 8.45 W | 26.78 V | pass |
| r4 | 7.5% | on | 10 ns | -9.06 [-9.30, -8.83] A; 8.02 V | 8.01-8.11 V | 19.918 ns | 238.58 ns | 0.50 A | 9.80-9.85 ns | 12.81 W | **55.38 W** | 6.46 W | 26.87 V | pass |
| r5 (sensitivity) | 3% | on | 2 ns | -3.28 [-3.69, -2.85] A; 9.88 V | 9.61-9.64 V | 17.887 ns | 226.37 ns | 0.88 A | 1.77-1.84 ns | 12.24 W | **10.05 W** | 9.94 W | 26.68 V | pass |

**Notes.**
- Vo is 1.0000 V in every run. P_out is 250 W.
- **Reverse time.** Reverse conduction occurs only on the low sides; no
  high side conducts in reverse (valley switching never reaches ZVS). It
  lasts about 0.2 ns less than t_d: the comparator decides at V_DS = 0,
  and the node reaches -Vf about 0.2 ns later.
- **P_rev per low-side switch** is 13.8-14.5 W at t_d = 10 ns and 2.5-2.6 W
  at 2 ns.
- **Fit coverage.**
  - The per-device reverse current at the start of conduction is 49-52 A
    (46 A at t_d = 2 ns).
  - Over the 9.8 ns interval, each phase's current falls by about 23 A,
    about 8 A per device. That estimate is from (V_SD + Vo)/L, not
    recorded. The conduction therefore spans roughly 41-52 A per device.
  - That lies inside the 10-100 A fit range. At 40-55 A the fit lies
    10-11 mV below the curve, so P_rev is underestimated by about 0.5%.

## 2. Checks

- **Regression gate.** r0 (drop off) replays A86 run n3 bit-identically:
  1781 sections, difference 0.0, equal end state.
- **The data** (BOUNDARY Section 2). The digitised Fig. 8 and EPC's public
  SPICE model (library v1.93, evaluated independently) agree:
  - within 6-12 mV over 1-100 A at 25 C;
  - within 26 mV up to 400 A.
- **The stamp.** With SL4 alone carrying 160 A in reverse, the node settles
  at -2.4055 V, against -(Vf + R 160/3) = -2.4054 V.

## 3. Predictions (BOUNDARY Section 5) against the results

| | predicted | result |
|---|---|---|
| P_rev at t_d = 10 ns | 60-75 W | 55.4-56.8 W: 6% below the range |
| P_rev at t_d = 2 ns | 10-20 W | 10.05 W |
| Ton increase | about 2.2 ns | 1.84 ns (3%) |

The estimate assumed 160 A over the whole interval. The current actually
starts at about 150 A and falls by about 23 A.

## 4. Consequences

- **Device realism at this level: two steps done.**
  - Datasheet Coss(V) (A86): P24's 2% works.
  - Reverse drop (A87): soft switching and 2% still hold.
- **The dominant loss is now a controller-timing choice.** The adopted
  controller turns the low side on only after a comparator plus a 10 ns
  latency, and it pays for that in reverse conduction.
  - What real GaN designs do, per A57 and the literature on adaptive
    dead time:
    - keep reverse conduction to about a nanosecond or less;
    - predict the low-side edge rather than react to it.
  - This is the next step at this level. It is a controller change, not a
    device one: a predictive or adaptive low-side turn-on. It follows the
    same approach as the high side's predictive valley timing, and also
    goes into the Verilog controller.
- **P24's module efficiency cannot be judged** until the dead time is
  realistic. A76-A86's loss numbers had no reverse loss at all.

## 5. Limits

- **The device.**
  - The 25 C curve, and VGS = 0 V off-state.
  - A negative off bias would raise the drop; the datasheet notes this.
  - The fit overestimates the drop below 5 A, but no such current occurred.
  - Temperature is not covered: at 125 C, the Fig. 8 curves cross the
    25 C curve near 50 A, which is the operating current.
- **The circuit.** A86's otherwise idealised module:
  - lumped R;
  - no package or PCB parasitics (next level);
  - Cout 4.672 mF (inherited, suspect);
  - one module.
- **The loss figures are electrical proxies.** Gate charge, magnetics and
  switching overlap are absent, and P_on is a proxy.
- **r5 is a sensitivity run,** not an adopted controller change.
- **The dither threshold (1 A) is a `PROJECT_DECISION`.**

## 4a. Literature check (after the runs)

Y. Zhang et al., "Analysis of Dead-Time Energy Loss in GaN-Based TCM
Converters With an Improved GaN HEMT Model," IEEE TPEL 38(2), 2023,
DOI 10.1109/TPEL.2022.3217456. The PDF is not in this repository.

TCM is triangular-current-mode soft switching with a reverse current. It
is the same mechanism as this module's negative-current target.

1. **The model form is the standard one.** The paper writes the self-
   commutated reverse-conduction voltage as V_RC = Vth - V_goff +
   R_on i_d. A87's Vf + R I, fitted to the datasheet curve at VGS = 0 V,
   is that static form.
2. **A dynamic effect the static curve omits.** In Schottky-type p-GaN
   gate HEMTs, the threshold rises with the voltage the device blocked
   before conducting in reverse, by charge stored in the floating p-GaN
   layer (their Eq. 2, from Xu et al., TPEL 36(5), 2021).
   - This raises the reverse drop, and ignoring it underestimates the
     reverse-conduction loss.
   - For GaN Systems GS66516T they measure -4.41 V after blocking 20 V and
     -4.61 V after 30 V (Fig. 7, small current, negative off bias).
   - **For EPC2067 it cannot be quantified from public data.** The
     coupling capacitance C_sh needs a double-pulse measurement, and EPC's
     public SPICE model is static. This project has not established
     whether EPC2067's gate is of that type.
   - **A87's P_rev is therefore the static value.** If the low sides
     (blocking 12 V) behaved like GS66516T, the drop would rise by about
     0.1-0.2 V. That scale is taken from their device, not from ours.
     P_rev would rise by about 4-8%.
3. **Dead time is a trade-off, not a minimisation.**
   - Too short: turn-on before zero voltage adds turn-on loss.
   - Too long: reverse conduction.
   - Unoptimised dead time was 44.5% of their converter's total loss.
   - They compute a reference dead time from a model of the turn-off
     transient. They note that adaptive methods need fast detection or
     look-up tables.
   - For this module the low-side edge follows a high-side turn-off at
     about 150 A, and the node falls in about 1 ns. A predicted low-side
     turn-on, with an early/late corrector like the high side's, is the
     matching next step.
4. **Gate-loop dynamics are also outside this model.** The gate driver's
   finite ramp, the gate delay and the Miller plateau set the turn-off
   time at high current; this model's channels switch ideally. They would
   matter for a turn-off overlap loss, and they need the gate driver's
   data, which P24 does not publish.

## 5a. Reproduction

```
python3 a87_check_fig8_vs_epc_model.py <path/to/EPCGaNLibrary.lib>   # EPC's public library, not in this repo
zsh run_a87.sh
python3 a87_analyze.py
```

The mathematical-model side:

```
python3 -m scripts.audit_p24_drop_orbits --pct 3.0          # and 2.0, 5.0, 7.5; --td 2
```

The datasheet PDF and the SPICE library are not in this repository.
