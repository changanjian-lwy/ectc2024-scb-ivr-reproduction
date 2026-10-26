"""A252 analysis (BOUNDARY Section 2): each arm against the final configuration's record (A246 run_h_) through
A246's one1 (A240's peak after 300 us, whole-run peak, Vo's minimum, q1-q5).
  python3 a252_analyze.py -> a252_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a246_analyze", TA / "A246_p24_held_report_floor" / "a246_analyze.py")
A46 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A46)
_m = importlib.util.spec_from_file_location("a252_make_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(_m)
_m.loader.exec_module(MC)


def main():
    res = {}
    for arm, (row, dt) in MC.ARMS.items():
        f = HERE / "cosim" / f"run_{arm}_{row}.json"
        if not f.exists():
            res[arm] = None; continue
        (v, q), (h, qh) = A46.one1(f, row), A46.one1(TA / "A246_p24_held_report_floor" / "cosim" / f"run_h_{row}.json", row)
        keep = ("peak_after_t0", "peak_whole", "vo_min_v")
        res[arm] = {"row": row, "dt_fix_ns": dt, "x": {k: v[k] for k in keep} | {"q": q}, "h": {k: h[k] for k in keep} | {"q": qh},
                    "criteria": {"k1": bool(q["q1"] and q["q2"])}}
    (HERE / "a252_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for arm, x in res.items():
        if x:
            print(f"{arm} {x['row']}: peak after 300 us {x['x']['peak_after_t0']:.1f} A (h {x['h']['peak_after_t0']:.1f}), "
                  f"whole {x['x']['peak_whole']:.1f} (h {x['h']['peak_whole']:.1f}), Vo min {x['x']['vo_min_v']:.4f} "
                  f"(h {x['h']['vo_min_v']:.4f}), q1/q2 {x['x']['q']['q1']}/{x['x']['q']['q2']}")


if __name__ == "__main__":
    main()
