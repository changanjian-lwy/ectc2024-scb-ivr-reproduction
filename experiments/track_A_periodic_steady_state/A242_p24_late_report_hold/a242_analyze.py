"""A242 analysis (BOUNDARY Section 2), A241's measures on arm l: stage 1 = A240's rows against A240's records
(a240_analyze.one), stage 2 = A236's rows and A237's re-applications against their references (a236_analyze.row and
its criteria); each row's shortest predictive turn-on delay per phase after the event and the late reports the hold
kept (turn-ons with lo_pos and not early); the identity row and the unit / regression logs. Missing rows are listed.
  python3 a242_analyze.py -> a242_summary.json"""
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


MC = _load("a242_make_cfgs", HERE / "make_cfgs.py")
A41 = _load("a241_analyze", TA / "A241_p24_dt_pred_fall_limit" / "a241_analyze.py")
A40, A36, delay_min = A41.A40, A41.A36, A41.delay_min
UNIT_N, PK_TOL, VO_TOL_MV = 121, 2.0, 5.0
WIDE = A36.WIDE + MC.A37_ROWS


def held(f, t0):
    """Late reports the hold kept: turn-ons from t0 with lo_pos and not early (every module)."""
    r = json.loads(Path(f).read_text())
    return sum(1 for md in [r] + r.get("modules_rest", []) for x in md["turnons_last"]
               if x["t_s"] >= t0 and x.get("lo_pos") and x.get("early") is False)


def identity():
    logs = PROJECT / "tmp" / "logs"
    u = re.findall(r"TESTS=(\d+) PASS=(\d+) FAIL=(\d+)", (logs / "a242_unit.log").read_text())
    n_pass, n_fail = sum(int(p) for _, p, _ in u), sum(int(f) for _, _, f in u)
    reg = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a242_reg_{k}.log").read_text())) for k in ("quick", "full")}
    o = COS / f"run_o_{MC.IDENT}.json"
    same = A36.same(o, MC.ref(MC.IDENT)) if o.exists() else None
    return {"unit_pass": n_pass, "unit_fail": n_fail, "regression": reg, "o_row": same,
            "g0": bool(n_pass == UNIT_N and n_fail == 0 and all(reg.values()) and same and all(same.values()))}


def stage1():
    rows = {}
    for row in MC.STAGE1:
        f = COS / f"run_l_{row}.json"
        if not f.exists():
            rows[row] = None; continue
        b, fk = row.split("_")[1], float(row.split("_")[2][:-1])
        v, q = A40.one(f, b, fk)
        rv, _ = A40.one(MC.ref(row), b, fk)
        v["delay_min_ns"], rv["delay_min_ns"] = delay_min(f, A40.T0), delay_min(MC.ref(row), A40.T0)
        v["held_late"] = held(f, A40.T0)
        c = {"g1": q["q1"], "g2": q["q4"], "g3": bool(q["q2"] and q["q5"]),
             "g4": bool(v["vo_min_v"] >= rv["vo_min_v"] - VO_TOL_MV * 1e-3)}
        rows[row] = {"l": {k: v[k] for k in v if k != "reapp"}, "ref": {k: rv[k] for k in rv if k != "reapp"},
                     "l_reapp": v["reapp"], "criteria": c}
    return rows


def stage2():
    rows = {}
    for name in MC.STAGE2:
        f = COS / f"run_l_{name}.json"
        if not f.exists():
            rows[name] = None; continue
        h, ref = A36.row(name, f), A36.row(name, MC.ref(name))
        c = {}
        if name in A36.SKIP:
            c["g7"] = bool(h["q1_run"] and abs(h["vmin_a"] - ref["vmin_a"]) <= 1.0 and abs(h["vmax_a"] - ref["vmax_a"]) <= 1.0)
        else:
            cfg = json.loads(f.read_text())["cfg"]
            t0 = (cfg.get("line_step") or cfg["load_step"])["t_us"] * 1e-6
            h["delay_min_ns"], ref["delay_min_ns"] = delay_min(f, t0), delay_min(MC.ref(name), t0)
            h["held_late"] = held(f, t0)
            i_lim = ref["peak_whole"] + 2.0 if name in A36.ITEM2 else A36.A34.I_LIM
            c["g5"] = bool(A36.A34_limits(h, i_lim) and (h["n_mod"] == 1 or h["f3"]))
            tol = 10.0 if name in WIDE else PK_TOL
            c["g6"] = bool(h["post_pk"] <= ref["post_pk"] + tol and h["new_after"] <= ref["new_after"]
                           and (name in WIDE or abs(h["vo_ext_mv"]) <= abs(ref["vo_ext_mv"]) + 1.0))
        rows[name] = {"l": h, "ref": ref, "ref_record": str(MC.ref(name).relative_to(TA)), "criteria": c}
    return rows


def main():
    res = {"identity": identity(), "stage1": stage1(), "stage2": stage2()}
    main_c = {"g0": res["identity"]["g0"]}
    for st, keys in (("stage1", ("g1", "g2", "g3", "g4")), ("stage2", ("g5", "g6", "g7"))):
        done = [x for x in res[st].values() if x]
        for k in keys:
            have = [x["criteria"][k] for x in done if k in x["criteria"]]
            main_c[k] = all(have) if have else None
        res[f"{st}_complete"] = len(done) == len(res[st])
    res["criteria_main"] = main_c
    (HERE / "a242_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["stage1"].items():
        if not x:
            print(f"{row:12s} missing"); continue
        v, r = x["l"], x["ref"]
        print(f"{row:12s} pk {v['peak_after_t0']:.1f} (A240 {r['peak_after_t0']:.1f}) A, Vo {v['vo_min_v']:.4f}..{v['vo_max_v']:.4f} "
              f"(A240 {r['vo_min_v']:.4f}..{r['vo_max_v']:.4f}), delay min {[round(d, 1) for d in v['delay_min_ns']]} "
              f"(A240 {[round(d, 1) for d in r['delay_min_ns']]}), late {v['late_after_t0']} ({r['late_after_t0']}), "
              f"held {v['held_late']} | " + "".join(k for k, ok in x["criteria"].items() if not ok))
    for n, x in res["stage2"].items():
        if not x:
            print(f"{n:14s} missing"); continue
        h, r = x["l"], x["ref"]
        if n in A36.SKIP:
            print(f"{n:14s} valleys {h['vmin_a']:+.2f}/{h['vmax_a']:+.2f} (ref {r['vmin_a']:+.2f}/{r['vmax_a']:+.2f}) | {x['criteria']}")
        else:
            print(f"{n:14s} post {h['post_pk']:.1f} (ref {r['post_pk']:.1f}) A | Vo {h['vo_ext_mv']:+.1f} ({r['vo_ext_mv']:+.1f}) mV | "
                  f"held {h['held_late']} | oracle {h['oracle_after']} (ref {r['oracle_after']}) | {x['criteria']}")
    print("identity", res["identity"], "main", res["criteria_main"])


if __name__ == "__main__":
    main()
