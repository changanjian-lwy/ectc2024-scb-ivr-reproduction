"""A239 analysis (BOUNDARY Section 2): start-ups through a225_analyze.startup, releases through a237_analyze.one,
skipping valleys through a221_analyze.true_valleys; the return time against Co (V_pk - 1.01 V) / I.
  python3 a239_analyze.py -> a239_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a239_make_cfgs", HERE / "make_cfgs.py")
A25 = _load("a225_analyze", TA / "A225_p24_startup_items_recheck" / "a225_analyze.py")
A37 = _load("a237_analyze", TA / "A237_p24_true_light_load" / "a237_analyze.py")
A21 = _load("a221_analyze", TA / "A221_p24_core_loss_and_pause" / "a221_analyze.py")
CO, BAND, V_START = 4.672e-3, 0.01, 1.05
I_LIM, V_LIM, VALLEY = 200.0, 40.0, (-20.0, -12.0)
M3_REL, M3_ABS, M5_US = 0.15, 3.0, 60.0


def after_peak(r, t0):
    """Vo's maximum after t0, the time from it to Vo's last exit from 1 % and the time above 1.05 V (s -> us)."""
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    m = ts >= t0
    k = int(np.argmax(vo[m])); tpk = ts[m][k]
    a = ts >= tpk
    out = np.where(np.abs(vo[a] - 1) > BAND)[0]
    back = None if len(out) and out[-1] == a.sum() - 1 else 1e6 * ((ts[a][out[-1]] if len(out) else tpk) - tpk)
    dts = np.diff(ts, append=ts[-1])
    return {"v_pk": float(vo[m][k]), "t_pk_us": 1e6 * tpk, "back_from_pk_us": back,
            "t_above_1p05_us": 1e6 * float(dts[m & (vo > V_START)].sum())}


def valleys(r):
    tv = A21.true_valleys(r, 60e-6)
    va = [y for p in tv.values() for y in p]
    return {"by_phase": tv, "min_a": min(va) if va else None, "max_a": max(va) if va else None}


def main():
    res = {"rows": {}}
    for row in MC.START:
        f = COS / f"run_{row}.json"
        r = json.loads(f.read_text())
        v = A25.startup(f)
        v.update(after_peak(r, 0.0))
        v["sources_modified"] = r["provenance"]["cosim_sources_modified"]
        lim = bool(v["status"] == "COMPLETED" and v["peak_whole"] <= I_LIM and v["vds_v"] <= V_LIM
                   and not v["overlaps"] and not v["shoot_on"])
        v["pred_back_us"] = 1e6 * CO * (v["v_pk"] - 1 - BAND) / (0.5 * (v["v_pk"] + 1 + BAND) / MC.R_MIN)
        c = {"m0": not v["sources_modified"], "m1": lim, "m2": all(abs(x - 1) <= BAND for x in v["vo_last"]),
             "m5": bool(v["back_from_pk_us"] is not None and v["back_from_pk_us"] <= M5_US)}
        res["rows"][row] = {"m": v, "criteria": c}
    for row, (_, i_cc, _) in MC.RELEASE.items():
        f = COS / f"run_{row}.json"
        r = json.loads(f.read_text())
        v = A37.one(f)
        v.update(after_peak(r, A37.T_REL))
        v["sources_modified"] = r["provenance"]["cosim_sources_modified"]
        v["pred_back_us"] = 1e6 * CO * (v["v_pk"] - 1 - BAND) / i_cc
        v["valleys"] = valleys(r)
        b, p = v["back_from_pk_us"], v["pred_back_us"]
        c = {"m0": not v["sources_modified"], "m1": v["limits"], "m2": v["vo_end_in"],
             "m3": bool(b is not None and abs(b - p) <= M3_REL * p + M3_ABS),
             "m4": bool(v["valleys"]["min_a"] is not None and VALLEY[0] <= v["valleys"]["min_a"] and v["valleys"]["max_a"] <= VALLEY[1])}
        res["rows"][row] = {"m": v, "criteria": c}
    res["criteria_main"] = {k: all(x["criteria"][k] for x in res["rows"].values() if k in x["criteria"])
                            for k in ("m0", "m1", "m2", "m3", "m4", "m5")}
    (HERE / "a239_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for row, x in res["rows"].items():
        v = x["m"]
        va = v.get("valleys")
        print(f"{row:8s} Vo pk {v['v_pk']:.4f} V at {v['t_pk_us']:.1f} us, back {v['back_from_pk_us']} us (pred {v['pred_back_us']:.1f}), "
              f">1.05 V {v['t_above_1p05_us']:.1f} us, peak {v['peak_whole']:.1f} A, V_DS {v['vds_v']:.1f}"
              + (f", valleys {va['min_a']:.1f}..{va['max_a']:.1f}" if va else f", hand {v['hand_pk']:.1f} A")
              + f" | {x['criteria']}")
    print("main", res["criteria_main"])


if __name__ == "__main__":
    main()
