# A35 hybrid-controller boundary

- Parent power stage/state/device model: A27; 9% remains the labelled P25
  commutation-margin branch.
- Control-only change: every high side turns off after relative `TON`; peak
  current is measured at that edge. Other transitions remain physical events.
- Next high-side admission requires its nominal `T/nP` slot and `Vds=0`.
- If the early ZVS window has disappeared at the slot, the controller remains
  blocked. It must not hard-switch or retune a component.
- This first run tests H1-to-H2 and accepts a documented missed-slot failure.
