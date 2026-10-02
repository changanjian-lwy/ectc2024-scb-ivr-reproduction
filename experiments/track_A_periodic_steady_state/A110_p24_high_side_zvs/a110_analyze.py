"""A110 analysis against BOUNDARY Section 3. Per n row (and C02's 5% reference), over the last 200 periods: each
phase's high-side turn-on V_DS, valley, peak and low-side turn-on V_DS maximum; Ton and the period; the D62 middle-case
loss budget on the run's measured waveforms (scb_ivr.p24_loss_budget.measure / budget), its reverse conduction
included. At 30%: the load steps and jitter against C02's. Writes a110_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402
from scb_ivr.p24_loss_budget import budget, measure  # noqa: E402

spec = importlib.util.spec_from_file_location("d62_script", PROJECT / "scripts" / "p24_loss_budget.py")
D62 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D62)
MIDDLE = D62.SCENARIOS["middle"]
LF = 1.4666667e-9
C02 = PROJECT / "experiments" / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
PRED = {   # pct: (HS-on V_DS, Ton ns, period ns, peak A, efficiency %), BOUNDARY Section 3
    5: (8.96, 18.33, 233.7, 131.25, 88.16), 10: (7.02, 20.00, 253.7, 137.5, 89.28), 15: (4.98, 21.67, 273.7, 143.75, 89.97),
    20: (2.89, 23.33, 293.7, 150.0, 90.26), 25: (0.74, 25.00, 313.7, 156.25, 90.21), 30: (0.0, 26.67, 333.7, 162.5, 89.91)}
LSB = 4e-9 / 128


def load(p):
    return json.loads(Path(p).read_text())


def row(d, t1=None):
    w = window_stats(d, t1=t1)
    m = measure(d, t1=t1)
    b = budget(m["phases"], m["ton_s"], m["period_s"], LF, MIDDLE, m["rails_v"], m["dv_next_v"], p_rev=m["p_rev_w"],
               p_out=m["p_out_w"])
    return {"hs_on_vds_v": [p["hs_on_vds_v"] for p in w["phases"]], "valleys_a": [p["i_off_mean_a"] for p in w["phases"]],
            "peaks_a": [p["peak"] for p in m["phases"]], "ls_on_vds_max_v": [p["ls_on_vds_max_v"] for p in w["phases"]],
            "off_sd_a": [p["i_off_sd_a"] for p in w["phases"]], "ton_ns": m["ton_s"] * 1e9, "period_ns": m["period_s"] * 1e9,
            "vo_mean_v": w["vo_mean_v"], "overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "late_fires": d["late_fires"],
            "budget_w": b, "efficiency_pct": b["efficiency"] * 100, "p_rev_w": m["p_rev_w"]}


def main():
    res = {}
    rows = [(5, C02 / "run_s1_n0.json")] + [(p, HERE / "cosim" / f"run_n{p}.json") for p in (10, 15, 20, 25, 30)]
    for pct, path in rows:
        if not path.exists():
            continue
        x = row(load(path))
        hs, ton, per, pk, eff = PRED[pct]
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0, "ls_zvs": max(x["ls_on_vds_max_v"]) <= 0.0,
             "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3,
             "ton_4pct": abs(x["ton_ns"] / ton - 1) <= 0.04, "period_4pct": abs(x["period_ns"] / per - 1) <= 0.04,
             "peak_5A": all(abs(v - pk) <= 5.0 for v in x["peaks_a"]),
             "efficiency_0p7": abs(x["efficiency_pct"] - eff) <= 0.7}
        if pct == 30:
            c["hs_zvs_0p3V"] = max(x["hs_on_vds_v"]) <= 0.3
        elif pct > 5:
            c["hs_d57_0p6V"] = all(abs(v - hs) <= 0.6 for v in x["hs_on_vds_v"])
        x["criteria"] = c
        res[f"n{pct}"] = x
        b = x["budget_w"]
        print(f"{pct:2d}%: HS on " + "/".join(f"{v:5.2f}" for v in x["hs_on_vds_v"]) + f" V (D57 {hs:.2f}), valleys "
              + "/".join(f"{v:+.1f}" for v in x["valleys_a"]) + ", peaks " + "/".join(f"{v:.0f}" for v in x["peaks_a"])
              + f" A, Ton {x['ton_ns']:.2f} ns, T {x['period_ns']:.1f} ns, ipk {x['ipk_a']:.0f} A, LS max {max(x['ls_on_vds_max_v']):+.2f} V, "
              f"Vo {x['vo_mean_v']:.5f}")
        print("     loss " + ", ".join(f"{k} {v:.2f}" for k, v in b.items() if k not in ("total", "efficiency"))
              + f" | total {b['total']:.2f} W, efficiency {x['efficiency_pct']:.2f}% (pred {eff:.2f}%)")
        if pct > 5:
            print("     criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    effs = {k: v["efficiency_pct"] for k, v in res.items()}
    if len(effs) == 6:
        best = max(effs, key=effs.get)
        res["criteria_efficiency"] = {"max_at_15_25": best in ("n15", "n20", "n25"),
                                      "n30_above_n5_by_1": effs["n30"] - effs["n5"] >= 1.0}
        print(f"efficiency maximum at {best}; 30% - 5% = {effs['n30'] - effs['n5']:+.2f} points; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in res["criteria_efficiency"].items()))
    for name, ref in (("n30_s_p62", "s1_s_p62"), ("n30_s_m62", "s1_s_m62")):
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d, r = load(p), load(C02 / f"run_{ref}.json")
        s, rs = step_stats(d), step_stats(r)
        x = {"step": s, "ref_step": rs, "overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "late_fires": d["late_fires"]}
        x["criteria"] = {"no_overlap": d["overlaps"] == 0, "peak_200a": d["ipk_a"] <= 200.0,
                         "step_25pct": abs(s["extreme_mv"] / rs["extreme_mv"] - 1) <= 0.25}
        res[name] = x
        print(f"{name}: step {s['extreme_mv']:+.2f} mV, back {s['back_within_1pct_us']:.2f} us (5%: {rs['extreme_mv']:+.2f} / "
              f"{rs['back_within_1pct_us']:.2f}); ipk {d['ipk_a']:.0f} A, overlaps {d['overlaps']}; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in x["criteria"].items()))
    p = HERE / "cosim" / "run_n30_j30.json"
    if p.exists():
        x, r = row(load(p)), row(load(C02 / "run_s1_j30.json"))
        x["criteria"] = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0,
                         "sd_band": all(abs(a / b - 1) <= 0.5 for a, b in zip(x["off_sd_a"], r["off_sd_a"])),
                         "hs_zvs_0p5V": max(x["hs_on_vds_v"]) <= 0.5}
        res["n30_j30"] = x
        print(f"n30_j30: HS on " + "/".join(f"{v:.2f}" for v in x["hs_on_vds_v"]) + " V, sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"])
              + " (5% j30 " + "/".join(f"{v:.2f}" for v in r["off_sd_a"]) + f"), efficiency {x['efficiency_pct']:.2f}%; "
              + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in x["criteria"].items()))
    (HERE / "a110_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a110_summary.json")


if __name__ == "__main__":
    main()
