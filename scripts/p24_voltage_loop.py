"""D59: the P24 module's output-voltage loop, a sampled PI on Ton (A104).

    python3 scripts/p24_voltage_loop.py

1. Validation: A100's +-62.5 A steps with the present integral loop (ki 0.25 ns/V) against the co-simulation.
2. Designs at 30, 60, 100 and 150 kHz (P for the crossover, the integral zero at fc / 5): gains in LSB and in the
   bridge's ns/V units, crossover and phase margin with a 0.75-period delay; the series-capacitor resonances.
3. Predictions for A104: the +-62.5 A steps; A103's c1d start-up with each loop, and the recovery from c1d's
   measured handover state (1.013 V, Ton 568 LSB).
Writes symbolic_derivations/03_P24_native/diagnostics/D59_voltage_loop.json and A104's d59_predictions.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

from scb_ivr.p24_startup_averaged import LSB, Module  # noqa: E402
from scb_ivr.p24_voltage_loop import design_pi, ladder_f, margins, plant, startup, step, step_metrics  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
A104 = TA / "A104_p24_voltage_loop_pi"
KI_NOW = 0.25 / (LSB * 1e9)          # 0.25 ns/V -> LSB per V per sample
DESIGNS = {"fc30": 30e3, "fc60": 60e3, "fc100": 100e3, "fc150": 150e3}
VO_HAND_C1D = 1.013                  # A103 c1d's Vo at the handover (co-simulation), Ton 568 LSB


def time_above(t, vo, level):
    """Length of the excursion above level that contains the maximum (0 if the maximum is below)."""
    i = int(np.argmax(vo))
    if vo[i] <= level:
        return 0.0
    a = b = i
    while a > 0 and vo[a - 1] > level:
        a -= 1
    while b < len(vo) - 1 and vo[b + 1] > level:
        b += 1
    return float((t[b] - t[a]) * 1e6)


def startup_metrics(t, vo):
    i = int(np.argmax(vo))
    bad = np.nonzero(np.abs(vo - 1.0) > 0.01)[0]
    return {"vo_max_v": float(vo[i]), "t_vo_max_us": float(t[i] * 1e6), "t_above_1v_us": time_above(t, vo, 1.0),
            "t_above_1v005_us": time_above(t, vo, 1.005), "settle_1pct_us": float(t[bad[-1]] * 1e6) if len(bad) else 0.0}


def main():
    m = Module()
    g, g_src, g_load = plant(m)
    out = {"conditions": {"g_a_per_lsb": g, "g_src_s": g_src, "g_load_s": g_load, "co_f": m.co, "ts_s": 232.2e-9,
                          "plant_pole_hz": (g_load + g_src) / m.co / (2 * np.pi), "ladder_hz_cs3uF": ladder_f()}}
    print(f"plant: g {g:.3f} A/LSB, pole {out['conditions']['plant_pole_hz'] / 1e3:.1f} kHz; series-capacitor resonances (Cs 3 uF) "
          + ", ".join(f"{f / 1e3:.0f}" for f in ladder_f()) + " kHz")

    print("\n1. validation: A100's steps, integral loop ki 0.25 ns/V")
    val = {}
    for tag, i_step in (("m62", -62.5), ("p62", 62.5)):
        t, vo, ton = step(i_step, 0.0, KI_NOW)
        x = step_metrics(t, vo, ton)
        d = json.loads((TA / "A100_timed_turn_off_load_steps" / "cosim" / f"run_ref_{tag}.json").read_text())
        s = [q for q in d["sections"] if q["t_s"] >= 400e-6]
        dv = [q["vo"] - 1.0 for q in s]
        j = int(np.argmax(np.abs(dv)))
        val[tag] = {"model": x, "cosim_extreme_mv": dv[j] * 1e3, "cosim_t_extreme_us": (s[j]["t_s"] - 400e-6) * 1e6}
        print(f"   {tag}: model {x['extreme_mv']:+.1f} mV at {x['t_extreme_us']:.1f} us | co-simulation {dv[j] * 1e3:+.1f} mV at {val[tag]['cosim_t_extreme_us']:.1f} us")
    out["validation"] = val
    fc0, pm0 = margins(0.0, KI_NOW, m)
    out["present_loop"] = {"ki_lsb_per_v": KI_NOW, "fc_hz": fc0, "pm_deg": pm0}
    print(f"   present loop: crossover {fc0 / 1e3:.1f} kHz, phase margin {pm0:.0f} deg")

    print("\n2-3. designs and predictions")
    pred = {"ref": {"kp_ns_per_v": 0.0, "ki_ns_per_v": 0.25}}
    t, vo, ton = startup(0.0, KI_NOW)
    pred["ref"]["startup"] = startup_metrics(t, vo)
    t, vo, ton = step(0.0, 0.0, KI_NOW, m, t_end=120e-6, vo0=VO_HAND_C1D)
    pred["ref"]["from_c1d_handover"] = startup_metrics(t, vo)
    for tag, i_step in (("m62", -62.5), ("p62", 62.5)):
        pred["ref"][tag] = step_metrics(*step(i_step, 0.0, KI_NOW))
    for name, fc in DESIGNS.items():
        kp, ki = design_pi(fc, m)
        f, pm = margins(kp, ki, m)
        row = {"fc_target_hz": fc, "kp_lsb_per_v": kp, "ki_lsb_per_v_per_sample": ki,
               "kp_ns_per_v": kp * LSB * 1e9, "ki_ns_per_v": ki * LSB * 1e9,
               "kp_lsb_per_adc_lsb": kp * 0.5e-3, "fc_hz": f, "pm_deg": pm}
        for tag, i_step in (("m62", -62.5), ("p62", 62.5)):
            row[tag] = step_metrics(*step(i_step, kp, ki, m))
        t, vo, ton = startup(kp, ki)
        row["startup"] = startup_metrics(t, vo)
        t, vo, ton = step(0.0, kp, ki, m, t_end=120e-6, vo0=VO_HAND_C1D)
        row["from_c1d_handover"] = startup_metrics(t, vo)
        pred[name] = row
    for name, row in pred.items():
        hdr = (f"   {name:5s}: kp {row['kp_ns_per_v']:6.1f} ns/V, ki {row['ki_ns_per_v']:5.2f} ns/V"
               + (f" (fc {row['fc_hz'] / 1e3:5.1f} kHz, PM {row['pm_deg']:3.0f} deg, {row['kp_lsb_per_adc_lsb']:.2f} LSB per ADC LSB)" if "fc_hz" in row else ""))
        print(hdr)
        for tag in ("m62", "p62"):
            x = row[tag]
            print(f"          {tag}: {x['extreme_mv']:+6.1f} mV at {x['t_extreme_us']:4.1f} us, back within 1% {x['back_within_1pct_us']:5.1f} us, "
                  f"late Ton p-p {x['ton_pp_late_lsb']:.0f} LSB, late Vo p-p {x['vo_pp_late_mv']:.2f} mV")
        s = row["startup"]
        h = row["from_c1d_handover"]
        print(f"          from c1d's handover state (1.013 V): {h['t_above_1v005_us']:.1f} us above 1.005 V, {h['t_above_1v_us']:.1f} us above 1 V")
        print(f"          start-up (c1d): max {s['vo_max_v']:.4f} V at {s['t_vo_max_us']:.1f} us, {s['t_above_1v_us']:.1f} us above 1 V "
              f"({s['t_above_1v005_us']:.1f} us above 1.005 V), within 1% from {s['settle_1pct_us']:.1f} us")
    out["predictions"] = pred
    (DIAG / "D59_voltage_loop.json").write_text(json.dumps(out, indent=1, default=float))
    A104.mkdir(parents=True, exist_ok=True)
    (A104 / "d59_predictions.json").write_text(json.dumps(pred, indent=1, default=float))
    print(f"\nwrote {(DIAG / 'D59_voltage_loop.json').relative_to(ROOT)} and {(A104 / 'd59_predictions.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
