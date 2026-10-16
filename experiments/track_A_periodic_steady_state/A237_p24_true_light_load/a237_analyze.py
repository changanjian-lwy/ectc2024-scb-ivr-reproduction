"""A237 analysis (BOUNDARY Section 2): each true-load row and, where it exists, the same release on the 4 mOhm base
(A229's record).
  python3 a237_analyze.py -> a237_summary.json
Also: time above VRD 11.1's +50 mV, the references' skipping valleys, and the trace of the re-application swing
(each phase's turn-on delay after its low-side turn-off, valley and gate-level peak per 2 us window)."""
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
T_REL, T_RE, BAND, I_LIM, V_LIM, V_VRD = 300e-6, 380e-6, 0.01, 200.0, 40.0, 1.05
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
    hi = m & (vo > V_VRD)
    dts = np.diff(ts, append=ts[-1])
    v = {"status": r["status"], "peak_whole": max(e["i_max_a"] for e in g), "vds_v": max(r["vds_max_v"]),
         "overlaps": r["overlaps"], "shoot_on": sum(r["gate_stats"]["shoot_on"]),
         "vo_rel_peak_mv": 1e3 * (vo[m][k] - 1), "t_rel_peak_us": 1e6 * (tpk - T_REL),
         "back_us": (1e6 * (ts[after][out[-1]] - T_REL) if len(out) and ts[after][out[-1]] < stop - 1e-6 else
                     (None if len(out) else 1e6 * (tpk - T_REL))),
         "t_above_vrd_us": 1e6 * float(dts[hi].sum()), "t_last_above_vrd_us": 1e6 * (ts[hi][-1] - T_REL) if hi.any() else 0.0,
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


def swing(f, phase, t0=378e-6, t1=412e-6, w=2e-6):
    """Per window: the phase's turn-on delay after its low-side turn-off (+ the driver lead), valley, gate-level peak."""
    r = json.loads(Path(f).read_text())
    lead = r["driver"].get("hs_on_lead_ns", 0.0)
    lo = [x for x in r["lowoffs_last"] if x["phase"] == phase]
    g = [e for e in r["gate_offs_last"] if e["phase"] == phase]
    rows = []
    for x in (x for x in r["turnons_last"] if x["phase"] == phase and t0 <= x["t_s"] < t1):
        lw = min(lo, key=lambda y: abs(y["t_s"] - x["t_s"]))
        pk = min(g, key=lambda e: abs(e["t_s"] - x["t_s"] - 35e-9))
        rows.append((x["t_s"], (x["t_s"] - lw["t_s"]) * 1e9 + lead, lw["i_a"], pk["i_max_a"]))
    out = []
    for a in np.arange(t0, t1, w):
        q = [z for z in rows if a <= z[0] < a + w]
        if q:
            out.append({"t_us": 1e6 * a, "delay_ns": [min(z[1] for z in q), max(z[1] for z in q)],
                        "valley_a": [min(z[2] for z in q), max(z[2] for z in q)], "peak_a": max(z[3] for z in q)})
    return out


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
            s = A29.skip_file(A29C / f"run_{MC.REF[row]}.json", SKIP_Z[row])
            ref["skip"] = {k: s[k] for k in ("vmin_a", "vmax_a", "in_band", "q1_run")}
        if i_re:
            c["g4"] = bool(h["post_pk"] <= I_LIM and h["post_pk"] <= ref["post_pk"] + 10.0)
        res["rows"][row] = {"true_load": h, "ref_4mohm": ref, "criteria": c}
    res["criteria_main"] = {k: all(v["criteria"][k] for v in res["rows"].values() if k in v["criteria"])
                            for k in ("g0", "g1", "g2", "g3", "g4")}
    res["swing_phase2_N75"] = {"true_load": swing(COS / "run_cw5_N75.json", 2),
                               "ref_4mohm": swing(A29C / f"run_{MC.REF['cw5_N75']}.json", 2)}
    logs = PROJECT / "tmp" / "logs"
    res["identity"] = {k: bool(re.search(rf"REGRESSION {k} PASS", (logs / f"a237_reg{k[0]}.log").read_text())) for k in ("quick", "full")}
    res["criteria_main"]["id"] = all(res["identity"].values())
    (HERE / "a237_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for n, v in res["rows"].items():
        h, r = v["true_load"], v["ref_4mohm"]
        fmt = lambda x: "-" if x is None else f"{x:.1f}"
        print(f"{n:9s} rel peak {h['vo_rel_peak_mv']:+.1f} mV, back {fmt(h['back_us'])} us, before re / end {h['vo_before_re_v']:.4f} / "
              f"{h['vo_end_v'][1]:.4f} V, >1.05 V {h['t_above_vrd_us']:.1f} us" + (f" | post {h['post_pk']:.1f} A, dip {h['vo_re_min_mv']:+.1f} mV" if 'post_pk' in h else "")
              + (f" | ref: peak {r['vo_rel_peak_mv']:+.1f}, back {fmt(r['back_us'])}" + (f", post {r['post_pk']:.1f}, dip {r['vo_re_min_mv']:+.1f}" if 'post_pk' in r else "") if r else "")
              + (f" | skip {h['skip']}" if 'skip' in h else "") + f" | {v['criteria']}")
    print("main", res["criteria_main"], "identity", res["identity"])


if __name__ == "__main__":
    main()
