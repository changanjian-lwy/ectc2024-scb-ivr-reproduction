"""A77 analysis: the Verilog co-simulation's steady state against A76 run 1 (the Python event controller).

Reads cosim/run_c*.json and the A76 reference; writes a77_summary.json.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "A76_p24_single_module_control_rules" / "a76_summary.json"
LAST, PER = 50, 20
HOW = {0: "pred", 1: "valley", 2: "zvs", 3: "restart"}


def summarize(path):
    d = json.loads(path.read_text()); cfg = d["cfg"]
    secs = d["sections"]
    t_from = secs[-(LAST + 1)]["t_s"]
    last = secs[-(PER + 1):]
    per = np.diff([s["t_s"] for s in last])
    di = max(abs(x - y) for s in last for x, y in zip(s["i"], last[-1]["i"]))
    ton = [t for t in d["turnons_last"] if t["t_s"] > t_from]
    lo = [t for t in d["lowoffs_last"] if t["t_s"] > t_from]
    n = len(secs[-1]["i"])
    how = {k: dict(Counter(HOW[t["how"]] for t in ton if t["phase"] == k)) for k in range(1, n + 1)}
    vds = {k: [t["vds_v"] for t in ton if t["phase"] == k] for k in range(1, n + 1)}
    edge = {k: [t["i_a"] for t in lo if t["phase"] == k] for k in range(1, n + 1)}
    s = secs[-1]
    return {
        "case": path.stem[4:], "t_clk_ns": cfg["t_clk_ns"], "fine": cfg["fine"], "t_drv_ns": cfg["t_drv_ns"],
        "i_target_a": cfg["i_target"], "t_end_us": d["t_end_s"] * 1e6, "wall_s": d["wall_s"],
        "period_ns": float(np.mean(per) * 1e9), "period_spread_ns": float(np.ptp(per) * 1e9), "vo_v": s["vo"],
        "section_i_a": s["i"], "last20_max_di_a": di,
        "turnon_how_last50": how,
        "turnon_vds_mean_max_last50": {k: [float(np.mean(v)), float(np.max(v))] if v else None for k, v in vds.items()},
        "lowoff_edge_i_mean_min_max_last50": {k: [float(np.mean(v)), float(np.min(v)), float(np.max(v))] if v else None
                                              for k, v in edge.items()},
        "late_fires": d["late_fires"], "trim_final": d["trim_final"],
        "theta_final_a": [cfg["i_target"] + c * cfg["trim_lsb_a"] for c in d["trim_final"]],
        "dt_pred_final_ns": d["dt_pred_final_ns"],
    }


def main():
    ref = json.loads(REF.read_text())["runs"]["r1_pred_td10_trim"]
    rows = {p.stem[4:]: summarize(p) for p in sorted((HERE / "cosim").glob("run_c*.json"))}
    print(f"reference A76 r1: T {ref['period_ns']:.3f} ns Vo {ref['vo_v']:.4f} "
          f"Vds {[round(v[0], 2) for v in ref['turnon_vds_mean_max_last50'].values()]} how {ref['turnon_how_last50']}")
    for k, r in rows.items():
        print(f"{k:28s} T {r['period_ns']:.3f} ns (spread {r['period_spread_ns']:.3f}) Vo {r['vo_v']:.4f} "
              f"dither {r['last20_max_di_a']:.3g} A late {r['late_fires']} trim {r['trim_final']} "
              f"dt_pred {np.round(r['dt_pred_final_ns'], 2)}")
        for ph in r["turnon_how_last50"]:
            print(f"     phase {ph}: {r['turnon_how_last50'][ph]} Vds mean/max {np.round(r['turnon_vds_mean_max_last50'][ph], 2)}"
                  f" low-off edge i {np.round(r['lowoff_edge_i_mean_min_max_last50'][ph], 2)}")
    (HERE / "a77_summary.json").write_text(json.dumps({"reference_a76_r1": {k: ref[k] for k in (
        "period_ns", "vo_v", "turnon_how_last50", "turnon_vds_mean_max_last50", "lowoff_edge_i_mean_min_max_last50")},
        "runs": rows}, indent=1))


if __name__ == "__main__":
    main()
