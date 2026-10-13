"""A213 cosim cfg: A206's binding row B_S75_hot_p5 (slow 0.75 L0 board, 125 C, +4.8 V / 1 us at 500.3155 us, final
configuration on plant V6, low sides 0.36 ohm) with replay snapshots and the gate-edge log: a settled window before
the step and one from the step past the peak. End 524.5 us (A206's row ran to 581.3 us).
  python3 make_cfgs.py -> cosim/cfg_S75_hot_p5.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "A206_p24_low_side_zvs_turn_on" / "cosim" / "cfg_B_S75_hot_p5_ls0p3.json"
SNAP, EDGES, T_END = [[481.0, 484.0], [499.9, 523.6]], [480.9, 524.0], 524.5

if __name__ == "__main__":
    c = json.loads(SRC.read_text())
    c = dict(c, snap_us=SNAP, debug_edges_us=EDGES, t_end_us=T_END, out="run_S75_hot_p5.json",
             note=c["note"].replace("A206 B_S75_hot_p5_ls0p3", "A213 S75_hot_p5") + f"; snapshots {SNAP} us, end {T_END} us")
    (HERE / "cosim").mkdir(exist_ok=True)
    (HERE / "cosim" / "cfg_S75_hot_p5.json").write_text(json.dumps(c, indent=1) + "\n")
    print(c["line_step"], c["t_end_us"], c["gate"])
