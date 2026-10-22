"""D88: published and catalogue air-core inductors on the 2.5 MHz and 5 MHz designs (as D83 did with HBS1 units).

    PYTHONPATH=src python3 scripts/p24_air_core_units.py

Each unit (L, R_DC, current rating, Q at a test frequency, footprint) is arranged s in series x p in parallel to give the
design's phase L within 2 % with the per-unit rms current (the phase's rms / p) at most its rating; an air core does
not saturate, so the ratings are thermal. Copper per module: DC 4 x 62.5^2 x R_DC s / p; ripple: the record's triangle
as harmonics (D87) through R_AC(n f) = max(R_DC, R_Q sqrt(n f / f_Q)), R_Q = 2 pi f_Q L / Q (skin-effect scaling from the
catalogue Q; units without a Q are taken at R_DC, a lower bound). Semiconductor block as D87 (gate-level at 2.5 MHz,
a band at 5 MHz). Writes symbolic_derivations/03_P24_native/diagnostics/D88_air_core_units.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import p24_air_core as AC  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
# name: (L nH, R_DC mOhm, rating A, Q, f_Q Hz, footprint mm2, height mm, source and conditions)
UNITS = {
    "FIVR package, Burton 2014 [17]": (1.2, 7.0, 8.0, None, None, None, None,
                                        "P24 Table 2: in-package air core, 8 A, 140 MHz (Haswell FIVR)"),
    "FIVR package, Lambert 2016 [11]": (2.5, 40.7, 5.0, None, None, None, None,
                                         "P24 Table 2: 3DL, 5 A, 140 MHz (40.7 mOhm repeats [13]'s; unverified)"),
    "InFO 3D, Chen 2016 [15]": (2.5, 12.0, 8.0, None, None, None, None, "P24 Table 2: TSMC InFO, 8 A, 90 MHz"),
    "InFO, Yu 2015 [16]": (1.2, 7.1, 0.6, None, None, None, None, "P24 Table 2: InFO substrate, 0.6 A, 140 MHz"),
    "PCB embedded, Dou 2018 [13]": (685.0, 40.7, 1.0, None, None, None, None,
                                     "P24 Table 2: PCB air, 1 A, 2 MHz (same numbers as its MPC-spiral row; unverified)"),
    "Coilcraft 1515SQ-47N": (47.0, 6.35, 4.9, 230.0, 400e6, 3.8 * 3.8, None, "Doc 720-1 (2021): Irms = 20 K rise"),
    "Coilcraft 2222SQ-111": (110.0, 6.5, 5.7, 140.0, 50e6, 5.6 * 5.6, None, "Doc 720-1 (2021): Irms = 20 K rise"),
    "Coilcraft 2929SQ-501": (500.0, 16.5, 4.3, 180.0, 50e6, 7.49 * 7.24, None, "Doc 720-1 (2021): Irms = 20 K rise"),
    "Wurth WE-ACHC 7449152022": (22.0, 0.55, 40.0, 280.0, 100e6, 12.0 * 11.5, 6.6,
                                 "we-online.com: L at 1 MHz, Q min at 100 MHz, IR = 40 K rise"),
    "Wurth WE-ACHC 7449150023": (23.0, 1.2, 30.0, 191.0, 100e6, 10.0 * 10.0, 4.0, "as above, 1010 size"),
    "Wurth WE-ACHC 7449152066": (66.0, 0.99, 32.0, 245.0, 100e6, 12.0 * 11.5, 8.8, "as above"),
    "Wurth WE-ACHC 7449152090": (90.0, 1.21, 30.0, 226.0, 100e6, 12.0 * 11.5, None, "as above"),
}
L_TOL = 0.02


def arrangement(lu, l_t, p_min, s_max=400):
    best = None
    for s in range(1, s_max + 1):
        p = max(p_min, round(s * lu / l_t))
        if p < 1 or abs(s * lu / p / l_t - 1) > L_TOL:
            continue
        if best is None or s * p < best[0] * best[1]:
            best = (s, p)
    return best


def evaluate(unit, design, semis):
    lu, rdc, irat, q, fq, area, height, _ = unit
    f, d, l_t = design["f_hz"], design["duty"], design["l_phase_nh"]
    dis = design["di_pp_a"]
    i_rms = math.sqrt(AC.I_DC ** 2 + max(dis) ** 2 / 12)
    p_min = math.ceil(i_rms / irat - 1e-9)
    arr = arrangement(lu, l_t, p_min)
    if arr is None:
        return None
    s, p = arr
    r_ph = rdc * 1e-3 * s / p
    rq = None if q is None else 2 * math.pi * fq * lu * 1e-9 / q
    n, _ = AC.harmonics(1.0, d)
    r_n = np.full(n.shape, rdc * 1e-3) if rq is None else np.maximum(rdc * 1e-3, rq * np.sqrt(n * f / fq))
    p_ac = sum(float(np.sum(AC.harmonics(x, d)[1] ** 2 / 2 * r_n * s / p)) for x in dis)
    p_dc = AC.N_PH * AC.I_DC ** 2 * r_ph
    return {"s": s, "p": p, "units_per_phase": s * p, "l_phase_nh": s * lu / p, "r_per_l_uohm_per_nh": 1e3 * rdc / lu,
            "unit_rms_a": i_rms / p, "r_ac_over_r_dc_at_f": None if rq is None else max(1.0, rq * math.sqrt(f / fq) / (rdc * 1e-3)),
            "area_cm2_per_phase": None if area is None else s * p * area / 100, "height_mm": height,
            "copper_dc_w": p_dc, "copper_ac_w": p_ac,
            "eff_pct": [100 * AC.P_OUT / (AC.P_OUT + x + p_dc + p_ac) for x in semis]}


def main():
    d87 = json.loads((DIAG / "D87_air_core.json").read_text())
    d83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]
    out = {"units": {k: dict(zip(("l_nh", "r_dc_mohm", "rating_a", "q", "f_q_hz", "footprint_mm2", "height_mm", "source"), v))
                     for k, v in UNITS.items()}, "designs": {}}
    for name in ("2.5MHz", "5MHz"):
        dz = d83[name]
        design = {"f_hz": dz["f_hz"], "duty": dz["duty"], "l_phase_nh": dz["l_phase_nh"], "di_pp_a": dz["di_pp_a"]}
        semis = d87["designs"][name]["semis_w"]
        out["designs"][name] = {"design": design, "semis_w": semis,
                                "units": {k: evaluate(v, design, semis) for k, v in UNITS.items()}}
    (DIAG / "D88_air_core_units.json").write_text(json.dumps(out, indent=1) + "\n")
    for name, dd in out["designs"].items():
        print(f"{name} (f {dd['design']['f_hz'] / 1e6:.2f} MHz, L {dd['design']['l_phase_nh']:.2f} nH, semis "
              f"{dd['semis_w'][0]:.1f}-{dd['semis_w'][1]:.1f} W)")
        for k, r in dd["units"].items():
            if r is None:
                print(f"  {k}: no arrangement within 2 %")
                continue
            ar = "-" if r["area_cm2_per_phase"] is None else f"{r['area_cm2_per_phase']:.1f} cm2"
            ra = "-" if r["r_ac_over_r_dc_at_f"] is None else f"{r['r_ac_over_r_dc_at_f']:.1f}"
            print(f"  {k}: {r['s']}x{r['p']} = {r['units_per_phase']} units, R/L {r['r_per_l_uohm_per_nh']:.0f} uOhm/nH, "
                  f"unit rms {r['unit_rms_a']:.1f} A, Rac/Rdc {ra}, area {ar}; copper {r['copper_dc_w']:.1f} + "
                  f"{r['copper_ac_w']:.1f} W; eff {min(r['eff_pct']):.1f}-{max(r['eff_pct']):.1f} %")


if __name__ == "__main__":
    main()
