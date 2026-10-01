"""A98 analysis: jitter statistics of co-simulation runs, on the same definitions as D53's Monte Carlo
(src/scb_ivr/p24_jitter.mc_stats), over each run's last 200 cycles.

cosim_stats(run): per phase, the low-side turn-off current spread and two-cycle component; the high-side early
fraction (turn-on before the valley), the high-side error (turn-on - valley) mean and spread over the other
turn-ons, and the valley time after the actual low-side turn-off; the low-side early fraction (turn-on before the
crossing) and error (turn-on - crossing); the period spread; the windowed dither (A89's metric over windows of 20
sections). Run as a script: the archived jitter runs of A92, A93 and A97 and A98's runs, and A98's runs against
D53's predictions (d53_predictions.json, BOUNDARY Section 5.3: spread within 20% and early fraction within 8
points of the median, phases 2-4); writes a98_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
sys.path.insert(0, str(TA.parents[1] / "src"))
from scb_ivr.p24_jitter import two_cycle, windowed_dither  # noqa: E402

LAST = 200


def cosim_stats(path):
    d = json.loads(Path(path).read_text())
    out = {"ilo_sd_a": [], "ilo_two_cycle_a": [], "early_high_frac": [], "eh_mean_sd_ns": [], "valley_sd_ns": [],
           "early_low_frac": [], "el_mean_sd_ns": []}
    for k in range(1, 5):
        lo = [o for o in d["lowoffs_last"] if o["phase"] == k]
        ilo = np.array([o["i_a"] for o in lo][-LAST:])
        out["ilo_sd_a"].append(float(ilo.std())); out["ilo_two_cycle_a"].append(two_cycle(ilo))
        ton = [t for t in d["turnons_last"] if t["phase"] == k][-LAST:]
        early = np.array([bool(t.get("early")) for t in ton])
        out["early_high_frac"].append(float(early.mean()))
        eh = np.array([t["err_s"] * 1e9 for t in ton if t.get("err_s") is not None])
        out["eh_mean_sd_ns"].append([float(eh.mean()), float(eh.std())])
        t_lo = np.array([o["t_s"] for o in lo])
        val = []
        for t in ton:
            if t.get("err_s") is None:
                continue
            prev = t_lo[t_lo < t["t_s"]]
            if len(prev):
                val.append((t["t_s"] - t["err_s"] - prev[-1]) * 1e9)
        out["valley_sd_ns"].append(float(np.std(val)))
        lon = [x for x in d["lowons_last"] if x["phase"] == k and x["mode_p"]][-LAST:]
        out["early_low_frac"].append(float(np.mean([not x["crossed"] for x in lon])))
        el = np.array([(x["t_since_off_s"] - x["t_cross_rel_s"]) * 1e9 for x in lon if x["crossed"]])
        out["el_mean_sd_ns"].append([float(el.mean()), float(el.std())])
    sec = d["sections"][-(LAST + 1):]
    out["period_sd_ns"] = float(np.std(np.diff([s["t_s"] for s in sec])) * 1e9)
    dith = windowed_dither(np.array([s["i"] for s in sec[1:]]))
    out["dither_window_mean_sd_a"] = [float(dith.mean()), float(dith.std())]
    return out


RUNS = {  # name: (rule, sigma_ps, path relative to TA)
    "A92_n0": ("fixed", 0, "A92_verilog_error_based_correctors/cosim/run_n0_nominal.json"),
    "A92_j30": ("fixed", 30, "A92_verilog_error_based_correctors/cosim/run_j30_jitter_30ps.json"),
    "A92_j100": ("fixed", 100, "A92_verilog_error_based_correctors/cosim/run_j100_jitter_100ps.json"),
    "A93_n0": ("follow", 0, "A93_verilog_period_following_slots/cosim/run_n0_both.json"),
    "A93_j30": ("follow", 30, "A93_verilog_period_following_slots/cosim/run_j30_both.json"),
    "A93_j100": ("follow", 100, "A93_verilog_period_following_slots/cosim/run_j100_both.json"),
    "A97_n0": ("avg", 0, "A97_verilog_averaged_period_slots/cosim/run_n0_avg_guard.json"),
    "A97_j30": ("avg", 30, "A97_verilog_averaged_period_slots/cosim/run_j30_avg_guard.json"),
    "A97_j100": ("avg", 100, "A97_verilog_averaged_period_slots/cosim/run_j100_avg_guard.json"),
}


def main():
    out = {}
    runs = dict(RUNS)
    for p in sorted((HERE / "cosim").glob("run_*.json")):
        runs[f"A98_{p.stem[4:]}"] = ("avg", None, str(p.relative_to(TA)))
    for name, (rule, sig, rel) in runs.items():
        s = cosim_stats(TA / rel)
        out[name] = {"rule": rule, "sigma_ps": sig, **s}
        f = lambda v: [round(x, 3) for x in v]  # noqa: E731
        print(f"{name:14s} ilo sd {f(s['ilo_sd_a'])} | early_h {f(s['early_high_frac'])} | eh sd "
              f"{f([x[1] for x in s['eh_mean_sd_ns']])} | valley sd {f(s['valley_sd_ns'])} | early_l "
              f"{f(s['early_low_frac'])} | el sd {f([x[1] for x in s['el_mean_sd_ns']])} | T sd {s['period_sd_ns']:.3f} | "
              f"dither {s['dither_window_mean_sd_a'][0]:.2f}")
    pred = json.loads((HERE / "d53_predictions.json").read_text())
    out["against_d53"] = {}
    for name, pr in pred.items():
        r = out.get(f"A98_{name}")
        if r is None:
            continue
        sd_med, eh_med = pr["ilo_sd_ph2_4_p5_p50_p95"][1], pr["early_high_ph2_4_p5_p50_p95"][1]
        sd_rel = [r["ilo_sd_a"][k + 1] / sd_med[k] - 1 for k in range(3)]
        eh_dif = [r["early_high_frac"][k + 1] - eh_med[k] for k in range(3)]
        ok = all(abs(x) <= 0.20 for x in sd_rel) and all(abs(x) <= 0.08 for x in eh_dif)
        out["against_d53"][name] = {"spread_rel_to_median": sd_rel, "early_minus_median": eh_dif, "agree": ok}
        print(f"{name:8s} spread vs D53 median {[f'{x:+.0%}' for x in sd_rel]} | early - median "
              f"{[f'{x * 100:+.1f} pt' for x in eh_dif]} | {'AGREES' if ok else 'OUTSIDE'} (BOUNDARY 5.3)")
    (HERE / "a98_summary.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
