# A10 - eight-slow-state shooting iteration 1

- Compared with A09.
- Only solver state changes: A09's measured final values become the next
  initial values for `VC1/VC2/VC3/Vout/IL1/IL2/IL3/IL4`.
- Compatible node voltages are reconstructed from the capacitor-voltage seeds;
  36/24/12 V are no longer hardcoded in this iteration.
- No component, threshold, detector window, gate timing, topology or
  capacitance value changes.
- This is fixed-point iteration, not active balancing and not parameter fitting.
