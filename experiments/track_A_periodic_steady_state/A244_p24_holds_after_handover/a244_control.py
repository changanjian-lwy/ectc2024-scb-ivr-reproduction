"""A244 control (BOUNDARY Section 4): each stage-2 miss at k 0 / 2 / 4 of T / 6, arm r (reference cfg; A244's run_cr_
or else A243's) against arm w, with a236_analyze.row's measures and A243's c1. A232's step families (f_N75 / f_N0) use
their rows as the positions.
  python3 a244_control.py -> a244_control.json"""
from __future__ import annotations

import json

from a244_analyze import A36, COS, HERE, MC, PK_TOL, WIDE, _load

MCC = _load("a244_make_ctrl_cfgs", HERE / "make_ctrl_cfgs.py")
C43 = MCC.C43 / "cosim"


def files(row, fam):
    if fam:
        ks = [k for k in (0, 2, 4) if f"{row}_k{k}" in MC.STAGE2]
        return ({k: MC.ref(f"{row}_k{k}") for k in ks}, {k: COS / f"run_w_{row}_k{k}.json" for k in ks})
    r = {0: MC.ref(row)} | {k: (COS if (COS / f"run_cr_{row}_k{k}.json").exists() else C43) / f"run_cr_{row}_k{k}.json"
                            for k in MCC.KS}
    w = {0: COS / f"run_w_{row}.json"} | {k: COS / f"run_cw_{row}_k{k}.json" for k in MCC.KS}
    return r, w


def control(row, fam):
    """row: a missed row, or with fam its step family (f_N75), whose rows are the positions."""
    name = f"{row}_k0" if fam else row
    fr, fw = files(row, fam)
    if not all(f.exists() for f in list(fr.values()) + list(fw.values())):
        return None
    m = {arm: {k: A36.row(name, f) for k, f in fs.items()} for arm, fs in (("r", fr), ("w", fw))}
    worst = {arm: {"post_pk": max(x["post_pk"] for x in m[arm].values()),
                   "peak_whole": max(x["peak_whole"] for x in m[arm].values()),
                   "new_after": max(x["new_after"] for x in m[arm].values()),
                   "vo_abs_mv": max(abs(x["vo_ext_mv"]) for x in m[arm].values())} for arm in m}
    wr, ww = worst["r"], worst["w"]
    tol = 10.0 if name in WIDE else PK_TOL
    c1 = bool(ww["post_pk"] <= wr["post_pk"] + tol and ww["new_after"] <= wr["new_after"]
              and (name not in A36.ITEM2 or ww["peak_whole"] <= wr["peak_whole"] + 2.0)
              and (name in WIDE or ww["vo_abs_mv"] <= wr["vo_abs_mv"] + 1.0))
    keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv", "oracle_after")
    return {"positions": {arm: {k: {q: x[q] for q in keep} for k, x in m[arm].items()} for arm in m},
            "worst": worst, "c1": c1}


def main():
    keys = {MCC.family(r) or r: bool(MCC.family(r)) for r in MCC.missed()}
    res = {row: control(row, fam) for row, fam in keys.items()}
    res["all_scatter"] = all(x and x["c1"] for x in res.values())
    (HERE / "a244_control.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res.items():
        if row == "all_scatter" or not x:
            print(row, x if row == "all_scatter" else "missing"); continue
        p = x["positions"]
        print(f"{row:14s} post r {[round(p['r'][k]['post_pk'], 1) for k in p['r']]} w {[round(p['w'][k]['post_pk'], 1) for k in p['w']]}"
              f" | NEW r {[p['r'][k]['new_after'] for k in p['r']]} w {[p['w'][k]['new_after'] for k in p['w']]}"
              f" | |Vo| r/w {x['worst']['r']['vo_abs_mv']:.1f}/{x['worst']['w']['vo_abs_mv']:.1f} | c1 {x['c1']}")


if __name__ == "__main__":
    main()
