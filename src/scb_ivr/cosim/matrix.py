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
  is above 1%. A106's statistics. A trace still outside its band at its last sample has not recovered: inf.
- Interleave (C01/C02): phase_waveform (a phase's current, linear between its low-side turn-off, high-side turn-on and
  high-side turn-off events), lsoff_after (each phase's MEAN low-side turn-off after a reference run's phase-1
  turn-on), output_ripple (the summed current of several modules' phases, pk-pk and ac rms, optionally re-placed),
  gaps_per_cycle (every consecutive pair of low-side turn-offs of all phases against the local master period / (M N):
  the cycle-by-cycle spacing error, which the mean positions hide).
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
    back = float((ta[bad[-1]] - t_step) * 1e6) if len(bad) else 0.0
    if len(bad) and bad[-1] == len(va) - 1:                  # still outside at the last sample: not recovered
        back = float("inf")
    lad_back = float((ta[lad[-1]] - t_step) * 1e6) if len(lad) else 0.0
    if len(lad) and lad[-1] == len(da) - 1:
        lad_back = float("inf")
    return {"extreme_mv": float((va[i] - vref) * 1e3), "t_extreme_us": float((ta[i] - t_step) * 1e6),
            "back_within_1pct_us": back,
            "ladder_dev_before": float(dev[~a][-200:].max()), "ladder_dev_peak": float(da.max()),
            "ladder_back_below_1pct_us": lad_back}


GRID_S = 15.625e-12                # the waveform grid, 1/2 LSB at 250 MHz


def phase_waveform(d, k, g, shift=0.0):
    """Phase k's current (A) on the time grid g (s), linear between its recorded low-side turn-off (valley), high-side
    turn-on and high-side turn-off (peak) events, the events moved by shift (s)."""
    ev = sorted((x["t_s"], x["i_a"]) for key in ("lowoffs_last", "turnons_last", "highoffs_last") for x in d[key]
                if x["phase"] == k)
    return np.interp(g, np.array([e[0] for e in ev]) + shift, np.array([e[1] for e in ev]))


def ref_turnons(ref, t1=None, n_periods=200):
    """The reference run's last n phase-1 turn-on times (s) before t1, and their mean period (s)."""
    secs = [s for s in ref["sections"] if t1 is None or s["t_s"] < t1][-n_periods:]
    t = np.array([s["t_s"] for s in secs])
    return t, float(np.mean(np.diff(t)))


def lsoff_after(ref, d, t1=None, n_periods=200, n_phases=4):
    """Per phase of run d, the mean time (s) from the reference run's last phase-1 turn-on to the phase's low-side
    turn-off, over the reference's last n periods (before t1)."""
    t_on, _ = ref_turnons(ref, t1, n_periods)
    out = []
    for k in range(1, n_phases + 1):
        ts = [x["t_s"] for x in d["lowoffs_last"] if x["phase"] == k and t_on[0] <= x["t_s"] <= t_on[-1]]
        out.append(float(np.mean([t - t_on[t_on <= t][-1] for t in ts])))
    return out


def output_ripple(runs, ref=None, t1=None, n_periods=200, n_phases=4, shift=None, trim=20):
    """The summed current of every phase of runs (a list of module results) over the reference's last n periods with
    trim periods cut at each end: {"pkpk_a", "rms_ac_a", "mean_a"}. shift(m, k) (s) re-places module m's phase k."""
    t_on, _ = ref_turnons(ref or runs[0], t1, n_periods)
    g = np.arange(t_on[trim], t_on[-trim], GRID_S)
    tot = sum(phase_waveform(r, k, g, shift(m, k) if shift else 0.0)
              for m, r in enumerate(runs) for k in range(1, n_phases + 1))
    return {"pkpk_a": float(np.ptp(tot)), "rms_ac_a": float(np.std(tot)), "mean_a": float(np.mean(tot))}


def gaps_per_cycle(runs, t0, t1, n_phases=4):
    """Every consecutive pair of low-side turn-offs of all phases of runs (a list of module results, the master first)
    in [t0, t1], against the master period containing it divided by the number of phases: {"max_abs_ns", "sd_ns",
    "n"}. Unlike lsoff_after's mean positions, this is the spacing of each switching cycle."""
    on = np.array([s["t_s"] for s in runs[0]["sections"]])
    ev = np.sort(np.array([x["t_s"] for r in runs for x in r["lowoffs_last"] if t0 <= x["t_s"] <= t1]))
    g = np.diff(ev)
    idx = np.clip(np.searchsorted(on, ev[:-1]) - 1, 0, len(on) - 2)
    dev = (g - (on[idx + 1] - on[idx]) / (len(runs) * n_phases)) * 1e9
    return {"max_abs_ns": float(np.abs(dev).max()), "sd_ns": float(np.std(dev)), "n": int(len(g))}

