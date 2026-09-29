"""A80 analysis: the full Verilog module controller from zero, against its Python reference run (A79).

Reads cosim/run_f*.json and each case's reference run; writes a80_summary.json.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LAST, PER = 50, 20
HOW = {0: "pred", 1: "valley", 2: "zvs", 3: "restart", 4: "timed"}


def settle(secs, t_from, vref=1.0, tol=0.01):
    """Time after t_from from which Vo stays within tol of vref (None if it never does)."""
    t_in = None
    for s in reversed([s for s in secs if s["t_s"] >= t_from]):
        if abs(s["vo"] - vref) > tol * vref:
            break
        t_in = s["t_s"]
    return None if t_in is None else (t_in - t_from) * 1e6


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
    return {
        "case": path.stem[4:], "i_target_a": cfg["i_target"], "ki_ns_per_v": cfg["ki_ns_per_v"],
        "t_mode_p_us": t_hand * 1e6, "settle_1pct_us_after_handover": settle(secs, t_hand, cfg["vref_v"]),
        "period_ns": float(np.mean(per) * 1e9), "period_spread_ns": float(np.ptp(per) * 1e9),
        "vo_v": s["vo"], "vo_ripple_last20_mv": 1e3 * float(np.ptp([x["vo"] for x in last])),
        "ton_final_ns": d["ton_final_lsb"] * d["lsb_s"] * 1e9, "ladder_ratio": [v / s["vin_v"] for v in s["vcs_v"]],
        "last20_max_di_a": di, "turnon_how_last50": how,
        "turnon_vds_mean_max_last50": {k: [float(np.mean(v)), float(np.max(v))] if v else None for k, v in vds.items()},
        "all_soft_once_per_cycle": ok, "late_fires": d["late_fires"], "trim_final": d["trim_final"],
        "dt_pred_final_ns": d["dt_pred_final_ns"], "wall_s": d["wall_s"],
        "vds_max_v": max(d["vds_max_v"]) if "vds_max_v" in d else None, "ipk_a": d.get("ipk_a"),
    }


def main():
    rows = {p.stem[4:]: summarize(p) for p in sorted((HERE / "cosim").glob("run_f*.json"))}
    for k, r in rows.items():
        print(f"{k:34s} mode P at {r['t_mode_p_us']:.2f} us, settle 1% {r['settle_1pct_us_after_handover']} us, "
              f"T {r['period_ns']:.2f} ns (spread {r['period_spread_ns']:.1f}) Vo {r['vo_v']:.4f} "
              f"(ripple {r['vo_ripple_last20_mv']:.2f} mV) Ton {r['ton_final_ns']:.3f} ns soft {r['all_soft_once_per_cycle']} "
              f"dither {r['last20_max_di_a']:.3g} A trim {r['trim_final']}")
        for ph, h in r["turnon_how_last50"].items():
            print(f"     phase {ph}: {h} Vds mean/max {np.round(r['turnon_vds_mean_max_last50'][ph], 2)}")
    (HERE / "a80_summary.json").write_text(json.dumps({"runs": rows}, indent=1))


if __name__ == "__main__":
    main()
