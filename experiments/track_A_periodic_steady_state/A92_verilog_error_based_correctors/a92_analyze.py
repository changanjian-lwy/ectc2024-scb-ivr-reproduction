"""A92 analysis: the gate g0 against A89 r2, and the error-based correctors against A91's runs.

Uses A89's gate() and summarize() and A91's low_offsets() and hard_on_loss_bounds() (read-only imports) and adds,
over the last LAST cycles: the high-side error (actual turn-on - valley) from the bridge's turn-on records, the
low-side error distribution (early fraction, beyond the 0.16 ns window), the final dtl / dt_pred, and the A91 run
of the same name for comparison. Writes a92_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A89_verilog_predicted_low_side"))
sys.path.insert(0, str(HERE.parent / "A91_verilog_gate_driver_timing"))
from a89_analyze import LAST, gate, summarize  # noqa: E402
from a91_analyze import hard_on_loss_bounds, low_offsets  # noqa: E402

A89_R2 = HERE.parent / "A89_verilog_predicted_low_side" / "cosim" / "run_r2_device_low_pred_blank.json"
A91 = HERE.parent / "A91_verilog_gate_driver_timing" / "cosim"
WINDOW_NS = 0.16


def errors(d):
    secs = d["sections"]
    t_from = secs[-(LAST + 1)]["t_s"]
    lows = [x for x in d.get("lowons_last", []) if x["t_s"] > t_from and x["mode_p"]]
    el = [(x["t_since_off_s"] - x["t_cross_rel_s"]) * 1e9 for x in lows if x["crossed"]]
    n_early = sum(not x["crossed"] for x in lows)
    highs = [x for x in d.get("turnons_last", []) if x["t_s"] > t_from and "early" in x]
    eh = [x["err_s"] * 1e9 for x in highs if not x["early"] and x["err_s"] is not None]
    return {"low_edges": len(lows), "low_early_frac": n_early / len(lows) if lows else None,
            "low_beyond_window_frac": sum(e > WINDOW_NS for e in el) / len(lows) if lows else None,
            "low_err_ns_mean_std_max": [float(np.mean(el)), float(np.std(el)), float(np.max(el))] if el else None,
            "high_edges": len(highs), "high_early_frac": sum(x["early"] for x in highs) / len(highs) if highs else None,
            "high_err_ns_mean_std_max": [float(np.mean(eh)), float(np.std(eh)), float(np.max(eh))] if eh else None,
            "dtl_final_ns": d.get("dtl_final_ns"), "dt_pred_final_ns": d.get("dt_pred_final_ns")}


def row_of(p):
    d = json.loads(p.read_text())
    row = {"status": d.get("status"), "driver": d.get("driver"), "overlaps": d.get("overlaps"),
           "first_overlap": d.get("first_overlap"), "t_end_s": d["t_end_s"], "sections": len(d["sections"])}
    if d.get("status") == "COMPLETED" and len(d["sections"]) > LAST + 1:
        row.update(summarize(p)); row.update(low_offsets(d)); row.update(errors(d))
    row["hard_on_estimate_mode_p"] = hard_on_loss_bounds(d)
    return row


def main():
    out = {"gates": {}, "runs": {}, "a91_same_name": {}}
    g0 = HERE / "cosim" / "run_g0_gate_a89r2.json"
    if g0.exists():
        out["gates"]["g0_vs_A89_r2"] = gate(A89_R2, g0)
        print("GATE g0_vs_A89_r2", out["gates"]["g0_vs_A89_r2"])
    for p in sorted((HERE / "cosim").glob("run_*.json")):
        name = p.stem[4:]
        r = out["runs"][name] = row_of(p)
        q = A91 / p.name
        if q.exists() and name != "g0_gate_a89r2":
            a = row_of(q)
            out["a91_same_name"][name] = {k: a.get(k) for k in ("status", "first_overlap", "last20_max_di_a", "p_rev_w",
                                                                  "hard_on_estimate_mode_p", "ton_final_ns")}
        if "ton_final_ns" in r:
            print(f"{name:26s} {r['status']} Ton {r['ton_final_ns']:.3f} T {r['period_ns']:.2f} Vo {r['vo_v']:.4f} soft "
                  f"{r['all_soft_once_per_cycle']} dither {r['last20_max_di_a']:.3f} P_rev {r.get('p_rev_w', 0):.3f} W "
                  f"Vdsmax {r['vds_max_v']:.2f} ipk {r['ipk_a']:.0f} overlaps {r['overlaps']}")
            print(f"     low: early {r['low_early_frac']:.3f} beyond {r['low_beyond_window_frac']:.3f} err "
                  f"{np.round(r['low_err_ns_mean_std_max'], 3).tolist()} | high: early {r['high_early_frac']:.3f} err "
                  f"{np.round(r['high_err_ns_mean_std_max'], 3).tolist()} | dtl {np.round(r['dtl_final_ns'], 3).tolist()} "
                  f"dt_pred {np.round(r['dt_pred_final_ns'], 3).tolist()} | hard-on {r['hard_on_estimate_mode_p']}")
            print("     high-side Vds mean/max", {k: np.round(v, 2).tolist() for k, v in r["turnon_vds_mean_max_last50"].items()})
        else:
            print(f"{name:26s} {r['status']} stopped at {r['t_end_s'] * 1e6:.3f} us; first overlap {r['first_overlap']}")
    (HERE / "a92_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
