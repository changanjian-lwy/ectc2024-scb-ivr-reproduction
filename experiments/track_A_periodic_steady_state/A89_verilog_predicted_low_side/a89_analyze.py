"""A89 analysis (copied from A85's): the gate g0 against A85 r7, and the reverse-conduction loss and low-side edges of
g1 (device realism, reactive low side) and r1 (device realism, timed low side).

Reads cosim/run_*.json and A85's run_r7; writes a89_summary.json.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LAST, PER = 50, 20
HOW = {0: "pred", 1: "valley", 2: "zvs", 3: "restart", 4: "timed"}
A85_R7 = HERE.parent / "A85_verilog_ton_resolution" / "cosim" / "run_r7_5pct_fb7.json"


def settle(secs, t_from, vref=1.0, tol=0.01):
    """Time after t_from from which Vo stays within tol of vref (None if it never does)."""
    t_in = None
    for s in reversed([s for s in secs if s["t_s"] >= t_from]):
        if abs(s["vo"] - vref) > tol * vref:
            break
        t_in = s["t_s"]
    return None if t_in is None else (t_in - t_from) * 1e6


def gate(ref_path, new_path):
    """Bit-identity of the co-simulation: sections (t, v, i) and the controller's final registers."""
    a, b = json.loads(ref_path.read_text()), json.loads(new_path.read_text())
    sa, sb = a["sections"], b["sections"]
    dv = max(abs(x - y) for s, r in zip(sa, sb) for x, y in zip(s["v"] + s["i"], r["v"] + r["i"]))
    dt = max(abs(s["t_s"] - r["t_s"]) for s, r in zip(sa, sb))
    regs = {k: a[k] == b[k] for k in ("dt_pred_final_ns", "trim_final", "ton_final_lsb", "late_fires", "async_fires",
                                      "steps", "vds_max_v", "ipk_a")}
    ok = len(sa) == len(sb) and dv == 0.0 and dt == 0.0 and all(regs.values())
    return {"reference": str(ref_path.relative_to(HERE.parent)), "sections": [len(sa), len(sb)], "max_abs_diff_v_i": dv,
            "max_abs_diff_t_s": dt, "equal_registers": regs, "pass": bool(ok)}


