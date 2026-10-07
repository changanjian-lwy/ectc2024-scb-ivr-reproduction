"""D76: the inductor array's core loss (HBS1-class MPC, R_acx metric) on the three design records, and what it does to
the efficiency and to the frequency choice (D67 / D72).

    PYTHONPATH=src python3 scripts/p24_core_loss.py

Core loss per phase = kappa R_acx(f, D) L I_ac^2 (scb_ivr.p24_core_loss), kappa 1 (small signal) / 2 / 4 (Alvarez Barros
et al. 2021: large signal "over four times" small signal in the MHz range). Converter loss at 25 C: D73's split (D72
arrays, N = 29-31 / 40 units); package terms from D75 (20 mm deep module). Writes symbolic_derivations/03_P24_native/
diagnostics/D76_core_loss.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_electrothermal as ET  # noqa: E402
import scb_ivr.p24_core_loss as C  # noqa: E402
import scb_ivr.p24_loss_budget as lb  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
DESIGNS = {"5MHz": (TA / "A112_p24_zvs_designs_matrix/cosim/run_p20_n0.json", 1.4666667e-9, (31, 40)),
           "2.5MHz": (TA / "A124_p24_two_point_five_mhz/cosim/run_p125_n0.json", 2.93333332e-9, (29, 40)),
           "1MHz": (TA / "A118_p24_floor_turn_off/cosim/run_f6_n0.json", 7.3333333e-9, (29, 40))}
KAPPA = (1.0, 2.0, 4.0)
PKG = {"429um_50pH": ("429um", 1.7), "86um_150pH": ("86um", 6.6)}


def main():
    d73 = json.loads((DIAG / "D73_electrothermal.json").read_text())
    d75 = json.loads((DIAG / "D75_footprint.json").read_text())
    out = {"kappa": KAPPA, "racx_table": {"d": C.RACX_D.tolist(), **{f"{f:g}": v.tolist() for f, v in C.RACX_HBS1.items()}},
           "designs": {}}
    print("HBS1 R_acx exponent in f (2-8 MHz) at D 0.05 / 0.077 / 0.1: "
          + " / ".join(f"{C.exponent(dd):.2f}" for dd in (0.05, 0.077, 0.1)))
    for name, (path, l_ph, ns) in DESIGNS.items():
        m = lb.measure(json.loads(path.read_text()))
        f, dty = 1.0 / m["period_s"], m["ton_s"] / m["period_s"]
        r = C.racx(f, dty)
        i_ac = [abs(p["peak"] - p["valley"]) / np.sqrt(12) for p in m["phases"]]
        core1 = C.module_core_loss(m, l_ph, 1.0)
        rec = {"f_hz": f, "duty": dty, "racx_mohm_per_nh": r * 1e-6, "omega_l_mohm": 2e3 * np.pi * f * l_ph,
               "tan_delta_equiv": r / (2 * np.pi * f), "i_ac_rms_a": i_ac, "extrapolated": f < 0.95 * 2e6,
               "core_w": {f"k{k:g}": k * core1 for k in KAPPA}, "by_n": {}}
        for n in ns:
            x = d73["designs"][f"{name}_N{n}"]
            p25, p_out = x["p25_w"], x["split_25c"]["p_out"]
            cu = x["split_25c"]["cu"]
            row = {"p25_w": p25, "copper_w": cu, "eff_no_core": 100 * p_out / (p_out + p25)}
            for k in KAPPA:
                core = k * core1
                row[f"eff_k{k:g}"] = 100 * p_out / (p_out + p25 + core)
                for pk, (cu_key, loop) in PKG.items():
                    lat = d75["lateral"][cu_key]["w_20mm"]
                    row[f"eff_k{k:g}_{pk}"] = 100 * p_out / (p_out + p25 + core + lat + loop)
            rec["by_n"][f"N{n}"] = row
        out["designs"][name] = rec
        print(f"{name}: f {f / 1e6:.2f} MHz, D {dty:.3f}, R_acx {r * 1e-6:.3f} mOhm/nH{' (extrapolated)' if f < 2e6 else ''}, "
              f"I_ac {np.mean(i_ac):.1f} A rms, tan-delta equiv {rec['tan_delta_equiv']:.3f}; core per module "
              + " / ".join(f"{v:.1f}" for v in rec["core_w"].values()) + " W at kappa 1 / 2 / 4")
        # hot: D73's temperature laws (switch conduction and all copper at T), the core loss held constant
        for n in ns:
            l25 = d73["designs"][f"{name}_N{n}"]["split_25c"]
            hot = {}
            for k in (0.0,) + KAPPA:
                core = k * core1
                for pk, (cu_key, loop) in [("converter", (None, 0.0))] + list(PKG.items()):
                    pkg = None if cu_key is None else {"lat_cu": d75["lateral"][cu_key]["w_20mm"], "loop": loop}
                    p85 = ET.p_at(l25, 85.0, pkg) + core
                    hot[f"k{k:g}_{pk}"] = {"eff_85C": 100 * l25["p_out"] / (l25["p_out"] + p85), "p85_w": p85,
                                           "r_th_max_tin25": 60.0 / p85, "r_th_max_tin45": 40.0 / p85}
            rec["by_n"][f"N{n}"]["hot"] = hot
        for nk, row in rec["by_n"].items():
            print(f"   {nk}: copper {row['copper_w']:.1f} W, eff {row['eff_no_core']:.2f} % -> "
                  + " / ".join(f"{row[f'eff_k{k:g}']:.2f}" for k in KAPPA) + " % (kappa 1 / 2 / 4); with package 429 / 86 um: "
                  + " | ".join("/".join(f"{row[f'eff_k{k:g}_{pk}']:.1f}" for pk in PKG) for k in KAPPA))
    print("85 C (all copper hot), converter | + package 429 um / 50 pH | 86 um / 150 pH; R_th max per module (K/W) T_in 25 C:")
    for name, rec in out["designs"].items():
        for nk, row in rec["by_n"].items():
            h = row["hot"]
            print(f"   {name} {nk}: " + "; ".join(
                f"k{k:g} {h[f'k{k:g}_converter']['eff_85C']:.1f} | {h[f'k{k:g}_429um_50pH']['eff_85C']:.1f} | "
                f"{h[f'k{k:g}_86um_150pH']['eff_85C']:.1f} % (R_th {h[f'k{k:g}_86um_150pH']['r_th_max_tin25']:.2f}-"
                f"{h[f'k{k:g}_converter']['r_th_max_tin25']:.2f})" for k in (0.0,) + KAPPA))
    # frequency ranking at each kappa, best unit count per design
    out["ranking"] = {}
    for k in (0.0,) + KAPPA:
        key = "eff_no_core" if k == 0 else f"eff_k{k:g}"
        best = {name: max(rec["by_n"].values(), key=lambda r: r[key])[key] for name, rec in out["designs"].items()}
        worst = {name: min(rec["by_n"].values(), key=lambda r: r[key])[key] for name, rec in out["designs"].items()}
        out["ranking"][f"k{k:g}"] = {"best_n": best, "fewest_n": worst}
        print(f"kappa {k:g}: " + ", ".join(f"{nm} {worst[nm]:.2f}-{best[nm]:.2f} %" for nm in best)
              + f"  -> best {max(best, key=best.get)}")
    (DIAG / "D76_core_loss.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D76_core_loss.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
