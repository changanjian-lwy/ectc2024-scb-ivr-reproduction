# A33 boundary

- Parent power stage and state seed: A27.
- Sequence slot only is replaced by the compiled `P25_NP4_EXTENSION` truth
  table: one 20-state rotating event machine.
- Negative-current input remains the labelled 9% P25 sensitivity value.
- No absolute phase-time transition exists inside the controller.
- Device Coss, ideal reverse clamp, topology, L, capacitors, output boundary,
  initial state and timestep are unchanged.
- Acceptance: parser/run completion, ordered H1-off/L1-on/L2-off/H2-on events,
  H2 Vds zero at admission, no same-leg commanded overlap. Failure is retained.
