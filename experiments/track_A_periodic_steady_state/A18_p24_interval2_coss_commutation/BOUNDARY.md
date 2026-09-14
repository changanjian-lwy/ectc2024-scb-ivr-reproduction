# A18 - P24 Interval 2 Coss commutation observation

## Source event and sequence

Primary source: P24 Sec. II-B, second interval `(t1,t2)`.

1. `QH1` turns off at `t1`.
2. Positive `iL1` charges the output capacitance of `QH1`.
3. The same current discharges the output capacitance of `QL1`.
4. `QL1` becomes eligible to turn on when its drain-source voltage reaches zero.

P24 does not publish the exact commutation capacitance, dead time, transition
duration, or a measured waveform. Its Fig. 4 is explicitly theoretical.

## Parent and only change

- Electrical parent: unchanged A16 periodic candidate.
- Previous observation: A17 P24 Interval 1.
- Only change: observation window and acceptance metrics move from Interval 1
  to the commutation immediately after `t1`.
- No electrical parameter, initial condition, command expression or timestep is
  changed after observing the result.

## Locked implementation boundary

- `CH_TOTAL=385 pF` and `CL_TOTAL=770 pF` are candidate scalar capacitances from
  the GS61008T device-data module already adopted before A18; they are not
  values published by P24.
- Added P24 nanofarad parallel capacitor remains zero because P24 gives no
  numerical value. Therefore this experiment tests inherent/candidate Coss
  commutation only.
- The low-side command is admitted at `V(x1)<=0`; no guessed fixed dead time is
  introduced.
- The ideal 1 V output source remains an isolation boundary.

## Acceptance checks

1. `Vds(QL1)=V(x1)` must fall from a positive value to zero after `QH1` turns
   off.
2. `Vds(QH1)=VIN-V(a1)` must rise during the same transition.
3. `iL1` must remain positive during the capacitive commutation.
4. The zero crossing must occur before another commanded high-side event.

Passing these checks establishes only the P24 Interval-2 commutation mechanism;
it does not establish device loss, optimum added capacitance, or hardware ZVS.
