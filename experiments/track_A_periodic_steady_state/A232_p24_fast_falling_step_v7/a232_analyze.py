"""A232 analysis (BOUNDARY Section 2): per run the post-step peak, V_DS, overlaps / shoot-through, Vo after the step and
over the last 20 us, and a142_oracles.check's events from the step on, by class; z1 / z2 on arm b.
  python3 a232_analyze.py -> a232_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a142_oracles", TA / "A142_p24_random_stimulus" / "a142_oracles.py")
ORA = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ORA)
COS = HERE / "cosim"
I_LIM, V_LIM, BAND = 200.0, 40.0, 0.01


def one(f):
    r = json.loads(Path(f).read_text())
    t = r["cfg"]["line_step"]["t_us"] * 1e-6
    sec = r["sections"]
    ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    g = max((e for e in r["gate_offs_last"] if e["t_s"] >= t), key=lambda e: e["i_max_a"])
    cls = {}
    for e in ORA.check(f)["events"]:
        if e["t_s"] >= t:
            cls[e["cls"]] = cls.get(e["cls"], 0) + 1
    last = ts >= ts[-1] - 20e-6
    m = {"status": r["status"], "post_pk": g["i_max_a"], "post_pk_phase": g["phase"], "post_pk_dt_us": (g["t_s"] - t) * 1e6,
         "peak_whole": max(e["i_max_a"] for e in r["gate_offs_last"]), "vds_v": max(r["vds_max_v"]), "overlaps": r["overlaps"],
         "shoot_on": sum(r["gate_stats"]["shoot_on"]), "vo_after_mv": [1e3 * (float(vo[ts >= t].min()) - 1), 1e3 * (float(vo[ts >= t].max()) - 1)],
         "vo_end_v": [float(vo[last].min()), float(vo[last].max())], "oracle_after": cls,
         "late_after": int(sum(sec[-1]["late"]) - sum(sec[int(np.searchsorted(ts, t)) - 1]["late"]))}
    m["z2"] = bool(m["status"] == "COMPLETED" and m["peak_whole"] <= I_LIM and m["vds_v"] <= V_LIM and not m["overlaps"]
                   and not m["shoot_on"] and all(abs(v - 1) <= BAND for v in m["vo_end_v"]))
    m["z1"] = bool(m["oracle_after"].get("K3", 0) == 0 and m["oracle_after"].get("NEW", 0) == 0)
    return m


def main():
    res = {"runs": {}}
    for f in sorted(COS.glob("run_*.json")):
        res["runs"][f.stem[4:]] = one(f)
    b = {n: v for n, v in res["runs"].items() if n.endswith("_b")}
    for n, v in res["runs"].items():
        v["criteria"] = {k: v[k] for k in ("z1", "z2")} if n.endswith("_b") else {}
    res["criteria_main"] = {"z1": all(v["z1"] for v in b.values()), "z2": all(v["z2"] for v in b.values())}
    (HERE / "a232_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["runs"].items():
        print(f"{n:14s} post {v['post_pk']:6.1f} A (ph {v['post_pk_phase']}, +{v['post_pk_dt_us']:.1f} us) | Vo {v['vo_after_mv'][0]:+.1f}/"
              f"{v['vo_after_mv'][1]:+.1f} mV | V_DS {v['vds_v']:.1f} | late {v['late_after']} | oracle {v['oracle_after']} | z1 {v['z1']} z2 {v['z2']}")
    print("main", res["criteria_main"])


if __name__ == "__main__":
    main()
