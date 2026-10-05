"""A140 cosim cfgs and registered D63 predictions. Arms on the adopted single-module design (C10 template: g125 + vff
rel_q8 320, rel_lp 1, seed 2): B = as adopted (gth 100), G = gth 50 (the D63 fix candidate), O = no vff. Line steps at
1000 us (+ k x 125 ns for the step-position repeats), end 1200 us, as A138. Predictions: a140_d63.run, mean / min /
max over 8 step positions, and the fraction of positions whose falling-term gate opens. Writes cosim/cfg_*.json and
a140_predictions.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a140_d63 as D  # noqa: E402

PROJECT = HERE.parents[2]
TEMPLATE = PROJECT / "experiments" / "track_C_multi_module" / "C10_seed_before_entry" / "cosim" / "cfg_s100_l_p48_1us.json"
COS = HERE / "cosim"
T_STEP_US, T_END_US, DT_POS_US = 1000.0, 1200.0, 0.125
ARMS = {"B": {}, "G": {"gth": 50}, "O": None}
# (arm, L x, dv, slews, step positions)
RUNS = [("B", 1.0, -4.8, (2.0, 2.5, 3.0, 4.0), (0,)), ("G", 1.0, -4.8, (1.0, 2.0, 2.5, 3.0, 4.0, 5.1), (0,)),
        ("B", 1.0, -6.4, (2.4, 3.1, 4.0), (0,)), ("G", 1.0, -6.4, (2.4, 3.1, 4.0, 5.7), (0,)),
        ("B", 1.0, -8.0, (4.0, 10.0), (0,)), ("G", 1.0, -8.0, (4.0, 10.0), (0,)),
        ("B", 1.3, -8.0, (10.0,), (0,)), ("G", 1.3, -8.0, (10.0, 12.1), (0,)),
        ("B", 0.7, -4.8, (2.4,), (0,)), ("G", 0.7, -4.8, (2.4,), (0,)),
        ("B", 0.7, 4.8, (10.0, 40.0), (0,)), ("B", 0.7, 4.8, (20.0,), (1, 2, 3)),
        ("O", 0.7, 4.8, (5.0, 20.0), (0,)), ("B", 0.7, 8.0, (20.0, 50.0), (0,)),
        ("G", 0.7, 4.8, (20.0,), (0,))]                       # identity: rising, gate never opens -> = A139 ur01
# runs of the adopted design already on record (A138 / A139 cosim, same RTL): name -> (arm, m, dv, slew, pos, path)
REUSED = {"B_L100_m4.8_s1.0": "extensions/ml_design_assist/experiments/A138_gp_boundary_map/cosim/run_vf05.json",
          "B_L100_m4.8_s5.125": "extensions/ml_design_assist/experiments/A139_gp_boundary_noise_floor/cosim/run_vf04.json",
          "B_L070_p4.8_s1.0": "extensions/ml_design_assist/experiments/A138_gp_boundary_map/cosim/run_xs070_l_p48_1us.json",
          "B_L070_p4.8_s5.0": "extensions/ml_design_assist/experiments/A138_gp_boundary_map/cosim/run_xs070_l_p48_5us.json",
          "B_L070_p4.8_s20.0": "extensions/ml_design_assist/experiments/A139_gp_boundary_noise_floor/cosim/run_ur01.json"}


def name(arm, m, dv, slew, pos):
    return f"{arm}_L{round(m * 100):03d}_{'m' if dv < 0 else 'p'}{abs(dv):.1f}_s{slew}" + (f"_q{pos}" if pos else "")


def cfg(n, arm, m, dv, slew, pos):
    t = json.loads(TEMPLATE.read_text())
    t["circuit"] = dict(t["circuit"], L=t["circuit"]["L"] * m)
    if ARMS[arm] is None:
        t.pop("vff")
    else:
        t["vff"] = dict(t["vff"], **ARMS[arm])
    t_step = T_STEP_US + pos * DT_POS_US
    t["line_step"] = {"t_us": t_step, "dv": dv, "slew_us": slew}
    t["t_end_us"] = T_END_US
    t["note"] = (f"A140 {n}: adopted single-module design, arm {arm} "
                 f"({'no vff' if ARMS[arm] is None else 'vff ' + json.dumps(ARMS[arm] or {'gth': 100})}), L x {m}, "
                 f"line step {dv:+.1f} V over {slew} us at {t_step:.3f} us.")
    t["out"] = f"run_{n}.json"
    (COS / f"cfg_{n}.json").write_text(json.dumps(t, indent=1) + "\n")


def predict(arm, m, dv, slew):
    p = D.BASE | ({"c": [0, 0, 0, 0], "cap": 0} if ARMS[arm] is None else ARMS[arm])
    rs = [D.run(m, 1.0, dv, slew, p, k) for k in range(D.N_POS)]
    pk = [r["peak"] for r in rs]
    return {"mean": float(np.mean(pk)), "min": float(np.min(pk)), "max": float(np.max(pk)),
            "gate_frac": float(np.mean([r["gate_n"] > 0 for r in rs])), "g_max": float(np.mean([r["g_max"] for r in rs]))}


def main():
    COS.mkdir(exist_ok=True)
    pred = {"note": "D63 + scb_vff (a140_d63.run), 8 step positions; ranks and locates, does not bound (A139: falling "
                    "D63 error +7.8 +- 19.6 A; A135: rising under-predicted by up to 17 A)", "runs": {}}
    for arm, m, dv, slews, poss in RUNS:
        for s in slews:
            for q in poss:
                n = name(arm, m, dv, s, q)
                cfg(n, arm, m, dv, s, q)
                pred["runs"][n] = predict(arm, m, dv, s)
    for n in REUSED:
        arm, L, d, s = n.split("_")
        pred["runs"][n] = predict(arm, int(L[1:]) / 100, (-1 if d[0] == "m" else 1) * float(d[1:]), float(s[1:]))
    (HERE / "a140_predictions.json").write_text(json.dumps(pred, indent=1) + "\n")
    print(f"{sum(len(r[3]) * len(r[4]) for r in RUNS)} cfgs, {len(pred['runs'])} predictions")
    for n, p in pred["runs"].items():
        print(f"{n:24s} {p['mean']:6.1f} ({p['min']:5.1f}-{p['max']:5.1f}) gate {p['gate_frac']:.2f}")


if __name__ == "__main__":
    main()
