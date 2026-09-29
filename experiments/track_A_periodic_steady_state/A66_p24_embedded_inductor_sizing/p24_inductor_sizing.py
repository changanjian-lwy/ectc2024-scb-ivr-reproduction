"""A66 - the two designs' phase-inductor loss under P24's own inductor technology.

No new solve. Inputs:

- P24_EXPLICIT (Sec. IV-A, Tables 2-3, Eqs. 5-6). Each phase inductor is n
  parallel embedded inductors, each carrying at most Ip(em) = 5 A peak. The
  core is the spiral MPC inductor of P24 ref. [10] (HBS1 material,
  Alvarez Barros et al., TCPMT 2021).
- Ref. [10] (EXTERNAL_DEVICE_DATA, `ref10_hbs1_digitized.json`):
  - DC resistances (Table II) and HBS1 inductances (Fig. 7);
  - small-signal racx(D, f) (Fig. 8);
  - large-to-small loss ratio kappa (Tables IV-V);
  - the loss model, Eqs. 1/11:
    `P_L = I_dc^2 R_dc + (delta_i)^2 L kappa racx(D, f)`,
    where delta_i is half the peak-to-peak ripple (Table IV reproduces it).
- A61's per-phase currents of A59's tuned orbits
  (`break_even_a59_reference.json`).

The AC term does not depend on how many embedded units are paralleled. With
n units, each has ripple delta_i/n and inductance n*L, so the n units
together lose `delta_i^2 * L * kappa * racx`: only the phase ripple and the
phase inductance matter. The DC term does depend on n, through R_phase =
R_unit/n.

PROJECT_DECISIONs:

- P24's 5 A rule is applied to each design's orbit peak current.
- R_unit(L_unit) is interpolated linearly over the six HBS1 designs of [10].
- racx at the SCB phase duty D = nP*Vo/Vin = 1/12 (5 MHz) is the mean of
  Fig. 8's six curves, with their spread as the range.
- For the "target material" of [10] Table VII (0.257 mOhm/nH, kappa = 4,
  stated for 12-1 V at 5 MHz; the text's example uses D = 0.19), racx is
  also scaled to D = 1/12 with HBS1's 5 MHz shape, racx(1/12)/racx(0.19).

Usage: python3 p24_inductor_sizing.py
"""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A61 = HERE.parent / "A61_inductor_loss_break_even" / "break_even_a59_reference.json"
REF10 = HERE / "ref10_hbs1_digitized.json"

# P24_EXPLICIT
P_TOTAL_W, VIN_V, VO_V, F_HZ, N_PHASE = 1000.0, 48.0, 1.0, 5e6, 4
IP_EM_A = 5.0
N_MODULE = 4                          # PROJECT_DECISION (A51-A64): 4 modules of 250 W
P_MODULE_W = P_TOTAL_W / N_MODULE
D_PHASE = N_PHASE * VO_V / VIN_V      # 1/12
ADVANTAGE_A59_W = 4.584417806318946   # ideal-switch advantage, 60 C (A59)
DESIGNS = ("IND037", "IND047", "IND036", "IND035", "IND046", "IND034")


def racx_at(ref, freq, d):
    grid = ref["fig8_hbs1_racx"]["D"]
    k = grid.index(d) if d in grid else None
    rows = ref["fig8_hbs1_racx"]["mohm_per_nH"][freq]
    vals = [row[k] if k is not None else float(np.interp(d, grid[:-1], row[:-1])) for row in rows]
    return float(np.mean(vals)), float(min(vals)), float(max(vals))


def r_unit_ohm(ref, l_unit_h):
    ls = [ref["fig7_hbs1_inductance_nH"]["designs"][n]["L_1MHz"] for n in DESIGNS]
    rs = [ref["tables"]["table_II_dcr_mohm"][n] for n in DESIGNS]
    order = np.argsort(ls)
    return float(np.interp(l_unit_h * 1e9, np.array(ls)[order], np.array(rs)[order])) * 1e-3


def design(ref, name, d):
    phases = d["phases"]
    peak = max(p["peak_a"] for p in phases)
    n = peak / IP_EM_A
    l_unit = d["inductance_h"] * n
    r_unit = r_unit_ohm(ref, l_unit)
    r_phase = r_unit / n
    sum_idc2 = sum(p["dc_a"] ** 2 for p in phases)
    sum_di2_l = sum((p["ripple_pp_a"] / 2) ** 2 for p in phases) * d["inductance_h"]
    return {"design": name, "L_phase_h": d["inductance_h"], "peak_a": peak,
            "ripple_pp_a": max(p["ripple_pp_a"] for p in phases),
            "n_units_per_phase": n, "L_unit_h": l_unit, "R_unit_ohm": r_unit, "R_phase_ohm": r_phase,
            "unit_half_ripple_a": max(p["ripple_pp_a"] for p in phases) / 2 / n,
            "P_dc_w": sum_idc2 * r_phase, "sum_delta_i2_L_A2H": sum_di2_l}


def p_ac(row, kappa_racx_mohm_per_nh):
    return row["sum_delta_i2_L_A2H"] * kappa_racx_mohm_per_nh * 1e6   # mOhm/nH = 1e6 Ohm/H


