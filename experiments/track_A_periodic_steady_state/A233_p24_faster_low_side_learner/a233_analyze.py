"""A233 analysis (BOUNDARY Section 2): a223_analyze.one on every event row against its lo_smax-64 reference record
(A225 / A229 / A228), a229_analyze.skip_file on the skipping row against A228's d0 means; m1-m5 per arm.
  python3 a233_analyze.py -> a233_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a229_analyze", TA / "A229_p24_kd_band" / "a229_analyze.py")
A29 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A29)
A23, A28 = A29.A23, A29.A28
COS = HERE / "cosim"
_m = importlib.util.spec_from_file_location("a233_make_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(_m)
_m.loader.exec_module(MC)
ITEM2, LOAD, W, LINE = ("a_S75h_d2", "a_S75h_d10", "a_S75h_d20", "a_S75_d20"), ("k_N0",), ("w5_N0", "w20_N0", "w5_N75"), ("l_N0_p48", "l_N0_m80")
D0 = (-16.16, -13.60)                                   # A228: N0 10 % d0 means (lowest / highest true valley)


def ref(row):
    src = TA / MC.SRC[row]
    return src.parent / json.loads(src.read_text())["out"]


def basic(m):
    return bool(m["status"] == "COMPLETED" and not m["overlaps"] and not m["shoot_on"] and m["vds_whole"] <= A23.V_LIM)


def main():
    res = {"rows": {}, "criteria_main": {}}
    for s in MC.SMAX:
        crit = {}
        for row in MC.SRC:
            f = COS / f"run_{row}_s{s}.json"
            if row == "z_N0_10":
                v = A29.skip_file(f, "z_N0_10")
                ok = bool(v["q1_run"] and v["vmin_a"] >= D0[0] - 1.0 and v["vmax_a"] <= D0[1] + 1.0)
                res["rows"][f"{row}_s{s}"] = {"skip": v, "m5": ok}
                crit.setdefault("m5", []).append(ok)
                continue
            m, r = A23.one(f), A23.one(ref(row))
            d = {"post_pk": m["post_pk"], "ref_post_pk": r["post_pk"], "vo_ext_mv": m["vo_ext_mv"], "ref_vo_ext_mv": r["vo_ext_mv"],
                 "peak_whole": m["peak_whole"], "vds_whole": m["vds_whole"], "late_after": sum(m["late_after"]),
                 "ref_late_after": sum(r["late_after"]), "basic": basic(m)}
            if row in ITEM2:
                k, ok = "m1", d["basic"] and m["post_pk"] <= A23.I_LIM
            elif row == "k_S75h":
                k, ok = "m2", d["basic"] and m["post_pk"] <= r["post_pk"] + 0.5
            elif row in LOAD:
                k, ok = "m3", d["basic"] and m["post_pk"] <= r["post_pk"] + 1.0 and abs(m["vo_ext_mv"]) <= abs(r["vo_ext_mv"]) + 1.0
            elif row in W:
                k, ok = "m3", (d["basic"] and m["peak_whole"] <= A23.I_LIM and abs(m["vo_last_min_v"] - 1) <= A23.VO_BAND
                               and abs(m["vo_last_max_v"] - 1) <= A23.VO_BAND and abs(m["vo_ext_mv"]) <= abs(r["vo_ext_mv"]) + 2.0)
            else:
                k, ok = "m4", d["basic"] and m["post_pk"] <= r["post_pk"] + 1.0 and abs(m["vo_ext_mv"]) <= abs(r["vo_ext_mv"]) + 1.0
            d[k] = bool(ok)
            res["rows"][f"{row}_s{s}"] = d
            crit.setdefault(k, []).append(bool(ok))
        res["criteria_main"][f"s{s}"] = {k: all(v) for k, v in crit.items()}
    passing = [s for s in MC.SMAX if all(res["criteria_main"][f"s{s}"].values())]
    res["adopt"] = passing[0] if passing else None
    (HERE / "a233_summary.json").write_text(json.dumps(A23.A16.clean(res), indent=1) + "\n")
    for n, d in res["rows"].items():
        if "skip" in d:
            print(f"{n:16s} valleys {d['skip']['vmin_a']:.1f}..{d['skip']['vmax_a']:.1f} (d0 means {D0}) | m5 {d['m5']}")
        else:
            k = [x for x in ("m1", "m2", "m3", "m4") if x in d][0]
            print(f"{n:16s} post {d['ref_post_pk']:6.1f} -> {d['post_pk']:6.1f} A | Vo {d['ref_vo_ext_mv']:+6.1f} -> {d['vo_ext_mv']:+6.1f} mV | "
                  f"late {d['ref_late_after']} -> {d['late_after']} | {k} {d[k]}")
    print("main", res["criteria_main"], "adopt", res["adopt"])


if __name__ == "__main__":
    main()
