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