def main():
    ref = json.loads(REF10.read_text())
    a61 = json.loads(A61.read_text())
    t = ref["tables"]
    rows = {k: design(ref, k, a61["designs"][k]) for k in ("zvs", "baseline")}
    z, b = rows["zvs"], rows["baseline"]
    racx5, racx5_lo, racx5_hi = racx_at(ref, "5MHz", 1 / 12)
    racx5_019 = racx_at(ref, "5MHz", 0.19)[0]
    kappa = t["table_V_kappa_hbs1_D0p5"]["5MHz"]
    kappa_lo, kappa_hi = min(t["table_IV_ind037_hbs1_5MHz"]["kappa"]), max(t["table_IV_ind037_hbs1_5MHz"]["kappa"])
    target = t["table_VII_target_12to1V_5MHz"]
    cases = {
        "HBS1 (P24's named material), 5 MHz, D = 1/12": kappa * racx5,
        "HBS1, low end (kappa and racx minima)": kappa_lo * racx5_lo,
        "HBS1, high end (kappa and racx maxima)": kappa_hi * racx5_hi,
        "[10] Table VII target material, face value": target["kappa"] * target["racx_mohm_per_nH"],
        "[10] Table VII target material, scaled to D = 1/12":
            target["kappa"] * target["racx_mohm_per_nH"] * racx5 / racx5_019,
    }
    out_cases = {}
    for label, kr in cases.items():
        pz, pb = p_ac(z, kr) + z["P_dc_w"], p_ac(b, kr) + b["P_dc_w"]
        out_cases[label] = {"kappa_racx_mohm_per_nH": kr,
                            "P_ac_w": {"zvs": p_ac(z, kr), "baseline": p_ac(b, kr)},
                            "P_total_w": {"zvs": pz, "baseline": pb},
                            "zvs_minus_baseline_w": pz - pb,
                            "baseline_inductor_efficiency": P_MODULE_W / (P_MODULE_W + pb),
                            "zvs_inductor_efficiency": P_MODULE_W / (P_MODULE_W + pz)}
    d_sum = z["sum_delta_i2_L_A2H"] - b["sum_delta_i2_L_A2H"]
    break_even = (ADVANTAGE_A59_W - (z["P_dc_w"] - b["P_dc_w"])) / (d_sum * 1e6)
    out = {"experiment": "A66",
           "classification": "SENSITIVITY_ONLY (P24_EXPLICIT inductor choice, EXTERNAL_DEVICE_DATA from ref. [10])",
           "duty_phase": D_PHASE, "racx_5MHz_D1_12_mohm_per_nH": [racx5, racx5_lo, racx5_hi],
           "racx_5MHz_D0p19_mohm_per_nH": racx5_019, "kappa_5MHz": [kappa, kappa_lo, kappa_hi],
           "designs": rows, "unit_count_ratio": z["n_units_per_phase"] / b["n_units_per_phase"],
           "ac_loss_ratio_zvs_over_baseline": z["sum_delta_i2_L_A2H"] / b["sum_delta_i2_L_A2H"],
           "cases": out_cases,
           "break_even_kappa_racx_mohm_per_nH": break_even,
           "measured_kappa_ripple_range_a": [0.07724, 0.5844],
           "a59_ideal_advantage_w": ADVANTAGE_A59_W}
    (HERE / "results.json").write_text(json.dumps(out, indent=1))
    print(f"D = {D_PHASE:.4f}; racx(5 MHz, D=1/12) = {racx5:.3f} [{racx5_lo:.3f}, {racx5_hi:.3f}] mOhm/nH; "
          f"kappa = {kappa:.3f} [{kappa_lo:.3f}, {kappa_hi:.3f}]")
    for r in rows.values():
        print(f"{r['design']:8s} n {r['n_units_per_phase']:.1f} units/phase, L_unit {r['L_unit_h'] * 1e9:.1f} nH, "
              f"R_unit {r['R_unit_ohm'] * 1e3:.1f} mOhm, R_phase {r['R_phase_ohm'] * 1e3:.3f} mOhm, "
              f"P_dc {r['P_dc_w']:.2f} W, unit half-ripple {r['unit_half_ripple_a']:.2f} A")
    print(f"unit-count ratio {out['unit_count_ratio']:.3f}; AC-loss ratio {out['ac_loss_ratio_zvs_over_baseline']:.3f}")
    for label, c in out_cases.items():
        print(f"{label}: kappa*racx {c['kappa_racx_mohm_per_nH']:.3f}; total {c['P_total_w']['zvs']:.1f} / "
              f"{c['P_total_w']['baseline']:.1f} W; diff {c['zvs_minus_baseline_w']:+.1f} W; "
              f"inductor efficiency {c['zvs_inductor_efficiency']:.1%} / {c['baseline_inductor_efficiency']:.1%}")
    print(f"break-even kappa*racx (keeps A59's {ADVANTAGE_A59_W:.2f} W): {break_even:.3f} mOhm/nH")


if __name__ == "__main__":
    main()
