"""A255 analysis (BOUNDARY Section 2): each run after the +62.5 A step at 500 us: the gate-record peak, Vo's minimum and
its last 20 us, the ladder's deviation max |rail - Vin / 4| (largest after the step, and in the last 20 us), V_DS,
late fires and the limit's fires. A246's k_N0 (h) and A254's run_l_k_N0 (l) are listed for the same step on N0.
  python3 a255_analyze.py -> a255_summary.json"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
T_STEP, TAIL, I_LIM, V_LIM, DEV_OK, VO_BAND = 500e-6, 20e-6, 200.0, 40.0, 1.0, 0.01
N0 = {"h": TA / "A246_p24_held_report_floor" / "cosim" / "run_h_k_N0.json",
      "l": TA / "A254_p24_peak_limit_measured_level" / "cosim" / "run_l_k_N0.json"}


def stats(f):
    d = json.loads(Path(f).read_text())
    S = [s for s in d["sections"] if s["t_s"] >= T_STEP]
    t = np.array([s["t_s"] for s in S])
    dev = np.array([max(abs(r - s["vin_v"] / 4) for r in (s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1],
                                                          s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2])) for s in S])
    vo = np.array([s["vo"] for s in S])
    tail = t >= t[-1] - TAIL
    g = [e["i_max_a"] for e in d["gate_offs_last"] if e["t_s"] >= T_STEP]
    return {"peak_a": max(g), "vo_min_v": float(vo.min()), "vo_tail_err_v": float(np.abs(vo[tail] - 1.0).max()),
            "dev_max_v": float(dev.max()), "dev_end_v": float(dev[tail].max()), "vds_max_v": max(d["vds_max_v"]),
            "late": sum(d["late_fires"]), "fires": len(d.get("ocp_fires", [])),
            "sources_modified": d["provenance"]["cosim_sources_modified"]}


def main():
    res = {"rows": {}, "n0": {a: stats(f) for a, f in N0.items()}}
    for b in ("N75", "S75h"):
        fh, fl = HERE / "cosim" / f"run_h_o125_{b}.json", HERE / "cosim" / f"run_l_o125_{b}.json"
        if not (fh.exists() and fl.exists()):
            res["rows"][b] = None; continue
        h, l = stats(fh), stats(fl)
        c = {"c1": bool(h["peak_a"] <= I_LIM and h["dev_end_v"] <= DEV_OK and h["vo_tail_err_v"] <= VO_BAND
                        and h["vds_max_v"] <= V_LIM),
             "c2": bool(l["dev_max_v"] <= DEV_OK and l["vo_min_v"] >= h["vo_min_v"] - 2e-3
                        and l["peak_a"] <= max(h["peak_a"], I_LIM))}
        res["rows"][b] = {"h": h, "l": l, "criteria": c}
    done = [x for x in res["rows"].values() if x]
    res["criteria"] = {k: all(x["criteria"][k] for x in done) for k in ("c1", "c2")} | {"complete": len(done) == 2}
    (HERE / "a255_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for b, x in list(res["rows"].items()) + [("N0 (A246 / A254)", {"h": res["n0"]["h"], "l": res["n0"]["l"], "criteria": {}})]:
        if not x:
            continue
        for a in ("h", "l"):
            s = x[a]
            print(f"{b:16s} {a}: peak {s['peak_a']:.1f} A, Vo min {1e3 * s['vo_min_v']:.1f} mV, ladder dev max / end "
                  f"{s['dev_max_v']:.2f} / {s['dev_end_v']:.2f} V, V_DS {s['vds_max_v']:.1f} V, fires {s['fires']}")
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
