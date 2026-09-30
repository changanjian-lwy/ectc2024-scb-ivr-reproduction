# A87 - the EPC2067 reverse-conduction drop in the P24 module (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`. Written before
any run.

## 1. Question

A86 runs the adopted P24 controller with EPC2067's datasheet Coss(V). Its
switches still reverse-conduct through **ideal** diodes: 0 V and no loss.

A GaN HEMT has no body diode. With the gate at 0 V it conducts in reverse
through its own channel once the source-drain voltage exceeds about 2 V.
EPC2067's Fig. 8 shows 2.40 V at 50 A per device (A57).

In this controller the low side conducts in reverse after every high-side
turn-off:
- the node falls to 0 V;
- the comparator fires;
- the low-side channel turns on only after the 10 ns comparator-to-gate
  latency (A75, `PROJECT_DECISION`).

**With the drop, what happens to:**
- soft switching;
- the operating point: Ton, the phase-4 current;
- the loss?

This is the second device-realism step at the single-module circuit level
(after A86). Package and PCB parasitics are the next level and are out of
scope.

## 2. Data: public, reliable, reproducible

**Source.** EPC2067 datasheet ("Revised October 21, 2021"; SHA-256
8271d9eb...2324f, as A59/A86), Fig. 8 "Typical Reverse Drain-Source
Characteristics":
- VGS = 0 V, per device, at 25 C and 125 C;
- VGS = 0 V off-state is EPC's recommendation, and is assumed here.

**Digitisation (A57, committed 69ae4c2; read-only here).**
- File: `A57_datasheet_reverse_conduction_pricing/epc2067_fig8_reverse_characteristics.csv`,
  SHA-256 aa2a002898b0e87e13d5327fb46df5430ac6ceeca647e2ee84374e9a6f554de5.
- Method: taken from the PDF's vector Bezier paths; the axis-map residual is
  at most 0.009 V.
- Temperature assignment (blue 25 C, red 125 C) was confirmed on a
  rendering of the figure.

**Independent check (before any run).** `a87_check_fig8_vs_epc_model.py`
evaluates EPC's public SPICE model (EPCGaNLibrary.lib, version 1.93,
2022-12-14, subcircuit EPC2067) at VGS = 0 V, with its series resistances.
The script reads a local copy of the library. The library is not in this
repository; only the comparison is.

| per-device current | Fig. 8, 25 C | EPC model, 25 C | difference |
|---:|---:|---:|---:|
| 1 A | 1.871 V | 1.865 V | -5 mV |
| 10 A | 2.105 V | 2.100 V | -6 mV |
| 50 A | 2.401 V | 2.391 V | -9 mV |
| 100 A | 2.676 V | 2.664 V | -12 mV |
| 400 A | 4.087 V | 4.061 V | -26 mV |

- At 125 C the two agree within 5-35 mV.
- Both put 0.5 A at about 1.80 V. The datasheet table's "VSD = 1.2 V typ at
  0.5 A" is inconsistent with both, as A57 noted; the curve governs.

## 3. Model used, and why

**The physical model** (A86's simulator, copied). The drop acts through the
full switching dynamics and the controller. Examples:
- the node sits at -Vf instead of 0 during reverse conduction;
- the inductor current falls faster;
- the voltage loop answers with Ton.

**Device model: constant drop plus resistance.** A diode-conducting device
(gate off, reverse current) carries I = (V_SD - Vf) / R.
- It is fitted by least squares to Fig. 8 at 25 C over 10-100 A per device
  (1 A spacing):
  - Vf = 2.0894 V;
  - R = 6.013 mOhm per device;
  - maximum error 44 mV in that range.
- Below 5 A it overestimates the drop by 0.09-0.29 V.
- A switch position with n devices has conductance n / R (n = 2 high, 3
  low) and the same Vf.
- **Why this form.**
  - It keeps the simulator's linear step: a conductance plus a constant
    source in the conducting topology.
  - It is the constant-drop form of A57 and D05, plus the resistance.
- **Checked after the runs:** the per-device reverse currents actually
  seen. The fit range must cover them.

**Diode logic.**
- A gate-off device turns on in reverse when V_DS < -Vf (ideal: < 0).
- It is cut within a step when its reverse current would change sign, that
  is, when V_DS > -Vf (ideal: > 0).
- Every other rule is unchanged, including the comparator: low-side
  turn-on is decided at V_DS = 0, then waits the latency.

**Loss record.** For each diode-conducting device, V_SD * I_SD is
integrated over each accepted step and reported per phase as `P_rev`. The
diode conduction time per edge is recorded too.

**Code.** `rev_drop` off gives the unchanged path. Gate r0 must replay
A86 run n3 bit-identically.

## 4. Runs

A86's adopted controller, with the datasheet Coss(V) on:
- predictive valley turn-on, with the corrector also learning at restart
  turn-ons;
- trim 0.5, no reactive ZVS;
- 10 ns latency;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- zero start, 388.61 us.

| run | target | reverse drop | latency t_d | purpose |
|---|---:|---|---:|---|
| r0 | 3% | off | 10 ns | gate (= A86 n3) |
| r1 | 3% | on | 10 ns | main |
| r2 | 2% | on | 10 ns | P24's stated value (soft in A86) |
| r3 | 5% | on | 10 ns | |
| r4 | 7.5% | on | 10 ns | |
| r5 | 3% | on | 2 ns | `SENSITIVITY_ONLY`: how much of the result is the 10 ns latency |

## 5. Predictions (written before the runs)

- **P_rev.** Per edge, the low side conducts about 10 ns at about 160 A,
  2.4 V (3 devices, about 53 A each):
  - about 3.8 uJ per edge;
  - x4 phases / 226 ns: **about 60-75 W at t_d = 10 ns**, against 250 W
    out;
  - **about 10-20 W at t_d = 2 ns** (r5).
- **Ton.** Each edge loses about 2.4 V x 10 ns / 1.4667 nH = 16 A of extra
  current decay. The loop must add about 2.4 x 10 / 11 = 2.2 ns of Ton
  (about 17.5 to about 19.7 ns).
- **Soft switching.** No confident prediction. The negative-current
  targets are enforced by the comparator and timers, but the whole orbit
  (currents, delays) shifts.

## 6. Reporting

Per run, against A86:
- criterion 2;
- per-phase turn-on voltage;
- phase 4's current at turn-off;
- Ton and period;
- P_cond, P_rev, and the P_on proxy;
- the diode conduction time per edge and the per-device reverse-current
  range (fit coverage).

## 7. Decides / does not decide

Decides:
- whether the adopted controller keeps every phase soft with the datasheet
  reverse drop;
- the size of the reverse-conduction loss with the 10 ns latency, and how
  much of it the latency causes.

Does not decide:
- a new low-side timing rule (the next step, if the loss is large);
- temperature (125 C curve) and gate-drive details (negative off bias);
- package and PCB parasitics (next level);
- the mathematical-model counterpart (to follow: D45 with a drop).
