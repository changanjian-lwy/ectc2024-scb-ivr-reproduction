"""D87: a parallel-plate (stripline) air-core inductor for the three designs, against the magnetic cores of D85 / D86.

    PYTHONPATH=src python3 scripts/p24_air_core.py

Per phase one single-turn parallel-plate loop (D64's model): plates of width w and length l, copper t, gap h.
- L = mu0 l h / w; at the design's L the plate area is smallest at w = 5 h (D64's fringing limit): A = 25 L h / mu0.
- DC: R = 2 rho L / (mu0 h t). Ripple: each harmonic n of the record's triangle (rise D, fall 1 - D) flows on the
  facing surfaces within delta_n = sqrt(rho / (pi n f mu0)): R_n = 2 rho L / (mu0 h min(t, delta_n)); the AC loss is
  sum_n a_n^2 / 2 R_n with a_n = dI |sin(pi n D)| / (pi^2 n^2 D (1 - D)) (checked against an FFT of the triangle).
- DC per phase = the load's 62.5 A; the ripple and D come from D83's records (A118 1 MHz design at 0.83 MHz, A124
  2.5 MHz at 1.98 MHz, A112 5 MHz at 3.52 MHz; V0-type plants, ideal inductor).
- Semiconductor block (chip, 25 C): D83's ideal-switch budget of each record plus the gate-level excess measured at
  2.5 MHz (D85: 26.25 W against D83's 20.24 W, +6.01 W), taken either constant or proportional to f (a band; only
  2.5 MHz has gate-level books).
Not modelled: fringing, the vias that close the loop, proximity between phases, the package's real gap and copper
(P24 gives neither). Writes symbolic_derivations/03_P24_native/diagnostics/D87_air_core.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
RHO, MU0 = 1.72e-8, 4e-7 * math.pi          # copper at 25 C (ohm m), H/m
I_DC, N_PH, P_OUT = 62.5, 4, 250.0
H_MM = (0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0)
T_UM = (35.0, 105.0, 300.0)
FOOT_CM2 = (0.25, 0.63, 1.0, 2.0)               # P24 Fig. 5 phase column 0.25, D75's 0.5-0.63, and larger
NH = 400                                        # harmonics


def harmonics(di, d):
    n = np.arange(1, NH + 1)
    return n, di * np.abs(np.sin(np.pi * n * d)) / (np.pi ** 2 * n ** 2 * d * (1 - d))


def check_fft(di, d, m=1 << 14):
    t = np.arange(m) / m
    w = np.where(t < d, t / d, 1 - (t - d) / (1 - d)) * di
    c = np.abs(np.fft.rfft(w - w.mean())) * 2 / m
    _, a = harmonics(di, d)
    return float(np.max(np.abs(c[1:21] - a[:20])) / a[0])


def copper(l, f, d, di_list, h, t):
    n, _ = harmonics(1.0, d)
    delta = np.sqrt(RHO / (np.pi * n * f * MU0))
    r_n = 2 * RHO * l / (MU0 * h * np.minimum(t, delta))
    r_dc = 2 * RHO * l / (MU0 * h * t)
    p_ac = sum(float(np.sum((harmonics(x, d)[1] ** 2 / 2) * r_n)) for x in di_list)
    return N_PH * I_DC ** 2 * r_dc, p_ac


def main():
    d83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]
    d85 = json.loads((DIAG / "D85_loss_ledger.json").read_text())
    it = d85["ledgers"]["N0_25C"]["items_w"]
    rest25 = sum(it.values()) - it["loop_damper_50pH"] - it["inductor_copper"]
    v0_25 = d83["2.5MHz"]["cases"]["steady"]["p25_w"] - d83["2.5MHz"]["cases"]["steady"]["copper_w"]
    excess, f25 = rest25 - v0_25, d83["2.5MHz"]["f_hz"]
    out = {"rest_gate_level_2p5mhz_w": rest25, "gate_level_excess_w": excess, "designs": {}}
    for name, v in d83.items():
        f, d, l = v["f_hz"], v["duty"], v["l_phase_nh"] * 1e-9
        st = v["cases"]["steady"]
        v0 = st["p25_w"] - st["copper_w"]
        semis = [v0 + excess, v0 + excess * f / f25]
        rows = []
        for h_mm in H_MM:
            for t_um in T_UM:
                h, t = h_mm * 1e-3, t_um * 1e-6
                p_dc, p_ac = copper(l, f, d, v["di_pp_a"], h, t)
                area = 25 * l * h / MU0 * 1e4
                rows.append({"h_mm": h_mm, "t_um": t_um, "area_cm2_min": area, "copper_dc_w": p_dc, "copper_ac_w": p_ac,
                             "eff_pct": [100 * P_OUT / (P_OUT + s + p_dc + p_ac) for s in semis]})
        best = {}
        for fc in FOOT_CM2:
            ok = [r for r in rows if r["area_cm2_min"] <= fc]
            if ok:
                b = max(ok, key=lambda r: r["eff_pct"][0])
                best[f"{fc:g}"] = {k: b[k] for k in ("h_mm", "t_um", "area_cm2_min", "copper_dc_w", "copper_ac_w", "eff_pct")}
        h80 = {}
        for t_um in T_UM:                                       # gap for 80 % with the higher semiconductor estimate
            def eff_at(h_mm):
                p_dc, p_ac = copper(l, f, d, v["di_pp_a"], h_mm * 1e-3, t_um * 1e-6)
                return 100 * P_OUT / (P_OUT + max(semis) + p_dc + p_ac)
            lo, hi = 0.05, 10.0
            if eff_at(hi) < 80:
                h80[f"{t_um:g}"] = None
                continue
            for _ in range(60):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if eff_at(mid) < 80 else (lo, mid)
            h80[f"{t_um:g}"] = {"h_mm": hi, "area_cm2_min": 25 * l * hi * 1e-3 / MU0 * 1e4}
        out["designs"][name] = {"h_for_80pct": h80, "f_hz": f, "duty": d, "l_nh": l * 1e9, "di_pp_a": v["di_pp_a"], "semis_w": semis,
                                "fft_check_rel": check_fft(v["di_pp_a"][0], d), "rows": rows, "best_by_footprint": best,
                                "h_max_mm_by_footprint": {f"{fc:g}": fc * 1e-4 * MU0 / (25 * l) * 1e3 for fc in FOOT_CM2}}
    (DIAG / "D87_air_core.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"gate-level excess at 2.5 MHz {excess:.2f} W (rest {rest25:.2f} W)")
    for name, v in out["designs"].items():
        print(f"{name}: f {v['f_hz'] / 1e6:.2f} MHz, L {v['l_nh']:.2f} nH, semis {v['semis_w'][0]:.1f}-{v['semis_w'][1]:.1f} W, "
              f"FFT check {v['fft_check_rel']:.1e}; h_max (0.25/0.63/1/2 cm2) "
              + "/".join(f"{x:.2f}" for x in v["h_max_mm_by_footprint"].values()) + " mm")
        for r in v["rows"]:
            if r["t_um"] == 105.0 or (r["t_um"] == 300.0 and r["h_mm"] >= 1.0):
                print(f"   h {r['h_mm']:.2f} mm t {r['t_um']:.0f} um: area {r['area_cm2_min']:.2f} cm2, copper {r['copper_dc_w']:.1f} + "
                      f"{r['copper_ac_w']:.1f} W, eff {r['eff_pct'][1]:.1f}-{r['eff_pct'][0]:.1f} %")
        print("   80 %: " + ", ".join(f"t {k} um h >= {x['h_mm']:.2f} mm ({x['area_cm2_min']:.2f} cm2)" if x else f"t {k} um: never"
                                     for k, x in v["h_for_80pct"].items()))
        for fc, b in v["best_by_footprint"].items():
            print(f"   footprint {fc} cm2: h {b['h_mm']} mm, t {b['t_um']:.0f} um -> {b['eff_pct'][1]:.1f}-{b['eff_pct'][0]:.1f} %")


if __name__ == "__main__":
    main()
