"""A234 analysis (BOUNDARY Section 2): every module of every run - start-up / handover / post-event peaks, V_DS, overlaps,
shoot-through, late fires, phase-1 rail of each module in mode P before the event (C10's lock gate), Vo after the event
and at the end, a142_oracles.check's events from the event on; f1-f3 on arm b.
  python3 a234_analyze.py -> a234_summary.json"""
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
I_LIM, V_LIM, BAND, RAIL_LOCK = 200.0, 40.0, 0.01, 13.5


def one(f):
    r = json.loads(Path(f).read_text())
    mods = [r] + r.get("modules_rest", [])
    ev = r["cfg"].get("line_step") or r["cfg"].get("load_step")
    t0, tp = ev["t_us"] * 1e-6, r["t_mode_p_s"]
    hi = [e for m in mods for e in m["highoffs_last"]]
    pk = lambda a, b: max((e["i_a"] for e in hi if a <= e["t_s"] < b), default=None)
    sec = r["sections"]; ts = np.array([q["t_s"] for q in sec]); vo = np.array([q["vo"] for q in sec])
    rail = [max((q["vin_v"] - q["vcs_v"][0] for q in m["sections"] if q.get("mode_p") and q["t_s"] < t0), default=None) for m in mods]
    cls = {}
    for e in ORA.check(f)["events"]:
        if e["t_s"] >= t0:
            cls[e["cls"]] = cls.get(e["cls"], 0) + 1
    last = ts >= ts[-1] - 20e-6
    out = {"status": [m["status"] for m in mods], "n_mod": len(mods), "t_mode_p_us": tp * 1e6,
           "start_pk": pk(0.0, tp), "hand_pk": pk(tp, tp + 40e-6), "post_pk": pk(t0, 1.0), "peak_whole": pk(0.0, 1.0),
           "vds_v": max(max(m["vds_max_v"]) for m in mods), "overlaps": sum(m["overlaps"] for m in mods),
           "shoot_on": sum(sum(m["gate_stats"]["shoot_on"]) for m in mods), "late": int(sum(sum(m["late_fires"]) for m in mods)),
           "rail1_max_v": rail, "vo_ext_mv": 1e3 * float(max(vo[ts >= t0] - 1.0, key=abs)),
           "vo_end_v": [float(vo[last].min()), float(vo[last].max())], "oracle_after": cls}
    out["f1"] = bool(all(s == "COMPLETED" for s in out["status"]) and out["peak_whole"] <= I_LIM and out["vds_v"] <= V_LIM
                     and not out["overlaps"] and not out["shoot_on"] and all(abs(v - 1) <= BAND for v in out["vo_end_v"])
                     and not cls.get("NEW"))
    out["f3"] = bool(all(x is not None and x <= RAIL_LOCK for x in rail))
    return out


def main():
    res = {"runs": {f.stem[4:]: one(f) for f in sorted(COS.glob("run_*.json"))}}
    for n, v in res["runs"].items():
        if n.endswith("_b"):
            d = res["runs"].get(n[:-2] + "_d0")
            v["f2"] = bool(d and v["post_pk"] <= d["post_pk"] + 5.0 and abs(v["vo_ext_mv"]) <= abs(d["vo_ext_mv"]) + 2.0)
            v["criteria"] = {k: v[k] for k in ("f1", "f2", "f3")}
    b = [v for n, v in res["runs"].items() if n.endswith("_b")]
    res["criteria_main"] = {k: all(v[k] for v in b) for k in ("f1", "f2", "f3")}
    (HERE / "a234_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["runs"].items():
        print(f"{n:18s} start {v['start_pk']:.1f} hand {v['hand_pk']:.1f} post {v['post_pk']:.1f} A | V_DS {v['vds_v']:.1f} | late {v['late']} | "
              f"rail1 {[round(x, 2) for x in v['rail1_max_v']]} | Vo {v['vo_ext_mv']:+.1f} mV end {v['vo_end_v'][0]:.4f}..{v['vo_end_v'][1]:.4f} | "
              f"oracle {v['oracle_after']} | f1 {v['f1']} f3 {v['f3']}" + (f" f2 {v['f2']}" if "f2" in v else ""))
    print("main", res["criteria_main"])


if __name__ == "__main__":
    main()
