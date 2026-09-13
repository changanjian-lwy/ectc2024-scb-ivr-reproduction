# Step 06 - R02 literature-supported startup module

## Literature screening

Four newly obtained papers were checked against the unresolved zero-start
boundary of the 2024 ECTC Fig. 3 reproduction.

| Source | Relevant contribution | Directly insert into P24 Fig. 3? |
|---|---|---|
| APEC 2016, 5-MHz two-phase SCB | Controlled current-source precharge to `Vin/2`, enable only after voltage monitoring; gives `tpc=C*DeltaV/Ipc` | Principle is useful; its single-capacitor circuit is not a direct four-phase implementation |
| TPEL 2018, modified SC HCR | Rearranges the power stage and adds a capacitor so the capacitors lie across the source before startup | No; it changes the converter topology |
| ECCE 2015, automatic current sharing | Explains steady-state charge-balance current sharing | Useful later for validation, not a startup circuit |
| IPEC 2018, passive divider startup | Gives input/flying-capacitor divider methods, states extension to arbitrary `N` levels, and draws a 3-phase SCB extension in Fig. 8(e)/(f) | Best available basis for a separate, replaceable P24 startup module; four-phase wiring remains an explicit extrapolation |

## R02A isolated experiment

Compared with R00, R02A does **not** run the PWM power stage. It isolates the
startup network so a failure cannot be confused with the earlier event-driven
gate controller failures.

Changed/added variables:

- four equal `10 uF` input-divider capacitors, taken unchanged from IPEC 2018
  Table II as a cross-source candidate;
- `5 nH + 10 mOhm` source parasitics, also from IPEC 2018 Table II;
- three ideal precharge diodes following the generalized Fig. 8(e) connection;
- the existing cross-source `53.8 uF` flying-capacitor bank value;
- a `1 us` 0-to-48-V input ramp, matching the fast-ramp case reported by IPEC
  2018 (not a parameter claimed by P24);
- no capacitor initial voltage, no PWM, and no active control.

Pass conditions:

1. numerical completion;
2. flying-capacitor voltages arise from zero and approach 36/24/12 V in order;
3. finite input and diode peak currents;
4. no result is labelled a P24 reproduction because the four-level startup
   network is an extrapolation from IPEC 2018.

## R02A first result - transferred divider, existing flying bank

- Status: **FAILED_PRECHARGE_ESTABLISHMENT / NUMERICALLY COMPLETED**.
- Final averages: `VC1=7.6168 V`, `VC2=1.0561 V`, `VC3=0.14375 V`.
- Errors relative to the non-imposed 36/24/12-V targets are `-78.84%`,
  `-95.60%`, and `-98.80%`.
- Peak source current is about `601.3 A`; diode peaks are about `518.0 A`,
  `72.25 A`, and `9.89 A`.
- Conclusion: transferring the IPEC `10 uF` divider values unchanged cannot
  charge the much larger `53.8 uF` flying banks. This is a charge-budget and
  capacitance-ratio failure, not a PWM/control failure.

## R02A controlled comparison

The same file is rerun as a two-step group. Only `CFLY` changes:

1. `1 uF`, the IPEC 2018 Table-II prototype value, to validate the copied
   passive-startup module itself;
2. `53.8 uF`, the existing cross-source candidate for the P24 module.

## R02A two-step result

LTspice 26.0.2 completed both steps without convergence errors.

| Quantity | Step 1: `CFLY=1 uF` (IPEC Table II) | Step 2: `CFLY=53.8 uF` (existing P24 candidate) |
|---|---:|---:|
| `VC1` final average | 35.4916 V | 7.6168 V |
| `VC2` final average | 21.8570 V | 1.0561 V |
| `VC3` final average | 10.4081 V | 0.14375 V |
| errors vs. 36/24/12 V | -1.41%, -8.93%, -13.27% | -78.84%, -95.60%, -98.80% |
| peak source current | 256.59 A | 601.30 A |
| diode-current peaks | 53.00/32.64/15.54 A | 518.05/72.25/9.89 A |

### Classification

- Step 1: **PASS_TOPOLOGY_PRINCIPLE / NOT_P24_REPRODUCTION**. With the
  paper's own `10 uF : 1 uF` divider-to-flying-capacitor scale, the generalized
  network establishes the correct descending voltage order and approaches the
  theoretical 36/24/12-V ladder. The residual errors are retained, not fitted.
- Step 2: **FAILED_CAPACITANCE_TRANSFER**. The same divider cannot supply the
  charge required by `53.8 uF` flying banks and produces an unacceptable surge.

### What may change next

The next experiment may sweep or derive divider capacitance/current limiting,
but must not change the P24 flying-bank value merely to make the plot look good.
The minimum divider charge budget and peak-current constraint must be written
before selecting values. PWM remains disconnected until the precharge module
passes those boundaries.

## R02B planned boundary sweep

The fixed flying-bank charge demand at 36/24/12 V is

`Qfly,total = 53.8 uF * (36 + 24 + 12) = 3.8736 mC`.

This is a charge-budget screening value, not an assertion that one source
branch supplies the entire sum independently. R02A also provides an empirical
boundary: the IPEC prototype works near a `CDIV:CFLY=10:1` scale, whereas the
unchanged transfer produced `10:53.8` and failed.

R02B therefore fixes `CFLY=53.8 uF` and runs only:

- `CDIV = 10, 53.8, 538, 1076 uF`;
- `TRAMP = 1, 10, 100 us`.

The 12 cases separate two effects: `CDIV` tests available charge; `TRAMP` tests
peak-current control. No case is selected from knowledge of its result.

