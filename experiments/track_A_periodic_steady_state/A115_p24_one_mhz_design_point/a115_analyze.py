"""A115 analysis against BOUNDARY Section 5, on the registered a115_predictions.json. Per n row, over the last 200
periods: each phase's high-side turn-on V_DS (mean and maximum), valley, peak, ripple (peak - valley) and low-side
turn-on V_DS maximum; Ton, the period, Vo, late fires; the D62 middle-case budget on the measured waveforms with
L = 7.333 nH (and the ideal-inductor case); the summed output current's pk-pk and the output-voltage ripple per
period (informational, against C02's 5 MHz s1_n0). Step rows: matrix.step_stats at 2000 us against D59. j30: the
turn-off sd and the high side against n10. Writes a115_summary.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import GRID_S, phase_waveform, ref_turnons, step_stats, window_stats  # noqa: E402
from scb_ivr.p24_loss_budget import budget, measure  # noqa: E402

spec = importlib.util.spec_from_file_location("d62_script", PROJECT / "scripts" / "p24_loss_budget.py")
D62 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D62)
L1, CO, T_STEP = 7.3333333e-9, 4.672e-3, 2000e-6
C02 = PROJECT / "experiments" / "track_C_multi_module" / "C02_uniform_interleave" / "cosim"
RIPPLE_5MHZ_5PCT = 140.6                     # A110 n5 (C02 s1_n0): mean peak - mean valley, A
PRED = json.loads((HERE / "a115_predictions.json").read_text())
ROWS = {"n5": 5.0, "n7p5": 7.5, "n10": 10.0, "n12p5": 12.5}


def load(p):
    return json.loads(Path(p).read_text())


def vo_ripple(d, lf_periods=50, n_phases=4):
    """Per period, medians over lf_periods periods (the run's last period left out: its later phases' events are cut
    by the run's end): the summed output current's pk-pk (A) and the output voltage's ripple (mV, pk-pk of the charge
    into Co with the period's linear trend removed)."""
    t_on, _ = ref_turnons(d, None, lf_periods + 2)
    t_on = t_on[:-1]
    g = np.arange(t_on[0], t_on[-1], GRID_S)
    tot = sum(phase_waveform(d, k, g) for k in range(1, n_phases + 1))
    q = np.cumsum(tot - tot.mean()) * GRID_S
    ipp, vpp = [], []
    for a, b in zip(t_on[:-1], t_on[1:]):
        s = (g >= a) & (g < b)
        x, y = g[s], q[s]
        y = y - np.polyval(np.polyfit(x - a, y, 1), x - a)
        ipp.append(np.ptp(tot[s])); vpp.append(np.ptp(y) / CO * 1e3)
    return {"i_pkpk_a": float(np.median(ipp)), "vo_ripple_mv": float(np.median(vpp))}


def settling(d, t_hand=360e-6, t_dip=140e-6):
    """Not registered (RESULTS 0.3): max |Vo - 1 V| (mV) at the sections over the handover's first t_dip, from then to
    the timed turn-off's start, and from 100 us after it to the end (or to the load step)."""
    s = d["sections"]
    t = np.array([x["t_s"] for x in s]); dv = np.abs(np.array([x["vo"] for x in s]) - 1.0) * 1e3
    t_lo = d["t_lo_timed_s"]
    t_end = d["cfg"]["load_step"]["t_us"] * 1e-6 if d["cfg"].get("load_step") else t[-1] + 1.0
    win = lambda a, b: float(dv[(t >= a) & (t < b)].max())
    return {"handover_mv": win(t_hand, t_hand + t_dip), "before_timed_mv": win(t_hand + t_dip, t_lo),
            "after_timed_mv": win(t_lo + 100e-6, t_end), "t_lo_timed_us": t_lo * 1e6}


def row(d, t1=None):
    w = window_stats(d, t1=t1)
    m = measure(d, t1=t1)
    args = (m["phases"], m["ton_s"], m["period_s"], L1)
    kw = dict(p_rev=m["p_rev_w"], p_out=m["p_out_w"])
    b = budget(*args, D62.SCENARIOS["middle"], m["rails_v"], m["dv_next_v"], **kw)
    bi = budget(*args, D62.SCENARIOS["middle_ideal_inductor"], m["rails_v"], m["dv_next_v"], **kw)
    t0, t1w = w["window_us"][0] * 1e-6, w["window_us"][1] * 1e-6
    on = [t for t in d["turnons_last"] if t0 <= t["t_s"] <= t1w]
    return {"hs_on_vds_v": [p["hs_on_vds_v"] for p in w["phases"]],
            "hs_on_vds_max_v": [max(t["vds_v"] for t in on if t["phase"] == k) for k in (1, 2, 3, 4)],
            "valleys_a": [p["valley"] for p in m["phases"]], "peaks_a": [p["peak"] for p in m["phases"]],
            "ripple_a": [p["peak"] - p["valley"] for p in m["phases"]],
            "ls_on_vds_max_v": [p["ls_on_vds_max_v"] for p in w["phases"]], "off_sd_a": [p["i_off_sd_a"] for p in w["phases"]],
            "ton_ns": m["ton_s"] * 1e9, "period_ns": m["period_s"] * 1e9, "rails_v": m["rails_v"], "vo_mean_v": w["vo_mean_v"],
            "overlaps": d["overlaps"], "ipk_a": d["ipk_a"], "late_fires": d["late_fires"], "budget_w": b,
            "efficiency_pct": b["efficiency"] * 100, "efficiency_ideal_inductor_pct": bi["efficiency"] * 100,
            "p_rev_w": m["p_rev_w"], "dt_pred_final_ns": d.get("dt_pred_final_ns")}


def main():
    res = {}
    ref5 = load(C02 / "run_s1_n0.json")
    res["ref_5mhz_s1_n0"] = {"ripple": vo_ripple(ref5), "period_ns": window_stats(ref5)["period_ns"]}
    print("5 MHz reference (C02 s1_n0): output current {i_pkpk_a:.1f} A pk-pk, Vo ripple {vo_ripple_mv:.3f} mV".format(
        **res["ref_5mhz_s1_n0"]["ripple"]))
    for name, pct in ROWS.items():
        p = HERE / "cosim" / f"run_{name}.json"
        if not p.exists():
            continue
        d = load(p)
        x, pr = row(d), PRED[f"1MHz_{name}"]
        x["output"] = vo_ripple(d)
        x["settling"] = settling(d)
        v1, v4 = pr["hs_on_vds_v_phase1"], pr["hs_on_vds_v_phase4"]
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0, "ls_zvs": max(x["ls_on_vds_max_v"]) <= 0.0,
             "vo_1mV": abs(x["vo_mean_v"] - 1.0) <= 1e-3, "late_5": sum(x["late_fires"]) <= 5,
             "period_2pct": abs(x["period_ns"] / pr["period_ns"] - 1) <= 0.02, "ton_5pct": abs(x["ton_ns"] / pr["ton_ns"] - 1) <= 0.05,
             "peak_5A": all(abs(v - pr["peak_a"]) <= 5.0 for v in x["peaks_a"]),
             "ripple_5A": all(abs(v - pr["ripple_pp_a"]) <= 5.0 for v in x["ripple_a"]),
             "efficiency_0p7": abs(x["efficiency_pct"] - pr["efficiency_pct"]["middle"]) <= 0.7}
        if pct == 12.5:
            c["hs_zvs_0p3V"] = max(x["hs_on_vds_v"]) <= 0.3
        else:
            c["hs_d57_0p6V"] = all(abs(v - v1) <= 0.6 for v in x["hs_on_vds_v"][:3]) and abs(x["hs_on_vds_v"][3] - v4) <= 1.0
        if pct == 10.0:
            c["hs_2p5V"] = max(x["hs_on_vds_v"]) <= 2.5
            c["ripple_1p10_5mhz"] = float(np.mean(x["ripple_a"])) <= 1.10 * RIPPLE_5MHZ_5PCT
        x["criteria"] = c
        res[name] = x
        b = x["budget_w"]
        print(f"{name}: HS on " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_v"]) + " V (max " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_max_v"])
              + f"; D57 {v1:+.2f} / phase 4 {v4:+.2f}); valleys " + "/".join(f"{v:+.1f}" for v in x["valleys_a"]) + ", peaks "
              + "/".join(f"{v:.1f}" for v in x["peaks_a"]) + f" (pred {pr['peak_a']:.1f}), ripple " + "/".join(f"{v:.1f}" for v in x["ripple_a"])
              + f" (pred {pr['ripple_pp_a']:.1f}) A")
        print(f"     Ton {x['ton_ns']:.2f} ns (pred {pr['ton_ns']:.2f}), T {x['period_ns']:.1f} ns (pred {pr['period_ns']:.1f}), ipk {x['ipk_a']:.0f} A, "
              f"LS max {max(x['ls_on_vds_max_v']):+.2f} V, Vo {x['vo_mean_v']:.5f} V, late {x['late_fires']}, sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"])
              + f"; output {x['output']['i_pkpk_a']:.1f} A pk-pk, Vo ripple {x['output']['vo_ripple_mv']:.3f} mV")
        print("     settling (not registered): |Vo - 1| max {handover_mv:.1f} mV after the handover, {before_timed_mv:.1f} mV until the "
              "timed turn-off ({t_lo_timed_us:.0f} us), {after_timed_mv:.1f} mV after it".format(**x["settling"]))
        print("     loss " + ", ".join(f"{k} {v:.2f}" for k, v in b.items() if k not in ("total", "efficiency"))
              + f" | total {b['total']:.2f} W, efficiency {x['efficiency_pct']:.2f}% (pred {pr['efficiency_pct']['middle']:.2f}%), "
              f"ideal inductor {x['efficiency_ideal_inductor_pct']:.2f}%")
        print("     criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    for pct, tag in ((5.0, "n5"), (10.0, "n10")):
        lp = PRED[f"loop_1MHz_{tag}"]
        for s in ("s_p62", "s_m62"):
            name = f"{tag}_{s}"
            p = HERE / "cosim" / f"run_{name}.json"
            if not p.exists():
                continue
            d = load(p)
            st, ps = step_stats(d, t_step=T_STEP), lp[s]
            c = {"no_overlap": d["overlaps"] == 0, "peak_200a": d["ipk_a"] <= 200.0,
                 "step_30pct": abs(st["extreme_mv"] / ps["extreme_mv"] - 1) <= 0.30,
                 "back_60us": st["back_within_1pct_us"] <= 60.0}
            res[name] = {"step": st, "d59": ps, "ipk_a": d["ipk_a"], "late_fires": d["late_fires"], "criteria": c,
                         "before": {k: v for k, v in row(d, t1=T_STEP).items() if k in ("hs_on_vds_v", "ripple_a", "vo_mean_v")}}
            print(f"{name}: step {st['extreme_mv']:+.2f} mV at {st['t_extreme_us']:.1f} us, back {st['back_within_1pct_us']:.2f} us "
                  f"(D59 {ps['extreme_mv']:+.2f} / {ps['back_within_1pct_us']:.2f}), ladder peak {st['ladder_dev_peak'] * 100:.2f}%, "
                  f"ipk {d['ipk_a']:.0f} A, late {d['late_fires']}; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    p = HERE / "cosim" / "run_n10_j30.json"
    if p.exists() and "n10" in res:
        x = row(load(p))
        c = {"no_overlap": x["overlaps"] == 0, "peak_200a": x["ipk_a"] <= 200.0, "sd_0p5A": max(x["off_sd_a"]) <= 0.5,
             "hs_n10_0p3V": all(abs(a - b) <= 0.3 for a, b in zip(x["hs_on_vds_v"], res["n10"]["hs_on_vds_v"]))}
        x["criteria"] = c
        res["n10_j30"] = x
        print("n10_j30: HS on " + "/".join(f"{v:+.2f}" for v in x["hs_on_vds_v"]) + " V, sd " + "/".join(f"{v:.2f}" for v in x["off_sd_a"])
              + f" (n10 " + "/".join(f"{v:.2f}" for v in res["n10"]["off_sd_a"]) + f"), ipk {x['ipk_a']:.0f} A, late {x['late_fires']}, "
              f"efficiency {x['efficiency_pct']:.2f}%; " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in c.items()))
    (HERE / "a115_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote a115_summary.json")


if __name__ == "__main__":
    main()
