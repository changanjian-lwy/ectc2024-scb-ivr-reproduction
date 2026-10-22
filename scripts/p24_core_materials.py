"""D86: the four metal-polymer core materials of Murali et al. (ECTC 2022) at the final design point.

    PYTHONPATH=src python3 scripts/p24_core_materials.py

Murali et al. built three embedded toroids (IND 1-3) in four Panasonic sheets (HBS1, XVSZ2, XVSZ3, XVSZ4) and measured
inductance spectra, small-signal r_acx against duty, DC bias to 2.5 A and the large-signal AC loss of IND 1 at 2 MHz with
a 250 mA ripple (±0.25 A, Fig. 10). This script takes those numbers (digitised below, figure and conditions on each
line) and puts each material on the 2.5 MHz design (N0, A124's waveform, as D83 / D85): one phase is p units in
parallel (s = 1), so the per-nH metrics carry over unchanged:
- copper (DC only, the load's 62.5 A per phase) = 4 x 62.5^2 x R_u / p with the material's lowest R_DC / L winding;
- core = M x L x sum over phases of (dI / 2)^2 ([10] Eq. (1)), M in mOhm/nH:
  - lower bound: M = the small-signal r_acx at 2 MHz, D 0.075 (Fig. 8, IND 1; kappa 1);
  - Murali's own large signal: M = P / (L i^2) from Fig. 11 at D 0.15 (its lowest duty), carried to D 0.075 with the
    small-signal ratio r_acx(0.075) / r_acx(0.15) of Fig. 8 (assumed: the large-to-small ratio does not change between
    D 0.15 and 0.075; Fig. 11's own rise from D 0.5 to 0.15 follows the small-signal one within 6 %).
The design runs at 1.98 MHz, so no frequency is extrapolated. Rest of the ledger: D85's chip items without the inductor
(N0, 25 C). Writes symbolic_derivations/03_P24_native/diagnostics/D86_core_materials.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import p24_hbs1_units as H  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
MATERIALS = ("HBS1", "XVSZ2", "XVSZ3", "XVSZ4")
R_DC_MOHM = {"IND1": 49.8, "IND2": 70.5, "IND3": 89.0}            # Table I, 4-probe, independent of the material
AREA_MM2 = {"IND1": 5.44, "IND2": 7.0, "IND3": 8.74}             # p. 1-2, lateral footprint
L_2MHZ_NH = {                                                     # Fig. 6 (IND 1) / Fig. 7 (IND 2, 3) at 2 MHz, 500 dpi
    "HBS1": {"IND1": 189.0, "IND2": 350.0},                       # IND 2 HBS1 lies under IND 2 XVSZ2's line (read 350)
    "XVSZ2": {"IND1": 226.0, "IND2": 350.0, "IND3": 420.0},
    "XVSZ3": {"IND1": 250.0, "IND2": 391.0},
    "XVSZ4": {"IND1": 367.0, "IND2": 475.0, "IND3": 595.0}}       # text: "about 600 nH at 2 MHz with the IND 3"
RACX_SS_2MHZ = {                                                  # Fig. 8 (a)-(d), IND 1's 2 MHz curve, mOhm/nH
    "HBS1": {0.075: 0.369, 0.15: 0.267},
    "XVSZ2": {0.075: 0.348, 0.15: 0.251},
    "XVSZ3": {0.075: 0.427, 0.15: 0.299},                         # IND 1 and IND 2 overlap
    "XVSZ4": {0.075: 0.436, 0.15: 0.32}}                          # 0.15: from D 0.1's 0.390 with HBS1's shape (unread)
P_LS_MW = {"HBS1": 18.03, "XVSZ2": 24.34, "XVSZ3": 23.47, "XVSZ4": 33.18}   # Fig. 11, IND 1, 2 MHz, ±0.25 A, D 0.15
I_HALF_PP = 0.25                                                  # A, Fig. 10
I_DC_PHASE, N_PH = 62.5, 4                                        # A per phase (250 A), phases


def main():
    d83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]["2.5MHz"]
    d85 = json.loads((DIAG / "D85_loss_ledger.json").read_text())["ledgers"]["N0_25C"]
    items = d85["items_w"]
    rest = sum(items.values()) - items["loop_damper_50pH"] - items["inductor_copper"]
    l_ph = H.DESIGNS["2.5MHz"][1]                                 # H, the design's phase inductance
    l_arr = d83["cases"]["steady"]["l_nh"] * 1e-9                 # D83's IND048 array
    s_i2 = sum((x / 2) ** 2 for x in d83["di_pp_a"])              # A^2, A124's waveform
    w_per_m = 1e6 * l_ph * s_i2                                   # W per (mOhm/nH) of the core metric
    peak, ripple = d83["i_peak_max_a"], max(d83["di_pp_a"]) / 2
    out = {"conditions": "N0, 2.5 MHz design (1.98 MHz, D 0.075), A124's waveform, 25 C, chip; per 250 W module",
           "rest_w": rest, "w_per_mohm_per_nh": w_per_m, "materials": {}}
    for m in MATERIALS:
        best = min(L_2MHZ_NH[m], key=lambda k: R_DC_MOHM[k] / L_2MHZ_NH[m][k])
        lu = L_2MHZ_NH[m][best]
        p = round(lu * 1e-9 / l_arr)
        r_u = R_DC_MOHM[best] * 1e-3
        cu_dc = N_PH * I_DC_PHASE ** 2 * r_u / p
        ss = RACX_SS_2MHZ[m]
        m_ls15 = P_LS_MW[m] * 1e-3 / (L_2MHZ_NH[m]["IND1"] * 1e-9 * I_HALF_PP ** 2) / 1e6   # mOhm/nH
        m_ls = m_ls15 * ss[0.075] / ss[0.15]
        core = {"kappa1": ss[0.075] * w_per_m, "murali_large_signal": m_ls * w_per_m}
        eff = {k: 100 * 250 / (250 + rest + cu_dc + v) for k, v in core.items()}
        budget80 = 250 / 0.80 - 250 - rest - cu_dc                  # core allowed for 80 %
        out["materials"][m] = {
            "winding": best, "l_unit_nh": lu, "r_unit_mohm": R_DC_MOHM[best], "r_per_l_uohm_per_nh": 1e3 * R_DC_MOHM[best] / lu,
            "units_per_phase": p, "l_phase_nh": lu / p, "area_cm2_per_phase": p * AREA_MM2[best] / 100,
            "unit_dc_a": I_DC_PHASE / p, "unit_peak_a": peak / p, "unit_half_pp_a": ripple / p,
            "copper_dc_w": cu_dc, "racx_ss_075": ss[0.075], "kappa_murali_015": m_ls15 / ss[0.15],
            "m_large_signal_075": m_ls, "core_w": core, "eff_pct": eff,
            "core_allowed_80pct_w": budget80, "m_allowed_80pct": budget80 / w_per_m}
    ref = d83["cases"]["steady"]
    out["d83_ind048"] = {"r_per_l_uohm_per_nh": ref["rl_uohm_per_nh"], "units_per_phase": ref["units"],
                         "area_cm2_per_phase": ref["area_cm2_per_phase"], "copper_dc_w": N_PH * I_DC_PHASE ** 2 * l_arr * ref["rl_uohm_per_nh"] * 1e3,
                         "racx_10_band_075": [d83["core"]["lo"]["racx_mohm_per_nh"], d83["core"]["hi"]["racx_mohm_per_nh"]],
                         "kappa_10": d83["kappa_nearest"]}
    (DIAG / "D86_core_materials.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"rest {rest:.2f} W, {w_per_m:.1f} W per mOhm/nH")
    for m, v in out["materials"].items():
        print(f"{m}: {v['winding']} {v['l_unit_nh']:.0f} nH / {v['r_unit_mohm']} mOhm = {v['r_per_l_uohm_per_nh']:.0f} uOhm/nH, "
              f"{v['units_per_phase']} units/phase, {v['area_cm2_per_phase']:.1f} cm2/phase; unit DC {v['unit_dc_a']:.2f} A, "
              f"half p-p {v['unit_half_pp_a']:.2f} A; copper DC {v['copper_dc_w']:.2f} W; kappa(D0.15) {v['kappa_murali_015']:.2f}; "
              f"M {v['m_large_signal_075']:.2f} mOhm/nH; core {v['core_w']['kappa1']:.1f} / {v['core_w']['murali_large_signal']:.1f} W; "
              f"eff {v['eff_pct']['kappa1']:.1f} / {v['eff_pct']['murali_large_signal']:.1f} %; 80 % needs M <= {v['m_allowed_80pct']:.2f}")
    r = out["d83_ind048"]
    print(f"D83 IND048: {r['r_per_l_uohm_per_nh']:.0f} uOhm/nH, {r['units_per_phase']} units, copper DC {r['copper_dc_w']:.2f} W, "
          f"[10] r_acx {r['racx_10_band_075'][0]:.3f}-{r['racx_10_band_075'][1]:.3f}, kappa {r['kappa_10']}")


if __name__ == "__main__":
    main()
