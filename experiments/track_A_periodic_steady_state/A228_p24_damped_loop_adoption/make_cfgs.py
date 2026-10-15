"""A228 cosim cfgs: the adoption check of A224's damped loop, plant V7, A222's trims, one module.
Arms: d0 = the final configuration as it is (no gate, no derivative term); k = vff rel_gate 25 + kd 355 ns/V, dead band
2 (A224); h = k + kd_hold 1 (A227).
- part S (the skipping rows' scatter): A224's three skipping rows (N0 10 %, N75 10 %, N0 no load) with the load released
  at 301.3 / 302.7 / 304.1 us (t1-t3) in all three arms, and N75 10 % at 300 us in d0 (t0; the other t0 records exist:
  A226 / A227 d0, A224 k, A227 h);
- part R (arm h on the rest of A224's rows): w20_N0, w30_S75h, u_N0, k_N0, l_N0_p48, l_N0_m80, k_S75h, h_S75_25.
    python3 make_cfgs.py -> cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M27 = _load("a227_make_cfgs", "A227_p24_kd_held_at_the_limit/make_cfgs.py")
M24, M23 = M27.M24, M27.M24.M23
KD = M27.KD
T_REL = {"t1": 301.3, "t2": 302.7, "t3": 304.1}
R_ROWS = ("w20_N0", "w30_S75h", "u_N0", "k_N0", "l_N0_p48", "l_N0_m80", "k_S75h")


def d0(c, what, name):
    x = copy.deepcopy(c)
    x["out"] = f"run_{name}.json"
    x["note"] = (f"A228 {name}: {what}; final configuration on plant V7 (r_core {x['circuit']['r_core']} ohm, ton_s_ns "
                 f"{x['ton_s_ns']}), skip {x.get('skip')}, no gate, no derivative term")
    return name, x


ARMS = {"d0": d0, "k": lambda c, what, name: M24.arm(c, what, name, KD), "h": M27.held}


def released(z, t):
    c, what = M24.z_row(*M24.Z_ROWS[z])
    c = copy.deepcopy(c)
    c["load_step"] = dict(c["load_step"], t_us=t)
    return c, what.replace("released at 300 us", f"released at {t} us")


def note(name, x):
    x["note"] = x["note"].replace("A224", "A228", 1).replace("A227", "A228", 1)
    return name, x


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    rows = [note(*ARMS[a](*released(z, t), f"{z}_{k}_{a}")) for k, t in T_REL.items() for z in M24.Z_ROWS for a in ARMS]
    rows.append(note(*d0(*released("z_N75_10", 300.0), "z_N75_10_t0_d0")))
    rows += [note(*M27.held(*M23.ROWS[r], f"{r}_h")) for r in R_ROWS]
    c = M23.load("A222_p24_v7_startup_trim/cosim/cfg_s_S75_25_r2.json")
    rows.append(note(*M27.held(c, "A222's S75 25 C start-up to 200 us", "h_S75_25_h")))
    order = [r for r in rows if r[0].startswith("z_")] + [r for r in rows if not r[0].startswith("z_")]
    for name, c in order:
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(n for n, _ in order) + "\n")
    print(len(order), "cfgs")
