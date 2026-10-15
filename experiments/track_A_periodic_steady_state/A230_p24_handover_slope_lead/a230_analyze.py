"""A230 analysis (BOUNDARY Section 2): a225_analyze.startup on every run; v1 on the lead arm's light rows, v2 on S75 at
125 C full load against its base arm, v3 = the 25 C full-load rows bit for bit their base arm (a228_analyze.same); j1 from
the regression logs.
  python3 a230_analyze.py -> a230_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, TA / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A25 = _load("a225_analyze", "A225_p24_startup_items_recheck/a225_analyze.py")
A28 = _load("a228_analyze", "A228_p24_damped_loop_adoption/a228_analyze.py")
A23 = A25.A23
COS = HERE / "cosim"
LIGHT = ("N0_0", "N0_10", "N0_30", "N75_0", "N75_30", "S75_30", "S75h_30")
VO_MAX, VO_DIP, TOL_A, TOL_V = 1.05, 0.99, 2.0, 0.002


def f6(m):
    return bool(m["status"] == "COMPLETED" and m["vo_max_v"] <= VO_MAX and m["peak_whole"] <= A23.I_LIM and not m["overlaps"]
                and not m["shoot_on"] and m["vds_v"] <= A23.V_LIM and all(abs(v - 1) <= A23.VO_BAND for v in m["vo_last"]))


def identity():
    logs = PROJECT / "tmp" / "logs"
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a230_reg_{k}.log").read_text())) for k in ("quick", "full")}
    return {"regression": reg, "j1": all(reg.values())}


def main():
    res = {"identity": identity(), "rows": {}}
    for r in LIGHT + ("S75h_100", "N0_100", "S75_100"):
        b, l = (A25.startup(COS / f"run_u_{r}_{a}.json") for a in ("base", "lead"))
        c = {}
        if r in LIGHT:
            c["v1"] = bool(f6(l) and l["vo_min_after_entry_v"] >= VO_DIP)
            b["f6"] = f6(b)
        elif r == "S75h_100":
            c["v2"] = bool(f6(l) and l["hand_pk"] <= b["hand_pk"] + TOL_A and l["vo_min_after_entry_v"] >= b["vo_min_after_entry_v"] - TOL_V
                           and l["vo_min_after_entry_v"] >= VO_DIP)
        else:
            c["v3"] = A28.same(COS / f"run_u_{r}_lead.json", COS / f"run_u_{r}_base.json")
        res["rows"][r] = {"base": b, "lead": l, "criteria": c}
    q = {"j1": res["identity"]["j1"]}
    for k in ("v1", "v2", "v3"):
        q[k] = all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"])
    res["criteria_main"], res["adopt"] = q, bool(all(q.values()))
    (HERE / "a230_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    print("j1", res["identity"])
    for r, v in res["rows"].items():
        b, l = v["base"], v["lead"]
        print(f"{r:9s} req {b['t_hand_req_us']} -> {l['t_hand_req_us']} us | Vin entry {b['vin_at_entry_v']:.1f} -> {l['vin_at_entry_v']:.1f} V | "
              f"Vo max {b['vo_max_v']:.4f} -> {l['vo_max_v']:.4f} | min after {b['vo_min_after_entry_v']:.4f} -> {l['vo_min_after_entry_v']:.4f} | "
              f"hand {b['hand_pk']:.1f} -> {l['hand_pk']:.1f} A | {v['criteria']}" + (f" base f6 {b['f6']}" if "f6" in b else ""))
    print("main", q, "adopt", res["adopt"])


if __name__ == "__main__":
    main()
