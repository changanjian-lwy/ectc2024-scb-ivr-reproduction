"""A74 analysis: regression gate against A73 run 5, and the 2 x 2 (shift rule x restart time) table.

Reads run_*.json written by a74_transient.py; writes regression_gate_vs_A73.json and a74_summary.json.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A73 = HERE.parent / "A73_p24_literature_startup_methods" / "run_r5_recheck_a72r9.json"
RUNS = {  # BOUNDARY Section 5; r0 = A73 run 5 replayed with the turn-on log (the regression gate)
    "r0_fixed_rs20": ("fixed", 20),
    "r1_adaptive_rs20": ("adaptive", 20),
    "r2_adaptive_rs60": ("adaptive", 60),
    "r3_fixed_rs60": ("fixed", 60),
}
LAST = 50  # cycles for the turn-on statistics
PER = 20   # sections for the periodicity test


def load(name):
    return json.loads((HERE / f"run_{name}.json").read_text())


def gate():
    ref, new = json.loads(A73.read_text()), load("r0_fixed_rs20")
    a, b = ref["sections"], new["sections"]
    same_count = len(a) == len(b) and ref["sections_total"] == new["sections_total"]
    dv = max(abs(x - y) for s, r in zip(a, b) for x, y in zip(s["v"] + s["i"], r["v"] + r["i"]))
    dt = max(abs(s["t_s"] - r["t_s"]) for s, r in zip(a, b))
    out = {"reference": "A73 run_r5_recheck_a72r9.json", "candidate": "run_r0_fixed_rs20.json",
           "sections_ref": ref["sections_total"], "sections_new": new["sections_total"],
           "max_abs_diff_v_i": dv, "max_abs_diff_t_s": dt,
           "end_equal": ref["end"]["y"] == new["end"]["y"] and ref["end"]["restart_count"] == new["end"]["restart_count"],
           "pass": bool(same_count and dv == 0.0 and dt == 0.0)}
    (HERE / "regression_gate_vs_A73.json").write_text(json.dumps(out, indent=1))
    return out


def summarize(name):
    d = load(name); e = d["end"]; secs = d["sections"]; n = len(secs[-1]["i"])
    tot = d["sections_total"] - 1
    last = secs[-(PER + 1):]
    per = np.diff([s["t_s"] for s in last])
    di = max(abs(x - y) for s in last for x, y in zip(s["i"], last[-1]["i"]))
    dvo = max(abs(s["vo"] - last[-1]["vo"]) for s in last)
    s = secs[-1]
    ton = [t for t in e["turnons_last"] if t["cycle"] >= tot - LAST]
    how = {k: dict(Counter(t["how"] for t in ton if t["phase"] == k)) for k in range(1, n + 1)}
    vds = {k: [t["vds_v"] for t in ton if t["phase"] == k] for k in range(1, n + 1)}
    rs_last = sum(1 for t in ton if t["how"] == "high_restart")
    return {
        "shift": RUNS[name][0], "t_restart_high_ns": RUNS[name][1], "status": e["status"], "t_end_us": e["t_s"] * 1e6,
        "handover_us": None if e["t_hand_actual_s"] is None else e["t_hand_actual_s"] * 1e6,
        "periodic": bool(di < 1e-3 and dvo < 1e-4), "last20_max_di_a": di, "last20_max_dvo_v": dvo,
        "period_ns": float(np.mean(per) * 1e9), "vo_v": s["vo"],
        "ladder_ratio": [v / s["vin_v"] for v in s["vcs_v"]], "section_i_a": s["i"],
        "section_state_v_i": s["v"] + s["i"],
        "turnon_how_last50": how,
        "turnon_vds_mean_max_last50": {k: [float(np.mean(v)), float(np.max(v))] if v else None for k, v in vds.items()},
        "restarts_last50": rs_last, "restart_count_total": e["restart_count"],
        "valley_firings_total": d["valley_events_count"],
        "vds_max_v": max(e["vds_max_v"].values()), "vds_max_by_switch": e["vds_max_v"],
        "ipk_a": max(x["ipk_a"] for x in secs), "t_meas_clamps": e["t_meas_clamps"],
        "t_meas_last_ns": e["t_meas_last_s"] * 1e9, "diode_cuts": e["diode_cuts"],
    }


def main():
    g = gate()
    print("gate:", g)
    rows = {k: summarize(k) for k in RUNS if (HERE / f"run_{k}.json").exists()}
    dep = {}
    for rule, a, b in (("fixed", "r0_fixed_rs20", "r3_fixed_rs60"), ("adaptive", "r1_adaptive_rs20", "r2_adaptive_rs60")):
        if a in rows and b in rows:
            x, y = np.array(rows[a]["section_state_v_i"]), np.array(rows[b]["section_state_v_i"])
            dep[rule] = {"max_abs_diff_section_v_i": float(np.max(np.abs(x - y))),
                         "period_diff_ns": rows[b]["period_ns"] - rows[a]["period_ns"],
                         "vo_diff_v": rows[b]["vo_v"] - rows[a]["vo_v"]}
    for k, r in rows.items():
        print(f"{k:18s} {r['status']:9s} periodic {r['periodic']} T {r['period_ns']:.3f} ns Vo {r['vo_v']:.4f} "
              f"ladder {np.round(r['ladder_ratio'], 4)} i {np.round(r['section_i_a'], 2)} "
              f"Vdsmax {r['vds_max_v']:.1f} ipk {r['ipk_a']:.0f} restarts(last50) {r['restarts_last50']} clamps {r['t_meas_clamps']}")
        for ph, h in r["turnon_how_last50"].items():
            print(f"     phase {ph}: {h}  Vds at turn-on mean/max {np.round(r['turnon_vds_mean_max_last50'][ph], 2)}")
    print("restart dependence:", dep)
    (HERE / "a74_summary.json").write_text(json.dumps({"gate": g, "runs": rows, "restart_dependence": dep}, indent=1))


if __name__ == "__main__":
    main()
