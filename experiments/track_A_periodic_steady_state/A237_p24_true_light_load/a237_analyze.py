"""A237 analysis (BOUNDARY Section 2): each true-load row and, where it exists, the same release on the 4 mOhm base
(A229's record).
  python3 a237_analyze.py -> a237_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
COS, A29C = HERE / "cosim", TA / "A229_p24_kd_band" / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a237_make_cfgs", HERE / "make_cfgs.py")
A29 = _load("a229_analyze", TA / "A229_p24_kd_band" / "a229_analyze.py")
T_REL, T_RE, BAND, I_LIM, V_LIM = 300e-6, 380e-6, 0.01, 200.0, 40.0
SKIP_Z = {"c10_N0": "z_N0_10", "c10_N75": "z_N75_10"}


def one(f):
    r = json.loads(Path(f).read_text())
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    g = r["gate_offs_last"]
    re_at = T_RE if r["cfg"].get("load_step2") else None
    stop = re_at or ts[-1] + 1e-9
    m = (ts >= T_REL) & (ts < stop)
    k = int(np.argmax(vo[m])); tpk = ts[m][k]
    after = (ts >= tpk) & (ts < stop)
    out = np.where(np.abs(vo[after] - 1) > BAND)[0]
    last = ts >= ts[-1] - 20e-6
    v = {"status": r["status"], "peak_whole": max(e["i_max_a"] for e in g), "vds_v": max(r["vds_max_v"]),
         "overlaps": r["overlaps"], "shoot_on": sum(r["gate_stats"]["shoot_on"]),
         "vo_rel_peak_mv": 1e3 * (vo[m][k] - 1), "t_rel_peak_us": 1e6 * (tpk - T_REL),
         "back_us": (1e6 * (ts[after][out[-1]] - T_REL) if len(out) and ts[after][out[-1]] < stop - 1e-6 else
                     (None if len(out) else 1e6 * (tpk - T_REL))),
         "vo_before_re_v": float(vo[ts < stop][-1]), "vo_end_v": [float(vo[last].min()), float(vo[last].max())]}
    if len(out) and out[-1] == len(vo[after]) - 1:
        v["back_us"] = None                                             # still outside at the window's end
    if re_at:
        v["post_pk"] = max(e["i_max_a"] for e in g if e["t_s"] >= re_at)
        v["vo_re_min_mv"] = 1e3 * (float(vo[ts >= re_at].min()) - 1)
    v["limits"] = bool(v["status"] == "COMPLETED" and v["peak_whole"] <= I_LIM and v["vds_v"] <= V_LIM
                       and not v["overlaps"] and not v["shoot_on"])
    v["vo_end_in"] = bool(all(abs(x - 1) <= BAND for x in v["vo_end_v"]))
    return v


def main():
    res = {"rows": {}}
    for row, (stem, i_cc, i_re) in MC.ROWS.items():
        f = COS / f"run_{row}.json"
        h = one(f)
        ref = one(A29C / f"run_{MC.REF[row]}.json") if row in MC.REF else None
        c = {"g1": h["limits"]}
        if i_cc == 0.0:
            c["g0"] = h["vo_end_in"]
        else:
            c["g2"] = h["vo_end_in"]
        if row in SKIP_Z:
            s = A29.skip_file(f, SKIP_Z[row])
            h["skip"] = {k: s[k] for k in ("vmin_a", "vmax_a", "in_band", "q1_run")}
            c["g3"] = bool(s["q1_run"] and s["in_band"])
        if i_re:
            c["g4"] = bool(h["post_pk"] <= I_LIM and h["post_pk"] <= ref["post_pk"] + 10.0)
        res["rows"][row] = {"true_load": h, "ref_4mohm": ref, "criteria": c}
    res["criteria_main"] = {k: all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"])
                            for k in ("g0", "g1", "g2", "g3", "g4")}
    logs = PROJECT / "tmp" / "logs"
    res["identity"] = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a237_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    (HERE / "a237_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["rows"].items():
        h, r = v["true_load"], v["ref_4mohm"]
        fmt = lambda x: "-" if x is None else f"{x:.1f}"
        print(f"{n:9s} rel peak {h['vo_rel_peak_mv']:+.1f} mV, back {fmt(h['back_us'])} us, before re / end {h['vo_before_re_v']:.4f} / "
              f"{h['vo_end_v'][1]:.4f} V" + (f" | post {h['post_pk']:.1f} A, dip {h['vo_re_min_mv']:+.1f} mV" if 'post_pk' in h else "")
              + (f" | ref: peak {r['vo_rel_peak_mv']:+.1f}, back {fmt(r['back_us'])}" + (f", post {r['post_pk']:.1f}, dip {r['vo_re_min_mv']:+.1f}" if 'post_pk' in r else "") if r else "")
              + (f" | skip {h['skip']}" if 'skip' in h else "") + f" | {v['criteria']}")
    print("main", res["criteria_main"], "identity", res["identity"])


if __name__ == "__main__":
    main()
