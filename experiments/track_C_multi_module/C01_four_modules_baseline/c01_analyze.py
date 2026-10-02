"""C01 analysis: four modules on one output, against BOUNDARY Section 4. Per run, over the last 200 master periods
(before the step for step runs):
- system: status, overlaps and peak current per module, the output join's largest difference;
- periods: each module's mean period; interleave: each slave's phase-1 low-side turn-off after the master's phase-1
  turn-on, modulo the period, against m T / 16, and its high-side turn-on;
- sharing: each module's current, the mean over its phases of (valley + peak) / 2;
- each module: valleys, peaks, high-side turn-on V_DS, low-side turn-on V_DS maximum, turn-off sd (shared statistics,
  scb_ivr.cosim.matrix.window_stats);
- Vo: the mean, the step's extreme (step_stats), the start-up peak.
Added after the runs (RESULTS Section 3):
- each module's current from its phases' piecewise-linear waveforms (valley at the low-side turn-off, the high-side
  turn-on, the peak at the high-side turn-off), and that current normalised so the modules sum to the load (Vo / 1 mOhm),
  because the registered (valley + peak) / 2 reads 2% high in absolute terms;
- the low-side turn-off of all M N phases after the master's phase-1 turn-on, and the summed output current's ripple
  (pk-pk, ac rms) for the actual placement and three re-placements of the same waveforms: slaves referenced to the
  master's low-side turn-off, a uniform T / 16 grid, and no interleave between modules.
Writes c01_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

RUNS = ("m4_n0", "m4_L5", "m4_j30", "m4_s_m250", "m4_s_p250")
D61_L5 = (236.9, 250.0, 250.0, 264.5)
D59 = {"m4_s_m250": 15.5, "m4_s_p250": -15.9}
R_SYS = 1e-3                       # the system load, 4 x 4 mOhm shares
GRID_S = 15.625e-12


def waveform(r, k, g, shift=0.0):
    """Phase k's current on the grid g, linear between its low-side turn-off, high-side turn-on and turn-off events."""
    ev = sorted((x["t_s"], x["i_a"]) for key in ("lowoffs_last", "turnons_last", "highoffs_last") for x in r[key] if x["phase"] == k)
    return np.interp(g, np.array([e[0] for e in ev]) + shift, np.array([e[1] for e in ev]))


def ripple(mods, m_on, period, dt_pred, n=4):
    """The summed output current over the window (20 periods trimmed at each end) for four placements."""
    g = np.arange(m_on[20], m_on[-20], GRID_S)
    m_n = len(mods) * n
    cases = {"actual": lambda m, k: 0.0,
             "slaves_ref_master_lsoff": lambda m, k: -dt_pred if m else 0.0,
             "uniform": lambda m, k: (-dt_pred if m else 0.0) + (dt_pred if k == 1 else 0.0),
             "no_module_interleave": lambda m, k: -m * period / m_n}
    out = {}
    for name, f in cases.items():
        s = sum(waveform(r, k, g, f(m, k)) for m, r in enumerate(mods) for k in range(1, n + 1))
        out[name] = {"pkpk_a": float(np.ptp(s)), "rms_ac_a": float(np.std(s))}
    one = waveform(mods[0], 2, g)
    s = sum(waveform(mods[0], 2, g, j * period / m_n) for j in range(m_n))
    out["ideal_phase2_copies"] = {"pkpk_a": float(np.ptp(s)), "rms_ac_a": float(np.std(s))}
    out["one_phase_pkpk_a"] = float(np.ptp(one))
    out["one_module_pkpk_a"] = float(np.ptp(sum(waveform(mods[0], k, g) for k in range(1, n + 1))))
    return out


