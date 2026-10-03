"""A118 configurations: the timed phase-1 turn-off with a comparator floor (cfg lo_floor 1, lo_floor_a 2 A; D63's
proposal, A120's search), on A115's 1 MHz 10% design (cfg_n10: timed, D59 60 kHz). One factor: the floor; Cs as the
second (6 uF, A120's feasible band; 15 uF, A115's) with controls without the floor.
Rows: n0 (the start-up included), the +-62.5 A load steps and the +-4.8 V input steps over 1, 5 and 20 us at 2000 us.
Writes cosim/cfg_*.json and cosim/ORDER.txt."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "A115_p24_one_mhz_design_point" / "cosim" / "cfg_n10.json"
STEPS = {"n0": None, "s_m62": ("load", -62.5, 0), "s_p62": ("load", 62.5, 0),
         "l_p48_1us": ("line", 4.8, 1), "l_m48_1us": ("line", -4.8, 1), "l_p48_5us": ("line", 4.8, 5),
         "l_m48_5us": ("line", -4.8, 5), "l_p48_20us": ("line", 4.8, 20), "l_m48_20us": ("line", -4.8, 20)}
ROWS = [(f"f6_{k}", 6, 1, k) for k in ("s_m62", "l_m48_1us", "l_p48_1us", "l_m48_5us", "l_p48_5us", "s_p62", "l_m48_20us",
                                         "l_p48_20us", "n0")] + \
       [("f15_s_m62", 15, 1, "s_m62"), ("f15_l_m48_5us", 15, 1, "l_m48_5us"), ("f15_l_p48_5us", 15, 1, "l_p48_5us"),
        ("t6_s_m62", 6, 0, "s_m62"), ("t6_l_m48_5us", 6, 0, "l_m48_5us")]

if __name__ == "__main__":
    for name, cs, floor, step in ROWS:
        c = json.loads(SRC.read_text())
        c["circuit"] = dict(c["circuit"], cs=cs * 1e-6)
        if floor:
            c["lo_floor"], c["lo_floor_a"] = 1, 2.0
        st = STEPS[step]
        if st is None:
            c["t_end_us"] = 2500.0
        elif st[0] == "load":
            c["load_step"] = {"t_us": 2000.0, "i_a": st[1]}; c["t_end_us"] = 3000.0
        else:
            c["line_step"] = {"t_us": 2000.0, "dv": st[1], "slew_us": float(st[2])}; c["t_end_us"] = 3000.0
        c["note"] = f"A118 {name}: A115's n10 with Cs {cs} uF" + (", the floor (lo_floor 1, 2 A)" if floor else ", no floor") + f", {step}."
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(r[0] for r in ROWS) + "\n")
    print(len(ROWS), "configurations")
