"""D83: the inductor array and its core loss rebuilt from the HBS1 units Alvarez Barros et al. actually measured
(TCPMT 11(12), 2021, pp. 2183-2192; P24's ref. [10]), on the three design records of D72 / D76.

    PYTHONPATH=src python3 scripts/p24_hbs1_units.py

Copper: R/L of a real HBS1 winding ([10] Table II R_DC, Fig. 7 / Table VI L), arranged s in series x p in parallel to
reach the record's L within 2 % with p >= the steady peak / 5 A and the DC / 2 A ([10] p. 2187), or p >= 40 (200 A).
Core: [10] Eq. (1), P = kappa r_acx(D, f) L (dI/2)^2 per phase (dI/2 = half peak-to-peak, [10] p. 2188), with the
embedded HBS1 r_acx of [10] Fig. 8 (digitised band over the windings) and kappa from [10] Table V; D76's convention
(dI^2 / 12) is kept alongside for the side-by-side. Other loss terms: D73's middle scenario (as D72 / D76). Also the
V7 plant's r_core with the embedded data. Writes symbolic_derivations/03_P24_native/diagnostics/D83_hbs1_units.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_electrothermal as ET  # noqa: E402  (D73's middle scenario and D72's power law, for the side-by-side)
import scb_ivr.p24_loss_budget as lb  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
DESIGNS = ET.DESIGNS                                   # name -> (record, L per phase, D72's N)
L0 = DESIGNS["2.5MHz"][1]                               # V7's nominal L (A221)

# [10] HBS1 windings: L (nH; Fig. 7 HBS1 panel 1-2 MHz, IND048 Table VI), R_DC (mOhm, Table II), drawn area (mm^2, Fig. 5)
UNITS = {"IND034": (18.8, 14.3, None), "IND046": (19.85, 13.6, 1.75 * 0.5), "IND035": (29.75, 21.3, 2.6 * 0.515),
         "IND036": (43.2, 24.9, 1.84 * 1.06), "IND047": (52.3, 29.0, 1.75 * 0.865), "IND048": (60.7, 22.8, 1.75 * 0.865),
         "IND037": (70.8, 39.3, 2.91 * 1.06)}
IND048_CELL_MM2 = 2.25 * 2.25                           # [10] Table VI "area"
I_UNIT_PEAK, I_UNIT_DC = 5.0, 2.0                       # A: [10] Table VI max current; DC above which R_DC, r_acx rise (p. 2187)
L_TOL = 0.02

# [10] Fig. 8 HBS1 panel (small signal, zero DC), mOhm/nH, band = lowest-highest winding, page at 600 dpi, axes on the
# gridlines (52.6 px per mOhm/nH, 677 px per unit D); +-0.04 at each edge
RD = np.array([0.03, 0.05, 0.06, 0.07, 0.075, 0.077, 0.08, 0.09, 0.10])
RACX = {2e6: (np.array([0.64, 0.52, 0.50, 0.48, 0.47, 0.47, 0.45, 0.43, 0.43]),
              np.array([0.79, 0.66, 0.62, 0.62, 0.60, 0.60, 0.60, 0.58, 0.56])),
        5e6: (np.array([2.02, 1.63, 1.51, 1.44, 1.38, 1.38, 1.36, 1.28, 1.23]),
              np.array([2.16, 1.76, 1.63, 1.55, 1.49, 1.49, 1.47, 1.38, 1.32])),
        10e6: (np.array([5.07, 4.13, 3.85, 3.64, 3.55, 3.51, 3.47, 3.30, 3.17]),
               np.array([5.83, 4.69, 4.25, 4.02, 3.83, 3.83, 3.68, 3.47, 3.30]))}
KAPPA_V = {2e6: 3.074, 3e6: 4.134, 4e6: 4.806, 5e6: 5.069}   # [10] Table V: IND037-HBS1, D = 0.5, zero DC
PKG = {"429um_50pH": ("429um", 1.7), "86um_150pH": ("86um", 6.6)}   # D76's package terms (D75 lateral, loop)
P24_PHASE_CM2 = {"fig5_column": 0.25, "d75_two_sites": 0.5, "package_over_16": 0.625}


def racx(f, d, edge, alpha_low=None):
    """Embedded HBS1 r_acx (mOhm/nH) at f, d for edge 0 (low) / 1 (high): linear in d, log-log in f between the curves
    (2-5 MHz exponent below 5 MHz, also below 2 MHz unless alpha_low is given)."""
    v = {fk: float(np.interp(d, RD, RACX[fk][edge])) for fk in RACX}
    lo, hi = (2e6, 5e6) if f <= 5e6 else (5e6, 10e6)
    a = math.log(v[hi] / v[lo]) / math.log(hi / lo)
    if f < 2e6 and alpha_low is not None:
        a = alpha_low
    return v[lo] * (f / lo) ** a


def kappa_nearest(f):
    return KAPPA_V[min(KAPPA_V, key=lambda k: abs(k - f))]


def arrangement(unit, l_target, p_min):
    """Fewest units (s series x p parallel) of one winding with s L_u / p within L_TOL of l_target and p >= p_min."""
    lu = UNITS[unit][0] * 1e-9
    best = None
    for s in range(1, 16):
        p = max(p_min, round(s * lu / l_target))
        if abs(s * lu / p / l_target - 1) <= L_TOL and (best is None or s * p < best["units"]):
            best = {"s": s, "p": p, "units": s * p, "l_nh": s * lu / p * 1e9}
    return best


def budget(m, l_ph, rl):
    lb.L_TECH["d83"] = rl
    b = lb.budget(m["phases"], m["ton_s"], m["period_s"], l_ph, dict(ET.MIDDLE, l_tech="d83"), m["rails_v"],
                  m["dv_next_v"], p_rev=m["p_rev_w"], p_out=m["p_out_w"])
    return b["total"], b["inductor_copper"]


def eff(p_out, p):
    return 100.0 * p_out / (p_out + p)


def main():
    d73 = json.loads((DIAG / "D73_electrothermal.json").read_text())
    d76 = json.loads((DIAG / "D76_core_loss.json").read_text())
    d75 = json.loads((DIAG / "D75_footprint.json").read_text())
    out = {"units": {k: {"l_nh": v[0], "r_mohm": v[1], "r_per_l_uohm_per_nh": 1e3 * v[1] / v[0], "area_drawn_mm2": v[2]}
                     for k, v in UNITS.items()},
           "racx_fig8": {"d": RD.tolist(), **{f"{f:g}": {"lo": a.tolist(), "hi": b.tolist()} for f, (a, b) in RACX.items()}},
           "kappa_table_v": {f"{f:g}": k for f, k in KAPPA_V.items()}, "designs": {}}
    for name, (path, l_ph, d72_n) in DESIGNS.items():
        m = lb.measure(json.loads(path.read_text()))
        f, dty, p_out = 1.0 / m["period_s"], m["ton_s"] / m["period_s"], m["p_out_w"]
        peaks = [p["peak"] for p in m["phases"]]
        dcs = [(p["peak"] + p["valley"]) / 2 for p in m["phases"]]
        di = [p["peak"] - p["valley"] for p in m["phases"]]
        rec = {"f_hz": f, "duty": dty, "l_phase_nh": l_ph * 1e9, "i_peak_max_a": max(peaks), "i_dc_a": dcs,
               "di_pp_a": di, "cases": {}}
        # D72 / D76 as published (D73 split, D76 core) and this script's reproduction of D73's p25
        for n in d72_n:
            x = d73["designs"][f"{name}_N{n}"]
            p25_rep = sum(ET.losses25(m, l_ph, n)[k] for k in ("sw", "cu", "fixed"))
            assert abs(p25_rep / x["p25_w"] - 1) < 1e-9, (name, n, p25_rep, x["p25_w"])
            r76 = d76["designs"][name]["by_n"][f"N{n}"]
            rec[f"d72_N{n}"] = {"rl_uohm_per_nh": 1e3 * ET.array_rl(n, l_ph) * 1e-6, "copper_w": x["split_25c"]["cu"],
                                "eff_no_core": r76["eff_no_core"], "eff_k1": r76["eff_k1"], "eff_k4": r76["eff_k4"]}
        rec["d76_core_w"] = d76["designs"][name]["core_w"]
        # core loss per module, [10] Eq. (1) (half p-p) and D76's convention (rms^2), at both band edges
        core = {}
        for edge, en in ((0, "lo"), (1, "hi")):
            for al in (None, 1.0):
                r = racx(f, dty, edge, al)
                s_hpp = sum(r * 1e6 * l_ph * (x / 2) ** 2 for x in di)
                tag = en + ("" if al is None else "_alpha_low_1")
                core[tag] = {"racx_mohm_per_nh": r, "k1_eq1_w": s_hpp, "k1_d76conv_w": s_hpp / 3.0}
        kap = kappa_nearest(f)
        rec.update(core=core, kappa_nearest=kap, kappa_band=[KAPPA_V[3e6], KAPPA_V[4e6]] if 3e6 < f < 4e6 else None,
                   racx_extrapolated=f < 0.98 * 2e6)
        sw_fixed = d73["designs"][f"{name}_N{d72_n[0]}"]["split_25c"]
        for case, p_min in (("steady", max(math.ceil(max(peaks) / I_UNIT_PEAK), math.ceil(max(dcs) / I_UNIT_DC))),
                            ("200A", max(40, math.ceil(max(dcs) / I_UNIT_DC)))):
            per_unit = {u: arrangement(u, l_ph, p_min) for u in UNITS}
            unit = min(UNITS, key=lambda u: UNITS[u][1] / UNITS[u][0])      # lowest R/L: copper = R/L x L x I_rms^2
            a = per_unit[unit]
            rl = UNITS[unit][1] / UNITS[unit][0] * 1e6                       # Ohm / H (= mOhm/nH x 1e6)
            p25, cu = budget(m, a["l_nh"] * 1e-9, rl)
            assert abs((p25 - cu) / (sw_fixed["sw"] + sw_fixed["fixed"]) - 1) < 1e-9
            area = {"drawn": a["units"] * UNITS[unit][2] / 100.0, "table_vi_cell": a["units"] * IND048_CELL_MM2 / 100.0}
            c = {"p_min": p_min, "unit": unit, "per_unit": per_unit, **a, "rl_uohm_per_nh": rl * 1e-3,
                 "i_unit_peak_a": max(peaks) / a["p"], "i_unit_dc_a": max(dcs) / a["p"],
                 "i_unit_half_pp_a": max(di) / 2 / a["p"], "copper_w": cu, "p25_w": p25,
                 "area_cm2_per_phase": area, "area_cm2_per_module": {k: 4 * v for k, v in area.items()},
                 "layers_needed": {k: {ak: math.ceil(av / ref - 1e-9) for ak, av in area.items()}
                                   for k, ref in P24_PHASE_CM2.items()},
                 "eff_no_core": eff(p_out, p25), "eff": {}}
            for tag, cv in core.items():
                for kn, kv in (("k1", 1.0), ("kV", kap)):
                    for conv in ("eq1", "d76conv"):
                        w = kv * cv[f"k1_{conv}_w"]
                        c["eff"][f"{tag}_{kn}_{conv}"] = eff(p_out, p25 + w)
                        for pk, (cu_key, loop) in PKG.items():
                            c["eff"][f"{tag}_{kn}_{conv}_{pk}"] = eff(p_out, p25 + w + d75["lateral"][cu_key]["w_20mm"] + loop)
            rec["cases"][case] = c
        out["designs"][name] = rec
        st = rec["cases"]["steady"]
        print(f"{name}: f {f / 1e6:.2f} MHz D {dty:.3f}; {st['unit']} {st['s']}x{st['p']} = {st['units']} "
              f"({st['l_nh']:.3f} nH), 200 A: {rec['cases']['200A']['s']}x{rec['cases']['200A']['p']}; copper "
              f"{st['copper_w']:.1f} W (D72 {rec[f'd72_N{d72_n[0]}']['copper_w']:.1f}); r_acx {core['lo']['racx_mohm_per_nh']:.3f}-"
              f"{core['hi']['racx_mohm_per_nh']:.3f}; core k1 Eq.(1) {core['lo']['k1_eq1_w']:.1f}-{core['hi']['k1_eq1_w']:.1f} W, "
              f"kappa {kap:.3f}; eff no core {st['eff_no_core']:.2f}, k1 {st['eff']['hi_k1_eq1']:.2f}-{st['eff']['lo_k1_eq1']:.2f}, "
              f"kV {st['eff']['hi_kV_eq1']:.2f}-{st['eff']['lo_kV_eq1']:.2f} %; D76 conv k1 "
              f"{st['eff']['hi_k1_d76conv']:.2f}-{st['eff']['lo_k1_d76conv']:.2f}, kV {st['eff']['hi_kV_d76conv']:.2f}-"
              f"{st['eff']['lo_kV_d76conv']:.2f} %; area {st['area_cm2_per_phase']['drawn']:.2f}-"
              f"{st['area_cm2_per_phase']['table_vi_cell']:.2f} cm2/phase")

    # V7's r_core (A221: r_core = (2 pi 8 MHz)^2 L / r_acx(8 MHz, D 0.077), toroid 2.557 mOhm/nH)
    d_fit, f8 = 0.077, 8e6
    rc = {"a221_toroid_8mhz": 2.557}
    v = {}
    for edge, en in ((0, "lo"), (1, "hi")):
        r5, r10 = float(np.interp(d_fit, RD, RACX[5e6][edge])), float(np.interp(d_fit, RD, RACX[10e6][edge]))
        v[f"loglog_{en}"] = r5 * (f8 / 5e6) ** (math.log(r10 / r5) / math.log(2.0))
        v[f"linear_{en}"] = r5 + (r10 - r5) * (f8 - 5e6) / 5e6
        dd = 0.04 * (1 if edge else -1)
        v[f"loglog_{en}_digit"] = (r5 + dd) * (f8 / 5e6) ** (math.log((r10 + dd) / (r5 + dd)) / math.log(2.0))
        v[f"10mhz_{en}"] = r10
    rc["racx_embedded"] = v
    w8, w10 = (2 * math.pi * f8) ** 2, (2 * math.pi * 10e6) ** 2
    rc["r_core_ohm"] = {k: {"L0": (w10 if k.startswith("10") else w8) * L0 / (x * 1e6),
                            "0.75L0": (w10 if k.startswith("10") else w8) * 0.75 * L0 / (x * 1e6)} for k, x in v.items()}
    rc["r_core_ohm"]["a221"] = {"L0": w8 * L0 / 2.557e6, "0.75L0": w8 * 0.75 * L0 / 2.557e6}
    # the parallel model under [10] Eq. (2): r_acx_model = 4 f^2 L / (D (1 - D) r_core) (checked by the harmonic sum)
    mm = np.arange(1, 200001)
    s2 = np.sum(np.sin(mm * np.pi * d_fit) ** 2 / (mm * np.pi) ** 4 * (2 * np.pi * mm * f8) ** 2)
    num = 2 / (d_fit * (1 - d_fit)) ** 2 * s2 * L0 / 2.90
    rc["eq2_check"] = {"harmonic_sum": num * 1e-6, "closed_form": 4 * f8 ** 2 * L0 / (d_fit * (1 - d_fit) * 2.90) * 1e-6}
    s_c = np.sum(np.sin(mm * np.pi * d_fit) ** 2 / (mm * np.pi) ** 4)
    rc["eq2_const_r_times_3L_over_r"] = float(2 / (d_fit * (1 - d_fit)) ** 2 * s_c * 3)
    op = out["designs"]["2.5MHz"]
    fo, do = op["f_hz"], op["duty"]
    eq = lambda r_core, f=fo, d=do: 4 * f ** 2 * L0 / (d * (1 - d) * r_core) * 1e-6          # mOhm/nH
    need = lambda target, f=fo, d=do: 4 * f ** 2 * L0 / (d * (1 - d) * target * 1e6)          # Ohm
    lo_r, hi_r = op["core"]["lo"]["racx_mohm_per_nh"], op["core"]["hi"]["racx_mohm_per_nh"]
    rc["operating_point"] = {
        "f_hz": fo, "duty": do, "v7_eq_racx_eq1_mohm_per_nh": eq(2.90), "v7_eq_racx_d76conv_mohm_per_nh": 3 * eq(2.90),
        "v7_core_w_module": sum(eq(2.90) * 1e6 * L0 * (x / 2) ** 2 for x in op["di_pp_a"]),
        "embedded_racx": [lo_r, hi_r], "kappa": op["kappa_nearest"],
        "r_core_for_k1": [need(hi_r), need(lo_r)], "r_core_for_kV": [need(op["kappa_nearest"] * hi_r),
                                                                    need(op["kappa_nearest"] * lo_r)],
        "r_core_eq2_at_8mhz": [4 * f8 ** 2 * L0 / (d_fit * (1 - d_fit) * v["loglog_hi"] * 1e6),
                               4 * f8 ** 2 * L0 / (d_fit * (1 - d_fit) * v["loglog_lo"] * 1e6)]}
    out["r_core"] = rc
    print("r_acx(8 MHz, D 0.077) embedded, log-log 5-10 MHz: "
          f"{v['loglog_lo']:.3f}-{v['loglog_hi']:.3f} (linear {v['linear_lo']:.3f}-{v['linear_hi']:.3f}, +-0.04 digit "
          f"{v['loglog_lo_digit']:.3f}-{v['loglog_hi_digit']:.3f}) mOhm/nH; r_core L0 "
          f"{rc['r_core_ohm']['loglog_hi']['L0']:.3f}-{rc['r_core_ohm']['loglog_lo']['L0']:.3f}, 0.75 L0 "
          f"{rc['r_core_ohm']['loglog_hi']['0.75L0']:.3f}-{rc['r_core_ohm']['loglog_lo']['0.75L0']:.3f} ohm "
          f"(A221 {rc['r_core_ohm']['a221']['L0']:.3f} / {rc['r_core_ohm']['a221']['0.75L0']:.3f}); 10 MHz fit L0 "
          f"{rc['r_core_ohm']['10mhz_hi']['L0']:.3f}-{rc['r_core_ohm']['10mhz_lo']['L0']:.3f}")
    o = rc["operating_point"]
    print(f"Eq.(2) check {rc['eq2_check']['harmonic_sum']:.4f} vs {rc['eq2_check']['closed_form']:.4f}; const R x3L/R "
          f"{rc['eq2_const_r_times_3L_over_r']:.6f}; V7 at {fo / 1e6:.2f} MHz books r_acx {o['v7_eq_racx_eq1_mohm_per_nh']:.3f} "
          f"(Eq.1) = {o['v7_core_w_module']:.1f} W/module; r_core for k1 {o['r_core_for_k1'][0]:.3f}-{o['r_core_for_k1'][1]:.3f}, "
          f"kV {o['r_core_for_kV'][0]:.3f}-{o['r_core_for_kV'][1]:.3f}, Eq.(2) fit at 8 MHz "
          f"{o['r_core_eq2_at_8mhz'][0]:.3f}-{o['r_core_eq2_at_8mhz'][1]:.3f} ohm")
    (DIAG / "D83_hbs1_units.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D83_hbs1_units.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
