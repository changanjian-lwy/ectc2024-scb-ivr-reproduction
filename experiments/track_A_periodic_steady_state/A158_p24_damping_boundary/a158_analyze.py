"""A158 analysis against BOUNDARY Section 2 -> a158_summary.json; prints <= 10 lines. A152's run_stats / judge per row
against the ideal-plant l_p48_1us reference; a row holds when the judge finds no start-up, post-step, NEW, late or Vo miss."""
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
    pred = json.loads((HERE / "a158_predictions.json").read_text())
    ref = B.run_stats(B.ref_path("l_p48_1us"))
    runs, holds = {}, {}
    for n in pred["h1"]:
        r = B.run_stats(COS / f"run_{n}.json")
        bad = B.judge(r, ref, False, 0.0)
        holds[n] = not (bad[1] + bad[2] + bad[3] + bad[4])
        runs[n] = dict(r, misses=bad, holds=holds[n])
    crit = {"1_h1_q_only": {n: holds[n] == pred["h1"][n] for n in holds},
            "2_q30_at_100ph": {"q30_s100": holds["q30_s100"]}}
    out = {"runs": runs, "criteria": crit, "h2_agrees": {n: holds[n] == pred["h2"][n] for n in holds}}
    (HERE / "a158_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for n, r in runs.items():
        print(f"{n}: holds {r['holds']} (H1 {pred['h1'][n]}, H2 {pred['h2'][n]}) V_DS {r['vds']['whole']:.1f} late {r['late']} "
              f"NEW {r['oracle_new']} post {r['peak_post']:.0f}")
    for k, v in crit.items():
        print(f"C{k}: {'PASS' if all(v.values()) else 'FAIL ' + ', '.join(n for n, x in v.items() if not x)}")
    print("H2 agrees on", sum(out["h2_agrees"].values()), "of", len(holds))


if __name__ == "__main__":
    main()
