# Extension: the LSCB capacitor ladder on the P24 module

**This is our extension, not part of the P24 / P25 reproduction.** It borrows the capacitor ladder of LSCB (Tong et
al., "A 2D-Extendable 48V-1V Ladder-Series-Capacitor Buck Converter for Computing Power Delivery", VLSI 2026):
four capacitors C_DC in series across Vin, and a clamp from each ladder node to the series node between two cells,
so that each flying capacitor stays near its Vin/4 multiple. The question is whether it helps P24's known weak spot,
a rising line step landing on rail 1 (A124, A148).

**Status (2026-10-09): A180 registered (open-loop power stage).** Step 2 (closed-loop cosim) depends on A180's
decision rule.

| item | path |
|---|---|
| A180: open-loop LTspice power stage, base vs diode / switched clamps and C_DC sizes | `experiments/A180_lscb_ladder_open_loop/` |
| netlist builder and metrics | `src/scb_ivr/extensions/lscb_ladder.py` |
| tests | `tests/extensions/test_lscb_ladder.py` |

**Run from the project root** (LTspice in its CrossOver bottle, see `scripts/p24_ltspice.py`):

```
python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_predict.py
PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_run.py --jobs 2
```

**Adaptation to P24.** P24 has one switch between cells (vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4). LSCB splits it into two
with a node in between, where its S_DC lands. Without that node a clamp at a_k is safe only as a diode with its anode
at the ladder, or as a switch closed while SL_k conducts.
