"""A244 analysis (BOUNDARY Section 2), A243's measures on arm w: stage 1 = A240's rows against A240's records
(a240_analyze.one), stage 2 = A236's rows and A237's re-applications against their references (a236_analyze.row and
its criteria). g0: unit tests and regression (tmp/logs/a244_*.log) and run_o_cw5_N75 = A243's run_b_cw5_N75. g8: each
run equals its reference before its disturbance (sections and edge lists: time, phase, current). The control's c1
(a244_control.json, BOUNDARY Section 4) is folded in when present.
  python3 a244_analyze.py -> a244_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
COS = HERE / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a244_make_cfgs", HERE / "make_cfgs.py")
A43 = _load("a243_analyze", TA / "A243_p24_hold_without_reversal" / "a243_analyze.py")
A40, A36, delay_min, held = A43.A40, A43.A36, A43.delay_min, A43.held
PK_TOL, VO_TOL_MV, UNIT_N, WIDE = A43.PK_TOL, A43.VO_TOL_MV, 123, A43.WIDE
SEC = ("t_s", "vo", "vin_v", "vcs_v", "ton_lsb")
EDGES = ("highoffs_last", "lowoffs_last", "turnons_last")


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a244_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a244_reg_{k}.log").read_text())) for k in ("quick", "full")}
    o = COS / f"run_o_{MC.IDENT}.json"
    same = A36.same(o, MC.A43 / "cosim" / f"run_b_{MC.IDENT}.json") if o.exists() else None
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "o_row": same,
            "g0": bool(n_pass == UNIT_N and n_fail == 0 and all(reg.values()) and same and all(same.values()))}


def t_dist(cfg):
    ev = cfg.get("line_step") or cfg.get("load_step") or cfg.get("load_pulse")
    return ev["t_us"] * 1e-6


def before(f, fr):
    """g8: the run and its reference agree before the disturbance (every module); the first difference if not."""
    a, b = json.loads(Path(f).read_text()), json.loads(Path(fr).read_text())
    t0 = t_dist(a["cfg"])
    first = None
    for ma, mb in zip([a] + a.get("modules_rest", []), [b] + b.get("modules_rest", [])):
        pairs = [([tuple(q[k] for k in SEC) for q in ma["sections"] if q["t_s"] < t0],
                  [tuple(q[k] for k in SEC) for q in mb["sections"] if q["t_s"] < t0])]
        pairs += [([(e["t_s"], e["phase"], e["i_a"]) for e in ma[k] if e["t_s"] < t0],
                   [(e["t_s"], e["phase"], e["i_a"]) for e in mb[k] if e["t_s"] < t0]) for k in EDGES]
        for x, y in pairs:
            if x != y:
                i = next((i for i, (p, q) in enumerate(zip(x, y)) if p != q), min(len(x), len(y)))
                t = (x[i] if i < len(x) else y[i])[0]
                first = t if first is None else min(first, t)
    return {"same": first is None, "first_diff_us": first and first * 1e6, "t_dist_us": t0 * 1e6}


def stage1():
    rows = {}
    for row in MC.STAGE1:
        f = COS / f"run_w_{row}.json"
        if not f.exists():
            rows[row] = None; continue
        b, fk = row.split("_")[1], float(row.split("_")[2][:-1])
        v, q = A40.one(f, b, fk)
        rv, _ = A40.one(MC.ref(row), b, fk)
        v["delay_min_ns"], rv["delay_min_ns"] = delay_min(f, A40.T0), delay_min(MC.ref(row), A40.T0)
        v["held"] = held(f, A40.T0)
        v["before"] = before(f, MC.ref(row))
        c = {"g1": q["q1"], "g2": q["q4"], "g3": bool(q["q2"] and q["q5"]),
             "g4": bool(v["vo_min_v"] >= rv["vo_min_v"] - VO_TOL_MV * 1e-3), "g8": v["before"]["same"]}
        rows[row] = {"w": {k: v[k] for k in v if k != "reapp"}, "ref": {k: rv[k] for k in rv if k != "reapp"},
                     "w_reapp": v["reapp"], "criteria": c}
    return rows


def stage2():
    rows = {}
    for name in MC.STAGE2:
        f = COS / f"run_w_{name}.json"
        if not f.exists():
            rows[name] = None; continue
        h, ref = A36.row(name, f), A36.row(name, MC.ref(name))
        h["before"] = before(f, MC.ref(name))
        c = {"g8": h["before"]["same"]}
        if name in A36.SKIP:
            c["g7"] = bool(h["q1_run"] and abs(h["vmin_a"] - ref["vmin_a"]) <= 1.0 and abs(h["vmax_a"] - ref["vmax_a"]) <= 1.0)
        else:
            t0 = t_dist(json.loads(f.read_text())["cfg"])
            h["delay_min_ns"], ref["delay_min_ns"] = delay_min(f, t0), delay_min(MC.ref(name), t0)
            h["held"] = held(f, t0)
            i_lim = ref["peak_whole"] + 2.0 if name in A36.ITEM2 else A36.A34.I_LIM
            c["g5"] = bool(A36.A34_limits(h, i_lim) and (h["n_mod"] == 1 or h["f3"]))
            tol = 10.0 if name in WIDE else PK_TOL
            c["g6"] = bool(h["post_pk"] <= ref["post_pk"] + tol and h["new_after"] <= ref["new_after"]
                           and (name in WIDE or abs(h["vo_ext_mv"]) <= abs(ref["vo_ext_mv"]) + 1.0))
        rows[name] = {"w": h, "ref": ref, "ref_record": str(MC.ref(name).relative_to(TA)), "criteria": c}
    return rows


def main():
    res = {"identity": identity(), "stage1": stage1(), "stage2": stage2()}
    main_c = {"g0": res["identity"]["g0"]}
    for st, keys in (("stage1", ("g1", "g2", "g3", "g4", "g8")), ("stage2", ("g5", "g6", "g7", "g8"))):
        done = [x for x in res[st].values() if x]
        for k in keys:
            have = [x["criteria"][k] for x in done if k in x["criteria"]]
            if have:
                main_c[k] = all(have) and main_c.get(k, True)
        res[f"{st}_complete"] = len(done) == len(res[st])
    ctl = HERE / "a244_control.json"
    if ctl.exists():
        c = json.loads(ctl.read_text())
        res["control"] = {r: {"criteria": {"c1": x["c1"]}} for r, x in c.items() if isinstance(x, dict)}
        main_c["c1"] = c["all_scatter"]
    res["criteria_main"] = main_c
    (HERE / "a244_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["stage1"].items():
        if not x:
            print(f"{row:12s} missing"); continue
        v, r = x["w"], x["ref"]
        print(f"{row:12s} pk {v['peak_after_t0']:.1f} (A240 {r['peak_after_t0']:.1f}) A, Vo {v['vo_min_v']:.4f}..{v['vo_max_v']:.4f} "
              f"(A240 {r['vo_min_v']:.4f}..{r['vo_max_v']:.4f}), late {v['late_after_t0']} ({r['late_after_t0']}), "
              f"held {v['held']} | " + "".join(k for k, ok in x["criteria"].items() if not ok))
    for n, x in res["stage2"].items():
        if not x:
            print(f"{n:14s} missing"); continue
        h, r = x["w"], x["ref"]
        if n in A36.SKIP:
            print(f"{n:14s} valleys {h['vmin_a']:+.2f}/{h['vmax_a']:+.2f} (ref {r['vmin_a']:+.2f}/{r['vmax_a']:+.2f}) | {x['criteria']}")
        else:
            print(f"{n:14s} post {h['post_pk']:.1f} (ref {r['post_pk']:.1f}) A | Vo {h['vo_ext_mv']:+.1f} ({r['vo_ext_mv']:+.1f}) mV | "
                  f"held {h['held']} | oracle {h['oracle_after']} (ref {r['oracle_after']}) | {x['criteria']}")
    print("identity", res["identity"], "main", res["criteria_main"])


if __name__ == "__main__":
    main()
