"""A243 control cfgs (BOUNDARY Section 5): the rows that missed g5 / g6, with their disturbance moved by k T / 6
(k 2 and 4, A232's positions; T = the reference record's median phase-1 turn-on interval in the 20 us before the
disturbance; both steps of a re-application move together). Arm r = the reference cfg (options absent), arm b =
the same + early_hold_a and late_hold_a 0.0. Position k 0 of each arm is the existing record (reference / run_b_).
  python3 make_ctrl_cfgs.py"""
from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a243_make_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(_s)
_s.loader.exec_module(MC)
ROWS = ("r_F0_lm48", "r_F0_lm80", "a_S75h_d20", "a_S75_d20", "u_N0", "w5_N0", "w20_N0")
KS = (2, 4)


def period_us(row):
    r = json.loads(MC.ref(row).read_text())
    t0 = (r["cfg"].get("line_step") or r["cfg"]["load_step"])["t_us"] * 1e-6
    on = [x["t_s"] for x in r["turnons_last"] if x["phase"] == 1 and t0 - 20e-6 <= x["t_s"] < t0]
    return statistics.median(b - a for a, b in zip(on, on[1:])) * 1e6


def moved(c, dt_us):
    c = dict(c)
    for k in ("line_step", "load_step", "load_step2"):
        if c.get(k):
            c[k] = dict(c[k], t_us=round(c[k]["t_us"] + dt_us, 4))
    c["t_end_us"] = round(c["t_end_us"] + dt_us, 4)
    return c


def main():
    for row in ROWS:
        c, t = json.loads(MC.src(row).read_text()), period_us(row)
        for k in KS:
            m = moved(c, k * t / 6)
            r = dict(m, out=f"run_cr_{row}_k{k}.json",
                     note=f"A243 control arm r: {MC.src(row).stem[4:]} moved by {k} T / 6 (T {t:.4f} us)")
            b = dict(m, out=f"run_cb_{row}_k{k}.json", early_hold_a=MC.HOLD_A, late_hold_a=MC.HOLD_A,
                     note=f"A243 control arm b: {MC.src(row).stem[4:]} moved by {k} T / 6 (T {t:.4f} us) + holds {MC.HOLD_A}")
            for arm, x in (("cr", r), ("cb", b)):
                (COS / f"cfg_{arm}_{row}_k{k}.json").write_text(json.dumps(x, indent=1) + "\n")
    print(len(list(COS.glob("cfg_c[rb]_*.json"))), "control cfgs")


if __name__ == "__main__":
    main()
