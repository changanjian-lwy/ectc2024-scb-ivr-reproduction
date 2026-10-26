"""A254 analysis (BOUNDARY Section 2): each row with the limit against its reference (the final configuration: A246
run_h_ / run_ch_, A251 run_h_ on A245's start-ups).
- stage 1 (A240's train, A246's position rows) through A246's one1 (A240's q0-q5);
- stage 2 through A236's row (skip rows: the valley range);
- start-ups through A245's one and A251's start_crit (A245's g1-g3);
- identity: A246's same (sections, edges, late fires, overlaps, peak) and the limit's fires per row.
  python3 a254_analyze.py -> a254_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a254_make_cfgs", HERE / "make_cfgs.py")
A51 = _load("a251_analyze", TA / "A251_p24_hold_after_startup" / "a251_analyze.py")
A46, A45, A36 = A51.A46, A51.A45, A51.A36
I_LIM, PK_TOL, VO_TOL, VO_TOL_MHZ, DEV_TOL = 200.0, 2.0, 1e-3, 2e-3, 0.2


def fires(d):
    return [x for md in [d] + d.get("modules_rest", []) for x in md.get("ocp_fires", [])]


def ref_of(row):
    return TA / json.loads((HERE / "cosim" / f"cfg_l_{row}.json").read_text())["note"].split()[1].replace("cfg_", "run_")


def stage1(row, f, r):
    base = row[:-3] if row[-3:-1] == "_k" else row         # a position row: p_<board>_<f>k_k<k>
    (v, q), (h, qh) = A46.one1(f, base), A46.one1(r, base)
    c = {"p4": bool(v["peak_after_t0"] <= max(h["peak_after_t0"], I_LIM) + PK_TOL
                    and v["vo_min_v"] >= h["vo_min_v"] - (VO_TOL_MHZ if base.endswith("_1000k") else VO_TOL)
                    and all(q[k] for k in ("q2", "q3", "q5") if qh[k]))}
    if base.endswith("_1000k"):
        c["p2"] = bool(q["q1"] and q["q2"])
    keep = ("peak_after_t0", "peak_whole", "vo_min_v")
    return {"o": {k: v[k] for k in keep} | {"q": q}, "h": {k: h[k] for k in keep} | {"q": qh}, "criteria": c}


def stage2(row, f, r):
    v, h = A36.row(row, f), A36.row(row, r)
    if row in A36.SKIP:
        c = {"p3": bool(abs(v["vmin_a"] - h["vmin_a"]) <= 1.0 and abs(v["vmax_a"] - h["vmax_a"]) <= 1.0)}
        keep = ("vmin_a", "vmax_a")
    else:
        c = {"p3": bool(v["peak_whole"] <= I_LIM and v["new_after"] <= h["new_after"]
                        and v["post_pk"] <= max(h["post_pk"], I_LIM) + PK_TOL
                        and abs(v["vo_ext_mv"]) <= abs(h["vo_ext_mv"]) + 2.0)}
        keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv")
    return {"o": {k: v[k] for k in keep}, "h": {k: h[k] for k in keep}, "criteria": c}


def start(row, f, r):
    v, h = A45.one(f), A45.one(r)
    cv, ch = A51.start_crit(v, h), A51.start_crit(h, h)
    c = {"p5": bool((all(cv.values()) or not all(ch.values())) and v["peak_a"] <= h["peak_a"] + PK_TOL
                    and v["dev_end_v"] <= h["dev_end_v"] + DEV_TOL)}
    keep = ("dev_end_v", "peak_a", "vds_max_v", "vo_min", "vo_max", "late", "new")
    return {"o": {k: v[k] for k in keep} | {"crit": cv}, "h": {k: h[k] for k in keep}, "criteria": c}


def one(row):
    f, r = HERE / "cosim" / f"run_l_{row}.json", ref_of(row)
    if not f.exists():
        return None
    fl, same = fires(json.loads(f.read_text())), A46.same(f, r)
    out = {"fires": len(fl), "fire_i_a": sorted(round(x["i_a"], 1) for x in fl)[-5:], "same": same}
    if row in MC.IDENT:
        out["criteria"] = {"p1": bool(same and not fl)}
        return out
    kind = stage1 if row.startswith("p_") else start if row in A51.MC.START else stage2
    out |= kind(row, f, r)
    out["criteria"]["p1"] = bool(same or fl)                 # no fire: the reference bit for bit
    return out


def main():
    res = {"rows": {row: one(row) for row in MC.rows()}}
    done = [x for x in res["rows"].values() if x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done if k in x["criteria"]) for k in ("p1", "p2", "p3", "p4", "p5")}
    res["criteria"]["complete"] = len(done) == len(res["rows"])
    (HERE / "a254_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if not x:
            continue
        o, h = x.get("o", {}), x.get("h", {})
        key = next((k for k in ("peak_whole", "peak_a", "vmin_a") if k in o), None)
        print(f"{row:16s} fires {x['fires']:4d} same {str(x['same']):5s} "
              + (f"{key} {o[key]:.1f} (h {h[key]:.1f}) " if key else "")
              + " ".join(k for k, v in x["criteria"].items() if not v))
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
