"""A185 cosim cfgs: A184 with a bumpless loop seed. ton_ns (the loop's reset value, scb_vff's C10 seed, the 0.5x / 2x
clamps) = T_ss + (kp + ki) (Vo_entry - vref), so that the loop's first Ton equals its steady Ton. T_ss = the board's
mean loop Ton over 450-495 us and Vo_entry = Vo at the first mode-P section, both from A184's 25 C run of the same
board (its mode S is A184's bit for bit): a factory step after the mode-S trim. Hot runs keep the 25 C seed (locked).
  python3 make_cfgs.py   seeds.json, cosim/cfg_<cond>_p0.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a184_make", TA / "A184_p24_startup_own_ton" / "make_cfgs.py")
A184 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A184)
REC = TA / "A184_p24_startup_own_ton" / "cosim"
COS = HERE / "cosim"
SEED_FROM = {"S75": "S75_25", "S0": "S0_25", "N0": "N0_25", "N75": "N75_25", "N07": "N07_25", "N13": "N13_25", "F0": "F0_25",
             "M4": "M4_25"}
# A184's conditions: every 25 C board (the c6 misses N0 / F0 / N13 / four modules, and the passes as checks) + hot
CONDS = {"S75_25": True, "N0_25": True, "S0_25": False, "N75_25": False, "N07_25": False, "N13_25": False, "F0_25": False,
         "M4_25": False, "N0_hot": False, "S0_hot": False, "S75_hot": False}


def seed(cond):
    r = json.loads((REC / f"run_{cond}_p0.json").read_text())
    c, tp, lsb = r["cfg"], r["t_mode_p_s"], r["lsb_s"]
    ent = next(q for q in r["sections"] if q["t_s"] > tp)
    tss = float(np.mean([q["ton_lsb"] for q in r["sections"] if 450e-6 <= q["t_s"] < 495e-6])) * lsb * 1e9
    return round(tss + (c["kp_ns_per_v"] + c["ki_ns_per_v"]) * (ent["vo"] - c["vref_v"]), 3), tss, ent["vo"]


def main():
    seeds = {b: dict(zip(("seed_ns", "t_ss_ns", "vo_entry_v"), seed(cond))) for b, cond in SEED_FROM.items()}
    (HERE / "seeds.json").write_text(json.dumps(seeds, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []
    for cond, full in CONDS.items():
        b = cond.split("_")[0]
        c = json.loads((TA / "A184_p24_startup_own_ton" / "cosim" / f"cfg_{cond}_p0.json").read_text())
        c = dict(c, ton_ns=seeds[b]["seed_ns"], out=f"run_{cond}_p0.json",
                 note=c["note"].replace("A184", "A185").replace(f"loop seed / clamps from {c['ton_ns']} ns",
                                                                f"bumpless loop seed {seeds[b]['seed_ns']} ns")
                 .replace(f"loop from {c['ton_ns']} ns", f"bumpless loop seed {seeds[b]['seed_ns']} ns"))
        (COS / f"cfg_{cond}_p0.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(f"{cond}_p0")
    order.insert(0, order.pop(order.index("M4_25_p0")))           # longest first
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", {b: s["seed_ns"] for b, s in seeds.items()})


if __name__ == "__main__":
    main()
