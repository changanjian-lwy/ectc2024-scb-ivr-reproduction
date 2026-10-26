"""A253 analysis (BOUNDARY Section 2): each row with the limit against the final configuration's record (A246 run_h_):
stage 1 through A246's one1 (A240's q1-q5), stage 2 through A236's row (A234's limits); identity rows through A246's
same (turn-ons, turn-offs, sections, late fires, overlaps, peak); the limit's fires per row.
  python3 a253_analyze.py -> a253_summary.json"""
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


MC = _load("a253_make_cfgs", HERE / "make_cfgs.py")
A46 = _load("a246_analyze", TA / "A246_p24_held_report_floor" / "a246_analyze.py")
A36, REF = A46.A36, TA / "A246_p24_held_report_floor" / "cosim"
I_LIM, VO_TOL_MV, PK_TOL = 200.0, 2.0, 2.0


def fires(f):
    d = json.loads(Path(f).read_text())
    return [x for md in [d] + d.get("modules_rest", []) for x in md.get("ocp_fires", [])]


def one(row):
    f, r = HERE / "cosim" / f"run_o_{row}.json", REF / f"run_h_{row}.json"
    if not f.exists():
        return None
    fl = fires(f)
    out = {"fires": len(fl), "fire_i_a": [round(x["i_a"], 1) for x in fl[:20]], "same": A46.same(f, r)}
    if row in MC.IDENT:
        out["criteria"] = {"o1": bool(out["same"] and not fl)}
    elif row.startswith("p_"):
        (v, q), (h, qh) = A46.one1(f, row), A46.one1(r, row)
        keep = ("peak_after_t0", "peak_whole", "vo_min_v")
        out |= {"o": {k: v[k] for k in keep} | {"q": q}, "h": {k: h[k] for k in keep} | {"q": qh}}
        out["criteria"] = {"o2": bool(q["q1"] and q["q2"]),
                           "o4": bool(q["q3"] and v["vo_min_v"] >= h["vo_min_v"] - VO_TOL_MV * 1e-3)}
    else:
        v, h = A36.row(row, f), A36.row(row, r)
        keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv")
        out |= {"o": {k: v[k] for k in keep}, "h": {k: h[k] for k in keep}}
        out["criteria"] = {"o3": bool(v["peak_whole"] <= I_LIM and v["new_after"] <= h["new_after"]
                                      and v["post_pk"] <= max(h["post_pk"], I_LIM) + PK_TOL
                                      and abs(v["vo_ext_mv"]) <= abs(h["vo_ext_mv"]) + VO_TOL_MV)}
    return out


def main():
    res = {"rows": {row: one(row) for row in MC.ACT + MC.IDENT}}
    done = [x for x in res["rows"].values() if x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done if k in x["criteria"]) for k in ("o1", "o2", "o3", "o4")}
    res["criteria"]["complete"] = len(done) == len(res["rows"])
    (HERE / "a253_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if not x:
            continue
        o, h = x.get("o", {}), x.get("h", {})
        print(f"{row:14s} fires {x['fires']:3d} same {x['same']} "
              + (f"peak {o['peak_whole']:.1f} (h {h['peak_whole']:.1f}) " if o else "")
              + (f"Vo min {o['vo_min_v']:.4f} (h {h['vo_min_v']:.4f}) " if "vo_min_v" in o else "")
              + (f"Vo ext {o['vo_ext_mv']:.1f} (h {h['vo_ext_mv']:.1f}) mV" if "vo_ext_mv" in o else "")
              + " " + " ".join(k for k, v in x["criteria"].items() if not v))
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