## R02B result

Status: **COMPLETED / FEASIBLE_TREND / NO PASS CLAIM**. All 12 LTspice steps
completed without a convergence error.

| `CDIV` | `TRAMP` | `VC1/VC2/VC3` final (V) | normalized ladder error | source peak (A) |
|---:|---:|---:|---:|---:|
| 10 uF | 1 us | 7.617/1.056/0.144 | 2.732 | 601.33 |
| 53.8 uF | 1 us | 20.989/7.877/2.628 | 1.870 | 1719.64 |
| 538 uF | 1 us | 32.341/19.917/9.484 | 0.481 | 3084.92 |
| 1076 uF | 1 us | 34.046/21.793/10.631 | 0.260 | 3429.57 |
| 10 uF | 10 us | 6.715/0.927/0.126 | 2.764 | 60.13 |
| 53.8 uF | 10 us | 18.537/6.952/2.317 | 2.002 | 190.29 |
| 538 uF | 10 us | 32.341/19.917/9.484 | 0.481 | 841.85 |
| 1076 uF | 10 us | 34.046/21.793/10.631 | 0.260 | 1442.41 |
| 10 uF | 100 us | 6.637/0.916/0.124 | 2.767 | 6.01 |
| 53.8 uF | 100 us | 18.311/6.867/2.289 | 2.015 | 19.03 |
| 538 uF | 100 us | 32.341/19.917/9.484 | 0.481 | 84.24 |
| 1076 uF | 100 us | 34.046/21.793/10.631 | 0.260 | 150.15 |

### Controlled conclusions

1. Increasing `CDIV` monotonically improves the charge available to the fixed
   `53.8 uF` flying banks. This validates the R02A charge-budget diagnosis.
2. For `CDIV >= 538 uF`, changing `TRAMP` from 1 to 100 us leaves the final
   capacitor voltages unchanged within the printed precision but greatly
   reduces peak current. Thus final charge and surge control are separable
   design axes in this idealized module.
3. The largest tested divider produces the best ladder, but the residual
   undercharge is preserved. No capacitance has been fitted to 36/24/12 V.
4. The apparently best tested compromise is `CDIV=1076 uF`, `TRAMP=100 us`,
   with 34.046/21.793/10.631 V and 150.15 A source peak. It is **not** a pass:
   P24 gives no allowed startup-input-current limit and this capacitance is a
   sensitivity value, not a reported component.
5. The `125 A` P24 Table-I number is a phase-inductor peak in normal boundary
   operation. It must not silently be reused as a source-startup-current limit.

### Gate before R02C

Do not connect PWM yet. First choose and document one of two defensible gates:

- obtain the allowable module/input startup-current limit and practical
  divider-capacitance budget from the authors; or
- keep the current limit symbolic and compare passive startup against the
  APEC-2016 controlled-current precharge method as two candidate modules.

Only after a startup module satisfies an explicit current/voltage gate may it
hand control to the P24 four-phase switching sequence.

## Reference-chain audit before R02C

Neither P24 nor P25 provides or directly cites an exact four-phase startup
circuit. Therefore R02C cannot be represented as an author-specified circuit.
P25 does directly cite Roberts and Prodić, "Modulation Improvements for
High-Phase-Count Series-Capacitor Buck Converters," DOI
`10.1109/OJPEL.2024.3417017`; this is reserved for the later PWM takeover gate,
not used to fill the present startup circuit.

## R02C active-current precharge test

R02C applies the APEC-2016 Sec. IV-B/Eq. (5) timing law to three independent
precharge branches. Fixed values are `CFLY=53.8 uF`, `Ipc=10 mA`, `Vin=48 V`,
and zero stored energy. The expected completion times after the 1-us rail ramp
are:

- `VC1 -> 36 V`: `193.681 ms`;
- `VC2 -> 24 V`: `129.121 ms`;
- `VC3 -> 12 V`: `64.561 ms`.

The three-branch extension is explicitly a model hypothesis. The exact current
source circuit, tolerance, compliance, voltage detector bands, and PWM-release
logic remain unresolved.

## R02C result

Status: **PASS_TIMING_LAW / NOT_HARDWARE_VALIDATED / NOT_P24_REPRODUCTION**.

| Quantity | Predicted | LTspice | Difference |
|---|---:|---:|---:|
| `VC1` reaches 36 V | 193.681 ms | 193.682542 ms | +1.542 us |
| `VC2` reaches 24 V | 129.121 ms | 129.123034 ms | +2.034 us |
| `VC3` reaches 12 V | 64.561 ms | 64.560856 ms | -0.144 us |

Final 210-220-ms averages are `36.00060/24.00046/12.00082 V`. Peak input
current is `30.000 mA`, equal to three simultaneous ideal 10-mA branches.

The result validates the equation-level module and exposes its cost: at the
present `53.8 uF` candidate value, 10 mA requires nearly 194 ms before all
three banks are ready. It does not validate a physical three-output current
source, detector tolerance, or takeover circuit. These remain named unknowns.

## Next hard gate - PWM takeover

Before combining R02C with the P24 switching stage, transcribe the high-phase-
count modulation constraints from the paper directly cited by P25:

G. Roberts and A. Prodić, "Modulation Improvements for High-Phase-Count
Series-Capacitor Buck Converters," IEEE Open Journal of Power Electronics,
2024, DOI `10.1109/OJPEL.2024.3417017`.

This source is required to avoid inventing the four-phase release sequence.
Until it is reviewed, the combined precharge-to-PWM experiment remains blocked
at the timing-definition boundary, not at the numerical-parameter boundary.
