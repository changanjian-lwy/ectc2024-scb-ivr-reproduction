"""A128 registered predictions (before any run): D63 (A127's environment) with the RTL-exact feed-forward of
scb_vff.v - 20 mV Vin codes sampled once per period, low-passes by shifts (2^-2, 2^-6), Q16 coefficients, phase 1's cap
from the previous sample (one-period lag) with the one-step Vin prediction - and without it, on A124's seven step
rows (Cs x 1, 600 periods). A125's bands on the peak (Mondrian and signed, 80%) and the magnitude band on Vo's
extreme (x0.56-1.44, chosen post hoc in A125). Writes a128_predictions.json."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ML = HERE.parent
spec = importlib.util.spec_from_file_location("run_a127", ML / "A127_ppo_anchored_feedforward" / "run_a127.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
spec = importlib.util.spec_from_file_location("run_a125", ML / "A125_conformal_registration" / "run_a125.py")
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
F = R.F
VFF = json.loads((HERE / "cosim" / "cfg_v125_l_p48_1us.json").read_text())["vff"]
LSBV, LSB, VO = VFF["vin_lsb_v"], 4e-9 / 128, round(1.0 / VFF["vin_lsb_v"])


def law_rtl(env):
    st = env.__dict__.setdefault("_rtl", {})
    v = round(env.vin / LSBV)
    if env.k == 0 or not st:
        st.update(lp2=v, lp20=v, cap=None, vp=v)
    cap_prev = st["cap"]
    st["lp2"] += (v - st["lp2"]) / 2 ** VFF["sh2"]
    st["lp20"] += (v - st["lp20"]) / 2 ** VFF["sh20"]
    g = max(st["lp2"] - v, 0.0)
    scale = [min(max(1 + c * g / 65536, 0.5), 1.25) for c in VFF["c"]]
    rail = (2 * v - st["vp"]) - 0.75 * st["lp20"] - VO
    st["vp"] = v
    st["cap"] = round(VFF["k"] / rail) * LSB if rail > 0 else math.inf
    return scale, [cap_prev if cap_prev is not None else math.inf, math.inf, math.inf, math.inf]


def main():
    env = R.make_env("vin_ff")
    out = {}
    for name, dist in F.A124_ROWS.items():
        row = {}
        for arm, law in (("vff", law_rtl), ("none", F.law_none)):
            recs, _, div = R.run(env, ("law", law), dist, 1.0, 600)
            s = F.summarise(recs)
            row[arm] = {"peak_a": s["peak_a"], "peaks_a": s["peaks_a"], "extreme_mv": s["extreme_mv"], "diverged": div}
        group = "rising" if dist[0] == "line" and dist[1] > 0 else "other"
        p, mv = row["vff"]["peak_a"], row["vff"]["extreme_mv"]
        row["band_peak_M80"] = C.register_band(p, "peak", group, 0.2, "M")
        row["band_peak_G80"] = C.register_band(p, "peak", group, 0.2, "G")
        row["band_abs_mv"] = [0.56 * abs(mv), 1.44 * abs(mv)]
        out[name] = row
        print(f"{name:16s}: D63 vff {p:5.1f} A (none {row['none']['peak_a']:5.1f}), M80 {row['band_peak_M80'][0]:.0f}-{row['band_peak_M80'][1]:.0f}, "
              f"G80 {row['band_peak_G80'][0]:.0f}-{row['band_peak_G80'][1]:.0f}; Vo {mv:+.1f} mV (none {row['none']['extreme_mv']:+.1f})")
    (HERE / "a128_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
