"""A231 analysis (BOUNDARY Section 2): a225_analyze.startup on every run (through a230_analyze); x1 on the lead arm's
125 C 30 % rows, x2 on the 125 C full-load rows against their base arm; the 20 % rows are information.
  python3 a231_analyze.py -> a231_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a230_analyze", TA / "A230_p24_handover_slope_lead" / "a230_analyze.py")
A30 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A30)
COS = HERE / "cosim"
ROWS = ("N0h_30", "N75h_30", "N0h_100", "N75h_100", "N0_20", "N75_20")


def main():
    res = {"rows": {}}
    for r in ROWS:
        b, l = (A30.A25.startup(COS / f"run_u_{r}_{a}.json") for a in ("base", "lead"))
        b["f6"], l["f6"] = A30.f6(b), A30.f6(l)
        c = {}
        if r.endswith("h_30"):
            c["x1"] = bool(l["f6"] and l["vo_min_after_entry_v"] >= A30.VO_DIP)
        elif r.endswith("h_100"):
            c["x2"] = bool(l["f6"] and l["hand_pk"] <= b["hand_pk"] + A30.TOL_A
                           and l["vo_min_after_entry_v"] >= b["vo_min_after_entry_v"] - A30.TOL_V and l["vo_min_after_entry_v"] >= A30.VO_DIP)
        res["rows"][r] = {"base": b, "lead": l, "criteria": c}
    q = {k: all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"]) for k in ("x1", "x2")}
    res["criteria_main"], res["adopt"] = q, bool(all(q.values()))
    (HERE / "a231_summary.json").write_text(json.dumps(A30.A23.A16.clean(res), indent=1) + "\n")
    for r, v in res["rows"].items():
        b, l = v["base"], v["lead"]
        print(f"{r:9s} req {b['t_hand_req_us']} -> {l['t_hand_req_us']} us | Vo max {b['vo_max_v']:.4f} -> {l['vo_max_v']:.4f} | "
              f"min after {b['vo_min_after_entry_v']:.4f} -> {l['vo_min_after_entry_v']:.4f} | hand {b['hand_pk']:.1f} -> {l['hand_pk']:.1f} A | "
              f"f6 {b['f6']} -> {l['f6']} | {v['criteria']}")
    print("main", q, "adopt", res["adopt"])


if __name__ == "__main__":
    main()
