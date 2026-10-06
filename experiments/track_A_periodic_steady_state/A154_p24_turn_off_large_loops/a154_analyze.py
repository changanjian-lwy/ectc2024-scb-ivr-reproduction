"""A154 analysis against BOUNDARY Section 2 -> a154_summary.json; prints <= 15 lines. Per run A152's run_stats (A148
oracles, start-up / post-step peaks, V_DS windows, Vo recovery) plus the channel edge power in the steady window
(900-1000 us, sections' edge_energy_j)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_spec = importlib.util.spec_from_file_location("a152_analyze", HERE.parent / "A152_p24_drive_spec_robustness" / "a152_analyze.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


def edge_w(path, t0=900e-6, t1=1000e-6):
    d = json.loads(Path(path).read_text())
    secs = [q for q in d["sections"] if t0 <= q["t_s"] < t1 and "edge_energy_j" in q]
    return float(np.sum([np.sum(q["edge_energy_j"]) for q in secs]) / (t1 - t0)) if secs else None


def main():
    pred = json.loads((HERE / "a154_predictions.json").read_text())["rows"]
    runs, c1, c2, c3, c4 = {}, {}, {}, {}, {}
    for n, p in pred.items():
        f = COS / f"run_{n}.json"
        r = B.run_stats(f)
        r["edge_w"] = edge_w(f)
        v = r["vds"]["whole"]
        runs[n] = dict(r, pred=p)
        c1[n] = abs(v - p["vds_max_v"]) <= 1.5
        c2[n] = (v <= 40.0) == p["le_40"]
        c3[n] = r["edge_w"] is not None and abs(r["edge_w"] / p["p_edge_w"] - 1.0) <= 0.30
        c4[n] = (bool(r["ok_status"]) and r["peak_post"] <= 190.0 and not r["oracle_new"] and r["start_pk"] is not None
                 and r["start_pk"] <= 180.0)
    crit = {"1_vds_band": c1, "2_40v_side": c2, "3_edge_loss": c3, "4_controller": c4}
    (HERE / "a154_summary.json").write_text(json.dumps({"runs": runs, "criteria": crit}, indent=1, default=float) + "\n")
    for n, r in runs.items():
        p = r["pred"]
        print(f"{n}: V_DS {r['vds']['whole']:.1f} (pred {p['vds_max_v']:.1f}; steady {r['vds']['steady']:.1f}, post "
              f"{r['vds']['post']:.1f}) | edge {r['edge_w']:.1f} W (pred {p['p_edge_w']:.1f}) | start {r['start_pk']:.0f} A, Vo hand "
              f"{r['vo_hand']:.3f} | post {r['peak_post']:.0f} A, NEW {r['oracle_new']}, late {r['late']}, back "
              f"{r['back_within_1pct_us']:.1f} us")
    for k, v in crit.items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(n for n, ok in v.items() if not ok)}")


if __name__ == "__main__":
    main()
