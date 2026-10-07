"""A164 cosim cfgs: the gate drive over the datasheet-consistent spread (A163 RESULTS) with three changes to A163's S50:
r_on 3.0 ohm with a +-20 % driver tolerance (A164 pre: at +-30 % no single resistor holds both the fast corner's V_DS
and the slow corner's timing), a lead on predictive high-side turn-ons (bridge driver "hs_on_lead_ns"), and a
per-board start-up trim (each board's start-up ton set from one start-up run).
Boards: device corner x inductor corner. Corners: nom; ff = threshold -0.3 V + driver x 0.8; ss = threshold +1.0 V +
charge x 1.29 + driver x 1.2; hot = 125 C. (cosim_cal_r35/: the same calibration at 3.5 ohm / +-30 %, before the
change; not used.)
  python3 make_cfgs.py cal   stage 1: cosim_cal/cfg_<board>.json, start-up to 150 us at a first-guess ton
  python3 make_cfgs.py       stage 2: the trim ton = ton0 + (1.035 - Vo(143.5 us)) / 0.026 per board (one shot, slope
                             from A163's diagnostics 0.025-0.0265 V/ns) -> cosim/cfg_*.json, cosim/ORDER.txt, trims.json"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
_spec = importlib.util.spec_from_file_location("a163_make_cfgs", HERE.parent / "A163_p24_gate_driven_edges" / "make_cfgs.py")
MC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MC)
M = MC.M

L_PH, R_ON, R_OFF, LEAD = 50, 3.0, 0.3, 8.0
VO_TGT, SLOPE = 1.035, 0.026
CORNERS = {"nom": {}, "ff": {"dk2": -0.3, "r_scale": 0.8}, "ss": {"dk2": 1.0, "cg_scale": 1.29, "r_scale": 1.2},
           "hot": {"temp": 125.0}}
# board: (corner, L row prefix, first-guess ton ns: the 3.5 ohm trims (cosim_cal_r35) less ~0.8 ns, ss from the
# pre run ss20_lead8 (Vo 1.068 V at 49.5 ns))
BOARDS = {"nom_L0": ("nom", "", 39.6), "nom_L07": ("nom", "L07_", 34.3), "nom_L13": ("nom", "L13_", 41.0),
          "ff_L0": ("ff", "", 37.85), "ss_L0": ("ss", "", 48.2), "hot_L0": ("hot", "", 39.25)}
# run: (board, row, lead ns)
RUNS = ([("nom_L0", r, LEAD) for r in ("l_p48_1us", "s_p62", "l_m80_10us", "slew4")]
        + [("nom_L07", "L07_l_p48_1us", LEAD), ("nom_L13", "L13_l_p48_1us", LEAD)]
        + [("ff_L0", r, LEAD) for r in ("l_p48_1us", "s_p62", "l_m80_10us")]
        + [("ss_L0", r, LEAD) for r in ("l_p48_1us", "s_p62", "l_m80_10us", "slew4")]
        + [("hot_L0", r, LEAD) for r in ("l_p48_1us", "s_p62")]
        + [("nom_L0", r, 0.0) for r in ("l_p48_1us", "l_m80_10us")])


def gate_cfg(cfg, corner, ton, lead):
    g = {"dev": "EPC2067", "r_on": R_ON, "r_off": R_OFF, "meas": "act"}
    for k, v in CORNERS[corner].items():
        if k == "r_scale":
            g["r_on"], g["r_off"] = round(R_ON * v, 4), round(R_OFF * v, 4)
        else:
            g[k] = v
    out = dict(M.package(cfg, L_PH, round(M.E.q_rp(L_PH * 1e-12, 7), 4), 36.0, round(ton, 3)), gate=g, late_log=1)
    if lead:
        out["driver"] = dict(cfg.get("driver") or {}, hs_on_lead_ns=lead)
    return out


def cal():
    CAL.mkdir(exist_ok=True)
    for b, (corner, lp, ton0) in BOARDS.items():
        cfg = dict(gate_cfg(MC.row_cfg(lp + "l_p48_1us"), corner, ton0, 0.0), t_end_us=150.0, out=f"run_{b}.json",
                   note=f"A164 stage 1: board {b} start-up at ton {ton0} ns")
        (CAL / f"cfg_{b}.json").write_text(json.dumps(cfg, indent=1) + "\n")


def trims():
    out = {}
    for b, (_, _, ton0) in BOARDS.items():
        r = json.loads((CAL / f"run_{b}.json").read_text())
        vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
        out[b] = {"ton0_ns": ton0, "vo0": vo, "ton_ns": round(ton0 + (VO_TGT - vo) / SLOPE, 3)}
    return out


def main():
    tr = trims()
    (HERE / "trims.json").write_text(json.dumps(tr, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A164 {name}: {note}"),
                                                         indent=1) + "\n")
        order.append(name)
    m4 = json.loads((M.A143C / "cfg_g5_l_p48_1us_k4.json").read_text())
    put("m4_nom_l_p48_1us", gate_cfg(m4, "nom", tr["nom_L0"]["ton_ns"], LEAD), "four modules, nom, lead 8 ns")
    for b, row, lead in RUNS:
        corner = BOARDS[b][0]
        name = f"{corner}{'' if lead else '_lead0'}_{row}"
        put(name, gate_cfg(MC.row_cfg(row), corner, tr[b]["ton_ns"], lead),
            f"{row}, 50 pH, r_on {R_ON} / r_off {R_OFF} ohm, corner {CORNERS[corner] or 'nominal'}, lead {lead} ns, "
            f"trimmed ton {tr[b]['ton_ns']} ns")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", {b: t["ton_ns"] for b, t in tr.items()})


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
