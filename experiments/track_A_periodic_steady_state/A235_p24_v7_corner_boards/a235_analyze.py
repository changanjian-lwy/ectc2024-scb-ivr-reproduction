"""A235 analysis (BOUNDARY Section 2).
  python3 a235_analyze.py 1   -> a235_trims.json (stage 1: Vo(143.5 us) and the trim rule)
  python3 a235_analyze.py [2] -> a235_summary.json (stage 2: c1 per run, c2 per 25 C start-up; the default)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
_s = importlib.util.spec_from_file_location("a142_oracles", TA / "A142_p24_random_stimulus" / "a142_oracles.py")
ORA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ORA)
_m = importlib.util.spec_from_file_location("a235_make_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(_m)
_m.loader.exec_module(MC)
TARGET, T_REF, LSB_NS = 1.035, 143.5e-6, 0.03125
SLOPE = {"F0": 0.0535, "N13": 0.0535, "S0": 0.0545}             # V/ns, A206
I_LIM, V_LIM, BAND = 200.0, 40.0, 0.01


def vo_at(r, t):
    sec = r["sections"]
    return float(np.interp(t, [q["t_s"] for q in sec], [q["vo"] for q in sec]))


def stage1():
    out = {"vo_1435_v": {}, "dton_s1_ns": dict(MC.DTON1), "steps": {}, "dton_ns": {}}
    for b in MC.BOARDS:
        r = json.loads((COS / f"run_t_{b}.json").read_text())
        v = vo_at(r, T_REF)
        k = int(round((TARGET - v) / SLOPE[b] / LSB_NS))
        out["vo_1435_v"][b], out["steps"][b] = v, k
        out["dton_ns"][b] = round(MC.DTON1[b] + k * LSB_NS, 5)
        out.setdefault("t_mode_p_us", {})[b] = r["t_mode_p_s"] * 1e6
        out.setdefault("vo_max_v", {})[b] = max(q["vo"] for q in r["sections"])
    (HERE / "a235_trims.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def one(f):
    r = json.loads(Path(f).read_text())
    ev = r["cfg"].get("line_step") or r["cfg"].get("load_step")
    t0 = ev["t_us"] * 1e-6 if ev else None
    sec = r["sections"]; ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    g = r["gate_offs_last"]
    m = {"status": r["status"], "t_mode_p_us": r["t_mode_p_s"] * 1e6, "vo_1435_v": vo_at(r, T_REF),
         "start_pk": max((e["i_max_a"] for e in g if e["t_s"] < r["t_mode_p_s"]), default=None),
         "hand_pk": max((e["i_max_a"] for e in g if r["t_mode_p_s"] <= e["t_s"] < r["t_mode_p_s"] + 40e-6), default=None),
         "peak_whole": max(e["i_max_a"] for e in g), "vds_v": max(r["vds_max_v"]), "overlaps": r["overlaps"],
         "shoot_on": sum(r["gate_stats"]["shoot_on"]), "vo_max_300_v": float(vo[ts <= 300e-6].max()),
         "vo_end_v": [float(vo[ts >= ts[-1] - 20e-6].min()), float(vo[ts >= ts[-1] - 20e-6].max())]}
    if t0 is not None:
        m["post_pk"] = max(e["i_max_a"] for e in g if e["t_s"] >= t0)
        m["vo_ext_mv"] = 1e3 * float(max(vo[ts >= t0] - 1.0, key=abs))
        cls = {}
        for e in ORA.check(f)["events"]:
            if e["t_s"] >= t0:
                cls[e["cls"]] = cls.get(e["cls"], 0) + 1
        m["oracle_after"] = cls
    m["c1"] = bool(m["status"] == "COMPLETED" and m["peak_whole"] <= I_LIM and m["vds_v"] <= V_LIM and not m["overlaps"]
                   and not m["shoot_on"] and m["vo_max_300_v"] <= 1.05 and all(abs(v - 1) <= BAND for v in m["vo_end_v"])
                   and not m.get("oracle_after", {}).get("NEW"))
    if "S0h" not in Path(f).stem:
        m["c2"] = bool(abs(m["vo_1435_v"] - TARGET) <= 0.002)
    m["criteria"] = {k: m[k] for k in ("c1", "c2") if k in m}
    return m


def stage2():
    res = {"trims": json.loads((HERE / "a235_trims.json").read_text()), "runs": {}}
    for f in sorted(COS.glob("run_r_*.json")):
        res["runs"][f.stem[4:]] = one(f)
    res["criteria_main"] = {k: all(v["criteria"][k] for v in res["runs"].values() if k in v["criteria"]) for k in ("c1", "c2")}
    (HERE / "a235_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["runs"].items():
        print(f"{n:14s} Vo(143.5) {v['vo_1435_v']:.4f} max300 {v['vo_max_300_v']:.4f} | start {v['start_pk']:.1f} hand {v['hand_pk']:.1f} "
              f"post {v.get('post_pk', float('nan')):.1f} A | V_DS {v['vds_v']:.1f} | Vo {v.get('vo_ext_mv', float('nan')):+.1f} mV | "
              f"oracle {v.get('oracle_after')} | {v['criteria']}")
    print("main", res["criteria_main"])


if __name__ == "__main__":
    stage1() if sys.argv[1:] == ["1"] else stage2()
