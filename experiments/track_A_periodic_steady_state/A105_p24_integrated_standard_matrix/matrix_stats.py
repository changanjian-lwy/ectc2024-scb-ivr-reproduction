"""A105: one set of statistics for every standard-matrix run (A97's and A100's references and A105's candidates), from
the run records over a window (default: the last 200 phase-1 periods of the run, or of the time before a load step):
overlaps, status, peak phase current and V_DS; Vo mean and peak-to-peak and the period's sd at the sections; per
phase the low-side turn-off current (mean, sd), the high-side turn-on V_DS (mean) and the low-side turn-on V_DS
(maximum)."""
from __future__ import annotations

import numpy as np

N = 4


def window_stats(d, t1=None, n_periods=200):
    secs = d["sections"]
    if t1 is not None:
        secs = [s for s in secs if s["t_s"] < t1]
    secs = secs[-n_periods:]
    t0, t1w = secs[0]["t_s"], secs[-1]["t_s"]
    t = np.array([s["t_s"] for s in secs]); vo = np.array([s["vo"] for s in secs])
    out = {"status": d["status"], "overlaps": d["overlaps"], "ipk_a": float(d["ipk_a"]), "vds_max_v": float(max(d["vds_max_v"])),
           "window_us": [t0 * 1e6, t1w * 1e6], "vo_mean_v": float(vo.mean()), "vo_pp_mv": float(np.ptp(vo) * 1e3),
           "period_ns": float(np.mean(np.diff(t)) * 1e9), "period_sd_ns": float(np.std(np.diff(t)) * 1e9), "phases": []}
    for k in range(N):
        sel = lambda recs: [r for r in recs if r["phase"] == k + 1 and t0 <= r["t_s"] <= t1w]
        off = [r["i_a"] for r in sel(d["lowoffs_last"])]
        on = [r["vds_v"] for r in sel(d["turnons_last"])]
        lo = [r["vds_v"] for r in sel(d.get("lowons_last", []))]
        out["phases"].append({"i_off_mean_a": float(np.mean(off)) if off else float("nan"),
                              "i_off_sd_a": float(np.std(off)) if off else float("nan"),
                              "hs_on_vds_v": float(np.mean(on)) if on else float("nan"),
                              "ls_on_vds_max_v": float(np.max(lo)) if lo else float("nan"), "n": len(off)})
    return out
