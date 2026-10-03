"""A124 analysis against BOUNDARY Section 3 (A115's row statistics with L = 2.933 nH; step_stats at 800 us; the peak
after the step from the high-side turn-off records; phase 1's turn-off currents). Writes a124_summary.json."""
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
A115.L1 = 7.3333333e-9 / 2.5                       # D62's inductor copper at this L
T_STEP = 800e-6
FLAG = {"p125_l_p48_5us", "p125_l_p48_1us"}


def load(p):
    return json.loads(Path(p).read_text())


def main():
    pr = load(HERE / "a124_predictions.json")
    res = {}
    for key, pct in (("p10", 10.0), ("p125", 12.5), ("p15", 15.0)):
        p = HERE / "cosim" / f"run_{key}_n0.json"
        if not p.exists():
            continue
        d = load(p); x = A115.row(d); q = pr["rows"][key]
        v1, v4 = q["hs_on_vds_v_phase1"], q["hs_on_vds_v_phase4"]
        c = {"no_overlap": x["overlaps"] == 0, "startup_200a": d["ipk_a"] <= 200.0, "ls_zvs": max(x["ls_on_vds_max_v"]) <= 0.0,
             "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3, "late_5": sum(x["late_fires"]) <= 5,
             "hs_d57": all(abs(a - v1) <= 0.6 for a in x["hs_on_vds_v"][:3]) and abs(x["hs_on_vds_v"][3] - v4) <= 1.0,
             "period_2pct": abs(x["period_ns"] / q["period_ns"] - 1) <= 0.02, "ton_5pct": abs(x["ton_ns"] / q["ton_ns"] - 1) <= 0.05,
             "peak_5A": all(abs(a - q["peak_a"]) <= 5.0 for a in x["peaks_a"]),
             "efficiency_0p7": abs(x["efficiency_pct"] - q["efficiency_pct"]["middle"]) <= 0.7}
        x["criteria"] = c; x["startup_ipk_a"] = d["ipk_a"]
        res[f"{key}_n0"] = x
        print(f"{key}_n0: HS " + "/".join(f"{a:+.2f}" for a in x["hs_on_vds_v"]) + f" V (D57 {v1:+.2f}/{v4:+.2f}), Ton {x['ton_ns']:.2f} (pred {q['ton_ns']:.2f}), "
              f"T {x['period_ns']:.1f} (pred {q['period_ns']:.1f}), peaks " + "/".join(f"{a:.0f}" for a in x["peaks_a"]) + f" (pred {q['peak_a']:.0f}), "
              f"efficiency {x['efficiency_pct']:.2f}% (pred {q['efficiency_pct']['middle']:.2f}), ideal {x['efficiency_ideal_inductor_pct']:.2f}%, "
              f"start-up {d['ipk_a']:.0f} A, sd " + "/".join(f"{a:.2f}" for a in x["off_sd_a"]) + "; " + ", ".join(f"{k} {'ok' if b else 'MISS'}" for k, b in c.items()))
    for name, m in pr["d63"].items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        st = step_stats(d, t_step=T_STEP)
        pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= T_STEP)
        ph1 = [q["i_a"] for q in d["lowoffs_last"] if q["phase"] == 1 and q["t_s"] >= T_STEP]
        late = sum(d["late_fires"]); back = st["back_within_1pct_us"]
        c = {"no_overlap": d["overlaps"] == 0, "no_runaway": late <= 100 and pk <= 400.0}
        if name.startswith("p") and "_1us" not in name:
            c.update(floor_holds=min(ph1) >= -18.6, peak_200a=pk <= 200.0, back_100us=back <= 100.0)
            if name not in FLAG:
                c["peak_10pct_d63"] = abs(pk / m["peak_max_a"] - 1) <= 0.10
        if name.startswith("t"):
            c["recovers_100us"] = back <= 100.0
        res[name] = {"peak_after_a": pk, "step": st, "ph1_min_a": min(ph1), "late": late, "d63": m, "criteria": c}
        print(f"{name:16s}: peak after {pk:5.0f} A (D63 {m['peak_max_a']:.0f}), Vo {st['extreme_mv']:+8.2f} mV (D63 {m['extreme_mv']:+.1f}), back "
              f"{back:7.2f} us, phase 1 min {min(ph1):+.1f} A, late {late}; " + ", ".join(f"{k} {'ok' if b else 'MISS'}" for k, b in c.items()))
    (HERE / "a124_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a124_summary.json")


if __name__ == "__main__":
    main()
