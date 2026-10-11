"""A194 analysis (BOUNDARY Section 2). Per draw: c1 COMPLETED / 0 shoot-throughs / 0 overlaps; c2 physical peak
<= 200 A over the whole run (start-up, handover = entry .. + 25 us, after the event); c3 V_DS <= 40 V; c4 Vo within
1 V +- 50 mV from 20 us after the handover; c5 Vo back inside 1 % at most 60 us after the event ends and inside
from there on. Diagnostics from the A179 / A174 chain: late fires before / after the event, oracle NEW events,
interlock holds. Writes a194_summary.json.
  python3 a194_analyze.py [run_*.json ...]"""
from __future__ import annotations

import glob
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a179", TA / "A179_p24_interlock_release_threshold" / "a179_analyze.py")
A179 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A179)
I_LIM, V_LIM, VO_BAND, PCT, T_BACK_US = 200.0, 40.0, 0.050, 0.010, 60.0


def run(path):
    r = json.loads(Path(path).read_text())
    cfg = r["cfg"]
    ev = cfg.get("line_step") or cfg["load_step"]
    t0 = ev["t_us"] * 1e-6
    t1 = t0 + ev.get("slew_us", 0.0) * 1e-6                       # the event ends
    tp, g = r["t_mode_p_s"], r["gate_offs_last"]
    pk = lambda a, b: max((e["i_max_a"] for e in g if a <= e["t_s"] < b), default=0.0)
    st = A179.stats(path)
    sec = [(q["t_s"], q["vo"]) for q in r["sections"]]
    band = [abs(v - 1.0) for t, v in sec if t >= tp + 20e-6]
    out_1pct = [t for t, v in sec if t >= t1 and abs(v - 1.0) > PCT]
    back_us = (max(out_1pct) - t1) * 1e6 if out_1pct else 0.0
    post = [v - 1.0 for t, v in sec if t >= t0]
    out = {"status": r["status"], "shoot_on": st.get("shoot_on"), "overlaps": st.get("overlaps"),
           "start_pk": pk(0.0, tp), "hand_pk": pk(tp, tp + 25e-6), "pre_pk": pk(tp + 25e-6, t0), "post_pk": pk(t0, 1.0),
           "vds_whole": st.get("vds_whole"), "vo_dev_max_mv": 1e3 * max(band), "back_1pct_us": back_us,
           "vo_post_min_mv": 1e3 * min(post), "vo_post_max_mv": 1e3 * max(post),
           "late_pre": st.get("late_pre"), "late_post": st.get("late_post"), "oracle_new": st.get("oracle_new"),
           "il_holds": st.get("il_holds"), "t_mode_p_us": tp * 1e6}
    whole = max(out["start_pk"], out["hand_pk"], out["pre_pk"], out["post_pk"])
    out["criteria"] = {"c1": r["status"] == "COMPLETED" and not out["shoot_on"] and not out["overlaps"],
                       "c2": whole <= I_LIM, "c3": out["vds_whole"] is not None and out["vds_whole"] <= V_LIM,
                       "c4": out["vo_dev_max_mv"] <= 1e3 * VO_BAND, "c5": back_us <= T_BACK_US}
    return Path(path).stem[4:], out


def main():
    files = sys.argv[1:] or sorted(glob.glob(str(HERE / "cosim" / "run_*.json")))
    res = dict(run(f) for f in files)
    if not sys.argv[1:]:
        (HERE / "a194_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    miss = {k: [c for c, ok in s["criteria"].items() if not ok] for k, s in res.items()}
    for k, s in res.items():
        print(f"{k:24s} start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} pre {s['pre_pk']:5.1f} post {s['post_pk']:5.1f} A  V {s['vds_whole']:.1f}  "
              f"Vo {s['vo_post_min_mv']:+.1f}/{s['vo_post_max_mv']:+.1f} mV back {s['back_1pct_us']:.1f} us  late {s['late_pre']}/{s['late_post']} "
              f"NEW {s['oracle_new']} holds {s['il_holds']}  {'PASS' if not miss[k] else 'MISS ' + ','.join(miss[k])}")
    print(len(res), "draws;", sum(1 for m in miss.values() if not m), "pass all;",
          {c: sum(1 for m in miss.values() if c in m) for c in ("c1", "c2", "c3", "c4", "c5")})


if __name__ == "__main__":
    main()
