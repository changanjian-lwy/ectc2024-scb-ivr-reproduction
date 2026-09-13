# Step 20 - R04D3C P25 five-percent target mapped to P24 commutation

## Controlled change

Baseline: R04D3A.  The only changed variable is
`NEG_FRAC: 0.01 -> 0.05`.  Topology, initial state, inductance, scalar switch
capacitances, switch population and physical-event termination condition are
unchanged.

This is a cross-paper control experiment.  It is not labelled as a P24-native
reproduction because P24 states 1%-2%, while the P25 design section uses up to
5% for the negative-current design target.

## Result

- Low-side turn-off: 9.26738 ns.
- Current at turn-off: -6.25 A = -5% of the retained 125 A phase peak.
- Maximum phase-1 switching-node voltage: 8.10626 V.
- Minimum high-side Vds after turn-off: 3.87440 V.
- Target high-side zero-Vds event: not reached.

Compared with the 1% baseline, the commutation moves substantially farther in
the expected direction, but 5% is still insufficient under the selected
GS61008T scalar-capacitance plug-in.

## Remaining non-equivalences

### Inside/between the papers

- P24 states a 1%-2% negative-current target; P25 Mode 4 says 5%-10%, while
  the P25 design section uses up to 5%. These remain separate source branches.
- P24 targets 48 V, four phases and the Table-I analytical case; the P25
  prototype is 12 V, three phases per module, three modules, 22 nH and 0.5 MHz.
- P24 Eq.(4) evaluation retained by this project gives 1.4667 nH for the
  selected case, whereas the corresponding Table-I printed entry has already
  been recorded as a numerical conflict. The calculated value controls.

### Missing source data

- P25 gives capacitor families but not complete capacitance/parallel-count,
  ESR and ESL specifications.
- Added high/low commutation/snubber capacitances are discussed but their
  prototype values are not reported.
- Nonlinear Coss/Qoss curves are not incorporated by the paper tables.
- Exact zero-cross detector threshold, propagation delay, gate delay and dead
  time are not reported.
- Startup/precharge sequence and the periodic-state inductor-current vector
  are not reported.

### Present model boundary

- GS61008T CO(TR)=385 pF over 0-50 V is used as a fixed scalar; the actual
  transition is near 12 V and Coss is nonlinear.
- The low side uses two parallel devices and therefore 770 pF in this model;
  package/layout and any added capacitors are absent.
- R04D3C is a local phase-1 commutation model with a stiff 1 V output, not a
  complete four-phase charge-balanced periodic orbit.
- Its capacitor state is chained from R04D2A, whose earlier ladder state was a
  periodic-state candidate rather than a demonstrated zero-start solution.
