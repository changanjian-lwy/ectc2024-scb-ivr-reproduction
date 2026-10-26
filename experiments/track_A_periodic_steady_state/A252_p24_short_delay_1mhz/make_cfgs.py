"""A252 cfgs (BOUNDARY Section 1): the final configuration's 1 MHz train rows (A246 cfg_h_) with phases 2-4 held at a
short delay from reset (A249's dt_fix_ns): S75h at the learner's own median during the train (4.41 / 4.34 / 4.16 ns,
A246's record), N75 at 5 and 9 ns (its learner stays at 13-15 ns there).
  python3 make_cfgs.py -> cosim/cfg_<arm>_<row>.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A46 = TA / "A246_p24_held_report_floor" / "cosim"
ARMS = {"s4": ("p_S75h_1000k", [4.41, 4.34, 4.16]), "n5": ("p_N75_1000k", [5.0, 5.0, 5.0]),
        "n9": ("p_N75_1000k", [9.0, 9.0, 9.0])}


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    for arm, (row, dt) in ARMS.items():
        c = json.loads((A46 / f"cfg_h_{row}.json").read_text())
        c.update(dt_fix_ns=dt, out=f"run_{arm}_{row}.json", note=f"A252 arm {arm}: A246 cfg_h_{row} + dt_fix_ns {dt}")
        (HERE / "cosim" / f"cfg_{arm}_{row}.json").write_text(json.dumps(c, indent=1) + "\n")


if __name__ == "__main__":
    main()
