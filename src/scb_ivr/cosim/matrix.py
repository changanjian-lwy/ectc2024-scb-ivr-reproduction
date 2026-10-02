"""The standard matrix as one shared definition, and the statistics every candidate is scored with.

The matrix is TRADEOFF_SCORECARD Section 5's, plus A106's line steps.
- ROWS: name -> what the row changes in a step-free base configuration: the driver (mismatch m, jitter sigma), a load
  or line step at 400 us, and the end time (500 us without a step, 600 us with one).
- configs(base, rows): the configurations of a candidate, one per row (note and output name left to the caller).
- window_stats(run, t1=None, n_periods=200): over the last n periods (before t1 if given): status, overlaps, peak
  current and V_DS, Vo mean and peak-to-peak, the period's sd at the sections, and per phase the low-side turn-off
  current (mean, sd), the high-side turn-on V_DS (mean) and the low-side turn-on V_DS (maximum). A105's statistics.
- step_stats(run, t_step=400e-6): Vo's extreme after the step and its time, the last exit from 1 V +/- 1%; the ladder
  deviation max |VCs_k / Vin - (N - k) / N| (A73's formula) before the step, its peak after it, and the last time it
  is above 1%. A106's statistics.
"""
from __future__ import annotations

import copy

import numpy as np

T_STEP_US = 400.0
T_STEP_S = 400e-6                  # the same instant in seconds, written as A105/A106 wrote it

ROWS = {
    "n0": {"driver": (0.0, 0.0)},
    "m1n": {"driver": (-1.0, 0.0)},
    "m1p": {"driver": (1.0, 0.0)},
    "m3n": {"driver": (-3.4, 0.0)},
    "m3p": {"driver": (3.4, 0.0)},
    "j30": {"driver": (0.0, 30.0)},
    "j100": {"driver": (0.0, 100.0)},
    "s_m25": {"load_step": -25.0},
    "s_p25": {"load_step": 25.0},
    "s_m62": {"load_step": -62.5},
    "s_p62": {"load_step": 62.5},
    "l_m48_1us": {"line_step": (-4.8, 1.0)},
    "l_p48_1us": {"line_step": (4.8, 1.0)},
    "l_m48_10us": {"line_step": (-4.8, 10.0)},
    "l_p48_10us": {"line_step": (4.8, 10.0)},
    "l_m80_10us": {"line_step": (-8.0, 10.0)},
}


def configs(base: dict, rows=None) -> dict:
    """{row: configuration}: base (step-free) with the row's driver, step and end time."""
    out = {}
    for name in (rows or ROWS):
        r = ROWS[name]
        c = copy.deepcopy(base)
        c.pop("load_step", None); c.pop("line_step", None)
        m, sig = r.get("driver", (0.0, 0.0))
        c["driver"] = {"m_ns": m, "sigma_ps": sig, "seed": 1}
        c["t_end_us"] = 500.0
        if "load_step" in r:
            c["load_step"] = {"t_us": T_STEP_US, "i_a": r["load_step"]}; c["t_end_us"] = 600.0
        if "line_step" in r:
            dv, slew = r["line_step"]
            c["line_step"] = {"t_us": T_STEP_US, "dv": dv, "slew_us": slew}; c["t_end_us"] = 600.0
        out[name] = c
    return out


def window_stats(d, t1=None, n_periods=200, n_phases=4):
    secs = d["sections"]
    if t1 is not None:
        secs = [s for s in secs if s["t_s"] < t1]
    secs = secs[-n_periods:]
    t0, t1w = secs[0]["t_s"], secs[-1]["t_s"]
    t = np.array([s["t_s"] for s in secs]); vo = np.array([s["vo"] for s in secs])
    out = {"status": d["status"], "overlaps": d["overlaps"], "ipk_a": float(d["ipk_a"]), "vds_max_v": float(max(d["vds_max_v"])),
           "window_us": [t0 * 1e6, t1w * 1e6], "vo_mean_v": float(vo.mean()), "vo_pp_mv": float(np.ptp(vo) * 1e3),
           "period_ns": float(np.mean(np.diff(t)) * 1e9), "period_sd_ns": float(np.std(np.diff(t)) * 1e9), "phases": []}
    for k in range(n_phases):
        sel = lambda recs: [r for r in recs if r["phase"] == k + 1 and t0 <= r["t_s"] <= t1w]
        off = [r["i_a"] for r in sel(d["lowoffs_last"])]
        on = [r["vds_v"] for r in sel(d["turnons_last"])]
        lo = [r["vds_v"] for r in sel(d.get("lowons_last", []))]
        out["phases"].append({"i_off_mean_a": float(np.mean(off)) if off else float("nan"),
                              "i_off_sd_a": float(np.std(off)) if off else float("nan"),
                              "hs_on_vds_v": float(np.mean(on)) if on else float("nan"),
                              "ls_on_vds_max_v": float(np.max(lo)) if lo else float("nan"), "n": len(off)})
    return out


def step_stats(d, t_step=T_STEP_S, vref=1.0):
    secs = d["sections"]
    t = np.array([s["t_s"] for s in secs]); vo = np.array([s["vo"] for s in secs])
    vin = np.array([s["vin_v"] for s in secs]); vcs = np.array([s["vcs_v"] for s in secs])
    n = vcs.shape[1] + 1
    a = t >= t_step
    ta, va = t[a], vo[a]
    i = int(np.argmax(np.abs(va - vref)))
    bad = np.nonzero(np.abs(va - vref) > 0.01 * vref)[0]
    dev = np.max(np.abs(vcs / vin[:, None] - np.array([(n - k) / n for k in range(1, n)])), axis=1)
    da = dev[a]
    lad = np.nonzero(da > 0.01)[0]
    return {"extreme_mv": float((va[i] - vref) * 1e3), "t_extreme_us": float((ta[i] - t_step) * 1e6),
            "back_within_1pct_us": float((ta[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0,
            "ladder_dev_before": float(dev[~a][-200:].max()), "ladder_dev_peak": float(da.max()),
            "ladder_back_below_1pct_us": float((ta[lad[-1]] - t_step) * 1e6) if len(lad) else 0.0}
