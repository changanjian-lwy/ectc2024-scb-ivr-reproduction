"""A215 analysis (BOUNDARY Section 2). Each row by its source experiment's analysis function, next to the source
record read the same way:
  nominal rows (A212): a212_analyze.one -> c6, c7;      binding rows (A206): a206_analyze.whole -> c6, after_step;
  30 % rows (A208, A210): a208_analyze.one -> r1..r4, with A210's valley band on its board.
"runs" holds the criteria rows (M = 16: c2, M = 32: c3); "information" the slower-clock rows (not criteria).
c1 from tmp/logs (unit tests, regression quick and full), c4-c6 from a215_synth.json.
  python3 a215_analyze.py -> a215_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MK = _load("a215_cfgs", HERE / "make_cfgs.py")
A12 = _load("a212_analyze", TA / "A212_p24_nominal_rows_v6" / "a212_analyze.py")
A8 = _load("a208_analyze", TA / "A208_p24_ton_lower_limit" / "a208_analyze.py")
A6 = A12.A6
COS = HERE / "cosim"
BAND_N75 = (-20.0, -12.0)                       # A210's r4 band on N75 (the same as N0's)
KEEP = {"nominal": ("status", "sources_modified", "start_pk", "hand_pk", "peak_whole", "post_pk", "post_pk_phase", "vds_whole",
                    "vo_max_to_300us", "vo_after_min_mv", "vo_after_max_mv", "vo_end_mv", "late_after", "oracle_new_after",
                    "ton_reg_min_after_ns", "il_holds"),
        "binding": ("status", "sources_modified", "start_pk", "hand_pk", "peak_whole", "post_pk", "post_pk_phase", "vds_whole",
                    "vo_max_to_300us", "vo_min_mv", "vo_max_mv", "late_after", "il_holds"),
        "light": ("status", "sources_modified", "vo_end_v", "vo_end_min_v", "vo_end_max_v", "vo_after_min_v", "vo_after_max_v",
                  "ton_reg_end_ns", "valley_end_a", "late_end", "freq_mhz", "works")}


def kind(name):
    return "nominal" if name.startswith("n_") else "binding" if name.startswith("B_") else "light"


def one(path, name):
    k = kind(name)
    if k == "nominal":
        m = A12.one(path)
    elif k == "binding":
        m = A6.whole(path)
        m.update({a: b for a, b in A6.after_step(path).items() if a not in ("record", "commit")})
    else:
        m = A8.one(path)
        if name.startswith("r_N75"):
            va = [x for v in m["valley_end_a"].values() for x in v]
            m["criteria"]["r4"] = bool(len(m["valley_end_a"]) == 4 and min(va) >= BAND_N75[0] and max(va) <= BAND_N75[1]
                                       and not any(m["late_end"]))
            m["works"] = bool(m["criteria"]["r1"] and m["criteria"]["r2"] and m["criteria"]["r4"])
    out = {a: m.get(a) for a in KEEP[k]}
    out.update(kind=k, criteria=m["criteria"], wall_s=m.get("wall_s"))
    return out


def identity():
    logs = PROJECT / "tmp" / "logs"
    unit = (logs / "a215_unit.log").read_text()
    n = re.search(r"ALL PASSED (\d+) tests", unit)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a215_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    return {"c1": bool(n and all(reg.values())), "unit_tests": int(n.group(1)) if n else None, "regression": reg}


def main():
    res = {"runs": {}, "information": {}, "reference": {}}
    for name in MK.SRC:
        ref = TA / MK.SRC[name] / "cosim" / f"run_{name}.json"
        if ref.exists():
            res["reference"][name] = one(ref, name)
    for f in sorted(COS.glob("run_*.json")):
        tag, name = f.stem[4:].split("_", 1)
        res["runs" if tag.startswith("m") else "information"][f"{tag}_{name}"] = one(f, name)
    for m, c in (("m16", "c2"), ("m32", "c3")):
        rows = {n: v for n, v in res["runs"].items() if n.startswith(m + "_")}
        res[f"criteria_{c}"] = {c: bool(len(rows) == len(MK.SRC) and all(all(v["criteria"].values()) for v in rows.values())),
                                "rows": len(rows), "failing": sorted(n for n, v in rows.items() if not all(v["criteria"].values()))}
    res["criteria_identity"] = identity()
    sy = HERE / "a215_synth.json"
    if sy.exists():
        res["criteria_synthesis"] = {k: v for k, v in json.loads(sy.read_text())["criteria_synthesis"].items() if not k.startswith("numbers")}
    (HERE / "a215_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    f1 = lambda x: "-" if x is None else f"{x:.2f}"
    for grp in ("reference", "runs", "information"):
        for n, v in res[grp].items():
            if v["kind"] == "light":
                print(f"{grp[:3]} {n:26s} {v['status'][:4]} Vo end {v['vo_end_min_v']:.4f}..{v['vo_end_max_v']:.4f} after {v['vo_after_min_v']:.4f}.."
                      f"{v['vo_after_max_v']:.4f} | reg {v['ton_reg_end_ns'][0]:.2f}..{v['ton_reg_end_ns'][1]:.2f} | late {v['late_end']} | {v['criteria']}")
            else:
                lo, hi = (v["vo_after_min_mv"], v["vo_after_max_mv"]) if v["kind"] == "nominal" else (v["vo_min_mv"], v["vo_max_mv"])
                print(f"{grp[:3]} {n:26s} {v['status'][:4]} post {f1(v['post_pk'])} (ph {v['post_pk_phase']}) start {f1(v['start_pk'])} hand {f1(v['hand_pk'])} "
                      f"whole {f1(v['peak_whole'])} | V_DS {v['vds_whole']:.1f} | Vo<=300us {v['vo_max_to_300us']:.4f} after {lo:+.1f}/{hi:+.1f} mV | "
                      f"late {v['late_after']} | {v['criteria']}")
    print({k: v for k, v in res.items() if k.startswith("criteria")})


if __name__ == "__main__":
    main()
