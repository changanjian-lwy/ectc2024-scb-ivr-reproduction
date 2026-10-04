"""A133 analysis. `pilot DIR`: per run - rails at fixed times, then over the last 200 periods the rails, per-phase valley
(mean / min), peak, turn-on V_DS (min), Vo peak-to-peak, late fires, the peak after mode P + 100 us; to stdout."""
from __future__ import annotations

import bisect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import scb_ivr.p24_loss_budget as LB  # noqa: E402

T_US = (144, 160, 200, 300, 500, 700, 1000, 1500, 2000)


def rails(s):
    v = s["vcs_v"]
    return [s["vin_v"] - v[0], v[0] - v[1], v[1] - v[2], v[2]]


def tail(d, n=200):
    secs = d["sections"][-n:]
    t0 = secs[0]["t_s"]
    m = LB.measure(d, n_periods=n)
    ph = lambda recs, k: [r for r in recs if r["phase"] == k and r["t_s"] >= t0]
    tp = (d["t_mode_p_s"] or 0.0) + 100e-6
    return {"rails_v": m["rails_v"], "period_ns": m["period_s"] * 1e9, "ton_ns": m["ton_s"] * 1e9,
            "valley_mean_a": [p["valley"] for p in m["phases"]],
            "valley_min_a": [min(r["i_a"] for r in ph(d["lowoffs_last"], k)) for k in (1, 2, 3, 4)],
            "peak_a": [p["peak"] for p in m["phases"]],
            "von_min_v": [min(r["vds_v"] for r in ph(d["turnons_last"], k)) for k in (1, 2, 3, 4)],
            "vo_pp_mv": (max(s["vo"] for s in secs) - min(s["vo"] for s in secs)) * 1e3,
            "late": d["late_fires"], "ipk_a": d["ipk_a"],
            "ipk_after_a": max((r["i_a"] for r in d["highoffs_last"] if r["t_s"] >= tp), default=None)}


def pilot(folder):
    out = {}
    for f in sorted(Path(folder).glob("run_*.json")):
        d = json.loads(f.read_text())
        ts = [s["t_s"] for s in d["sections"]]
        traj = {}
        for t in T_US:
            i = bisect.bisect_left(ts, t * 1e-6)
            if i < len(ts):
                traj[t] = [round(x, 1) for x in rails(d["sections"][i])]
        tl = tail(d)
        out[f.stem] = {"traj": traj, **tl}
        f2 = lambda xs: "/".join(f"{x:.1f}" for x in xs)
        print(f"{f.stem}: " + " | ".join(f"{t}:{f2(v)}" for t, v in traj.items()))
        print(f"   tail rails {f2(tl['rails_v'])} V, valley {f2(tl['valley_mean_a'])} (min {f2(tl['valley_min_a'])}) A, "
              f"peak {f2(tl['peak_a'])} A, V_on min {f2(tl['von_min_v'])} V, Vo pp {tl['vo_pp_mv']:.1f} mV, "
              f"T {tl['period_ns']:.0f} ns, Ton {tl['ton_ns']:.1f} ns, late {tl['late']}, ipk {tl['ipk_a']:.0f} / after {tl['ipk_after_a']:.0f} A")
    (Path(folder) / "pilot_summary.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "pilot":
        pilot(sys.argv[2])
