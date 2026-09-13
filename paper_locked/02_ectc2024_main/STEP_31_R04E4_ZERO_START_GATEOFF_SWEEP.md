# Step 31 - R04E4 zero-start gate-off threshold sweep

## Question

Can an earlier QH1 current-limit event prevent the post-turn-off peak found in
R04E3, without changing the P24 5-MHz operating target or forcing phase rotation?

Only `I_GATE_OFF` was swept: `0.1, 0.25, 0.5, 1, 2, 5, 10 A`. The negative
target remained the P24 upper source-native value, 2% of each swept command
threshold. The original R04E3 file and all framework modules remain unchanged.

## Boundary corrections discovered during the experiment

Three startup definitions were executed and kept conceptually separate:

1. A 10-ps rail ramp while QH1 was already enabled. Rejected: rail establishment
   and controller enable were accidentally simultaneous.
2. QH1 held off until 0.1/10 ns after the rail ramp. Rejected for low thresholds:
   Coss displacement current triggered the current comparator before a commanded
   power pulse. This established the need for enable/blanking semantics.
3. Final powered-rail boundary: 48 V is present at the DC solution; QH1 is off;
   device Coss assumes its natural off-state voltage; flying/output capacitors
   and inductor currents remain zero; the controller enables at 10 ns.

The final boundary does not preset the flying ladder to `36/24/12 V`.

## Final powered-rail results

All seven thresholds triggered at approximately `10.00081 ns` with the same
measured current `13.9435 A`; all reached a physical peak of `14.1878 A` and a
minimum of `-14.1711 A`. QL1 zero-Vds occurred near `10.2282 ns`. Inductor-current
zero occurred at `1.63962 us`. No case reached the QH1 high-side zero-Vds exit;
all ended in controller state 4, `COMMUTATE_HIGH_TO_ZVS`.

The threshold sweep therefore has no control authority over the first current
impulse. At controller enable, QH1 hard-switches while its Coss is charged to the
off-state voltage. An ideal switch plus the scalar Coss model produces a rapid
charge-redistribution/LC transient before the event controller can turn QH1 off.
The observed scale is physically consistent with stored Coss energy, although
its exact waveform and loss are not hardware-accurate because nonlinear Coss,
gate slew, loop impedance and package parasitics are unavailable.

## Verdict

Status: **FAILED_ALL_GATEOFF_THRESHOLDS; FIRST_ZVS_OR_PRECHARGE_REQUIRED**.

Earlier gate-off threshold selection cannot solve the first-turn-on boundary.
R04E1 without the device-Coss plugin showed that the predictive pulse law can
limit the inductive ramp; R04E4 with the existing GS61008T scalar Coss plugin
shows that a powered-rail first hard turn-on precedes that control action.

The next experiments must be separate startup-method branches rather than more
gate-off tuning:

1. coordinated low-voltage/input-ramp enable using no added package power part;
2. output or ladder pre-bias/precharge, explicitly adding its source/path;
3. first-hard-switch acceptance using a nonlinear device model and measured
   input-loop/gate-slew data.

None is specified by P24/P25. Selecting a hardware branch requires the intended
system power-up sequence or startup circuit information from the project owner.
