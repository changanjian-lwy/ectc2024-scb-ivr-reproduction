"""A193 analysis (BOUNDARY Section 2): a192_analyze.run per run (c1 start-up / handover, c2 post-step, c3 V_DS +
COMPLETED + 0 shoot-throughs / overlaps, c7 Vo <= 1.05 V over 0-300 us), with the 25 C references at the same step
position: A192 (lead 9.5 ns) and A184 (lead 8 ns). Writes a193_summary.json.
  python3 a193_analyze.py"""
from __future__ import annotations

import glob
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a192", TA / "A192_p24_slow_lead_rows" / "a192_analyze.py")
A192 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A192)
REF25 = {"lead9p5": TA / "A192_p24_slow_lead_rows" / "cosim" / "run_S75_25_p48_1us_p{k}.json",
         "lead8": TA / "A184_p24_startup_own_ton" / "cosim" / "run_S75_25_p{k}.json"}


def main():
    res = {}
    for f in sorted(glob.glob(str(HERE / "cosim" / "run_*.json"))):
        stem, out = A192.run(f)
        k = stem.rsplit("_p", 1)[1]
        out["ref25"] = {}
        for lab, pat in REF25.items():
            p = Path(str(pat).format(k=k))
            if p.exists():
                st = A192.A179.stats(str(p))
                out["ref25"][lab] = {x: st.get(x) for x in A192.DIAG}
        res[stem] = out
    (HERE / "a193_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, s in res.items():
        r = s["ref25"]
        print(f"{k:20s} start {s['start_pk']:5.1f} hand {s['hand_pk']:5.1f} post {s['peak_post']:5.1f} V {s['vds_whole']:.1f} "
              f"late {s['late_post']} NEW {s['oracle_new']} ext {s['extreme_mv']:+.1f} back {s['back_within_1pct_us']} | 25 C: "
              + " ".join(f"{lab} {v['peak_post']:.1f}" for lab, v in r.items()) + f" {s['criteria']}")


if __name__ == "__main__":
    main()
