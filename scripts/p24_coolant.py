"""D77: a microchannel coolant model in place of D74's uniform h - what flow, pressure and pumping power keep the
module at 85 C once the coolant heats along the channels.

    PYTHONPATH=src python3 scripts/p24_coolant.py [--jobs 8]

Cooler (scb_ivr.p24_microchannel): parallel channels under the spreader along the 20 mm columns, effective h on the
cooled face from Shah-London Nu and fin efficiency, optional interface resistance (a cold plate attached through a TIM
instead of channels in the spreader). Module: D74's stack, full length, coolant coupled channel by channel
(scb_ivr.p24_thermal.coupled(coolant=...)); losses as D74 (D75 lateral copper, D76 core loss at kappa 1 / 4), glass-1
fill 2 % (D74's design point) or 19.6 %. Flow quoted per module with its half of the strip: a quarter of the package.
Checks: Shah-London limits; a 2D finite-volume fin against tanh(mH) / mH; full = half module at uniform h; coolant
energy balance; m_dot -> infinity = uniform h.
Writes symbolic_derivations/03_P24_native/diagnostics/D77_coolant.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_thermal_stack as S  # noqa: E402
from scb_ivr import p24_microchannel as M  # noqa: E402
from scb_ivr import p24_thermal as T  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
WIDTH, LENGTH = 12.5e-3, 20e-3     # cooled face of one module + half the strip (a quarter of the package), channel length
COOLERS = {"cu_100_400": (100e-6, 400e-6, 100e-6, T.K_CU, 0.0),
           "cu_50_300": (50e-6, 300e-6, 50e-6, T.K_CU, 0.0),
           "cu_200_500": (200e-6, 500e-6, 100e-6, T.K_CU, 0.0),
           "si_100_400": (100e-6, 400e-6, 100e-6, 148.0, 0.0),
           "cu_100_400_tim": (100e-6, 400e-6, 100e-6, T.K_CU, 0.05e-4)}   # + 0.05 K cm^2/W interface
FLOWS = (0.4e-3, 0.6e-3, 1e-3, 2e-3, 4e-3)      # kg/s per module (0.4 g/s = the framework's 1.6 g/s over 4 modules)
T_IN = (25.0, 45.0)
T_LIMIT = 85.0


def cooler_h(name, m_dot):
    w_c, h_c, w_w, k_s, r_int = COOLERS[name]
    c = M.cooler(w_c, h_c, w_w, k_s, m_dot, WIDTH, LENGTH)
    c["h_face"] = 1.0 / (1.0 / c["h_eff"] + r_int)
    return c


def run(job):
    tag, cooler, m_dot, t_in, kappa, fill = job
    c = cooler_h(cooler, m_dot)
    src, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH", 1.0, kappa)
    m = T.build({"f_g1": fill, "h_bot": c["h_face"], "t_cool": t_in, "t_cu": 86e-6, "y_full": True})
    t, st, s2, it, fh = T.coupled(m, src, a_sw, a_cu, method="cg", max_iter=300,
                                  coolant={"m_dot": m_dot, "t_in": t_in, "cp": M.WATER["cp"]})
    return {"tag": tag, "cooler": cooler, "m_dot_module": m_dot, "t_in": t_in, "kappa": kappa, "fill": fill,
            "h_face": c["h_face"], "h_eff": c["h_eff"], "re": c["re"], "dp_pa": c["dp_pa"], "pump_w": c["pump_w"] * 1.0,
            "t_max": st["t_max"], "junction_max": st["junction_max"], "inductor_max": st["inductor_max"],
            "p_total_w": st["p_total_w"], "t_out_mean": st["coolant_t_out_mean"], "t_out_max": st["coolant_t_out_max"],
            "iterations": it, "energy_rel": st["coolant_heat_w"] / st["p_total_w"] - 1}


def checks():
    out = {"shah_london": {"nu_h1_plates": M.nu_h1(1e-12), "nu_h1_square": M.nu_h1(1.0), "fre_plates": M.f_re(1e-12),
                           "fre_square": M.f_re(1.0), "reference": [8.235, 3.608, 24.0, 14.227]}}
    # 2D fin: half fin of width w/2, height H, root at fixed temperature, convective side, adiabatic tip
    w, hgt, k, h = 100e-6, 400e-6, T.K_CU, 21000.0
    g = T.Grid(np.linspace(0, w / 2, 11), [0, 1e-3], np.linspace(0, hgt, 81))
    s = T.Solver(g, k, k, k, {"z0": ("T", 1.0), "x1": ("h", h, 0.0)})
    tt = s.solve(np.zeros(g.shape))
    q_num = -s.face_heat(tt)["z0"]
    q_ana = M.fin_efficiency(h, k, w, hgt) * h * hgt * 1e-3 * 1.0
    out["fin_2d"] = {"q_numeric_w": q_num, "q_analytic_w": q_ana, "rel": q_num / q_ana - 1}
    # full = half module (uniform h), and m_dot -> infinity = uniform h
    src, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH", 1.0, 1.0)
    base = {"f_g1": 0.02, "h_bot": 9e4, "t_cool": 25.0, "t_cu": 86e-6}
    half = T.coupled(T.build(base), src, a_sw, a_cu, method="cg")[1]
    full = T.coupled(T.build(dict(base, y_full=True)), src, a_sw, a_cu, method="cg")[1]
    inf = T.coupled(T.build(dict(base, y_full=True)), src, a_sw, a_cu, method="cg",
                    coolant={"m_dot": 1e3, "t_in": 25.0, "cp": M.WATER["cp"]})[1]
    out["symmetry_and_limit"] = {"t_max_half": half["t_max"], "t_max_full": full["t_max"], "t_max_coolant_inf": inf["t_max"]}
    # grid: y cells halved at a finite flow
    fine = []
    for dy in (0.25e-3, 0.125e-3):
        st = T.coupled(T.build(dict(base, y_full=True, dy=dy)), src, a_sw, a_cu, method="cg", max_iter=300,
                       coolant={"m_dot": 1e-3, "t_in": 25.0, "cp": M.WATER["cp"]})[1]
        fine.append({"dy_mm": dy * 1e3, "t_max": st["t_max"], "t_out_mean": st["coolant_t_out_mean"]})
    out["grid_y"] = fine
    return out


def min_flow(rows):
    """Smallest flow per module with t_max <= T_LIMIT, log-interpolated between the swept flows; None if none holds."""
    rows = sorted(rows, key=lambda r: r["m_dot_module"])
    if rows[0]["t_max"] <= T_LIMIT:
        return rows[0]["m_dot_module"], "below the sweep"
    for a, b in zip(rows[:-1], rows[1:]):
        if a["t_max"] > T_LIMIT >= b["t_max"]:
            u = (a["t_max"] - T_LIMIT) / (a["t_max"] - b["t_max"])
            return float(np.exp(np.log(a["m_dot_module"]) + u * (np.log(b["m_dot_module"]) - np.log(a["m_dot_module"])))), ""
    return None, "not within 4 g/s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    args = ap.parse_args()
    jobs = []
    for cooler in COOLERS:
        for kappa in (1.0, 4.0):
            for fill in (0.02, 0.196):
                for t_in in T_IN:
                    for m_dot in FLOWS:
                        jobs.append((f"{cooler}|k{kappa:g}|f{fill:g}|T{t_in:g}", cooler, m_dot, t_in, kappa, fill))
    with ProcessPoolExecutor(args.jobs) as pool:
        rows = list(pool.map(run, jobs))
        chk = pool.submit(checks).result()
    groups = {}
    for r in rows:
        groups.setdefault(r["tag"], []).append(r)
    out = {"coolers": {k: list(v) for k, v in COOLERS.items()}, "flows_per_module": FLOWS, "t_in": T_IN,
           "cooler_props": {c: {f"{m * 1e3:g}gs": cooler_h(c, m) for m in FLOWS} for c in COOLERS},
           "rows": rows, "min_flow": {}, "checks": chk}
    print(f"{len(rows)} coupled solves with the coolant; worst energy balance "
          f"{max(abs(r['energy_rel']) for r in rows):.1e}, iterations <= {max(r['iterations'] for r in rows)}")
    c = chk
    print(f"checks: Shah-London Nu {c['shah_london']['nu_h1_plates']:.3f} / {c['shah_london']['nu_h1_square']:.3f}, fRe "
          f"{c['shah_london']['fre_plates']:.2f} / {c['shah_london']['fre_square']:.2f}; 2D fin {c['fin_2d']['rel'] * 100:+.2f} %; "
          f"half / full / m_dot->inf {c['symmetry_and_limit']['t_max_half']:.4f} / {c['symmetry_and_limit']['t_max_full']:.4f} / "
          f"{c['symmetry_and_limit']['t_max_coolant_inf']:.4f} C; dy 0.25 -> 0.125 mm: "
          + " -> ".join(f"{x['t_max']:.3f}" for x in c["grid_y"]))
    for cooler in COOLERS:
        p = out["cooler_props"][cooler]
        print(f"{cooler}: h_face {p['1gs']['h_face']:.0f} W/m2K; at 1 / 4 g/s per module Re {p['1gs']['re']:.0f} / "
              f"{p['4gs']['re']:.0f}, dp {p['1gs']['dp_pa'] / 1e3:.1f} / {p['4gs']['dp_pa'] / 1e3:.1f} kPa, pump "
              f"{p['1gs']['pump_w'] * 1e3:.1f} / {p['4gs']['pump_w'] * 1e3:.0f} mW")
        for tag, rs in groups.items():
            if not tag.startswith(cooler + "|"):
                continue
            mf, note = min_flow(rs)
            out["min_flow"][tag] = {"m_dot_module": mf, "note": note}
            rs = sorted(rs, key=lambda r: r["m_dot_module"])
            print(f"   {tag[len(cooler) + 1:]:14s} T_max " + " / ".join(f"{r['t_max']:.0f}" for r in rs)
                  + f" C at {', '.join(f'{m * 1e3:g}' for m in FLOWS)} g/s; T_out " + " / ".join(f"{r['t_out_mean']:.0f}" for r in rs)
                  + f"; min flow {'none' if mf is None else f'{mf * 1e3:.2f} g/s'} {note}")
    (DIAG / "D77_coolant.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D77_coolant.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
