"""A249 analysis (BOUNDARY Section 2): each fixed-delay arm (s, o) against the row's final-configuration record.
Stage 1 (A240's train): A246's one1 (A240's peak after 300 us, Vo's minimum, q4); stage 2: A236's row (post-event
peak, NEW, Vo's extreme, limits); start-up: A245's one (every rail against Vin / 4 at the end, Vo after mode P).
Every run: the phases 2-4 dt_pred at the end against its dt_fix_ns (c0), and the learned turn-ons of phases 2-4 with
V_DS > HARD_V at the actual turn-on, 20 us or more after mode P (hard, as A245; reported).
  python3 a249_analyze.py -> a249_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a249_make_cfgs", HERE / "make_cfgs.py")
A46 = _load("a246_analyze", TA / "A246_p24_held_report_floor" / "a246_analyze.py")
A45 = _load("a245_analyze", TA / "A245_p24_reverse_conduction_delay" / "a245_analyze.py")
A36 = A46.A36
Q4_N0, PK_TOL, VO_TOL, LSB_NS, HARD_V = 171.5, 2.0, 1e-3, 0.03125, 6.0
STAGE1 = ("p_N0_100k", "p_N0_100k_k2", "p_N0_100k_k4", "p_N0_60k", "p_N75_100k", "p_S75h_100k")
STAGE2 = ("a_S75h_d20", "f_N75_k4")
START = ("u_S75h_30",)


def hard(f):
    d = json.loads(Path(f).read_text())
    n = 0
    for md in [d] + d.get("modules_rest", []):
        t0 = (md.get("t_mode_p_s") or d["t_mode_p_s"]) + 20e-6
        n += sum(1 for x in md["turnons_last"] if x["phase"] > 1 and x["how"] == 0 and x["t_s"] > t0
                 and x.get("vds_act_v", 0.0) > HARD_V)
    return n


def fixed_ok(f):
    d = json.loads(Path(f).read_text())
    want = d["cfg"]["dt_fix_ns"]
    got = d["dt_pred_final_ns"][1:]
    return bool(all(abs(a - b) <= LSB_NS for a, b in zip(got, want))), got


def stage1_row(row, f):
    base = row.replace("_k2", "").replace("_k4", "")
    v, q = A46.one1(f, base)
    return {"peak_after_t0": v["peak_after_t0"], "vo_min_v": v["vo_min_v"], "q4": q["q4"]}


def compare(row, arm):
    f, ref = COS / f"run_{arm}_{row}.json", MC.REFS[row]
    if not f.exists():
        return None
    ok0, got = fixed_ok(f)
    out = {"dt_final_ns": got, "c0": ok0, "hard": hard(f), "hard_ref": hard(ref)}
    if row in STAGE1:
        h, r = stage1_row(row, f), stage1_row(row, ref)
        out |= {"h": h, "ref": r}
        if row.startswith("p_N0_100k"):
            out["c1"] = bool(h["peak_after_t0"] <= Q4_N0)
        else:
            out["c2"] = bool(h["peak_after_t0"] <= r["peak_after_t0"] + PK_TOL and h["vo_min_v"] >= r["vo_min_v"] - VO_TOL)
    elif row in STAGE2:
        h, r = A36.row(row, f), A36.row(row, ref)
        tol = 10.0 if row in A36.ITEM2 else PK_TOL
        keep = ("post_pk", "new_after", "vo_ext_mv", "peak_whole")
        out |= {"h": {k: h.get(k) for k in keep}, "ref": {k: r.get(k) for k in keep}}
        out["c2"] = bool(h["post_pk"] <= r["post_pk"] + tol and h["new_after"] <= r["new_after"]
                         and abs(h["vo_ext_mv"]) <= abs(r["vo_ext_mv"]) + 1.0)
    else:
        h, r = A45.one(f), A45.one(ref)
        keep = ("dev_end_v", "rails_end_v", "vo_min", "vo_max", "peak_a", "vds_max_v", "new", "late")
        out |= {"h": {k: h[k] for k in keep}, "ref": {k: r[k] for k in keep}}
        out["c2"] = bool(h["dev_end_v"] <= 1.0 and h["vo_min"] >= min(0.99, r["vo_min"]))
    return out


def main():
    res = {arm: {row: compare(row, arm) for row in MC.ROWS} for arm in ("s", "o")}
    crit = {}
    for arm, rows in res.items():
        done = [x for x in rows.values() if x]
        crit[arm] = {k: all(x[k] for x in done if k in x) for k in ("c0", "c1", "c2")}
        crit[arm]["complete"] = len(done) == len(rows)
    res["criteria"] = crit
    (HERE / "a249_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for arm in ("s", "o"):
        for row, x in res[arm].items():
            if not x:
                continue
            h, r = x["h"], x["ref"]
            key = ("peak_after_t0", "vo_min_v") if row in STAGE1 else ("post_pk", "new_after") if row in STAGE2 else ("dev_end_v", "vo_min")
            print(f"{arm} {row:14s} " + " ".join(f"{k} {h[k]:.4g} (ref {r[k]:.4g})" for k in key)
                  + f" hard {x['hard']} (ref {x['hard_ref']}) | " + " ".join(k for k in ("c0", "c1", "c2") if k in x and not x[k]))
    print("criteria", crit)


if __name__ == "__main__":
    main()
