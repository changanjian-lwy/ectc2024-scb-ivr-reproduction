"""A164 pre-registration check (not judged): does a slower turn-on resistor plus a high-side turn-on lead in the
driver hold the valley timing at the datasheet's slow corner, without shoot-through, and what start-up ton does each
corner need? Runs to 300 us of l_p48_1us (handover ~144 us, then ~150 us of mode P).
Corners (datasheet-consistent, A163 RESULTS): nom; ff = threshold -0.3 V + driver x 0.7; ss = threshold +1.0 V +
charge x 1.29 + driver x 1.3; hot = 125 C. Point: 50 pH Q 7, r_on 3.5 / r_off 0.3 ohm per device.
  python3 a164_pre.py cfgs   -> cosim_pre/cfg_*.json
  python3 a164_pre.py        -> a164_pre.json (Vo at 143.5 us, peaks, final dt_pred, late fires, shoot-through)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PRE = HERE / "cosim_pre"
_spec = importlib.util.spec_from_file_location("a163_make_cfgs", HERE.parent / "A163_p24_gate_driven_edges" / "make_cfgs.py")
MC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MC)

R_ON, R_OFF = 3.5, 0.3
CORNERS = {"nom": {}, "ff": {"dk2": -0.3, "r_scale": 0.7}, "ss": {"dk2": 1.0, "cg_scale": 1.29, "r_scale": 1.3},
           "hot": {"temp": 125.0}}
# start-up ton guesses for Vo(143.5 us) ~1.035 V: 37.887 + 0.9 at 2.5 ohm, + ~1 ns for 3.5 ohm, the corner's extra
# on-time loss (~2 x its single-edge turn-on delay change, A163 s50vthmax) and minus the lead
RUNS = [("nom", 0.0, 39.8), ("nom", 8.0, 31.8), ("ff", 0.0, 39.2), ("ff", 8.0, 31.2), ("ss", 0.0, 52.0),
        ("ss", 4.0, 48.0), ("ss", 8.0, 44.0), ("hot", 0.0, 39.8), ("hot", 8.0, 31.8)]


def gate_cfg(corner, lead, ton, t_end=300.0):
    cfg = MC.M.package(MC.row_cfg("l_p48_1us"), 50, round(MC.M.E.q_rp(50e-12, 7), 4), 36.0, ton)
    g = {"dev": "EPC2067", "r_on": R_ON, "r_off": R_OFF, "meas": "act"}
    for k, v in CORNERS[corner].items():
        if k == "r_scale":
            g["r_on"], g["r_off"] = round(R_ON * v, 4), round(R_OFF * v, 4)
        else:
            g[k] = v
    out = dict(cfg, gate=g, ton_ns=ton, t_end_us=t_end)
    if lead:
        out["driver"] = {"hs_on_lead_ns": lead}
    return out


def cfgs():
    PRE.mkdir(exist_ok=True)
    for c, lead, ton in RUNS:
        name = f"{c}_lead{lead:g}"
        (PRE / f"cfg_{name}.json").write_text(json.dumps(dict(gate_cfg(c, lead, ton), out=f"run_{name}.json",
                                                              note=f"A164 pre: {c}, lead {lead} ns, ton {ton} ns"),
                                                         indent=1) + "\n")


def stats(path):
    r = json.loads(path.read_text())
    go, s = r["gate_offs_last"], [q for q in r["sections"] if "vds_win_v" in q]
    g = r.get("gate_stats", {})
    return {"ton_ns": r["cfg"]["ton_ns"], "vo_143_5": float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6])),
            "start_pk": max(e["i_max_a"] for e in go if e["t_s"] < 140e-6),
            "hand_pk": max(e["i_max_a"] for e in go if 140e-6 <= e["t_s"] < 200e-6),
            "steady_pk": max(e["i_max_a"] for e in go if e["t_s"] >= 200e-6),
            "vds_max": max(max(q["vds_win_v"]) for q in s), "late": [int(x) for x in r["late_fires"]],
            "dt_pred_ns": r["dt_pred_final_ns"], "shoot_on": g.get("shoot_on"), "overlaps": r["overlaps"],
            "delay_on_ns": [x * 1e9 for x in g.get("delay_on_s", [0, 0])],
            "vo_end": float(np.mean([q["vo"] for q in r["sections"][-50:]])), "status": r["status"]}


def main():
    out = {}
    for c, lead, _ in RUNS:
        p = PRE / f"run_{c}_lead{lead:g}.json"
        if p.exists():
            out[p.stem[4:]] = st = stats(p)
            print(f"{p.stem[4:]:10s} ton {st['ton_ns']:5.1f} Vo {st['vo_143_5']:.3f} start {st['start_pk']:5.1f} hand "
                  f"{st['hand_pk']:5.1f} steady {st['steady_pk']:5.1f} V {st['vds_max']:4.1f} late {st['late']} dtp "
                  f"{[round(x, 1) for x in st['dt_pred_ns']]} shoot {sum(st['shoot_on'] or [0])} ovl {st['overlaps']}")
    (HERE / "a164_pre.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    cfgs() if sys.argv[1:] == ["cfgs"] else main()
