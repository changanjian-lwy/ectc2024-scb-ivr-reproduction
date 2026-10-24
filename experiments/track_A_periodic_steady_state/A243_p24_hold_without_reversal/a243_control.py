"""A243 control (BOUNDARY Section 5): each missed row at k 0 / 2 / 4 of T / 6, arm r (reference cfg) against arm b
(holds 0.0), with a236_analyze.row's measures; c1 compares arm b's worst over the positions with arm r's worst.
f_N75 uses A232's existing positions (f_N75_k0 / k2 / k4 and A243's run_b_ of them).
  python3 a243_control.py -> a243_control.json"""
from __future__ import annotations

import json

from a243_analyze import A36, COS, HERE, MC, PK_TOL, WIDE, _load

MCC = _load("a243_make_ctrl_cfgs", HERE / "make_ctrl_cfgs.py")


def files(row):
    if row == "f_N75":
        return ({k: MC.ref(f"f_N75_k{k}") for k in (0, 2, 4)},
                {k: COS / f"run_b_f_N75_k{k}.json" for k in (0, 2, 4)})
    r = {0: MC.ref(row)} | {k: COS / f"run_cr_{row}_k{k}.json" for k in MCC.KS}
    b = {0: COS / f"run_b_{row}.json"} | {k: COS / f"run_cb_{row}_k{k}.json" for k in MCC.KS}
    return r, b


def control(row):
    name = "f_N75_k0" if row == "f_N75" else row
    fr, fb = files(row)
    if not all(f.exists() for f in list(fr.values()) + list(fb.values())):
        return None
    m = {arm: {k: A36.row(name, f) for k, f in fs.items()} for arm, fs in (("r", fr), ("b", fb))}
    worst = {arm: {"post_pk": max(x["post_pk"] for x in m[arm].values()),
                   "peak_whole": max(x["peak_whole"] for x in m[arm].values()),
                   "new_after": max(x["new_after"] for x in m[arm].values()),
                   "vo_abs_mv": max(abs(x["vo_ext_mv"]) for x in m[arm].values())} for arm in m}
    wr, wb = worst["r"], worst["b"]
    tol = 10.0 if name in WIDE else PK_TOL
    c1 = bool(wb["post_pk"] <= wr["post_pk"] + tol and wb["new_after"] <= wr["new_after"]
              and (name not in A36.ITEM2 or wb["peak_whole"] <= wr["peak_whole"] + 2.0)
              and (name in WIDE or wb["vo_abs_mv"] <= wr["vo_abs_mv"] + 1.0))
    lim = {k: bool(A36.A34_limits(x, wr["peak_whole"] + 2.0 if name in A36.ITEM2 else A36.A34.I_LIM))
           for k, x in m["b"].items()}
    keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv", "oracle_after")
    return {"positions": {arm: {k: {q: x[q] for q in keep} for k, x in m[arm].items()} for arm in m},
            "worst": worst, "c1": c1, "b_limits": lim}


def main():
    res = {row: control(row) for row in ("f_N75",) + MCC.ROWS}
    res["all_scatter"] = all(x and x["c1"] for x in res.values())
    (HERE / "a243_control.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res.items():
        if row == "all_scatter" or not x:
            print(row, x if row == "all_scatter" else "missing"); continue
        p = x["positions"]
        print(f"{row:11s} post r {[round(p['r'][k]['post_pk'], 1) for k in p['r']]} b {[round(p['b'][k]['post_pk'], 1) for k in p['b']]}"
              f" | whole r/b {x['worst']['r']['peak_whole']:.1f}/{x['worst']['b']['peak_whole']:.1f}"
              f" | NEW r {[p['r'][k]['new_after'] for k in p['r']]} b {[p['b'][k]['new_after'] for k in p['b']]}"
              f" | |Vo| r/b {x['worst']['r']['vo_abs_mv']:.1f}/{x['worst']['b']['vo_abs_mv']:.1f} | c1 {x['c1']} lim {all(x['b_limits'].values())}")


if __name__ == "__main__":
    main()
