"""A148 criterion 1: D63's V_DS block against the cosim's turn-ons (A143 lo_learn 4 records at L0, mode P): each
turn-on's V_DS against the table at the same phase's previous low-side turn-off current and the rail of the nearest
earlier section -> a148_von_check.json."""
from __future__ import annotations

import bisect
import glob
import json
from pathlib import Path

import numpy as np

from scb_ivr.p24_valley_map import _bilinear

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
A143 = PROJECT / "experiments/track_A_periodic_steady_state/A143_p24_short_comparator_phase/cosim"
FILES = sorted(set(glob.glob(str(A143 / "run_g[125]*_k4.json")) + glob.glob(str(A143 / "run_g[34]_s100_*_k4.json"))))


def pairs(path, tab):
    r = json.loads(Path(path).read_text())
    t_step = (r["cfg"].get("line_step") or {}).get("t_us", 1000.0) * 1e-6
    sec = r["sections"]
    ts = [s["t_s"] for s in sec]
    lows = {k: [(e["t_s"], e["i_a"]) for e in r["lowoffs_last"] if e["phase"] == k] for k in range(1, 5)}
    out = []
    for e in r["turnons_last"]:
        k, t = e["phase"], e["t_s"]
        if t < 150e-6:
            continue
        lo = lows[k]
        j = bisect.bisect([x[0] for x in lo], t) - 1
        if j < 0 or t - lo[j][0] > 60e-9:
            continue
        s = sec[max(bisect.bisect(ts, t) - 1, 0)]
        v = [s["vin_v"]] + s["vcs_v"] + [0.0]
        rail = v[k - 1] - v[k]
        pred = _bilinear(tab["currents"], tab["rails"], tab["v4"] if k == 4 else tab["v13"], lo[j][1], rail)
        out.append((k, t >= t_step and t < t_step + 40e-6, lo[j][1], rail, e["vds_v"], pred))
    return out


def stats(rows):
    err = np.array([p - m for *_, m, p in rows])
    return {"n": len(rows), "median_abs": float(np.median(np.abs(err))), "p90_abs": float(np.percentile(np.abs(err), 90)),
            "p99_abs": float(np.percentile(np.abs(err), 99)), "bias": float(np.mean(err))}


def main():
    tab = json.loads((HERE / "a148_von_table.json").read_text())
    rows = [x for f in FILES for x in pairs(f, tab)]
    out = {"files": [Path(f).name for f in FILES], "all": stats(rows)}
    for k in range(1, 5):
        out[f"ph{k}"] = stats([x for x in rows if x[0] == k])
        out[f"ph{k}_post"] = stats([x for x in rows if x[0] == k and x[1]]) if any(x[0] == k and x[1] for x in rows) else None
    hard = [x for x in rows if x[0] == 1 and x[4] > 8.0]
    out["ph1_hard"] = stats(hard) if hard else None
    bins = [(-40, -20), (-20, -10), (-10, 0), (0, 10), (10, 30)]
    out["ph1_by_ioff"] = {f"{a}..{b}": stats([x for x in rows if x[0] == 1 and a <= x[2] < b]) for a, b in bins
                          if any(x[0] == 1 and a <= x[2] < b for x in rows)}
    (HERE / "a148_von_check.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out.items():
        if k != "files" and v and "n" in v:
            print(f"{k:10s} n {v['n']:6d} median {v['median_abs']:.2f} p90 {v['p90_abs']:.2f} p99 {v['p99_abs']:.2f} bias {v['bias']:+.2f}")
    for k, v in out["ph1_by_ioff"].items():
        print(f"ph1 i_off {k:8s} n {v['n']:6d} median {v['median_abs']:.2f} p90 {v['p90_abs']:.2f} bias {v['bias']:+.2f}")


if __name__ == "__main__":
    main()
