"""A168 cosim cfgs: the adopted drive (A164 + A167: r_on R / r_off 0.3 ohm +-20 %, 8 ns turn-on lead ramped in over 20 us
after mode P, per-board start-up trim) at a larger power loop. Configurations (loop pH, nominal r_on ohm):
P60 (60, 3.0) the spec as it stands; Q60 (60, 3.5) its fallback if P60's fast corner passes 40 V; Q75 (75, 4.0).
Boards and corners are A164's (nom / ff / ss; ss = threshold +1.0 V, Q_G x 1.29, driver x 1.2, so 4.8 ohm at Q75).
  python3 make_cfgs.py cal   stage 1: cosim_cal/cfg_<config>_<board>.json, start-up to 150 us at a first-guess ton
  python3 make_cfgs.py       stage 2: trim ton = ton0 + (1.035 - Vo(143.5 us)) / 0.026 per board -> cosim/cfg_*.json,
                             cosim/ORDER.txt (longest first), trims.json"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS, CAL = HERE / "cosim", HERE / "cosim_cal"
A4D = HERE.parent / "A164_p24_gate_drive_spread"
_s = importlib.util.spec_from_file_location("a164_make_cfgs", A4D / "make_cfgs.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)
MC, M, CORNERS = A4.MC, A4.M, A4.CORNERS

R_OFF, LEAD, RAMP_US = 0.3, 8.0, 20.0
VO_TGT, SLOPE = 1.035, 0.026
CONFIGS = {"P60": (60, 3.0), "Q60": (60, 3.5), "Q75": (75, 4.0)}
BOARDS = {"nom_L0": ("nom", ""), "nom_L07": ("nom", "L07_"), "ff_L0": ("ff", ""), "ss_L0": ("ss", "")}
DTON_PER_OHM = 1.6        # first guess: A164's 3.0 ohm trims sat ~0.8 ns below its 3.5 ohm ones (cosim_cal_r35)
RUNS = {"P60": [("ff_L0", "l_p48_1us"), ("nom_L07", "L07_l_p48_1us"), ("nom_L0", "l_p48_1us"), ("ss_L0", "l_p48_1us")],
        "Q60": [("ff_L0", "l_p48_1us"), ("nom_L07", "L07_l_p48_1us"), ("ss_L0", "l_p48_1us"), ("ss_L0", "s_p62")],
        "Q75": [("ff_L0", "l_p48_1us"), ("nom_L07", "L07_l_p48_1us"), ("nom_L0", "l_p48_1us"), ("ss_L0", "l_p48_1us"),
                ("ss_L0", "s_p62")]}


def first_guess(conf, board):
    _, r = CONFIGS[conf]
    scale = {"ff": 0.8, "ss": 1.2}.get(BOARDS[board][0], 1.0)
    base = json.loads((A4D / "trims.json").read_text())[board]["ton_ns"]
    return round(base + DTON_PER_OHM * scale * (r - 3.0), 2)


def gate_cfg(cfg, conf, corner, ton, lead):
    l_ph, r_on = CONFIGS[conf]
    g = {"dev": "EPC2067", "r_on": r_on, "r_off": R_OFF, "meas": "act"}
    for k, v in CORNERS[corner].items():
        if k == "r_scale":
            g["r_on"], g["r_off"] = round(r_on * v, 4), round(R_OFF * v, 4)
        else:
            g[k] = v
    out = dict(M.package(cfg, l_ph, round(M.E.q_rp(l_ph * 1e-12, 7), 4), 36.0, round(ton, 3)), gate=g, late_log=1)
    if lead:
        out["driver"] = dict(cfg.get("driver") or {}, hs_on_lead_ns=lead, lead_ramp_us=RAMP_US)
    return out


def cal():
    CAL.mkdir(exist_ok=True)
    for conf in CONFIGS:
        for b, (corner, lp) in BOARDS.items():
            ton0 = first_guess(conf, b)
            cfg = dict(gate_cfg(MC.row_cfg(lp + "l_p48_1us"), conf, corner, ton0, 0.0), t_end_us=150.0,
                       out=f"run_{conf}_{b}.json", note=f"A168 stage 1: {conf} board {b} start-up at ton {ton0} ns")
            (CAL / f"cfg_{conf}_{b}.json").write_text(json.dumps(cfg, indent=1) + "\n")


def trims():
    out = {}
    for conf in CONFIGS:
        for b in BOARDS:
            r = json.loads((CAL / f"run_{conf}_{b}.json").read_text())
            vo = float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6]))
            ton0 = r["cfg"]["ton_ns"]
            out[f"{conf}_{b}"] = {"ton0_ns": ton0, "vo0": vo, "ton_ns": round(ton0 + (VO_TGT - vo) / SLOPE, 3)}
    return out


def main():
    tr = trims()
    (HERE / "trims.json").write_text(json.dumps(tr, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []
    for conf, runs in RUNS.items():
        l_ph, r_on = CONFIGS[conf]
        for b, row in runs:
            corner, ton = BOARDS[b][0], tr[f"{conf}_{b}"]["ton_ns"]
            name = f"{conf}_{corner}_{row}"
            cfg = gate_cfg(MC.row_cfg(row), conf, corner, ton, LEAD)
            note = (f"A168 {name}: {row}, {l_ph} pH, r_on {r_on} / r_off {R_OFF} ohm, corner {CORNERS[corner] or 'nominal'}, "
                    f"lead {LEAD} ns ramped over {RAMP_US} us, trimmed ton {ton} ns")
            (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=note), indent=1) + "\n")
            order.append(name)
    order.sort(key=lambda n: (0 if "_ss_" in n else 1 if "L07" in n else 2, n))     # slow corner runs longest
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", {k: t["ton_ns"] for k, t in tr.items()})


if __name__ == "__main__":
    cal() if sys.argv[1:] == ["cal"] else main()
