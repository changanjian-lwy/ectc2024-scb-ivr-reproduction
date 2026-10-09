# Extensions

**Our own additions beyond P24 and P25:** topology or hardware that neither paper has. They are kept apart from the
reproduction so that the two are never mixed.

**Each extension has its own folder:**
- experiments;
- derivations and their records;
- scripts;
- a README with its status and open decisions.

**Its Python modules and tests** are in `src/scb_ivr/extensions/` and `tests/extensions/`.

**Shared code.** Where an extension needs the shared co-simulation plant, the support is opt-in. Without it, every
result is bit-identical (`scripts/cosim_regression.py --full`).

**Numbering.** Experiment and derivation numbers (A…, D…) are shared with the main line, so every number stays
unique.

| extension | what | status |
|---|---|---|
| [aux_commutation_branch](aux_commutation_branch/README.md) | per phase, Lr and a bidirectional switch to a self-balanced Cm, for the high side's zero-voltage turn-on (A101, A102, D56, D57) | built and evaluated as cases; not adopted |
| [ml_design_assist](ml_design_assist/README.md) | machine learning that assists the physics models: an MLP surrogate of D63 (A120), a Gaussian-process residual and active learning (A121), a policy-gradient turn-off rule in the D63 environment (A122); numpy only | started 2026-10-03 |
| [lscb_ladder](lscb_ladder/README.md) | LSCB's capacitor ladder (Tong et al., VLSI 2026) with diode or switched clamps to the series nodes, against rising line steps on rail 1 (A180) | A180 + A182 done 2026-10-09, line closed: helps only as a switched clamp with C_DC >= 20 uF, triggered within ~0.45 us (0.75 V detector, <= 0.3 us delay) at twice the clamp current; not adopted, closed loop not run |
