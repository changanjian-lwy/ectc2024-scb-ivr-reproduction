"""A258 analysis (BOUNDARY Section 2):
- t0: HOLD rows, arm c equal to A256's run_s_ (A246's same);
- t1: pr rows, arm c meets A240's q1 + q2 (whole peak <= 200 A, V_DS <= 40 V, Vo above 1.05 V < 25 us);
- t2: REARM rows, arm c against A256's run_s_ (A236's row: peaks + 2 A, NEW, |Vo extreme| + 2 mV; ladder + 0.2 V);
- t3: ro_S75h, arm c against arm s, the same test.
Re-arm times come from ocp_susp. --preflight runs the same criteria on existing records standing in for the new
arms: pr arm c = A254's run_l_p_<board>_1000k (the limit without the overload), pr arm s = A246's run_h_ (no limit),
REARM / HOLD arm c = A256's run_s_ (ro_S75h has no stand-in).
  python3 a258_analyze.py [--preflight] -> a258_summary.json (not written with --preflight)"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a258_make_cfgs", HERE / "make_cfgs.py")
A56 = _load("a256_analyze", TA / "A256_p24_limit_suspends_on_overload" / "a256_analyze.py")
A36, A46, dev_max = A56.A36, A56.A46, A56.dev_max
A40 = A46.A40
C56, C54, C46 = (TA / d / "cosim" for d in ("A256_p24_limit_suspends_on_overload", "A254_p24_peak_limit_measured_level",
                                             "A246_p24_held_report_floor"))
PK_TOL, VO_TOL_MV, DEV_TOL, T_OVL_END = 2.0, 2.0, 0.2, 290e-6
PRE = "--preflight" in sys.argv


def path(arm, row):
    if not PRE:
        return HERE / "cosim" / f"run_{arm}_{row}.json"
    if row in MC.PR:
        return (C54 / f"run_l_p_{row[3:]}_1000k.json") if arm == "c" else (C46 / f"run_h_p_{row[3:]}_1000k.json")
    return None if row in MC.RO else C56 / f"run_s_{row}.json"


def t_event(d):
    c = d["cfg"]
    ev = c.get("load_step") or c.get("line_step") or c.get("load_pulse")
    return ev["t_us"] * 1e-6


def rearm_us(d, after):
    return [round(1e6 * x["t_s"], 2) for x in d.get("ocp_susp", []) if x["on"] == 0 and x["t_s"] >= after]


def train_row(f):
    """A236's row quantities for a pulse train (A236 reads only line and load steps), from the train's start."""
    d = json.loads(f.read_text())
    t0 = t_event(d)
    g = d["gate_offs_last"]
    return {"post_pk": max(e["i_max_a"] for e in g if e["t_s"] >= t0), "peak_whole": max(e["i_max_a"] for e in g),
            "new_after": sum(e["cls"] == "NEW" and e["t_s"] >= t0 for e in A36.ORA.check(f)["events"]),
            "vo_ext_mv": 1e3 * max((q["vo"] - 1.0 for q in d["sections"] if q["t_s"] >= t0), key=abs)}


def against(fa, fb):
    """A256's s2 / s3 test with fb as the reference: (passes, a's metrics, b's metrics)."""
    da, db = json.loads(fa.read_text()), json.loads(fb.read_text())
    row = train_row if "load_pulse" in da["cfg"] else (lambda f: A36.row("k_N0", f))
    a, b = row(fa), row(fb)
    t0 = t_event(da)
    keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv")
    ma, mb = {k: a[k] for k in keep} | {"dev_max_v": dev_max(da, t0)}, {k: b[k] for k in keep} | {"dev_max_v": dev_max(db, t0)}
    ok = bool(ma["peak_whole"] <= mb["peak_whole"] + PK_TOL and ma["post_pk"] <= mb["post_pk"] + PK_TOL
              and ma["new_after"] <= mb["new_after"] and abs(ma["vo_ext_mv"]) <= abs(mb["vo_ext_mv"]) + VO_TOL_MV
              and ma["dev_max_v"] <= mb["dev_max_v"] + DEV_TOL)
    return ok, ma, mb


def one(row):
    fc = path("c", row)
    if fc is None or not fc.exists():
        return None
    if row in MC.HOLD:
        return {"criteria": {"t0": bool(A46.same(fc, C56 / f"run_s_{row}.json"))}}
    if row in MC.REARM:
        ok, mc, ms = against(fc, C56 / f"run_s_{row}.json")
        return {"c": mc, "a256": ms, "rearm_us": rearm_us(json.loads(fc.read_text()), 0.0), "criteria": {"t2": ok}}
    fs = path("s", row)
    out = {"rearm_us": {a: rearm_us(json.loads(f.read_text()), T_OVL_END) for a, f in (("c", fc), ("s", fs)) if f and f.exists()}}
    if row in MC.PR:
        for a, f in (("c", fc), ("s", fs)):
            if f and f.exists():
                v, q = A40.one(f, row[3:], 1000.0)
                out[a] = {k: v[k] for k in ("peak_whole", "peak_after_t0", "vds_v", "vo_min_v", "t_above_max_us", "events_over_lim")}
                out[a] |= {"q1": q["q1"], "q2": q["q2"]}
        out["criteria"] = {"t1": bool(out["c"]["q1"] and out["c"]["q2"])}
        return out
    if fs and fs.exists():
        ok, mc, ms = against(fc, fs)
        out |= {"c": mc, "s": ms, "criteria": {"t3": ok}}
    return out


def main():
    rows = MC.PR + MC.RO + MC.REARM + MC.HOLD
    res = {"preflight": PRE, "rows": {r: one(r) for r in rows}}
    done = [x for x in res["rows"].values() if x and "criteria" in x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done if k in x["criteria"]) for k in ("t0", "t1", "t2", "t3")}
    res["criteria"]["complete"] = len(done) == len(rows)
    if not PRE:
        (HERE / "a258_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if not x:
            print(f"{row:11s} -")
            continue
        extra = ""
        if row in MC.PR:
            extra = " ".join(f"{a}: peak {x[a]['peak_whole']:.1f} A q1 {x[a]['q1']} q2 {x[a]['q2']}" for a in ("c", "s") if a in x)
        elif "c" in x:
            ref = "a256" if "a256" in x else "s"
            extra = (f"peak c {x['c']['peak_whole']:.1f} {ref} {x[ref]['peak_whole']:.1f} A dev c {x['c']['dev_max_v']:.2f} "
                     f"{ref} {x[ref]['dev_max_v']:.2f} V")
        print(f"{row:11s} {x['criteria']} {extra} rearm {x.get('rearm_us', '')}")
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
