# Step 28 - R04E1 P24 phase-1 zero-energy predictive pulse

## What changed

Relative to R04E0, one replaceable controller output was connected to the
unchanged P24 four-phase power stage.  Only the P24-explicit first-interval
commands `QH1 + QS2` were applied. No phase rotation, precharge power branch,
new power switch, fitted capacitance, or periodic-state capacitor voltage was
inserted.

## Locked and exploratory boundaries

- P24 target: `Vin=48 V`, `Vout,target=1 V`, `nP=4`, `nM=4`, one 250-W module.
- `L=1.4666667 nH`: project/user-selected result recalculated from P24's
  printed equation and inputs; P24 Table-I `2.68 nH` remains an audit conflict.
- Flying/output capacitor banks are unchanged cross-source candidates already
  used by the project: `53.8 uF` and `4.672 mF`.
- All capacitor voltages and inductor currents start at zero.
- Exploratory current increment limit: `10 A`.
- Actual initial output voltage is `0 V`; the 1-V target is not substituted.
- Calculated pulse width:
  `tp=L*DeltaI/(Vin-Vout,initial)=0.3055556 ns`.
- The 10-ps input-source PWL and 1-MOhm node references are numerical
  initialization aids, not proposed package components. Their maximum DC draw
  is 48 uA.

## Run history

1. Exact UIC with 1-TOhm/1-GOhm references failed with a singular matrix at
   `x1`. This failure is retained as a zero-energy numerical-boundary result.
2. LTspice's generic `startup` option ran but delivered only `0.131 mA`, because
   the hidden source ramp had not established 48 V by the 0.1-ns pulse. This is
   rejected as a control result.
3. With the rail establishment made explicit, the first calculation used the
   1-V target instead of the actual 0-V startup output. It predicted 0.312057 ns
   and produced `10.2455 A`; the 2.45% excess exposed that boundary error.
4. Recalculation with actual `Vout,initial=0 V` produced the final run below.

## Actual final-run output

| Quantity | Result |
|---|---:|
| Calculated pulse width | 0.3055556 ns |
| `iL1` at gate-off | 10.032723 A |
| `iL1` peak through 2 ns | 10.032723 A |
| Current error relative to 10-A limit | +0.327% |
| `iL2` peak | approximately 0 A |
| `VC1` at gate-off | 26.70 uV |
| `VC2` at gate-off | approximately 0 V |
| `VC3` at gate-off | 0 V |
| `Vout` at gate-off | 0.329 uV |

The Python regression suite passes `98 tests`.

## Conclusion and claim boundary

Status: **PASSED_LOCAL_PREDICTIVE_CURRENT_INCREMENT; STARTUP_NOT_ESTABLISHED**.

The replaceable policy correctly converts the observed instantaneous voltage,
inductance and permitted current increment into a sub-nanosecond first pulse.
It does not yet establish the capacitor ladder: one pulse moves `VC1` only by
about 26.7 uV because the retained candidate capacitance is large.  Repeating
or rotating pulses cannot be authorized from this result alone. The next module
must define a safe event-based repetition/rotation rule and must keep any P25
four-phase extension separate from the P24-minimal branch.
