"""A183 analysis. Stage 1 (screen): per start-up run - Vo(143.5 us), the Cs ladder at mode P's entry (four phase
rails, max / min), mean mode-S valleys per phase (140 us .. entry), start-up peak (physical gate turn-off peaks before
mode P), handover peak (entry .. entry + 25 us), Vo minimum and largest loop Ton / cfg Ton in entry .. entry + 12 us,
V_DS, shoot-throughs / overlaps, status. Writes a183_screen.json.
  python3 a183_analyze.py screen"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def ladder(sec):
    vin, c = sec["vin_v"], sec["vcs_v"]
    return [vin - c[0], c[0] - c[1], c[1] - c[2], c[2]]


def start_stats(path):
    r = json.loads(Path(path).read_text())
    tp, lsb, S = r["t_mode_p_s"], r["lsb_s"], r["sections"]
    g = r["gate_offs_last"]
    pre = [q for q in S if q["t_s"] <= tp][-1]
    post = [q for q in S if tp < q["t_s"] < tp + 12e-6]
    rails = ladder(pre)
    lo = r["lowoffs_last"]
    valley = [float(np.mean([e["i_a"] for e in lo if e["phase"] == k and 140e-6 < e["t_s"] < tp])) for k in (1, 2, 3, 4)]
    ton_cfg = r["cfg"]["ton_ns"] * 1e-9 / lsb
    return {"t0_ns": r["cfg"]["t0_ns"], "ton_ns": r["cfg"]["ton_ns"], "status": r["status"],
            "vo_143_5": float(np.mean([q["vo"] for q in S if 143e-6 < q["t_s"] < 144e-6])),
            "rails_v": [round(x, 3) for x in rails], "rail_ratio": max(rails) / min(rails),
            "valley_a": [round(x, 1) for x in valley],
            "start_pk": max(e["i_max_a"] for e in g if e["t_s"] < tp),
            "hand_pk": max((e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6), default=None),
            "vo_min_hand": min(q["vo"] for q in post), "ton_max_hand": max(q["ton_lsb"] for q in post) / ton_cfg,
            "vds_max_v": max(r["vds_max_v"]), "shoot_on": int(sum(r.get("gate_stats", {}).get("shoot_on", [0]))),
            "overlaps": r.get("overlaps"), "late": r["late_fires"]}


def screen():
    out = {Path(f).stem[4:]: start_stats(f) for f in sorted(glob.glob(str(HERE / "cosim_screen" / "run_*.json")))}
    (HERE / "a183_screen.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, s in sorted(out.items(), key=lambda kv: (kv[1]["t0_ns"], kv[1]["ton_ns"])):
        print(f"{k:16s} Vo {s['vo_143_5']:.3f} rails {' '.join(f'{x:5.2f}' for x in s['rails_v'])} ({s['rail_ratio']:.2f}) "
              f"valley {' '.join(f'{x:6.1f}' for x in s['valley_a'])} | start {s['start_pk']:5.1f} hand {s['hand_pk'] or 0:5.1f} "
              f"Vo min {s['vo_min_hand']:.3f} Ton {s['ton_max_hand']:.2f}x | V {s['vds_max_v']:.1f} shoot {s['shoot_on']} {s['status']}")


if __name__ == "__main__":
    {"screen": screen}[sys.argv[1]]()
