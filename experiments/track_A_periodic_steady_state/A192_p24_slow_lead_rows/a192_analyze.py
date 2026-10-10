"""A192 analysis (BOUNDARY Section 2). Per run: c1 start-up (before mode P) and handover (entry .. + 25 us) <= 200 A on
every module; c2 post-step <= 200 A, c3 V_DS <= 40 V + COMPLETED + 0 shoot-throughs / overlaps (a179_analyze.stats);
c7 Vo <= 1.05 V over 0-300 us; c10 on -8 V / 10 us: post-step late fires <= 36.5 (A179's limit). Diagnostics against
A179's t_il 1.0 ns runs at the same row and position (lead 8 ns, 400 ns start-up): late fires, NEW events, Vo extreme
and recovery. Writes a192_summary.json.
  python3 a192_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a179", TA / "A179_p24_interlock_release_threshold" / "a179_analyze.py")
A179 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A179)
REF = {"S0_25_m80_10us": "ss_l_m80_10us", "S0_25_s_p62": "ss_s_p62", "M4ss_25_p48_1us": "m4_ss_l_p48_1us"}
DIAG = ("peak_post", "late_post", "oracle_new", "extreme_mv", "back_within_1pct_us")


def mods(r):
    return [r] + list(r.get("modules_rest") or [])


def run(path):
    r = json.loads(Path(path).read_text())
    stem = Path(path).stem[4:]
    st = A179.stats(path)
    sp, ep = [], []
    for m in mods(r):
        tp, g = m["t_mode_p_s"], m["gate_offs_last"]
        sp.append(max(e["i_max_a"] for e in g if e["t_s"] < tp))
        ep.append(max(e["i_max_a"] for e in g if tp <= e["t_s"] < tp + 25e-6))
    vmax = max(max(q["vo"] for q in m["sections"] if q["t_s"] < 300e-6) for m in mods(r))
    out = {"start_pk": max(sp), "hand_pk": max(ep), "vo_max_300us": vmax, **{k: st.get(k) for k in DIAG},
           "vds_whole": st.get("vds_whole"), "shoot_on": st.get("shoot_on"), "status": r["status"]}
    base, k = stem.rsplit("_p", 1)
    ref = REF.get(base)
    if ref:
        f = TA / "A179_p24_interlock_release_threshold" / "cosim" / f"run_t10_p{k}_{ref}.json"
        if f.exists():
            rs = A179.stats(str(f))
            out["a179_lead8"] = {x: rs.get(x) for x in DIAG}
    out["criteria"] = {"c1": out["start_pk"] <= 200.0 and out["hand_pk"] <= 200.0, "c2": st["peak_post"] <= 200.0,
                       "c3": bool(A179.ok({**st, "peak_post": 0.0})), "c7": vmax <= 1.05}
    if "m80_10us" in stem:
        out["criteria"]["c10"] = st["late_post"] <= 36.5
    return stem, out


def main():
    res = dict(run(f) for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))))
    (HERE / "a192_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        ref = s.get("a179_lead8")
        print(f"{k:22s} start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} post {s['peak_post']:5.1f} V {s['vds_whole']:.1f} "
              f"late_post {s['late_post']} NEW {s['oracle_new']} ext {s['extreme_mv']:+.1f} mV back {s['back_within_1pct_us']}"
              + (f" | lead 8: post {ref['peak_post']:.1f} late {ref['late_post']} NEW {ref['oracle_new']} ext {ref['extreme_mv']:+.1f}" if ref else "")
              + f" {s['criteria']}")


if __name__ == "__main__":
    main()
