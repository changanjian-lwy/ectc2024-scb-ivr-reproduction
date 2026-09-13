# Modular assembly architecture

## Principle

The framework is capability-driven, not a fixed converter script. An
experiment asks for capabilities; independently registered modules fill the
required slots. Registration does not mean adoption.

## Stable slots

| Slot | Example capability | Replaceable input |
|---|---|---|
| topology | `four_phase_power_topology` | P24 Fig. 3 or a future topology |
| analytical | `duty`, `critical_inductance` | P24 equations or another paper's model |
| sequence | `phase_local_three_interval_sequence` | P24 sequence or an explicitly selected alternative |
| commutation | `symbolic_coss_commutation` | P25 equations or another validated commutation model |
| controller | ZCD/blanking/variable off-time | measured controller or published implementation |
| startup | precharge/current-limit sequence | a compatible startup module |
| device | Coss/dead-time/device curves | GaN model, datasheet or measured data |

## Assembly behavior

1. The request lists required capabilities and allowed evidence classes.
2. The planner chooses P24 explicit modules first.
3. A selected module may declare additional requirements; the planner follows
   those dependencies recursively.
4. P25 fills only capabilities still absent after P24 selection.
5. A replacement device module can be appended to the catalogue without
   changing topology, equations or sequence code.
6. Two incompatible sequence implementations cannot occupy the sequence slot;
   the planner reports a slot conflict rather than merging them.
7. Missing dependencies and unresolved conflicts prevent netlist generation.

## Demonstrated requests

- Analytical-only request: selects only `p24_equations_1_to_6` and is ready.
- Numeric P24 commutation without device data: selects P24 topology/sequence
  plus P25 symbolic equations, then reports exactly
  `commutation_capacitance` and `dead_time` as missing.
- Same request with a replaceable external device module: becomes ready without
  modifying the framework.
- Requesting both P24 local sequence and P25 cross-phase sequence: blocked as a
  sequence-slot conflict.

## Next boundary

An `AssemblyPlan.ready` result means only that every requested slot is filled
and conflict-free. It does not prove that the electrical model is correct.
The later netlist emitter must preserve every module's evidence metadata in the
generated file header and acceptance report.
