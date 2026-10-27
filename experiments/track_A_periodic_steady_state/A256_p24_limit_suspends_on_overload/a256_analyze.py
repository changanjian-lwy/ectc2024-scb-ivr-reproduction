"""A256 analysis (BOUNDARY Section 2). Each run with the limit + n_susp against:
- IDENT rows: A254's record (A246's same: sections, edges, late fires, overlaps, peak);
- the other rows: the final configuration (A246 run_h_, A255 run_h_o125_) through A236's row (A253's o3) and the
  ladder's deviation max |rail - Vin / 4| on every module after the row's event; 1 MHz rows through A246's one1.
  python3 a256_analyze.py -> a256_summary.json"""
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


MC = _load("a256_make_cfgs", HERE / "make_cfgs.py")
A54 = _load("a254_analyze", TA / "A254_p24_peak_limit_measured_level" / "a254_analyze.py")
A46, A36 = A54.A46, A54.A36
A46C, A55C = TA / "A246_p24_held_report_floor" / "cosim", TA / "A255_p24_overload_on_2p2nh" / "cosim"
I_LIM, PK_TOL, VO_TOL_MV, DEV_V, DEV_TOL = 200.0, 2.0, 2.0, 1.0, 0.2
T_EVT = {"m4_s_p250": 400e-6}                       # the event's time; others: their cfg's load_step / line_step


def t_event(row):
    c = json.loads((HERE / "cosim" / f"cfg_s_{row}.json").read_text())
    for k in ("load_step", "line_step"):
        if k in c:
            return c[k]["t_us"] * 1e-6
    return T_EVT.get(row, 0.0)


def dev_max(d, t0):
    out = 0.0
    for md in [d] + d.get("modules_rest", []):
        for s in md.get("sections", []):
            if s["t_s"] < t0:
                continue
            v = s["vin_v"] / 4
            rails = (s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1], s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2])
            out = max(out, max(abs(r - v) for r in rails))
    return out


def one(row):
    f = HERE / "cosim" / f"run_s_{row}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    mods = [d] + d.get("modules_rest", [])
    out = {"fires": sum(len(md.get("ocp_fires", [])) for md in mods),
           "susp": [x for md in mods for x in md.get("ocp_susp", [])][:6]}
    if row in MC.IDENT:
        out["criteria"] = {"s1": A46.same(f, TA / "A254_p24_peak_limit_measured_level" / "cosim" / f"run_l_{row}.json")}
        if row.endswith("_1000k"):
            v, q = A46.one1(f, row)
            out["o"] = {"peak_whole": v["peak_whole"], "vo_min_v": v["vo_min_v"]}
            out["criteria"]["s4"] = bool(q["q1"] and q["q2"])
        return out
    r = (A55C / f"run_h_{row}.json") if row in MC.O125 else (A46C / f"run_h_{row}.json")
    name = "k_N0" if row in MC.O125 else row                 # A236's row(): the o125 rows are k_N0's kind
    v, h = A36.row(name, f), A36.row(name, r)
    t0 = t_event(row)
    dv, dh = dev_max(d, t0), dev_max(json.loads(r.read_text()), t0)
    keep = ("post_pk", "peak_whole", "new_after", "vo_ext_mv")
    out |= {"o": {k: v[k] for k in keep} | {"dev_max_v": dv}, "h": {k: h[k] for k in keep} | {"dev_max_v": dh}}
    ok3 = bool(v["peak_whole"] <= max(h["peak_whole"], I_LIM) + PK_TOL and v["new_after"] <= h["new_after"]
               and v["post_pk"] <= max(h["post_pk"], I_LIM) + PK_TOL and abs(v["vo_ext_mv"]) <= abs(h["vo_ext_mv"]) + VO_TOL_MV)
    key = "s2" if (row in MC.O125 or row in ("k_N0", "m4_s_p250")) else "s3"
    out["criteria"] = {key: bool(ok3 and dv <= max(dh, DEV_V) + DEV_TOL)}
    return out


def main():
    res = {"rows": {row: one(row) for row in MC.CHANGE + MC.O125 + MC.IDENT}}
    done = [x for x in res["rows"].values() if x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done if k in x["criteria"]) for k in ("s1", "s2", "s3", "s4")}
    res["criteria"]["complete"] = len(done) == len(res["rows"])
    (HERE / "a256_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        if not x:
            continue
        o, h = x.get("o", {}), x.get("h", {})
        print(f"{row:14s} fires {x['fires']:5d} susp {len(x['susp'])} "
              + (f"peak {o['peak_whole']:.1f} (h {h['peak_whole']:.1f}) dev {o['dev_max_v']:.2f} (h {h['dev_max_v']:.2f}) V "
                 f"Vo ext {o['vo_ext_mv']:.1f} (h {h['vo_ext_mv']:.1f}) mV " if h else "")
              + " ".join(k for k, v in x["criteria"].items() if not v))
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
