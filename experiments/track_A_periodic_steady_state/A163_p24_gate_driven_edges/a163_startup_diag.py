"""A163 post hoc diagnostic (not judged): the start-up handover against the gate delay. Runs to 190 us (handover at
~144 us) of S50 on l_p48_1us for the device corners x three start-up tons: nominal, threshold -0.3 V, +0.5 V, +1.0 V
(the largest rigid shift of EPC's typical curve that meets the datasheet's R_DS(on) max 1.55 mOhm and V_GS(TH) max
2.5 V; A163's +1.5 V gives 1.81 mOhm / 2.99 V), C_ISS x 1.5.
  python3 a163_startup_diag.py cfgs      -> cosim_diag/cfg_*.json
  python3 a163_startup_diag.py           -> a163_startup_diag.json (Vo at 143.5 us, peaks, V_DS, late fires)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DIAG = HERE / "cosim_diag"
sys.path.insert(0, str(HERE))
import make_cfgs as MC  # noqa: E402

CORNERS = {"nom": {}, "vthmin": {"dk2": -0.3}, "vth05": {"dk2": 0.5}, "vth10": {"dk2": 1.0}, "cissmax": {"cg_scale": 1.5}}
TONS = (37.887, 40.0, 42.5)


def cfgs():
    DIAG.mkdir(exist_ok=True)
    for c, sp in CORNERS.items():
        for ton in TONS:
            name = f"{c}_t{ton:g}"
            cfg = MC.gate_cfg(MC.row_cfg("l_p48_1us"), "S50", sp)
            cfg = dict(cfg, ton_ns=ton, t_end_us=190.0, out=f"run_{name}.json",
                       note=f"A163 start-up diagnostic: S50, corner {sp or 'nominal'}, start-up ton {ton} ns, to 190 us")
            (DIAG / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")


def stats(path):
    r = json.loads(path.read_text())
    go = r["gate_offs_last"]
    s = [q for q in r["sections"] if "vds_win_v" in q]
    return {"vo_143_5": float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6])),
            "start_pk": max(e["i_max_a"] for e in go if e["t_s"] < 140e-6),
            "hand_pk": max(e["i_max_a"] for e in go if e["t_s"] >= 140e-6),
            "vds_max": max(max(q["vds_win_v"]) for q in s), "late": int(sum(r["late_fires"])),
            "vo_max": max(q["vo"] for q in r["sections"]), "status": r["status"]}


def main():
    out = {}
    for c in CORNERS:
        for ton in TONS:
            p = DIAG / f"run_{c}_t{ton:g}.json"
            if p.exists():
                out[f"{c}_t{ton:g}"] = st = stats(p)
                print(f"{c:8s} ton {ton:6.3f}  Vo {st['vo_143_5']:.3f}  start {st['start_pk']:5.1f}  hand {st['hand_pk']:5.1f}"
                      f"  V {st['vds_max']:4.1f}  late {st['late']:4d}  Vo max {st['vo_max']:.3f}")
    (HERE / "a163_startup_diag.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    cfgs() if sys.argv[1:] == ["cfgs"] else main()
