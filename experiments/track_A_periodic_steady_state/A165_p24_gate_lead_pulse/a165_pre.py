"""A165 pre-registration check (not judged): the handover with the lead as a pulse shift (bridge driver lead_mode
"pulse": signed dt_pred, pulse width kept) instead of A164's turn-on-only lead (pulse wider by the lead).
Runs to 190 us of l_p48_1us at A164's trimmed tons: nominal L0 and L x 0.7 (A164: 150.6 / 218.6 A), the slow corner at
3.6 ohm (A164's +-20 %) and at 4.55 ohm (+-30 %, A164 pre: 228 A with the turn-on-only lead).
  python3 a165_pre.py cfgs  -> cosim_pre/cfg_*.json;   python3 a165_pre.py  -> a165_pre.json"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PRE = HERE / "cosim_pre"
_s = importlib.util.spec_from_file_location("a164_make_cfgs", HERE.parent / "A164_p24_gate_drive_spread" / "make_cfgs.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)

# name: (row, corner, r_on base, ton ns)
RUNS = {"nom_L0": ("l_p48_1us", "nom", 3.0, 39.615), "nom_L07": ("L07_l_p48_1us", "nom", 3.0, 34.813),
        "ss_r36": ("l_p48_1us", "ss", 3.0, 48.348), "ss_r455": ("l_p48_1us", "ss30", 3.5, 52.0)}
A4.CORNERS["ss30"] = {"dk2": 1.0, "cg_scale": 1.29, "r_scale": 1.3}
A4.CORNERS["ss10"] = {"dk2": 1.0, "cg_scale": 1.29, "r_scale": 1.1}
# second batch (after A164's slow-corner rows: 65 late fires in the handover, ~160 after rising line steps):
# the slow corner at +-10 % (3.3 ohm, lead 8) and at 3.6 ohm with a 12 ns lead (t_drv 14 ns so the bridge can apply it)
RUNS2 = {"ss_r33": ("l_p48_1us", "ss10", 3.0, 46.9, 8.0, None), "ss_r36_lead12": ("l_p48_1us", "ss", 3.0, 48.348, 12.0, 14.0)}


def cfgs():
    PRE.mkdir(exist_ok=True)
    for name, (row, corner, r_on, ton) in RUNS.items():
        A4.R_ON = r_on
        c = A4.gate_cfg(A4.MC.row_cfg(row), corner, ton, A4.LEAD)
        c["driver"] = dict(c["driver"], lead_mode="pulse")
        (PRE / f"cfg_{name}.json").write_text(json.dumps(dict(c, t_end_us=190.0, out=f"run_{name}.json",
                                                              note=f"A165 pre: {name}, lead 8 ns as a pulse shift"),
                                                         indent=1) + "\n")


def cfgs2():
    for name, (row, corner, r_on, ton, lead, t_drv) in RUNS2.items():
        A4.R_ON = r_on
        c = A4.gate_cfg(A4.MC.row_cfg(row), corner, ton, lead)
        c["driver"] = dict(c["driver"], lead_mode="pulse")
        if t_drv:
            c["t_drv_ns"] = t_drv
        (PRE / f"cfg_{name}.json").write_text(json.dumps(dict(c, t_end_us=190.0, out=f"run_{name}.json",
                                                              note=f"A165 pre: {name}"), indent=1) + "\n")


def main():
    out = {}
    for name in list(RUNS) + list(RUNS2):
        p = PRE / f"run_{name}.json"
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        go = r["gate_offs_last"]
        pk = lambda a, b: max(e["i_max_a"] for e in go if a * 1e-6 <= e["t_s"] < b * 1e-6)
        out[name] = st = {"vo_143_5": float(np.mean([q["vo"] for q in r["sections"] if 143e-6 < q["t_s"] < 144e-6])),
                          "mode_s_pk": pk(0, 143.5), "hand_pk": pk(143.5, 150), "after_pk": pk(150, 190),
                          "late": r["late_fires"], "dt_pred_ns": r["dt_pred_final_ns"], "overlaps": r["overlaps"],
                          "vds_max": max(max(q["vds_win_v"]) for q in r["sections"] if "vds_win_v" in q)}
        print(f"{name:8s} Vo {st['vo_143_5']:.3f} mode S {st['mode_s_pk']:5.1f} handover {st['hand_pk']:5.1f} after "
              f"{st['after_pk']:5.1f} V {st['vds_max']:4.1f} late {st['late']} dtp {[round(x, 1) for x in st['dt_pred_ns']]} "
              f"ovl {st['overlaps']}")
    (HERE / "a165_pre.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    cfgs() if sys.argv[1:] == ["cfgs"] else cfgs2() if sys.argv[1:] == ["cfgs2"] else main()
