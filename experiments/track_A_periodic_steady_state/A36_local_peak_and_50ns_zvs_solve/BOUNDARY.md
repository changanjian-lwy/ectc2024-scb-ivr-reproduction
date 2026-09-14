# A36 local two-residual solve boundary

- Parent: A35 hybrid fixed-TON/event-ZVS/slot-guard controller.
- Adjustable variables: `IL1_INIT` and `IL2_INIT` only.
- Locked: topology, 9% labelled P25 margin branch, device/Coss, ideal reverse
  clamp, capacitors, L, output boundary, TON, 50 ns slot and timestep.
- Residuals: `iL1(TON)-125 A` and first phase-2 high-side Vds-zero time minus
  50 ns.
- This is a local H1-to-H2 solve. It is not an eight-state periodic solution.