def run_summary(name):
    d = json.loads((HERE / "cosim" / f"run_{name}.json").read_text())
    mods = [d] + d["modules_rest"]
    t1 = 400e-6 if name.startswith("m4_s") else None
    sysd = d["system"]
    out = {"system": sysd, "modules": []}
    m_sec = [s for s in d["sections"] if t1 is None or s["t_s"] < t1][-200:]
    t0w, t1w = m_sec[0]["t_s"], m_sec[-1]["t_s"]
    m_on = np.array([s["t_s"] for s in m_sec])
    period = float(np.mean(np.diff(m_on)))
    for m, r in enumerate(mods):
        w = window_stats(r, t1=t1)
        peaks = [np.mean([h["i_a"] for h in r["highoffs_last"] if h["phase"] == k + 1 and t0w <= h["t_s"] <= t1w]) for k in range(4)]
        valleys = [p["i_off_mean_a"] for p in w["phases"]]
        cur = float(np.mean([(v + pk) / 2 for v, pk in zip(valleys, peaks)])) * 4
        g = np.arange(t0w, t1w, GRID_S)
        pl = float(sum(waveform(r, k, g).mean() for k in range(1, 5)))
        lo_all = []
        for k in range(1, 5):
            ts = [x["t_s"] for x in r["lowoffs_last"] if x["phase"] == k and t0w <= x["t_s"] <= t1w]
            lo_all.append(float(np.mean([t - m_on[m_on <= t][-1] for t in ts if (m_on <= t).any()]) * 1e9))
        row = {"period_ns": w["period_ns"], "current_a": cur, "valleys_a": valleys, "peaks_a": [float(x) for x in peaks],
               "hs_on_vds_v": [p["hs_on_vds_v"] for p in w["phases"]], "ls_on_vds_max_v": [p["ls_on_vds_max_v"] for p in w["phases"]],
               "off_sd_a": [p["i_off_sd_a"] for p in w["phases"]], "overlaps": r["overlaps"], "ipk_a": r["ipk_a"],
               "pl_current_a": pl, "lsoff_after_master_ns": lo_all, "dt_pred_ns": r["dt_pred_final_ns"], "ton_lsb": r["ton_final_lsb"]}
        if m > 0:
            lo1 = np.array([x["t_s"] for x in r["lowoffs_last"] if x["phase"] == 1 and t0w <= x["t_s"] <= t1w])
            on1 = np.array([x["t_s"] for x in r["turnons_last"] if x["phase"] == 1 and t0w <= x["t_s"] <= t1w])
            def after(ts):
                o = []
                for t in ts:
                    prev = m_on[m_on <= t]
                    if len(prev):
                        o.append(t - prev[-1])
                return np.array(o)
            a_lo, a_on = after(lo1), after(on1)
            row.update(lo1_after_master_ns=float(a_lo.mean() * 1e9), lo1_after_master_sd_ns=float(a_lo.std() * 1e9),
                       on1_after_master_ns=float(a_on.mean() * 1e9), target_ns=m * period / 16 * 1e9)
        out["modules"].append(row)
    vo = np.array([s["vo"] for s in m_sec])
    out["vo_mean_v"] = float(vo.mean()); out["master_period_ns"] = period * 1e9
    pl_sum = sum(mm["pl_current_a"] for mm in out["modules"])
    for mm in out["modules"]:
        mm["pl_current_norm_a"] = mm["pl_current_a"] / pl_sum * out["vo_mean_v"] / R_SYS
    out["pl_sum_a"] = pl_sum
    if name in ("m4_n0", "m4_L5"):
        out["ripple"] = ripple(mods, m_on, period, mods[0]["dt_pred_final_ns"][0] * 1e-9)
    su = [s["vo"] for s in d["sections"] if s["t_s"] < 400e-6]
    out["startup_vo_max_v"] = float(max(su))
    if name.startswith("m4_s"):
        out["step"] = step_stats(d)
    return out


