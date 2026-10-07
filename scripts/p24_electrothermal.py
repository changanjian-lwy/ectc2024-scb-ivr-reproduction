"""D73: a lumped electrothermal closure of the P24 module, in the form of the DVPD framework's loop (losses -> temperature
-> temperature-dependent losses, iterated to a fixed point; Krishnakumar et al. 2026, Fig. 4; Choi et al. TCPMT 2025).

    python3 scripts/p24_electrothermal.py

Losses per module at 25 C: D62's budget on the three design records with D72's buildable-array R/L (5 MHz A112 p20_n0,
2.5 MHz A124 p125_n0, 1 MHz A118 f6_n0; N = 29-31 / 40 units per phase), middle scenario otherwise; package terms from
D70 Section 2.5 (lateral copper 2.5 / 12.5 W at 429 / 86 um, loop 1.6 / 6.4 W at 50 / 150 pH, slow turn-on 0.1 / 0.2 W).
Temperature: switch conduction x (1 + A_SW (T - 25)) (EPC2067 R_on chord 25-125 C, A90's 1.586), copper (inductor array,
lateral) x (1 + A_CU (T - 25)); Coss, overlap, gate, Cs ESR, loop terms held constant. One thermal node per module:
T = T_in + R_th P(T) (R_th junction to coolant per 10 x 10 mm module; K/W = K cm^2/W here).
Writes symbolic_derivations/03_P24_native/diagnostics/D73_electrothermal.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import scb_ivr.p24_loss_budget as lb  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
DESIGNS = {"5MHz": (TA / "A112_p24_zvs_designs_matrix/cosim/run_p20_n0.json", 1.4666667e-9, (31, 40)),
           "2.5MHz": (TA / "A124_p24_two_point_five_mhz/cosim/run_p125_n0.json", 2.93333332e-9, (29, 40)),
           "1MHz": (TA / "A118_p24_floor_turn_off/cosim/run_f6_n0.json", 7.3333333e-9, (29, 40))}
A_SW = (0.8563 / 0.54 - 1.0) / 100.0       # 1 / K, EPC2067 normalized R_on, 25 -> 125 C chord (A90)
A_CU = 0.00393                             # 1 / K, copper
PKG = {"429um_50pH": {"lat_cu": 2.5, "loop": 1.7}, "86um_150pH": {"lat_cu": 12.5, "loop": 6.6}}   # D70 2.5 (+ slow turn-on)
MIDDLE = dict(ron=lb.RON_MAX, esr_cs=1.0e-3, q_gate=lb.QG_TYP, t_f=0.75e-9)
T_MAX = (85.0, 125.0)                      # the DVPD papers' threshold; the hot estimate used so far
T_IN = (25.0, 45.0)
DIE_MM2 = 2.85 * 3.25                      # EPC2067 die
RJC = 0.4                                  # K / W, EPC2067 junction to case


def array_rl(n, l_ph):
    """D72: R/L of an array of n HBS1-class units (R = 13.6 mOhm (L / 20 nH)^0.33)."""
    lu = n * l_ph
    return 13.6e-3 * (lu / 20e-9) ** 0.3297 / lu


def losses25(m, l_ph, n):
    lb.L_TECH["array"] = array_rl(n, l_ph)
    b = lb.budget(m["phases"], m["ton_s"], m["period_s"], l_ph, dict(MIDDLE, l_tech="array"), m["rails_v"], m["dv_next_v"],
                  p_rev=m["p_rev_w"], p_out=m["p_out_w"])
    fixed = b["series_caps"] + b["hard_turn_on"] + b["turn_off_overlap"] + b["gate_drive"] + b["reverse_conduction"]
    return {"sw": b["switch_conduction"], "cu": b["inductor_copper"], "fixed": fixed, "p_out": m["p_out_w"],
            "dies_sw": b["hard_turn_on"] + b["turn_off_overlap"] + b["reverse_conduction"], "gate": b["gate_drive"],
            "cs": b["series_caps"]}


def p_at(l25, t, pkg=None, copper_hot=True):
    """Module loss (W) with the switches at t and the copper at t (copper_hot) or 25 C."""
    tc = t if copper_hot else 25.0
    p = l25["sw"] * (1 + A_SW * (t - 25)) + l25["cu"] * (1 + A_CU * (tc - 25)) + l25["fixed"]
    if pkg:
        p += pkg["lat_cu"] * (1 + A_CU * (tc - 25)) + pkg["loop"]
    return p


def scaled(l25, pkg, s):
    """The same module carrying s x the current (I^2 R terms x s^2; D66's +-5 % inductor matching -> s = 1.05)."""
    l = dict(l25, sw=l25["sw"] * s * s, cu=l25["cu"] * s * s)
    return l, (dict(pkg, lat_cu=pkg["lat_cu"] * s * s) if pkg else None)


def layers(l25, t, pkg):
    """Where the module's heat is generated (W) at temperature t: GaN dies, gate drivers, series capacitors (glass 1),
    inductor array (glass 2), lateral copper (ABF) and the commutation-loop damping."""
    b = {"gan_dies": l25["sw"] * (1 + A_SW * (t - 25)) + l25["dies_sw"], "gate_driver": l25["gate"], "series_caps": l25["cs"],
         "inductor_array": l25["cu"] * (1 + A_CU * (t - 25))}
    b.update({"lateral_copper": pkg["lat_cu"] * (1 + A_CU * (t - 25)), "loop": pkg["loop"]})
    return b


def dpdt(l25, pkg=None, copper_hot=True):
    return l25["sw"] * A_SW + (copper_hot * (l25["cu"] + (pkg["lat_cu"] if pkg else 0.0)) * A_CU)


def fixed_point(l25, r_th, t_in, pkg=None, copper_hot=True):
    """T = t_in + r_th P(T), P linear in T: closed form; None past runaway (r_th dP/dT >= 1)."""
    k = dpdt(l25, pkg, copper_hot)
    if r_th * k >= 1.0:
        return None
    p25 = p_at(l25, 25.0, pkg, copper_hot)
    return (t_in + r_th * (p25 - 25.0 * k)) / (1.0 - r_th * k)


def die_map(m, t):
    """Per-die loss (W) at 2.5 MHz design: phase k's high-side die (conduction + hard turn-on + turn-off overlap), its
    low-side die; gate power stays in the driver. Switch temperature t."""
    f = 1.0 / m["period_s"]
    hot = 1 + A_SW * (t - 25)
    out = []
    for k, p in enumerate(m["phases"]):
        hs, ls, _ = lb.phase_ms(p["valley"], p["peak"], m["ton_s"], m["period_s"])
        e_on = lb.hard_on_energy(p["vds_on"], m["rails_v"][k], m["dv_next_v"][k], n_next=lb.N_H if k < 3 else 0)
        e_off = lb.turn_off_overlap(p["peak"], MIDDLE["t_f"])
        hs_die = hs * lb.RON_MAX * hot / lb.N_H ** 2 + (e_on + e_off) * f / lb.N_H
        ls_die = ls * lb.RON_MAX * hot / lb.N_L ** 2
        out.append({"phase": k + 1, "hs_die_w": hs_die, "ls_die_w": ls_die})
    return out


def main():
    out = {"assumptions": {"a_sw_per_k": A_SW, "a_cu_per_k": A_CU, "pkg": PKG, "t_max_c": T_MAX, "t_in_c": T_IN},
           "designs": {}}
    meas = {k: lb.measure(json.loads(p.read_text())) for k, (p, _, _) in DESIGNS.items()}
    print(f"A_SW {A_SW * 100:.3f} %/K, A_CU {A_CU * 100:.3f} %/K. Per module (250 W out).")
    for name, (_, l_ph, ns) in DESIGNS.items():
        for n in ns:
            l25 = losses25(meas[name], l_ph, n)
            key = f"{name}_N{n}"
            r = {"p25_w": p_at(l25, 25.0), "split_25c": l25, "eff": {}, "dpdt_w_per_k": {}, "r_th_max": {}, "r_th_runaway": {}}
            for t in (25.0, 85.0, 125.0):
                r["eff"][f"{t:.0f}C"] = 100 * l25["p_out"] / (l25["p_out"] + p_at(l25, t))
                r["eff"][f"{t:.0f}C_sw_only"] = 100 * l25["p_out"] / (l25["p_out"] + p_at(l25, t, copper_hot=False))
            for pk_name, pk in [("converter", None)] + list(PKG.items()):
                k = dpdt(l25, pk)
                r["dpdt_w_per_k"][pk_name] = k
                r["r_th_runaway"][pk_name] = 1.0 / k
                for tm in T_MAX:
                    for ti in T_IN:
                        r["r_th_max"][f"{pk_name}_Tmax{tm:.0f}_Tin{ti:.0f}"] = (tm - ti) / p_at(l25, tm, pk)
                r[f"p85_over_p25_{pk_name}"] = p_at(l25, 85.0, pk) / p_at(l25, 25.0, pk)
                r[f"p85_over_p25_sw_only_{pk_name}"] = p_at(l25, 85.0, pk, False) / p_at(l25, 25.0, pk, False)
                for t in (25.0, 85.0, 125.0):
                    r["eff"][f"{t:.0f}C_{pk_name}"] = 100 * l25["p_out"] / (l25["p_out"] + p_at(l25, t, pk))
                lm, pm = scaled(l25, pk, 1.05)
                r["r_th_max"][f"{pk_name}_Tmax85_Tin25_hot_module"] = 60.0 / p_at(lm, 85.0, pm)
                r["r_th_max"][f"{pk_name}_Tmax85_Tin45_hot_module"] = 40.0 / p_at(lm, 85.0, pm)
            r["layers_85C"] = {pk_name: layers(l25, 85.0, pk) for pk_name, pk in PKG.items()}
            out["designs"][key] = r
            print(f"{key:12s} P25 {r['p25_w']:5.1f} W  eff 25/85/125 C {r['eff']['25C']:.2f}/{r['eff']['85C']:.2f}/"
                  f"{r['eff']['125C']:.2f} %  (switches only hot: 85 C {r['eff']['85C_sw_only']:.2f})  dP/dT "
                  f"{r['dpdt_w_per_k']['converter']:.3f} W/K  P85/P25 {r['p85_over_p25_converter']:.3f}")
    d = out["designs"]["2.5MHz_N29"], out["designs"]["2.5MHz_N40"]
    print("2.5 MHz R_th max (K/W per module) for T <= 85 / 125 C, T_in 25 / 45 C:")
    for pk_name in ["converter"] + list(PKG):
        cells = [f"{min(x['r_th_max'][f'{pk_name}_Tmax{tm:.0f}_Tin{ti:.0f}'] for x in d):.2f}-"
                 f"{max(x['r_th_max'][f'{pk_name}_Tmax{tm:.0f}_Tin{ti:.0f}'] for x in d):.2f}" for tm in T_MAX for ti in T_IN]
        print(f"   {pk_name:11s} " + "  ".join(cells) + f"   runaway above {min(x['r_th_runaway'][pk_name] for x in d):.1f} K/W"
              f"   P85/P25 {min(x[f'p85_over_p25_{pk_name}'] for x in d):.3f}-{max(x[f'p85_over_p25_{pk_name}'] for x in d):.3f}")
    for pk_name in PKG:
        lo = [x["eff"][f"{t}C_{pk_name}"] for x in d for t in (25, 85, 125)]
        print(f"   {pk_name}: eff 25/85/125 C " + " | ".join("/".join(f"{x['eff'][f'{t}C_{pk_name}']:.1f}" for t in (25, 85, 125)) for x in d)
              + f"; hottest module (+5 % current) R_th max 85 C, T_in 25/45: "
              + "/".join(f"{min(x['r_th_max'][f'{pk_name}_Tmax85_Tin{ti}_hot_module'] for x in d):.2f}" for ti in (25, 45))
              + f"; P85/P25 switches only {min(x[f'p85_over_p25_sw_only_{pk_name}'] for x in d):.3f}")
    for x, nn in zip(d, (29, 40)):
        for pk_name, lay in x["layers_85C"].items():
            tot = sum(lay.values())
            print(f"   layers 85 C N{nn} {pk_name}: " + ", ".join(f"{q} {v:.1f} W ({100 * v / tot:.0f} %)" for q, v in lay.items()))
    m = meas["2.5MHz"]
    out["die_map_2.5MHz"] = {f"{t:.0f}C": die_map(m, t) for t in (25.0, 85.0)}
    for t in ("25C", "85C"):
        dm = out["die_map_2.5MHz"][t]
        hs, ls = max(x["hs_die_w"] for x in dm), max(x["ls_die_w"] for x in dm)
        print(f"die map {t}: high-side " + "/".join(f"{x['hs_die_w']:.2f}" for x in dm) + " W, low-side "
              + "/".join(f"{x['ls_die_w']:.2f}" for x in dm) + f" W; hottest die {max(hs, ls):.2f} W = "
              f"{100 * max(hs, ls) / DIE_MM2:.0f} W/cm2, {max(hs, ls) * RJC:.2f} K junction-to-case")
    out["die"] = {"area_mm2": DIE_MM2, "r_jc_k_per_w": RJC}
    (DIAG / "D73_electrothermal.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D73_electrothermal.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
