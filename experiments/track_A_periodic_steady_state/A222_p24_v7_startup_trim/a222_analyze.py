"""A222 analysis (BOUNDARY Section 2): k1 on the N0 row (A221's check, a221_analyze.check_row against A215's V6 record),
and for the start-up rows A206's whole-run numbers (a206_analyze.whole) against A215's V6 record of the same board:
Vo half a microsecond before mode P's entry, Vo's maximum before 200 us, the start-up and handover peaks.
  python3 a222_analyze.py -> a222_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A21 = _load("a221_analyze", "A221_p24_core_loss_and_pause/a221_analyze.py")
A6 = A21.A15.A6
COS = HERE / "cosim"
TOL_V, T_CUT = 2e-3, 200e-6
REF = {"s_N75_25": "m16_B_N75_25_p4_ls0p3", "s_S75_25": "m16_B_S75_25_p4_ls0p3"}


def startup(path):
    r = json.loads(Path(path).read_text())
    sec = r["sections"]
    t = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec]); mp = np.array([q.get("mode_p", 0) for q in sec])
    tp = float(t[np.argmax(mp > 0)])
    w = A6.whole(path)
    return {"t_mode_p_us": tp * 1e6, "vo_before_hand_v": float(vo[np.searchsorted(t, tp - 0.5e-6)]),
            "vo_max_v": float(vo[t < T_CUT].max()), "start_pk": w["start_pk"], "hand_pk": w["hand_pk"],
            "vds_whole": w["vds_whole"], "ton_s_ns": r["cfg"].get("ton_s_ns"), "c6": w["criteria"]["c6"]}


def main():
    res = {"check": {}, "startup": {}}
    f = COS / "run_k_n_s_p62.json"
    if f.exists():
        res["check"]["k_n_s_p62"] = A21.check_row(f, "k_n_s_p62")
    for name, src in REF.items():
        f = COS / f"run_{name}.json"
        if not f.exists():
            continue
        v7, v6 = startup(f), startup(TA / "A215_p24_buildable_ton_path" / "cosim" / f"run_{src}.json")
        d_hand, d_max = v7["vo_before_hand_v"] - v6["vo_before_hand_v"], v7["vo_max_v"] - v6["vo_max_v"]
        res["startup"][name] = {"v7": v7, "v6": v6, "d_vo_before_hand_mv": 1e3 * d_hand, "d_vo_max_mv": 1e3 * d_max,
                                "criteria": {"t1": bool(v7["c6"] and abs(d_hand) <= TOL_V and abs(d_max) <= TOL_V)}}
    (HERE / "a222_summary.json").write_text(json.dumps(A21.A16.clean(res), indent=1) + "\n")
    for n, v in res["check"].items():
        print(f"{n:12s} post {v['v7']['post_pk']:.2f} (V6 {v['v6']['post_pk']:.2f}) Vo<=300us {v['d_vo_300us_mv']:+.2f} mV "
              f"| {v['v7']['criteria']} {v['criteria']}")
    for n, v in res["startup"].items():
        print(f"{n:12s} mode P {v['v7']['t_mode_p_us']:.1f} us (V6 {v['v6']['t_mode_p_us']:.1f}) | Vo before {v['d_vo_before_hand_mv']:+.2f} mV, "
              f"max {v['d_vo_max_mv']:+.2f} mV | start {v['v7']['start_pk']:.1f} (V6 {v['v6']['start_pk']:.1f}) hand {v['v7']['hand_pk']:.1f} "
              f"(V6 {v['v6']['hand_pk']:.1f}) | {v['criteria']}")


if __name__ == "__main__":
    main()
