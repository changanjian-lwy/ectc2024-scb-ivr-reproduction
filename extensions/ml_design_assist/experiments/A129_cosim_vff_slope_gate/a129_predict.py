"""A129 registered predictions (before any run): D63 with A128's RTL-exact feed-forward (a128_predict.law_rtl) plus
the slope gate of scb_vff.v - the falling term acts only from the sample where g = max(lp2 - Vin, 0) reaches GTH codes
until g is back to 0 (lp2 in the RTL's Q8 integers, so g does reach 0); phase 1's cap is untouched. Rows: A124's seven
step rows (Cs x 1, 600 periods) with the gate, without it (A128) and without feed-forward, plus three falling rows
outside the matrix that show where the gate sits. A125's bands on the gated peak (Mondrian and signed, 80%) and the
|Vo| band (x0.56-1.44). Writes a129_predictions.json."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ML = HERE.parent
spec = importlib.util.spec_from_file_location("a128_predict", ML / "A128_cosim_vin_feedforward" / "a128_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
R, C, F = P.R, P.C, P.F
GTH = 100                                                     # gate threshold, Vin codes (20 mV): 2.0 V
EXTRA = {"x_l_m48_2us": ("line", -4.8, 2.0), "x_l_m48_3us": ("line", -4.8, 3.0), "x_l_m80_5us": ("line", -8.0, 5.0)}


def law_gated(env, gth=GTH):
    scale, caps = P.law_rtl(env)
    st = env._rtl
    v8 = round(env.vin / P.LSBV) * 256
    if env.k == 0 or "q2" not in st:
        st.update(q2=v8, gate=False, gmax=0.0, opened=None)
    st["q2"] += (v8 - st["q2"]) >> P.VFF["sh2"]
    g = max(st["q2"] - v8, 0)
    st["gate"] = True if g >= gth * 256 else (False if g == 0 else st["gate"])
    st["gmax"] = max(st["gmax"], g / 256)
    if st["gate"] and st["opened"] is None:
        st["opened"] = env.k
    return (scale if st["gate"] else [1.0] * 4), caps


def main():
    env = R.make_env("vin_ff")
    out = {"gth_codes": GTH}
    for name, dist in {**F.A124_ROWS, **EXTRA}.items():
        row = {}
        for arm, law in (("gated", law_gated), ("a128", P.law_rtl), ("none", F.law_none)):
            recs, _, div = R.run(env, ("law", law), dist, 1.0, 600)
            s = F.summarise(recs)
            row[arm] = {"peak_a": s["peak_a"], "peaks_a": s["peaks_a"], "extreme_mv": s["extreme_mv"], "diverged": div}
            if arm == "gated":
                row[arm].update(gmax_codes=env._rtl["gmax"], opened_period=env._rtl["opened"])
        group = "rising" if dist[0] == "line" and dist[1] > 0 else "other"
        p, mv = row["gated"]["peak_a"], row["gated"]["extreme_mv"]
        row["band_peak_M80"] = C.register_band(p, "peak", group, 0.2, "M")
        row["band_peak_G80"] = C.register_band(p, "peak", group, 0.2, "G")
        row["band_abs_mv"] = [0.56 * abs(mv), 1.44 * abs(mv)]
        out[name] = row
        g = row["gated"]
        print(f"{name:16s}: gated {p:5.1f} A (A128 {row['a128']['peak_a']:5.1f}, none {row['none']['peak_a']:5.1f}), "
              f"M80 {row['band_peak_M80'][0]:.0f}-{row['band_peak_M80'][1]:.0f}; Vo {mv:+.1f} mV; gmax {g['gmax_codes']:.0f}, "
              f"opened {g['opened_period']}")
    (HERE / "a129_predictions.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
