"""D74 verification of the conduction solver (scb_ivr.p24_thermal) against closed forms, datasheet data and itself.

    PYTHONPATH=src python3 scripts/p24_thermal_verify.py

V1 slab with uniform generation and a convective face (quadratic, exact): second-order convergence.
V2 1D stack of the module's layers (Cu / glass / ABF contrast ~1000, non-uniform cells): exact series resistance.
V3 one-layer rectangular flux channel, centred isoflux source, convective base (Muzychka et al. 2003 series).
V4 two-layer compound channel, copper spreader on glass (Yovanovich et al. 1999 series).
V5 orthotropic layer (homogenised via-filled glass) against the orthotropic series.
V6 homogenisation: explicitly resolved copper vias against the effective orthotropic medium (series of V5).
V7 EPC2067 junction to case: die on an isothermal plate against the datasheet's R_thJC 0.4 K/W.
V8 the module model: energy balance, direct = CG, lateral and vertical grid refinement.
Writes symbolic_derivations/03_P24_native/diagnostics/D74_verification.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scb_ivr import p24_thermal as T  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"


def surface_mean(g, t, src, q0, k_top):
    """Mean top-surface temperature over the source cells (cell centre + q dz / 2k)."""
    ts = t[:, :, -1] + np.where(src, q0 * g.dz[-1] / (2 * k_top[:, :, -1] if np.ndim(k_top) else 2 * k_top), 0.0)
    return float(ts[src].mean())


def channel_case(a, b, layers_bottom_up, h, c, d, q0, dxy, dz_list, kxy_cells=None, kz_cells=None, method="cg"):
    """Numerical flux channel: layers bottom-up [(t, kxy, kz)], source on the top face, convection at z0."""
    zb = np.concatenate([[0.0], np.cumsum([lt for lt, _, _ in layers_bottom_up])])
    ze = [0.0]
    for (lt, _, _), dz, z0 in zip(layers_bottom_up, dz_list, zb[:-1]):
        n = max(1, int(round(lt / dz)))
        ze.extend(z0 + lt * np.arange(1, n + 1) / n)
    # grid lines through the source edges, so the drawn source has the exact area
    g = T.Grid(T.edges([0, a / 2 - c / 2, a / 2 + c / 2, a], dxy), T.edges([0, b / 2 - d / 2, b / 2 + d / 2, b], dxy),
               np.array(ze))
    kxy = np.zeros(g.shape)
    kz = np.zeros(g.shape)
    for (lt, kx_, kz_), z0, z1 in zip(layers_bottom_up, zb[:-1], zb[1:]):
        m = g.box(z=(z0, z1))
        kxy[m], kz[m] = kx_, kz_
    if kxy_cells is not None:
        kxy, kz = kxy_cells(g), kz_cells(g)
    src = g.box(x=(a / 2 - c / 2, a / 2 + c / 2), y=(b / 2 - d / 2, b / 2 + d / 2))[:, :, 0]
    q = np.zeros(g.shape)
    q[:, :, -1] = src * q0 * g.dx[:, None] * g.dy[None, :]
    s = T.Solver(g, kxy, kxy, kz, {"z0": ("h", h, 0.0)}, method)
    t = s.solve(q)
    return surface_mean(g, t, src, q0, kz), s.face_heat(t)["z0"] / (q0 * src_area(g, src)), g.n


def src_area(g, src):
    return float((g.dx[:, None] * g.dy[None, :])[src].sum())


def order(errs, ratio=2.0):
    return [float(np.log(abs(e0 / e1)) / np.log(ratio)) for e0, e1 in zip(errs[:-1], errs[1:])]


def v1():
    length, k, qv, h, tf = 1e-3, 2.0, 1e8, 2e4, 25.0
    rows = []
    for nz in (4, 8, 16, 32, 64):
        g = T.Grid([0, 1e-3], [0, 1e-3], np.linspace(0, length, nz + 1))
        t, fh = T.solve(g, k, k, k, qv * g.volume(), {"z1": ("h", h, tf)})
        ex = T.slab_generation(g.zc, length, k, qv, h, tf)       # adiabatic at z = 0, cooled at z = L
        rows.append({"nz": nz, "max_err_k": float(np.abs(t[0, 0] - ex).max()),
                     "energy_rel": float(fh["z1"] / (qv * length * 1e-6) - 1)})
    return {"rows": rows, "order": order([r["max_err_k"] for r in rows]),
            "case": "L 1 mm, k 2, q''' 1e8 W/m3, h 2e4, adiabatic at z = 0"}


def v2():
    p = T.STACK
    layers = [(p["t_spreader"], T.K_CU), (p["t_attach"], p["k_attach"]), (p["t_die"], p["k_si"]), (p["t_bump"], 2.0),
              (p["t_abf"], T.K_ABF), (p["t_cu"], 0.7 * T.K_CU), (p["t_abf"], T.K_ABF), (p["t_g1"], p["k_glass"]),
              (p["t_abf"], T.K_ABF), (p["t_g2"], p["k_ind_z"])]
    zb = np.concatenate([[0.0], np.cumsum([t for t, _ in layers])])
    rng = np.random.default_rng(74)
    ze = [0.0]
    for (lt, _), z0 in zip(layers, zb[:-1]):
        cuts = np.sort(rng.uniform(0, 1, rng.integers(0, 4)))
        ze.extend(list(z0 + lt * cuts) + [z0 + lt])
    ze = np.unique(np.round(np.array(ze), 15))
    g = T.Grid([0, 1e-3], [0, 1e-3], ze)
    kz = np.zeros(g.shape)
    for (lt, k), z0, z1 in zip(layers, zb[:-1], zb[1:]):
        kz[g.box(z=(z0, z1))] = k
    qflux, h = 2e5, 2e4                                    # 20 W/cm^2 into the top face
    q = np.zeros(g.shape)
    q[0, 0, -1] = qflux * 1e-6
    t, fh = T.solve(g, kz, kz, kz, q, {"z0": ("h", h, 0.0)})
    t_top = t[0, 0, -1] + qflux * g.dz[-1] / (2 * kz[0, 0, -1])
    exact = qflux * (1 / h + sum(lt / k for lt, k in layers))
    return {"n_cells": int(g.n), "t_top_k": float(t_top), "exact_k": float(exact), "rel_err": float(t_top / exact - 1),
            "contrast": float(max(k for _, k in layers) / min(k for _, k in layers))}


def v3():
    a = b = 10e-3
    t1, k, h, c, d, q0 = 1e-3, 20.0, 1e4, 2e-3, 2e-3, 1e6
    exact, _ = T.flux_channel(a, b, [(t1, k, k)], h, (a / 2, b / 2, c, d, q0), 600, 600)
    rows = []
    for dxy in (0.5e-3, 0.25e-3, 0.125e-3, 0.0625e-3):
        num, eb, n = channel_case(a, b, [(t1, k, k)], h, c, d, q0, dxy, [dxy / 2])
        rows.append({"dxy_mm": dxy * 1e3, "n": n, "mean_rise_k": num, "rel_err": num / exact - 1, "energy_rel": eb - 1})
    errs = [r["rel_err"] for r in rows]
    rich = rows[-1]["mean_rise_k"] + (rows[-1]["mean_rise_k"] - rows[-2]["mean_rise_k"]) / (2 ** order(errs)[-1] - 1)
    return {"exact_k": exact, "rows": rows, "order": order(errs), "richardson_rel_err": rich / exact - 1,
            "case": "10 x 10 x 1 mm, k 20, h 1e4, 2 x 2 mm source 100 W/cm2 (Muzychka et al. 2003)"}


def v4():
    a = b = 10e-3
    c = d = 2.85e-3
    q0 = 1.33 / (c * d)
    top = (200e-6, T.K_CU, T.K_CU)
    bot = (300e-6, 1.1, 1.1)
    h = 2e4
    exact, _ = T.flux_channel(a, b, [top, bot], h, (a / 2, b / 2, c, d, q0), 600, 600)
    rows = []
    for dxy in (0.5e-3, 0.25e-3, 0.125e-3):
        num, eb, n = channel_case(a, b, [bot, top], h, c, d, q0, dxy, [50e-6, 25e-6])
        rows.append({"dxy_mm": dxy * 1e3, "n": n, "mean_rise_k": num, "rel_err": num / exact - 1, "energy_rel": eb - 1})
    return {"exact_k": exact, "rows": rows, "order": order([r["rel_err"] for r in rows]),
            "case": "200 um Cu on 300 um glass (k 1.1), h 2e4, die-size source 1.33 W (Yovanovich et al. 1999)"}


def v5():
    a = b = 5e-3
    c = d = 1e-3
    q0 = 1e6
    kxy, kz = T.via_k(0.05, T.K_CU, 1.1)
    lay = (300e-6, kxy, kz)
    h = 2e4
    exact, _ = T.flux_channel(a, b, [lay], h, (a / 2, b / 2, c, d, q0), 600, 600)
    iso, _ = T.flux_channel(a, b, [(300e-6, kz, kz)], h, (a / 2, b / 2, c, d, q0), 600, 600)
    rows = []
    for dxy in (0.25e-3, 0.125e-3, 0.0625e-3):
        num, eb, n = channel_case(a, b, [lay], h, c, d, q0, dxy, [25e-6])
        rows.append({"dxy_mm": dxy * 1e3, "n": n, "mean_rise_k": num, "rel_err": num / exact - 1})
    return {"kxy": kxy, "kz": kz, "exact_k": exact, "isotropic_kz_k": iso, "rows": rows,
            "order": order([r["rel_err"] for r in rows]),
            "case": f"300 um glass with 5 % Cu vias (kxy {kxy:.2f}, kz {kz:.1f}), 1 x 1 mm source, h 2e4"}


def v6():
    """Square copper pillars resolved by the grid (side s at pitch p, fill (s / p)^2, 4 cells per side) against the
    homogenised orthotropic layer with the same fill (series of V5): z is exact for any via shape, the in-plane value
    uses the cylinder formula. Bare glass faces, then 25 um copper on both faces (the landing / routing metal of a glass
    core). The source is 2-8 pitches wide, so the spreading length is close to the pitch."""
    out = []
    a = b = 1.44e-3
    c = d = 0.48e-3
    q0, h, tg, tc = 2e6, 2e4, 300e-6, 25e-6
    for caps in (False, True):
        for ratio, pitch in ((0.25, 240e-6), (0.25, 120e-6), (0.5, 60e-6)):
            side, f = ratio * pitch, ratio ** 2
            dxy = side / 4
            kxy_e, kz_e = T.via_k(f, T.K_CU, 1.1)
            cu = (tc, T.K_CU, T.K_CU)
            lay_h = [cu, (tg, kxy_e, kz_e), cu] if caps else [(tg, kxy_e, kz_e)]
            series, _ = T.flux_channel(a, b, lay_h, h, (a / 2, b / 2, c, d, q0), 400, 400)
            lay_r = [cu, (tg, 1.1, 1.1), cu] if caps else [(tg, 1.1, 1.1)]

            def kmap(g, side=side, pitch=pitch, caps=caps):
                u = np.abs((g.xc % pitch) - pitch / 2) < side / 2
                v = np.abs((g.yc % pitch) - pitch / 2) < side / 2
                k = np.where((u[:, None] & v[None, :])[:, :, None], T.K_CU, 1.1) * np.ones(g.shape)
                if caps:
                    k[:, :, (g.zc < tc) | (g.zc > tc + tg)] = T.K_CU
                return k

            num, eb, n = channel_case(a, b, lay_r, h, c, d, q0, dxy, [tc / 2, 25e-6, tc / 2] if caps else [25e-6],
                                      kxy_cells=kmap, kz_cells=kmap)
            g = T.Grid(T.edges([0, a], dxy), T.edges([0, b], dxy), [0, 1])
            drawn = float((kmap(g, caps=False)[:, :, 0] > 2).mean())
            out.append({"caps": caps, "fill": f, "pitch_um": pitch * 1e6, "pillar_um": side * 1e6, "fill_drawn": drawn,
                        "n": n, "resolved_k": num, "homogenised_series_k": series,
                        "rel_diff_resolved_vs_series": num / series - 1})
    return {"rows": out, "case": "1.44 x 1.44 mm channel, 300 um glass (k 1.1), 0.48 x 0.48 mm source 200 W/cm2, h 2e4"}


def v7():
    """Parameter check: the die's silicon (518 um) at k 120-148 W/(m K) against the datasheet's R_thJC."""
    p = T.STACK
    area = 2.85e-3 * 3.25e-3
    out = {f"k_si_{k:.0f}": {"r_jc_1d": p["t_die"] / (k * area)} for k in (120.0, 148.0)}
    g = T.Grid([0, 2.85e-3], [0, 3.25e-3], np.linspace(0, p["t_die"], 27))
    for k in (120.0, 148.0):
        q = np.zeros(g.shape)
        q[:, :, -1] = 1.0
        t, _ = T.solve(g, k, k, k, q, {"z0": ("T", 0.0)})
        out[f"k_si_{k:.0f}"]["r_jc_model_k_per_w"] = float(t[0, 0, -1] + 1.0 / area * g.dz[-1] / (2 * k))
    out["datasheet_r_jc"] = 0.4
    return out


def v8():
    import p24_thermal_stack as S
    src25, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH")
    out = []
    for f in (0.0, 0.02):
        row = {"f_g1": f}
        for label, prm, meth in (("base_direct", {}, "direct"), ("base_cg", {}, "cg"),
                                 ("dx_0.125", {"dx": 0.125e-3, "dy": 0.125e-3}, "cg"),
                                 ("dx_0.0625", {"dx": 0.0625e-3, "dy": 0.0625e-3}, "cg"),
                                 ("nz_x4", {"nz_scale": 4}, "cg")):
            m = T.build(dict(prm, f_g1=f))
            t, st, src, it, fh = T.coupled(m, src25, a_sw, a_cu, method=meth)
            row[label] = {"n": int(m["grid"].n), "junction_max": st["junction_max"], "inductor_max": st["inductor_max"],
                          "p_total_w": st["p_total_w"], "face_heat_w": 2 * fh["z0"], "iterations": it,
                          "energy_rel": 2 * fh["z0"] / st["p_total_w"] - 1}
        out.append(row)
    return out


def main():
    res = {"V1_slab_generation": v1(), "V2_layered_1d": v2(), "V3_flux_channel": v3(), "V4_compound_channel": v4(),
           "V5_orthotropic": v5(), "V6_resolved_vias": v6(), "V7_epc2067_rjc": v7(), "V8_module": v8()}
    r = res["V1_slab_generation"]
    print("V1 slab: max error " + " ".join(f"{x['max_err_k']:.2e}" for x in r["rows"]) + " K, order "
          + " ".join(f"{o:.2f}" for o in r["order"]))
    r = res["V2_layered_1d"]
    print(f"V2 layered 1D (contrast {r['contrast']:.0f}, {r['n_cells']} cells): {r['t_top_k']:.6f} vs {r['exact_k']:.6f} K, "
          f"rel {r['rel_err']:.1e}")
    for key in ("V3_flux_channel", "V4_compound_channel", "V5_orthotropic"):
        r = res[key]
        print(f"{key}: exact {r['exact_k']:.4f} K; rel error " + " ".join(f"{x['rel_err'] * 100:+.3f}%" for x in r["rows"])
              + "; order " + " ".join(f"{o:.2f}" for o in r["order"])
              + (f"; Richardson {r['richardson_rel_err'] * 100:+.3f}%" if "richardson_rel_err" in r else "")
              + (f"; isotropic-kz series would give {r['isotropic_kz_k']:.4f} K" if "isotropic_kz_k" in r else ""))
    for x in res["V6_resolved_vias"]["rows"]:
        print(f"V6 vias caps {x['caps']!s:5s} f {x['fill']:.4f} (drawn {x['fill_drawn']:.4f}) pitch {x['pitch_um']:.0f} um: resolved "
              f"{x['resolved_k']:.3f} K, homogenised series {x['homogenised_series_k']:.3f} K "
              f"({x['rel_diff_resolved_vs_series'] * 100:+.1f}%)")
    r = res["V7_epc2067_rjc"]
    print("V7 EPC2067 R_jc: " + ", ".join(f"{k} {v['r_jc_model_k_per_w']:.3f} K/W (1D {v['r_jc_1d']:.3f})"
                                         for k, v in r.items() if k.startswith("k_si")) + f"; datasheet {r['datasheet_r_jc']}")
    for row in res["V8_module"]:
        print(f"V8 module f_g1 {row['f_g1']}: " + "; ".join(
            f"{k} Tj {v['junction_max']:.3f} ind {v['inductor_max']:.3f} E {v['energy_rel']:.1e}"
            for k, v in row.items() if k != "f_g1"))
    (DIAG / "D74_verification.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D74_verification.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
