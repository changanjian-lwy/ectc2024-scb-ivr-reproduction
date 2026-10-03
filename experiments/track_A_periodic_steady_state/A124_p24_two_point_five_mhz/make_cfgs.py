"""A124 configurations: the adopted single module (C02 cosim/cfg_s1_n0.json: A105's I2 with slot_lo) moved from P24's
5 MHz column to 2.5 MHz, the frequency D64's inductor model favours at P24's in-package scale, with Eq. (4)'s 2.933 nH.
As A115 did for 1 MHz, by time scaling (K = 2): L and Cs x2 (Cs 6 uF: the same Q / Cs as 3 uF at 5 MHz); period
times x2 (mode S Ton and T0, rs_low, the input ramp, the handover, the run, the steps, lo_smax); node times x sqrt 2
(the predictive delay's start, step, cap, rs_high); D59's loop at 2.5 MHz, fc 100 kHz, designed at 12.5%
(a124_predictions.json); phase 1's floor at 2 A (A118). Rows: n0 at 10 / 12.5 / 15%; at 12.5% the +-62.5 A steps,
+-4.8 V over 1 and 5 us, -8 V over 10 us; a control without the floor (-62.5 A). Writes cosim/cfg_*.json, ORDER.txt."""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
C02 = HERE.parents[1] / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
K, KR = 2.0, math.sqrt(2.0)
L, CS, T_STEP = 7.3333333e-9 / 2.5, 6e-6, 800.0
STEPS = {"n0": None, "s_m62": ("load", -62.5, 0), "s_p62": ("load", 62.5, 0), "l_p48_1us": ("line", 4.8, 1), "l_m48_1us": ("line", -4.8, 1),
         "l_p48_5us": ("line", 4.8, 5), "l_m48_5us": ("line", -4.8, 5), "l_m80_10us": ("line", -8.0, 10)}
ROWS = [("p125_s_m62", 12.5, 1, "s_m62"), ("t125_s_m62", 12.5, 0, "s_m62"), ("p125_l_m48_1us", 12.5, 1, "l_m48_1us"),
        ("p125_l_p48_1us", 12.5, 1, "l_p48_1us"), ("p125_l_m80_10us", 12.5, 1, "l_m80_10us"), ("p125_s_p62", 12.5, 1, "s_p62"),
        ("p125_l_m48_5us", 12.5, 1, "l_m48_5us"), ("p125_l_p48_5us", 12.5, 1, "l_p48_5us"),
        ("p125_n0", 12.5, 1, "n0"), ("p10_n0", 10.0, 1, "n0"), ("p15_n0", 15.0, 1, "n0")]


def scaled(c, pct, floor, loop):
    c = dict(c)
    c["circuit"] = {"L": L, "cs": CS}
    for k in ("ton_ns", "t0_ns", "rs_low_ns", "t_hand_us"):
        c[k] = round(c[k] * K, 6)
    c["t_ramp_us"] = round(68.61 * K, 6)
    for k in ("dt_init_ns", "dt_step_ns", "dt_max_ns", "rs_high_ns"):
        c[k] = round(c[k] * KR, 6)
    c["lo_smax"] = int(c["lo_smax"] * K)
    c["kp_ns_per_v"], c["ki_ns_per_v"] = round(loop["kp_ns_per_v"], 3), round(loop["ki_ns_per_v"], 4)
    c["i_target"] = -pct / 100 * 125.0
    if floor:
        c["lo_floor"], c["lo_floor_a"] = 1, 2.0
    return c


if __name__ == "__main__":
    loop = json.loads((HERE / "a124_predictions.json").read_text())["loop"]
    for name, pct, floor, step in ROWS:
        c = scaled(json.loads((C02 / "cfg_s1_n0.json").read_text()), pct, floor, loop)
        st = STEPS[step]
        c.pop("load_step", None); c.pop("line_step", None)
        if st is None:
            c["t_end_us"] = 1000.0
        elif st[0] == "load":
            c["load_step"] = {"t_us": T_STEP, "i_a": st[1]}; c["t_end_us"] = 1200.0
        else:
            c["line_step"] = {"t_us": T_STEP, "dv": st[1], "slew_us": float(st[2])}; c["t_end_us"] = 1200.0
        c["note"] = f"A124 {name}: C02's s1_n0 at 2.5 MHz (L 2.933 nH, Cs 6 uF, times x2 / x sqrt 2, D59 100 kHz), {pct}%" + \
                    (", floor 2 A" if floor else ", no floor") + f", {step}."
        c["out"] = f"run_{name}.json"
        (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(r[0] for r in ROWS) + "\n")
    print(len(ROWS), "configurations")
