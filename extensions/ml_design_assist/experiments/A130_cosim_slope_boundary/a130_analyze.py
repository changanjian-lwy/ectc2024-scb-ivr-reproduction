"""A130 analysis against BOUNDARY Section 2: per row and phase the peak after the step, Vo extreme, late fires, vs
D63 and the A125 bands; spec table. Writes a130_summary.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402

ROWS = ("l_m80_6us", "l_m80_7p5us", "l_p48_2us", "l_p48_3us", "l_p80_10us")
PR = json.loads((HERE / "a130_predictions.json").read_text())


def main():
    out = {}
    for row in ROWS:
        res = {}
        for ph, t in (("a", 800e-6), ("b", 800.33e-6)):
            d = json.loads((HERE / "cosim" / f"run_y130_{row}_{ph}.json").read_text())
            pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= t)
            st = step_stats(d, t_step=800e-6)
            res[ph] = {"peak_a": pk, "extreme_mv": st["extreme_mv"], "late": sum(d["late_fires"]), "overlaps": d["overlaps"]}
        worst = max(res["a"]["peak_a"], res["b"]["peak_a"])
        p = PR[row]
        out[row] = {**res, "worst_a": worst, "verdict": "fail" if worst > 200 else "marginal" if worst > 193 else "pass",
                    "d63_a": p["gated"]["peak_a"], "in_M80": p["band_peak_M80"][0] <= worst <= p["band_peak_M80"][1],
                    "in_G80": p["band_peak_G80"][0] <= worst <= p["band_peak_G80"][1]}
        print(f"{row:12s} a {res['a']['peak_a']:6.1f} b {res['b']['peak_a']:6.1f} A  D63 {p['gated']['peak_a']:6.1f}  "
              f"Vo {res['a']['extreme_mv']:+.1f}/{res['b']['extreme_mv']:+.1f} mV  late {res['a']['late']}/{res['b']['late']}  "
              f"{out[row]['verdict']}  M80 {out[row]['in_M80']} G80 {out[row]['in_G80']}")
    (HERE / "a130_summary.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
