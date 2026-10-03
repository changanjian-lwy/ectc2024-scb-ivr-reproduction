"""D64: the switching frequency a stripline inductor implies (scb_ivr.p24_inductor_model).

    python3 scripts/p24_frequency_choice.py

For f = 0.5-5 MHz (L by Eq. (4)) and negative-current targets 2.5-30%: the converter's losses with an ideal inductor
(a115_predict.row: D57, the orbit, D62 middle), its ripple and switching frequency, and D57's threshold; then, for
each stripline (gap h, copper t), the copper loss and the efficiency. Per stripline: the best target at each f (with
the valley margin I_th - i_neg >= 2 A, the margin A118's floor design runs at), and the best f.
Writes symbolic_derivations/03_P24_native/diagnostics/D64_frequency_choice.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import required_i_neg  # noqa: E402
from scb_ivr.p24_inductor_model import MU0, Stripline, effective_r_per_l, skin_depth  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "a115_predict", ROOT / "experiments" / "track_A_periodic_steady_state" / "A115_p24_one_mhz_design_point" / "a115_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
OUT = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D64_frequency_choice.json"
FREQS = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0)
PCTS = (2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0)
STRIPS = [(h, t) for h in (0.2e-3, 0.5e-3, 1e-3, 2e-3, 4e-3) for t in (35e-6, 105e-6, 300e-6)]
MARGIN = 2.0
P_OUT = 250.0
AREAS = (0.25e-4, 0.5e-4, 1e-4, 2e-4)      # inductor footprint per phase, m^2 (0.25-2 cm^2)
H_MAX = 2e-3                               # the height cap, m


def converter():
    rows = {}
    for f in FREQS:
        lf = 7.3333333e-9 / f
        ith = required_i_neg(replace(EdgeCircuit(), lf=lf))
        rr = []
        for pct in PCTS:
            r = P.row(lf, pct)
            eff_i = r["efficiency_pct"]["middle_ideal_inductor"] / 100
            rr.append({"pct": pct, "loss_ideal_w": P_OUT * (1 / eff_i - 1), "ripple_pp_a": r["ripple_pp_a"], "f_sw_hz": 1e9 / r["period_ns"],
                       "hs_on_v": r["hs_on_vds_v_phase1"], "margin_a": ith - pct * 1.25, "copper_middle_w": r["budget_middle_w"]["inductor_copper"]})
        rows[f] = {"lf": lf, "i_th_a": ith, "rows": rr}
        print(f"f {f:4.2f} MHz, L {lf * 1e9:6.3f} nH, I_th {ith:5.1f} A ({ith / 1.25:4.1f}%): ideal-inductor loss "
              + ", ".join(f"{q['pct']:g}% {q['loss_ideal_w']:.1f} W" for q in rr))
    return rows


def main():
    conv = converter()
    out = {"converter": {str(k): v for k, v in conv.items()}, "strips": []}
    print("\nefficiency (%) with a stripline inductor, best target with a valley margin >= 2 A [target %]")
    print("h mm, t um   R/L dc uOhm/nH | " + " | ".join(f"{f:g} MHz" for f in FREQS) + " | best f")
    for h, t in STRIPS:
        s = Stripline(h, t)
        cells, best = [], None
        for f in FREQS:
            c = conv[f]
            cand = []
            for q in c["rows"]:
                if q["margin_a"] < MARGIN:
                    continue
                p_l = s.loss(c["lf"], q["f_sw_hz"], q["ripple_pp_a"])
                eff = P_OUT / (P_OUT + q["loss_ideal_w"] + p_l)
                cand.append((eff, q["pct"], p_l, effective_r_per_l(s, q["f_sw_hz"], q["ripple_pp_a"])))
            e, pct, p_l, rl = max(cand)
            cells.append({"f_mhz": f, "efficiency": e, "pct": pct, "copper_w": p_l, "r_per_l_eff_uohm_nh": rl * 1e-9 * 1e6})
            if best is None or e > best[0]:
                best = (e, f)
        out["strips"].append({"h_mm": h * 1e3, "t_um": t * 1e6, "r_per_l_dc_uohm_nh": s.r_per_l_dc() * 1e-3, "cells": cells,
                              "best_f_mhz": best[1], "best_eff": best[0]})
        print(f"{h * 1e3:4.1f}, {t * 1e6:5.0f}   {s.r_per_l_dc() * 1e-3:7.1f} | " + " | ".join(f"{c['efficiency'] * 100:5.2f} [{c['pct']:g}]" for c in cells)
              + f" | {best[1]:g} MHz")
    # a fixed footprint per phase (P24's in-package setting): the plates' width w = 5 h (the parallel-plate model's
    # validity) and l w = A give h = A mu0 / (25 L), capped at H_MAX; so a smaller L (a higher f) allows a taller gap
    print(f"\nefficiency (%) at a fixed inductor footprint per phase (w = 5 h, h <= {H_MAX * 1e3:g} mm), best target with margin >= 2 A")
    print("A cm2, t um | " + " | ".join(f"{f:g} MHz (h mm)" for f in FREQS) + " | best f")
    out["footprint"] = []
    for area in AREAS:
        for t in (105e-6, 300e-6):
            cells, best = [], None
            for f in FREQS:
                c = conv[f]
                h = min(area * MU0 / (25 * c["lf"]), H_MAX)
                st = Stripline(h, t)
                cand = []
                for q in c["rows"]:
                    if q["margin_a"] < MARGIN:
                        continue
                    p_l = st.loss(c["lf"], q["f_sw_hz"], q["ripple_pp_a"])
                    cand.append((P_OUT / (P_OUT + q["loss_ideal_w"] + p_l), q["pct"], p_l))
                e, pct, p_l = max(cand)
                cells.append({"f_mhz": f, "h_mm": h * 1e3, "efficiency": e, "pct": pct, "copper_w": p_l})
                if best is None or e > best[0]:
                    best = (e, f)
            out["footprint"].append({"area_cm2": area * 1e4, "t_um": t * 1e6, "cells": cells, "best_f_mhz": best[1]})
            print(f"{area * 1e4:5.2f}, {t * 1e6:4.0f} | " + " | ".join(f"{c['efficiency'] * 100:5.2f} ({c['h_mm']:.2f})" for c in cells)
                  + f" | {best[1]:g} MHz")
    print(f"\nskin depth: " + ", ".join(f"{f:g} MHz {skin_depth(f * 1e6) * 1e6:.0f} um" for f in FREQS))
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
