"""A161 analysis against BOUNDARY Section 2 -> a161_summary.json; prints <= 15 lines. A152's run_stats and judge per row
against the row's ideal-plant reference (A143 / A150 records); load-step Vo price 4.4 us at 150 pH (A152: 3.2 / 3.8 us at
50 / 100 pH)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
_spec = importlib.util.spec_from_file_location("a152_analyze", HERE.parent / "A152_p24_drive_spec_robustness" / "a152_analyze.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
PRICE = 4.4


def main():
    pred = json.loads((HERE / "a161_predictions.json").read_text())
    refs = {row: B.run_stats(B.ref_path(row)) for row in B.M.ROWS}
    crit, runs = {1: [], 2: [], 3: [], 4: []}, {}
    for row in B.M.ROWS:
        runs[row] = r = B.run_stats(COS / f"run_s150_{row}.json")
        for k, v in B.judge(r, refs[row], row.endswith("s_p62"), PRICE).items():
            crit[k] += [f"{row} {x}" for x in v]
    runs["m4"] = m4 = B.run_stats(COS / "run_m4_s150_l_p48_1us.json")
    b = B.judge(m4, B.run_stats(B.M.A143C / "run_g5_l_p48_1us_k4.json"), False, 0.0)
    c5 = b[1] + b[2] + b[3]
    out = {"criteria": {**{f"c{k}": {"pass": not v, "misses": v} for k, v in crit.items()}, "c5": {"pass": not c5, "misses": c5}},
           "runs": runs, "pred": pred}
    (HERE / "a161_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for row, r in runs.items():
        p = pred["vds"].get(row)
        print(f"{row:14s} V_DS {r['vds']['whole']:.1f}" + (f" (pred {p:.1f})" if p else "") + f" start {r['start_pk']:.0f} post "
              f"{r['peak_post']:.0f} late {r['late']} NEW {r['oracle_new']} Vo {r['vo_hand']:.3f}")
    print(" ".join(f"C{k[1:]} {'PASS' if v['pass'] else 'FAIL'}" for k, v in out["criteria"].items()))
    for k, v in out["criteria"].items():
        if v["misses"]:
            print(f"  {k}: " + "; ".join(v["misses"][:5]))


if __name__ == "__main__":
    main()
