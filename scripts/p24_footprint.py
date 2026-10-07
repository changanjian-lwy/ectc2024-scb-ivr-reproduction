"""D75: the module footprint - 20 EPC2067 per 250 W module do not fit P24's 10 x 10 mm site, so a module takes two
sites (10 x 20 mm, columns 20 mm long). What that changes in the package budgets (D65 / D70 / D72 / D73).

    PYTHONPATH=src python3 scripts/p24_footprint.py

Lateral Vo + GND copper: D65's loss scales as 1 / (copper thickness x module depth); its 10 mm values are rescaled to
the 20 mm column length. Package-inclusive efficiency at 25 C: D73's converter loss (D72 arrays, N = 29 / 40) + lateral
copper + loop (D70 Section 2.5, with the slow turn-on). Writes symbolic_derivations/03_P24_native/diagnostics/
D75_footprint.json.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
DIE_MM2 = 2.85 * 3.25
SITE_MM2 = 100.0
DEPTH_P24, DEPTH_MODULE = 10e-3, 20e-3
T_CU = (86e-6, 215e-6, 429e-6)
LOOP = {"50pH": 1.7, "150pH": 6.6}          # W per module, D70 2.5 / D73 (loop loss + slow turn-on)
I_MODULE = 250.0


def main():
    d65 = json.loads((DIAG / "D65_package_budget.json").read_text())
    d73 = json.loads((DIAG / "D73_electrothermal.json").read_text())
    lat = d65["lateral"]["35um"]
    k10 = (lat["vo_w"] + lat["gnd_w"]) * 35e-6                 # W m at 10 mm depth
    out = {"dies": {"ours_per_module": 20, "p24_per_module": 12, "die_mm2": DIE_MM2,
                    "ours_mm2": 20 * DIE_MM2, "p24_mm2": 12 * DIE_MM2, "site_mm2": SITE_MM2,
                    "package_cover_ours": 80 * DIE_MM2 / 1000.0, "package_cover_p24": 96 * DIE_MM2 / 1000.0},
           "module": {"footprint_mm": [10, 20], "die_cover": 20 * DIE_MM2 / 200.0,
                      "current_density_a_mm2": 4 * I_MODULE / 800.0},
           "lateral": {}, "package_efficiency_25C": {}}
    for t in T_CU:
        key = f"{t * 1e6:.0f}um"
        w10 = k10 / t
        w20 = w10 * DEPTH_P24 / DEPTH_MODULE
        out["lateral"][key] = {"w_10mm": w10, "w_20mm": w20, "r_mohm_20mm": 1e3 * w20 / I_MODULE ** 2,
                               "drop_pct_20mm": 100 * w20 / I_MODULE ** 2 * I_MODULE / 1.0}
    t_valid = k10 * DEPTH_P24 / DEPTH_MODULE / (0.02 * I_MODULE * 1.0)   # drop <= 2 % of 1 V
    out["one_way_2pct_cu_um"] = {"10mm": 1e6 * k10 / (0.02 * I_MODULE), "20mm": 1e6 * t_valid}
    for n in (29, 40):
        conv = d73["designs"][f"2.5MHz_N{n}"]["p25_w"]
        p_out = d73["designs"][f"2.5MHz_N{n}"]["split_25c"]["p_out"]
        row = {"converter": 100 * p_out / (p_out + conv)}
        for t in (86e-6, 429e-6):
            for lk, lw in LOOP.items():
                for depth, tag in ((DEPTH_P24, "10mm"), (DEPTH_MODULE, "20mm")):
                    w = k10 / t * DEPTH_P24 / depth
                    row[f"{t * 1e6:.0f}um_{lk}_{tag}"] = 100 * p_out / (p_out + conv + w + lw)
        out["package_efficiency_25C"][f"N{n}"] = row
    (DIAG / "D75_footprint.json").write_text(json.dumps(out, indent=1) + "\n")
    dd = out["dies"]
    print(f"dies: ours {dd['ours_mm2']:.0f} mm2 per module, P24 {dd['p24_mm2']:.0f} mm2, site {SITE_MM2:.0f} mm2; package cover "
          f"{100 * dd['package_cover_ours']:.0f} / {100 * dd['package_cover_p24']:.0f} %; module 10 x 20 mm, die cover "
          f"{100 * out['module']['die_cover']:.0f} %, {out['module']['current_density_a_mm2']:.2f} A/mm2")
    for key, v in out["lateral"].items():
        if key.endswith("um"):
            print(f"lateral {key}: {v['w_10mm']:.2f} W (10 mm) -> {v['w_20mm']:.2f} W (20 mm), drop {v['drop_pct_20mm']:.1f} %")
    print(f"copper for a 2 % one-way drop: {out['one_way_2pct_cu_um']['10mm']:.0f} um (10 mm) -> "
          f"{out['one_way_2pct_cu_um']['20mm']:.0f} um (20 mm)")
    for n, row in out["package_efficiency_25C"].items():
        print(f"{n}: converter {row['converter']:.2f} %; " + ", ".join(f"{k} {v:.1f}" for k, v in row.items() if k != "converter"))
    print(f"wrote {(DIAG / 'D75_footprint.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
