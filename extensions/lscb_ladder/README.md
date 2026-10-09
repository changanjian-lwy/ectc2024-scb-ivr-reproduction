# Extension: the LSCB capacitor ladder on the P24 module

**This is our extension, not part of the P24 / P25 reproduction.** It borrows the capacitor ladder of LSCB (Tong et
al., "A 2D-Extendable 48V-1V Ladder-Series-Capacitor Buck Converter for Computing Power Delivery", VLSI 2026):
four capacitors C_DC in series across Vin, and a clamp from each ladder node to the series node between two cells,
so that each flying capacitor stays near its Vin/4 multiple. The question is whether it helps P24's known weak spot,
a rising line step landing on rail 1 (A124, A148).

**Status (2026-10-09): line closed, not adopted (A180 + A182).**
- A180: only a switched clamp, closed in a window after the disturbance with C_DC >= 20 uF (Cs 6 uF), helps.
  - On +4.8 V / 1 us, rail 1 goes +4.64 -> +2.17 V (20 uF) / +1.68 V (60 uF), and phase 1's peak 243 -> 161 / 152 A
    in the open-loop stage.
  - LSCB's passive 0.7 V diode pumps the GaN dead-time current into Cs (phase spread 11 %).
  - A switch closed every period costs 4.6 W per module.
- A182 replaced A180's ideal trigger with a detector.
  - At a 0.75 V threshold (steady deviation 0.29 V) with <= 0.3 us delay, the benefit is kept (+2.16 V, 161 A).
  - The price is twice the clamp current (289 vs 146 A, resistance-limited).
  - At 1.0 us delay, or with a 1.5 V threshold, the benefit is lost.
- What it would take:
  - <= ~0.45 us total trigger latency;
  - a clamp rated ~2x, or current-limited;
  - four 20-60 uF capacitors at 12 V, three clamp switches with floating drives, and a detector per module.
- The closed-loop cosim (step 2) was not run, by the user's choice on 2026-10-09.

| item | path |
|---|---|
| A180: open-loop LTspice power stage, base vs diode / switched clamps and C_DC sizes (RESULTS, figure a180_up1.png; records: release records-a180) | `experiments/A180_lscb_ladder_open_loop/` |
| A182: the switched clamp opened by a detector (threshold 0.75 / 1.5 V, delay 0.1-1.0 us), two passes (RESULTS; records: release records-a182) | `experiments/A182_lscb_detector_clamp/` |
| netlist builder and metrics | `src/scb_ivr/extensions/lscb_ladder.py` |
| tests | `tests/extensions/test_lscb_ladder.py` |

**Run from the project root** (LTspice in its CrossOver bottle, see `scripts/p24_ltspice.py`):

```
python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_predict.py
PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_run.py --jobs 2
PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A182_lscb_detector_clamp/a182_run.py --jobs 4
```

**Adaptation to P24.** P24 has one switch between cells (vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4). LSCB splits it into two
with a node in between, where its S_DC lands. Without that node a clamp at a_k is safe only as a diode with its anode
at the ladder, or as a switch closed while SL_k conducts.
