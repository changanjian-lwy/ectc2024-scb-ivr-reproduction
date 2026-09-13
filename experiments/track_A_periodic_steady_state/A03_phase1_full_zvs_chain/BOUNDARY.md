# A03 - first complete phase-1 local ZVS chain

- Compared with: separately initialized R04D0, R04D1/2 and R04D3E.
- Changed: those local event stages are connected in one transient run, so all
  capacitor voltages, switching-node voltages and inductor currents propagate
  naturally across stage boundaries.
- Threshold branch: calibrated model `NEG_FRAC=8%`; this is not promoted to a
  P24 value. P24 1%-2% remains a separately recorded failed-ZVS branch with the
  selected scalar Coss.
- No external snubber, dead time, driver delay, nonlinear Coss, startup,
  four-phase rotation, periodic reset or feedback is added.
- Pass requires the ordered events HS1-off -> LS1-Vds-zero -> LS1-on ->
  IL1-zero -> LS1-off at -10 A -> HS1-Vds-zero -> HS1-on, with zero gate
  overlap. A completed LTspice run alone is not a pass.

## Run note

- First invocation stopped at netlist parsing because LTspice `.machine`
  output expressions do not accept the `||` operator. No electrical result was
  produced and no boundary was changed. The equivalent mutually-exclusive
  state sum is used for the corrected run.
- The corrected natural-state 8% run completed low-side ZVS and reached
  `iL1=-10.0007 A`, but high-side Vds bottomed at about `1.181 V` after low-side
  turn-off rather than zero. The isolated R04D3E 8% success therefore does not
  transfer unchanged into the shared-ladder chain.
- A follow-up one-variable sweep uses 8%, 9% and 10%. The upper value is the
  upper edge of the P25 Mode-4 text, and the sweep does not promote any value
  to the P24 source-native branch.
- Sweep result: 8% fails; 9% and 10% complete the local high-side ZVS return.
  The present coarse full-chain bracket is therefore greater than 8% and no
  greater than 9%. This bracket belongs only to the connected scalar-Coss
  model.
