"""D60: the series-capacitor ladder in mode P (relaxation, not resonance) with D59's loop (A107).

    python3 scripts/p24_ladder_loop.py

1. The ladder's time constants over the Cs range carried since CFLY_FIRST_PRINCIPLES_ESTIMATE (0.6-8.7 uF).
2. Validation against A106 (Cs 3 uF): the ladder deviation's peak after the line steps, and the slowest time constant
   fitted to the co-simulation's rising-step trace (5-16 us after the step).
3. Mode S (fixed timing during the input ramp): Roberts' resonances (Eq. 3.44) and the 68.61 us ramp's margin.
4. Predictions for A107 (I2 at Cs 0.6 and 8.7 uF): the line steps' ladder peak and settling (D60), the load steps'
   excursions (D59; Cs does not enter the averaged output equation).
Writes symbolic_derivations/03_P24_native/diagnostics/D60_ladder_loop.json and A107's d60_predictions.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

from scb_ivr.p24_ladder_loop import metrics, relaxation_us, run  # noqa: E402
from scb_ivr.p24_startup_averaged import LSB, Module  # noqa: E402
from scb_ivr.p24_voltage_loop import design_pi, ladder_f, step, step_metrics  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
A107 = TA / "A107_p24_series_capacitor_range"
CS = (0.6e-6, 1.45e-6, 3e-6, 4.34e-6, 8.7e-6)
BASE_DEV = 0.0047                 # A106's ladder deviation before the steps (the sampling offset at 48 V)


def main():
    m = Module()
    kp, ki = design_pi(100e3)
    out = {"conditions": {"ton_lsb": 568, "period_s": 232.2e-9, "lf_h": m.lf, "pi": {"kp_lsb_per_v": kp, "ki_lsb_per_v_per_sample": ki}}}
    print("1. ladder time constants in mode P (us), slowest first")
    out["relaxation_us"] = {}
    for cs in CS:
        r = relaxation_us(cs, m)
        out["relaxation_us"][f"{cs * 1e6:g}"] = r
        print(f"   Cs {cs * 1e6:5.2f} uF: " + ", ".join(f"{x:.2f}" for x in r))

    print("\n2. validation against A106 (3 uF)")
    s = json.loads((TA / "A106_p24_line_steps" / "a106_summary.json").read_text())
    val = {}
    for row, (dv, sl) in (("m48_1us", (-4.8, 1)), ("p48_1us", (4.8, 1)), ("m48_10us", (-4.8, 10)), ("p48_10us", (4.8, 10))):
        t, vo, ton, dev = run(kp, ki, cs=3e-6, dvin=dv, t_slew=sl * 1e-6)
        x = metrics(t, vo, dev, base_dev=BASE_DEV)
        c = s[f"pi100_{row}"]
        val[row] = {"d60": x, "cosim": {k: c[k] for k in ("extreme_mv", "ladder_dev_peak", "ladder_back_below_1pct_us")}}
        print(f"   {row}: ladder peak D60 {100 * x['ladder_dev_peak']:.2f}% / co-sim {100 * c['ladder_dev_peak']:.2f}%; "
              f"back below 1% D60 {x['ladder_back_below_1pct_us']:.1f} / co-sim {c['ladder_back_below_1pct_us']:.1f} us")
    d = json.loads((TA / "A106_p24_line_steps" / "cosim" / "run_pi100_p48_1us.json").read_text())
    secs = [q for q in d["sections"] if 405e-6 <= q["t_s"] <= 416e-6]
    tt = np.array([q["t_s"] for q in secs]); e1 = np.array([q["vcs_v"][0] / q["vin_v"] - 0.75 for q in secs])
    tail = np.median([q["vcs_v"][0] / q["vin_v"] - 0.75 for q in d["sections"] if q["t_s"] > 550e-6])
    tau = float(-1.0 / np.polyfit(tt, np.log(np.abs(e1 - tail)), 1)[0] * 1e6)
    val["slowest_tau_fit_us"] = {"cosim_rising_step": tau, "d60": relaxation_us(3e-6, m)[0]}
    print(f"   slowest time constant: co-simulation (rising step, 5-16 us) {tau:.1f} us, D60 {relaxation_us(3e-6, m)[0]:.1f} us")
    out["validation"] = val

    print("\n3. mode S (fixed timing, D = 568 LSB / 200 ns): Roberts' resonances and the 68.61 us ramp's margin")
    d_s = 568 * LSB / 200e-9
    rs = {}
    for cs in CS:
        f = ladder_f(cs, m, d=d_s)
        margin = 68.61e-6 / (0.35 / f[0])
        rs[f"{cs * 1e6:g}"] = {"f_hz": f, "ramp_margin_x": margin}
        print(f"   Cs {cs * 1e6:5.2f} uF: f1 {f[0] / 1e3:6.1f} kHz; ramp margin {margin:5.1f}x (Roberts used 30x)")
    out["mode_s"] = rs

    print("\n4. predictions for A107 (I2, Cs 0.6 and 8.7 uF)")
    pred = {}
    for cs in (0.6e-6, 8.7e-6):
        key = f"cs{cs * 1e6:g}".replace(".", "p")
        pred[key] = {"relaxation_us": relaxation_us(cs, m), "mode_s": rs[f"{cs * 1e6:g}"]}
        for row, (dv, sl) in (("l_m48_1us", (-4.8, 1)), ("l_p48_1us", (4.8, 1))):
            t, vo, ton, dev = run(kp, ki, cs=cs, dvin=dv, t_slew=sl * 1e-6)
            pred[key][row] = metrics(t, vo, dev, base_dev=BASE_DEV)
        for row, i_step in (("s_m62", -62.5), ("s_p62", 62.5)):
            pred[key][row] = step_metrics(*step(i_step, kp, ki, m))
        print(f"   {key}: time constants " + ", ".join(f"{x:.2f}" for x in pred[key]["relaxation_us"]) + " us; "
              + "; ".join(f"{r}: ladder {100 * pred[key][r]['ladder_dev_peak']:.2f}%, back below 1% {pred[key][r]['ladder_back_below_1pct_us']:.1f} us"
                          for r in ("l_m48_1us", "l_p48_1us"))
              + f"; steps {pred[key]['s_m62']['extreme_mv']:+.1f} / {pred[key]['s_p62']['extreme_mv']:+.1f} mV")
    out["predictions"] = pred
    (DIAG / "D60_ladder_loop.json").write_text(json.dumps(out, indent=1, default=float))
    A107.mkdir(parents=True, exist_ok=True)
    (A107 / "d60_predictions.json").write_text(json.dumps(pred, indent=1, default=float))
    print(f"\nwrote {(DIAG / 'D60_ladder_loop.json').relative_to(ROOT)} and {(A107 / 'd60_predictions.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
