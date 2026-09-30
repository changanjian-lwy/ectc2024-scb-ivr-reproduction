# A86 - the adopted P24 module controller with EPC2067's nonlinear Coss(V) (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`. Written before any
run.

## 1. Question

Every result from A69 to A85, and D43, uses a **linear** switch capacitance:
- EPC2067's printed Co(tr) of 1860 pF per device;
- 2 high-side and 3 low-side devices in parallel.

GaN Coss is strongly nonlinear. Over P24's 0-12 V operating range, EPC2067's
charge-equivalent capacitance is 2210 pF, 19% above Co(tr), and it falls
steeply above ~10 V. The single-module conclusions all rest on the
resonance of the switching nodes, so the nonlinear curve may move them:
- the phase-4 threshold (3%; A82);
- every phase soft at 3-7.5% with the fixed corrector;
- P24's 1-2% not enough.

**With the datasheet curve, do these conclusions hold, and where does the
threshold move?**

## 2. Data: public, reliable, reproducible

**Source.** EPC2067 datasheet, "Revised October 21, 2021", public at
https://epc-co.com/epc/Portals/0/epc/documents/datasheets/epc2067_datasheet.pdf.
The file used had SHA-256
8271d9eb71a3f78285c4c024ccfd06c33af129583c1bdef484d7dde01ae2324f. The PDF is
not in this repository.

**Digitisation (A59, committed a19fb96).**
- Fig. 5a (Coss, VGS = 0 V, typical, per device), taken from the PDF's
  vector Bezier paths, with the axes fitted by least squares on the tick
  labels.
- Files (read-only here):
  - `A59_nonlinear_coss_epc2067/epc2067_coss_qoss_eoss_digitized.csv`,
    SHA-256 dbce9a62b9a452abf8d5c21d1ea075fd305a18e64c30d91e0d8ecacee49f2652;
  - `epc2067_coss_digitization.json` (provenance, fit residuals), SHA-256
    293de42477f6a9301c85a0241975592a8851945d524209d1bcd15c29a6b79328.

**Independent check against the printed typical values.** Model: PCHIP of
the digitised Coss on a 0.1 V grid, with q(V) its exact antiderivative.

| quantity | from the digitised curve | printed | difference |
|---|---:|---:|---:|
| Coss at 20 V | 1063 pF | 1071 pF | 0.7% |
| Co(tr) (0-20 V) = Q(20) / 20 | 1864 pF | 1860 pF | 0.2% |
| Co(er) (0-20 V) = 2 Eoss(20) / 20^2 | 1598 pF | 1597 pF | 0.06% |

The curve, its integral (charge) and its second integral (energy) each
match an independent printed number.

**What this module does not use.** A vendor SPICE model. Its Coss is also
public (EPC's model download), but only the datasheet curve is used here.

## 3. Model used, and why

**The physical model** (A84's simulator, copied). A nonlinear capacitance
breaks the piecewise-linear structure that D43's exact map relies on. The
switching-level simulator handles it with a charge-based step.

**Implementation.**
- Each step first solves the linear system with the constant Co(tr)
  capacitance, as before (cached LU).
- For each of the eight switch branches, the constant-capacitance charge
  change `C_lin * dv` is then replaced by `n * (q(v1) - q(v0))`, with
  n = 2 (high) or 3 (low) devices.
- The corrected equation is solved by chord iteration on the cached LU,
  until `|dy| < 1e-7` (V or A), or by full Newton if that does not converge in
  8 iterations.

This is A59's charge-conserving correction transferred to the trapezoid
and backward-Euler steps of this simulator. With `nonlinear_coss` off, the
original code path runs unchanged.

**Regression gate (run n0).** Option off, A82 run 3's settings: bit-
identical to A82 run 3.

## 4. Runs

A82's sequence and adopted controller:
- predictive valley turn-on, with the corrector also learning at restart
  turn-ons;
- trim 0.5, no reactive ZVS;
- 10 ns latency;
- fixed shifts, restart 20 / 400 ns;
- integral loop ki 0.25 ns/V;
- zero start, 388.61 us.

| run | target (% of 125 A) | nonlinear Coss |
|---|---:|---|
| n0 | 3% | off (gate) |
| n1 | 2% | on |
| n2 | 2.5% | on |
| n3 | 3% | on |
| n4 | 5% | on |
| n5 | 7.5% | on |

## 5. Reporting

Per run, against its linear counterpart (A82 runs 5, 4, 3, 1; A79 run 3):
- criterion 2 (every phase soft once per cycle, no restart, Vds < 40 V,
  dither < 1 A);
- per-phase turn-on voltage;
- phase 4's turn-off current and delay;
- period, Ton, Vo, conduction loss;
- the chord-iteration statistics.

## 6. Decides / does not decide

Decides:
- whether the single-module conclusions survive the datasheet Coss(V);
- where the lower target now lies.

Does not decide:
- reverse-conduction voltage drop. The diode stays ideal here; the
  datasheet Fig. 8 drop is the next step;
- temperature;
- package and PCB parasitics;
- the mathematical-model counterpart, since D43 is piecewise-linear.

## 7. Amendment (after runs n0-n5, before n6-n8)

**Runs n1-n5 change the picture.** With the datasheet Coss(V), 2% (the top
of P24's stated 1-2%) settles with every phase soft. Phase 4 carries
-1.85 A at its turn-off, against +6.82 A with linear Coss (A82 run 5). The
lower end of P24's range, and the uniqueness at 2%, are therefore
declared as added runs:

| run | target | nonlinear Coss | kick |
|---|---:|---|---|
| n6 | 1% | on | - |
| n7 | 1.5% | on | - |
| n8 | 2% | on | phase 4's `dt_pred` to 20.2 ns at 250 us (A84 test) |

## 8. Amendment (after D44 and the step check; before runs e1, e2 and n0b)

**Why.** D44 (the mathematical model) replaces Coss by a charge-equivalent
linear value over three voltage ranges. None of them reproduces runs n1-n3:
- at 2%, every equivalent-linear case is restart-driven;
- at 3%, phase 4 carries -1.8 to -2.3 A at its turn-off, against -3.19 A in
  run n3.

**The step check** (`a86_verify_step.py`, written after runs n0-n5) rules
out an error in the nonlinear step.
- The full-circuit step and an independent 1-D ODE (DOP853, rtol 1e-12) of
  phase 4's node differ by the same amount with nonlinear and with linear
  Coss:
  - valley time 0.003 ns;
  - valley Vds 3-4 mV;
  - fall time at +120 A 0.0005 ns.
- The residue is the full circuit's a3 and out motion, which the 1-D
  reduction omits.

**Question.** Does the physical model, at D44's L2 capacitances (linear;
per device 1796.9 pF high, 2424.5 pF low), reproduce D44's L2 orbits?
- If yes: the two models agree at equal linear capacitance, and runs n1-n3
  differ from L2 because of the curve's shape, not the models.
- If no: the models disagree at L2, and the discrepancy is not about
  nonlinearity.

**Code change.** Two CLI options, `--c-high-pf` and `--c-low-pf` (per
device; unset = Params, as before). Run n0b repeats the gate with the
changed file.

| run | target | capacitance | D44 L2 prediction (phase 4 at turn-off) |
|---|---:|---|---|
| e1 | 3% | L2 linear | soft, -2.30 A, 10.16 V |
| e2 | 2% | L2 linear | restart, +6.25 A |
| n0b | 3% | default (gate, = A82 run 3) | bit-identical |

Tolerance, as D44 Section 5: +/-0.3 A and +/-0.15 V.
