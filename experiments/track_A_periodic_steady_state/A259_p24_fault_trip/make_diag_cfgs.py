"""A259's look beforehand (before its BOUNDARY): the final configuration with no fault path, under an output short
or a resistive overload above D89's ~136 % rating from 400 us, to see how fast Vo falls and the currents rise.
Base: A258's cfg_c_o125_<board> (final configuration + ocp n_cap 6) without its load step; cfg "short" adds the
resistance across r_load (4 mOhm, 250 A at 1 V): 0.25 / 1 mOhm shorts, 8 / 4 mOhm = 150 / 200 % load.
  python3 make_diag_cfgs.py -> cosim/cfg_d_*.json"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A58 = HERE.parent / "A258_p24_limit_count_cap" / "cosim"
ROWS = {"sh025_N75": ("N75", 0.25), "sh1_N75": ("N75", 1.0), "ov150_N75": ("N75", 8.0), "ov200_N75": ("N75", 4.0),
        "sh025_S75h": ("S75h", 0.25), "ov150_S75h": ("S75h", 8.0)}


def main():
    (HERE / "cosim").mkdir(exist_ok=True)
    for row, (b, r) in ROWS.items():
        c = json.loads((A58 / f"cfg_c_o125_{b}.json").read_text())
        c.pop("load_step")
        c.update(short={"t_us": 400.0, "r_mohm": r}, t_end_us=430.0, out=f"run_d_{row}.json",
                 note=f"A259 look beforehand: final configuration, no fault path, {r} mOhm across the output from 400 us")
        (HERE / "cosim" / f"cfg_d_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
    print(len(ROWS), "cfgs")


if __name__ == "__main__":
    main()