def summarize(path):
    d = json.loads(path.read_text()); cfg = d["cfg"]
    secs = d["sections"]
    t_from = secs[-(LAST + 1)]["t_s"]
    last = secs[-(PER + 1):]
    per = np.diff([s["t_s"] for s in last])
    di = max(abs(x - y) for s in last for x, y in zip(s["i"], last[-1]["i"]))
    ton = [t for t in d["turnons_last"] if t["t_s"] > t_from]
    n = len(secs[-1]["i"])
    how = {k: dict(Counter(HOW[t["how"]] for t in ton if t["phase"] == k)) for k in range(1, n + 1)}
    vds = {k: [t["vds_v"] for t in ton if t["phase"] == k] for k in range(1, n + 1)}
    t_hand = d["t_mode_p_s"] or 0.0
    s = secs[-1]
    ok = all(set(h) <= {"pred", "valley", "zvs"} and LAST - 1 <= sum(h.values()) <= LAST + 2 for h in how.values())
    lo = [x for x in d["lowoffs_last"] if x["t_s"] > t_from and x["phase"] == 4]
    row = {
        "case": path.stem[4:], "i_target_a": cfg["i_target"], "plant_flags": d.get("plant_flags"),
        "low_pred": cfg.get("low_pred", 0),
        "t_mode_p_us": t_hand * 1e6, "settle_1pct_us_after_handover": settle(secs, t_hand, cfg["vref_v"]),
        "period_ns": float(np.mean(per) * 1e9), "period_spread_ns": float(np.ptp(per) * 1e9),
        "vo_v": s["vo"], "vo_ripple_last20_mv": 1e3 * float(np.ptp([x["vo"] for x in last])),
        "ton_final_ns": d["ton_final_lsb"] * d["lsb_s"] * 1e9, "last20_max_di_a": di, "turnon_how_last50": how,
        "turnon_vds_mean_max_last50": {k: [float(np.mean(v)), float(np.max(v))] if v else None for k, v in vds.items()},
        "all_soft_once_per_cycle": ok, "late_fires": d["late_fires"], "trim_final": d["trim_final"],
        "dt_pred_final_ns": d["dt_pred_final_ns"], "wall_s": d["wall_s"],
        "vds_max_v": max(d["vds_max_v"]), "ipk_a": d.get("ipk_a"), "async_fires": d.get("async_fires"),
        "phase4_turnoff_i_mean_min_max": [float(np.mean([x["i_a"] for x in lo])), float(np.min([x["i_a"] for x in lo])),
                                          float(np.max([x["i_a"] for x in lo]))] if lo else None,
    }
    # A89: reverse-conduction loss and the low-side edges over the last LAST sections
    rev = [x for x in secs[-LAST:] if "rev_energy_j" in x]
    if rev:
        t_sec = float(np.mean(np.diff([x["t_s"] for x in secs[-(LAST + 1):]])))
        e = np.mean([x["rev_energy_j"] for x in rev], axis=0)
        tr = np.mean([x["rev_time_s"] for x in rev], axis=0)
        row.update(p_rev_w=float(np.sum(e) / t_sec), p_rev_per_switch_w=(e / t_sec).tolist(),
                   rev_time_per_cycle_ns=(tr * 1e9).tolist())
    lows = [x for x in d.get("lowons_last", []) if x["t_s"] > t_from and x["mode_p"]]
    if lows:
        row["low_edges_last50"] = {}
        for k in range(1, n + 1):
            lk = [x for x in lows if x["phase"] == k]
            crossed = [x for x in lk if x["crossed"]]
            row["low_edges_last50"][k] = {
                "edges": len(lk), "crossed_before_edge": len(crossed),
                "vds_at_edge_min_max_v": [float(min(x["vds_v"] for x in lk)), float(max(x["vds_v"] for x in lk))],
                "t_since_off_mean_ns": float(np.mean([x["t_since_off_s"] for x in lk]) * 1e9),
                "t_cross_rel_mean_ns": float(np.mean([x["t_cross_rel_s"] for x in crossed]) * 1e9) if crossed else None}
    if "dtl_final_ns" in d:
        row["dtl_final_ns"] = d["dtl_final_ns"]
    return row


def main():
    rows = {p.stem[4:]: summarize(p) for p in sorted((HERE / "cosim").glob("run_*.json"))}
    gates = {}
    for name, ref, cand in (("g0_vs_A85_r7", A85_R7, "run_g0_gate_a85r7.json"),
                            ("g0b_vs_A85_r7", A85_R7, "run_g0b_gate_a85r7.json"),                 # amendment (Section 8)
                            ("g1b_vs_g1", HERE / "cosim" / "run_g1_device_reactive_low.json", "run_g1b_regression_g1.json")):
        if (HERE / "cosim" / cand).exists() and ref.exists():
            gates[name] = gate(ref, HERE / "cosim" / cand)
    for k, g in gates.items():
        print("GATE", k, g)
    for k, r in rows.items():
        print(f"{k:28s} Ton {r['ton_final_ns']:.3f} ns T {r['period_ns']:.2f} Vo {r['vo_v']:.4f} settle "
              f"{r['settle_1pct_us_after_handover']} soft {r['all_soft_once_per_cycle']} dither {r['last20_max_di_a']:.3f} "
              f"P_rev {r.get('p_rev_w')} Vds max {r['vds_max_v']:.2f} phase-4 turn-off i {r['phase4_turnoff_i_mean_min_max']}")
        for ph, h in r["turnon_how_last50"].items():
            print(f"     phase {ph}: {h} Vds mean/max {np.round(r['turnon_vds_mean_max_last50'][ph], 2)}")
        if "low_edges_last50" in r:
            print("     low edges", r["low_edges_last50"], "dtl", r.get("dtl_final_ns"))
    (HERE / "a89_summary.json").write_text(json.dumps({"gates": gates, "runs": rows}, indent=1))


if __name__ == "__main__":
    main()
