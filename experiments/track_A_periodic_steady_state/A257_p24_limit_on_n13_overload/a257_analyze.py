"""A257 analysis (BOUNDARY Section 2). Per N13 row: n0 arm s = arm h before s's first fire (turn-ons and high-offs);
n1 arm h through A236's row (whole peak, V_DS), Vo over the last 20 us and A256's ladder deviation after the event;
n2 arm s against arm h through A256's s2 test.
  python3 a257_analyze.py -> a257_summary.json"""
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


A56 = _load("a256_analyze", TA / "A256_p24_limit_suspends_on_overload" / "a256_analyze.py")
A36, dev_max = A56.A36, A56.dev_max
ROWS = ("o125_N13", "lp48_N13")
I_LIM, PK_TOL, VO_TOL_MV, DEV_V, DEV_TOL, V_DS, VO_BAND, T_TAIL = 200.0, 2.0, 2.0, 1.0, 0.2, 40.0, 0.01, 20e-6


def before(d, t):
    return {k: [x for x in d[k] if x["t_s"] < t] for k in ("turnons_last", "highoffs_last")}


def one(row):
    fh, fs = HERE / "cosim" / f"run_h_{row}.json", HERE / "cosim" / f"run_s_{row}.json"
    if not (fh.exists() and fs.exists()):
        return None
    dh, ds = json.loads(fh.read_text()), json.loads(fs.read_text())
    c = dh["cfg"]
    t0 = (c.get("load_step") or c.get("line_step"))["t_us"] * 1e-6
    fires = ds.get("ocp_fires", [])
    t1 = min((x["t_s"] for x in fires), default=None)
    n0 = all(A36.same(fs, fh).values()) if t1 is None else before(ds, t1) == before(dh, t1)
    h, s = A36.row("k_N0", fh), A36.row("k_N0", fs)
    tail = [q["vo"] for q in dh["sections"] if q["t_s"] >= dh["sections"][-1]["t_s"] - T_TAIL]
    keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv", "vds_v")
    oh = {k: h[k] for k in keep} | {"dev_max_v": dev_max(dh, t0), "vo_tail_v": [min(tail), max(tail)]}
    os_ = {k: s[k] for k in keep} | {"dev_max_v": dev_max(ds, t0)}
    n1 = bool(oh["peak_whole"] <= I_LIM and oh["dev_max_v"] <= DEV_V and oh["vds_v"] <= V_DS
              and all(abs(v - 1.0) <= VO_BAND for v in tail))
    n2 = bool(os_["peak_whole"] <= max(oh["peak_whole"], I_LIM) + PK_TOL and os_["post_pk"] <= max(oh["post_pk"], I_LIM) + PK_TOL
              and os_["new_after"] <= oh["new_after"] and abs(os_["vo_ext_mv"]) <= abs(oh["vo_ext_mv"]) + VO_TOL_MV
              and os_["dev_max_v"] <= max(oh["dev_max_v"], DEV_V) + DEV_TOL)
    return {"fires": len(fires), "t_first_fire_us": t1 and t1 * 1e6, "susp": ds.get("ocp_susp", []),
            "h": oh, "s": os_, "criteria": {"n0": bool(n0), "n1": n1, "n2": n2}}


def main():
    res = {"rows": {row: one(row) for row in ROWS}}
    done = [x for x in res["rows"].values() if x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done) for k in ("n0", "n1", "n2")}
    res["criteria"]["complete"] = len(done) == len(ROWS)
    (HERE / "a257_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if x:
            h, s = x["h"], x["s"]
            print(f"{row:9s} fires {x['fires']:3d} susp {len(x['susp'])} peak h {h['peak_whole']:.1f} s {s['peak_whole']:.1f} A "
                  f"dev h {h['dev_max_v']:.2f} s {s['dev_max_v']:.2f} V Vo ext h {h['vo_ext_mv']:.1f} s {s['vo_ext_mv']:.1f} mV "
                  f"V_DS {h['vds_v']:.1f} V NEW h {h['new_after']} s {s['new_after']} " + str(x["criteria"]))
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
