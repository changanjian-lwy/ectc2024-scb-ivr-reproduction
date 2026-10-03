"""A118 analysis against BOUNDARY Section 2: per step row the peak after the step (high-side turn-off records after
2000 us), step_stats, phase 1's low-side turn-off currents after the step (the floor), the late fires; f6_n0 against
A115 n10 (A115's row statistics) and its start-up peak. Writes a118_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_analyze", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_analyze.py")
A115 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A115)
T_STEP = 2000e-6
WEAK = {"f6_l_p48_1us", "f6_l_p48_5us", "f6_l_p48_20us", "f15_l_p48_5us"}
HARD = {"f6_s_m62", "f6_s_p62", "f6_l_m48_5us", "f6_l_p48_5us", "f6_l_m48_20us", "f6_l_p48_20us"}


def load(p):
    return json.loads(Path(p).read_text())


def main():
    pred = load(HERE / "a118_predictions.json")
    res = {}
    for name, pr in pred.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        st = step_stats(d, t_step=T_STEP)
        pk = max(x["i_a"] for x in d["highoffs_last"] if x["t_s"] >= T_STEP)
        ph1 = [x["i_a"] for x in d["lowoffs_last"] if x["phase"] == 1 and x["t_s"] >= T_STEP]
        late = sum(d["late_fires"])
        back = st["back_within_1pct_us"]
        m = pr["model"]
        c = {"no_overlap": d["overlaps"] == 0}
        if name.startswith("f"):
            c["floor_holds_m15p5A"] = min(ph1) >= -15.5
        if name in ("f15_s_m62", "f6_s_m62"):
            c["extreme_27p2_8mV"] = abs(st["extreme_mv"] - 27.2) <= 8.0
            c["back_30us"] = back <= 30.0
        if name not in WEAK and not name.startswith("t"):
            c["peak_10pct_d63"] = abs(pk / m["peak_max_a"] - 1) <= 0.10
        if name in HARD:
            c["peak_200a"] = pk <= 200.0
            c["back_100us"] = back <= 100.0
            c["no_runaway"] = late <= 100 and pk <= 400.0
        if name == "t6_s_m62":
            c["no_floor_below_m20A"] = min(ph1) < -20.0
        res[name] = {"peak_after_a": pk, "step": st, "ph1_lowoff_min_a": min(ph1), "ph1_lowoff_max_a": max(ph1), "late_fires": late,
                     "ipk_a": d["ipk_a"], "d63": {"peak_a": m["peak_max_a"], "extreme_mv": m["extreme_mv"], "back_us": m["back_us"],
                                                  "outcome": pr["outcome"]}, "weak": name in WEAK, "criteria": c}
        print(f"{name:16s}: peak after {pk:5.0f} A (D63 {m['peak_max_a']:.0f}{', weak' if name in WEAK else ''}), Vo {st['extreme_mv']:+8.2f} mV "
              f"(D63 {m['extreme_mv']:+.1f}), back {back:7.2f} us (D63 {m['back_us']:.1f}), phase 1 turn-off [{min(ph1):+.1f}, {max(ph1):+.1f}] A, "
              f"late {late}; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    p = HERE / "cosim" / "run_f6_n0.json"
    if p.exists():
        d = load(p)
        x, r = A115.row(d), A115.row(load(HERE.parent / "A115_p24_one_mhz_design_point" / "cosim" / "run_n10.json"))
        c = {"no_overlap": x["overlaps"] == 0, "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3, "sd_0p02A": max(x["off_sd_a"]) <= 0.02,
             "efficiency_0p1": abs(x["efficiency_pct"] - r["efficiency_pct"]) <= 0.1, "startup_200a": d["ipk_a"] <= 200.0}
        x["criteria"] = c; x["hs_shift_v"] = [a - b for a, b in zip(x["hs_on_vds_v"], r["hs_on_vds_v"])]
        x["async_fires"] = d.get("async_fires"); x["trim_final"] = d.get("trim_final")
        res["f6_n0"] = x
        print(f"f6_n0: HS on " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + " V (shift " + "/".join(f"{a:+.2f}" for a in x["hs_shift_v"])
              + f"), valleys " + "/".join(f"{a:+.2f}" for a in x["valleys_a"]) + ", sd " + "/".join(f"{a:.2f}" for a in x["off_sd_a"])
              + f", efficiency {x['efficiency_pct']:.2f}% (A115 {r['efficiency_pct']:.2f}), start-up ipk {d['ipk_a']:.0f} A, Vo {x['vo_mean_v']:.5f}, "
              f"trim {d.get('trim_final')}, front-end fires {d.get('async_fires')}; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a118_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a118_summary.json")


if __name__ == "__main__":
    main()