def main():
    res = {}
    for name in RUNS:
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        x = run_summary(name)
        mods = x["modules"]
        curs = [mm["current_a"] for mm in mods]
        c = {"no_overlap": all(mm["overlaps"] == 0 for mm in mods), "peak_200a": max(mm["ipk_a"] for mm in mods) <= 200.0,
             "join_0p1mV": x["system"]["equalisation_max_v"] <= 1e-4,
             "locked": all(abs(mm["period_ns"] - mods[0]["period_ns"]) <= 0.1 for mm in mods[1:]),
             "slot": all(abs(mm["lo1_after_master_ns"] - mm["target_ns"]) <= 0.1 for mm in mods[1:]),
             "low_side_zvs": all(max(mm["ls_on_vds_max_v"]) <= 0.0 for mm in mods) if name != "m4_j30" else True,
             "vo": abs(x["vo_mean_v"] - 1.0) <= 1e-3, "startup": x["startup_vo_max_v"] <= 1.05}
        if name == "m4_L5":
            c["sharing_d61"] = all(abs(a - b) <= 3.0 for a, b in zip(curs, D61_L5))
            c["sharing_d61_normalised (added)"] = all(abs(mm["pl_current_norm_a"] - b) <= 3.0 for mm, b in zip(mods, D61_L5))
        elif name != "m4_j30":
            c["sharing_1pct"] = (max(curs) - min(curs)) / np.mean(curs) <= 0.02
        if name in D59:
            c["step_d59"] = abs(x["step"]["extreme_mv"] / D59[name] - 1) <= 0.3
        if name == "m4_j30":
            c["jitter_spread"] = all(0.48 * 0.7 <= s <= 0.53 * 1.3 for mm in mods for s in mm["off_sd_a"])
        x["criteria"] = c
        res[name] = x
        print(f"{name}: {x['system']['status']}, overlaps {[mm['overlaps'] for mm in mods]}, ipk {[round(mm['ipk_a']) for mm in mods]} A, "
              f"join max {x['system']['equalisation_max_v'] * 1e6:.1f} uV, Vo {x['vo_mean_v']:.4f} V, start-up max {x['startup_vo_max_v']:.4f} V, "
              f"master period {x['master_period_ns']:.2f} ns")
        for m, mm in enumerate(mods):
            extra = (f"; phase-1 low-side off {mm['lo1_after_master_ns']:.2f} ns after the master (target {mm['target_ns']:.2f}, sd {mm['lo1_after_master_sd_ns']:.3f}), "
                     f"high-side on {mm['on1_after_master_ns']:.2f} ns") if m else ""
            print(f"   module {m}: period {mm['period_ns']:.2f} ns, current {mm['current_a']:.1f} A, valleys " + "/".join(f"{v:+.2f}" for v in mm["valleys_a"])
                  + ", HS on " + "/".join(f"{v:.2f}" for v in mm["hs_on_vds_v"]) + ", LS max " + "/".join(f"{v:+.2f}" for v in mm["ls_on_vds_max_v"])
                  + ", off sd " + "/".join(f"{v:.2f}" for v in mm["off_sd_a"]) + extra)
        print("   added: piecewise-linear current " + "/".join(f"{mm['pl_current_a']:.1f}" for mm in mods) + f" A (sum {x['pl_sum_a']:.1f}), normalised to the load "
              + "/".join(f"{mm['pl_current_norm_a']:.1f}" for mm in mods) + " A; low-side turn-offs after the master's turn-on (ns): "
              + "; ".join("/".join(f"{v:.2f}" for v in mm["lsoff_after_master_ns"]) for mm in mods))
        if "ripple" in x:
            rp = x["ripple"]
            print(f"   added: output current ripple, one phase {rp['one_phase_pkpk_a']:.1f} A pk-pk, one module {rp['one_module_pkpk_a']:.1f}; system "
                  + ", ".join(f"{k} {v['pkpk_a']:.1f} A pk-pk / {v['rms_ac_a']:.2f} A rms" for k, v in rp.items() if isinstance(v, dict)))
        if "step" in x:
            print(f"   step: {x['step']['extreme_mv']:+.1f} mV at {x['step']['t_extreme_us']:.1f} us (D59 {D59[name]:+.1f}), back within 1% {x['step']['back_within_1pct_us']:.1f} us")
        print("   criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "c01_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("\nwrote c01_summary.json")


if __name__ == "__main__":
    main()
