"""A157 analysis against BOUNDARY Section 2 -> a157_summary.json; prints <= 12 lines. A152's run_stats / judge per row
against the ideal-plant reference of l_p48_1us (A143 g4_s100_l_p48_1us_k4)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_spec = importlib.util.spec_from_file_location("a152_analyze", HERE.parent / "A152_p24_drive_spec_robustness" / "a152_analyze.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


def main():
    pred = json.loads((HERE / "a157_predictions.json").read_text())
    ref = B.run_stats(B.ref_path("l_p48_1us"))
    runs, c1, c2, c3 = {}, {}, {}, {}
    for n, p in pred.items():
        r = B.run_stats(COS / f"run_{n}.json")
        bad = B.judge(r, ref, False, 0.0)
        runs[n] = dict(r, pred_vds=p, misses=bad)
        c1[n] = abs(r["vds"]["whole"] - p) <= 1.5
        if n != "q0_s125":
            c2[n] = not bad[1]
        c3[n] = not (bad[2] + bad[3] + bad[4])
    crit = {"1_vds_band": c1, "2_vds_40": c2, "3_controller": c3}
    (HERE / "a157_summary.json").write_text(json.dumps({"runs": runs, "criteria": crit}, indent=1, default=float) + "\n")
    for n, r in runs.items():
        print(f"{n}: V_DS {r['vds']['whole']:.1f} (pred {r['pred_vds']:.1f}) start {r['start_pk']:.0f} post {r['peak_post']:.0f} "
              f"late {r['late']} NEW {r['oracle_new']} {r['status'] if 'status' in r else ''} misses {sum(r['misses'].values(), [])}")
    for k, v in crit.items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(n for n, x in v.items() if not x)}")


if __name__ == "__main__":
    main()
