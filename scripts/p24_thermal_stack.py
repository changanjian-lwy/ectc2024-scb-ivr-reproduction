"""D74: the P24 module stack as a 3D conduction model with a convective cooling face - is the inductor layer the
bottleneck, and how much via copper does glass 1 need?

    PYTHONPATH=src python3 scripts/p24_thermal_stack.py [--jobs 8]

Losses: D73's per-module split for the 2.5 MHz design (D72 array, N = 29 units per phase; package cases 86 um / 150 pH
and 429 um / 50 pH) with D73's temperature coefficients, resolved per die / column (scb_ivr.p24_thermal.coupled).
Geometry: scb_ivr.p24_thermal.STACK (one 250 W module on two of P24's 10 x 10 mm sites; every dimension P24 does not
print is a scenario value). Cooling: the heat spreader's face (Fig. 5c-d, below the GaN dies) with h_bot to T_cool;
the processor-side face adiabatic unless h_top is set. Criterion: hottest point <= 85 C (the team's threshold).
Writes symbolic_derivations/03_P24_native/diagnostics/D74_thermal_stack.json.
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

from scb_ivr import p24_thermal as T  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
T_LIMIT = 85.0
FILLS = (0.0, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.1, 0.196)     # 0.196 = 30 um vias at 60 um pitch (VPD Table III)
H_BOT = (5e3, 1e4, 2e4, 5e4, 1e5)
T_COOL = (25.0, 45.0)
PKG_CU = {"86um_150pH": 86e-6, "429um_50pH": 429e-6}
CASES = {"buildable": 1.0, "d73_density": 2.0}                  # heat x 1 on 2 cm^2; x 2 = 250 W per cm^2 (D73)
COL_AREA = 10e-3 * 20e-3                                       # the module's phase-column area (m^2)


def sources(design="2.5MHz_N29", pkg="86um_150pH", scale=1.0):
    """Per-module 25 C losses for coupled(): per-die conduction / fixed parts recovered from D73's 25 / 85 C die map."""
    d = json.loads((DIAG / "D73_electrothermal.json").read_text())
    a_sw, a_cu = d["assumptions"]["a_sw_per_k"], d["assumptions"]["a_cu_per_k"]
    dm25, dm85 = d["die_map_2.5MHz"]["25C"], d["die_map_2.5MHz"]["85C"]
    cond, fixed = {}, {}
    for a, b in zip(dm25, dm85):
        c = [(b[k] - a[k]) / (60.0 * a_sw) for k in ("hs_die_w", "ls_die_w")]
        cond[a["phase"]] = tuple(scale * x for x in c)
        fixed[a["phase"]] = tuple(scale * (a[k] - x) for k, x in zip(("hs_die_w", "ls_die_w"), c))
    r = d["designs"][design]["split_25c"]
    pk = d["assumptions"]["pkg"][pkg]
    src = {"die_cond": cond, "die_fixed": fixed, "inductor": scale * r["cu"], "gate": scale * r["gate"],
           "caps": scale * r["cs"], "loop": scale * pk["loop"], "lat_cu": scale * pk["lat_cu"]}
    return src, a_sw, a_cu


def run(job):
    """One coupled solve; job = (tag, params, design, pkg, scale)."""
    tag, prm, design, pkg, scale = job
    prm = dict(prm)
    prm.setdefault("t_cu", PKG_CU[pkg])
    src25, a_sw, a_cu = sources(design, pkg, scale)
    m = T.build(prm)
    t, st, src, it, fh = T.coupled(m, src25, a_sw, a_cu, method="cg")
    z = m["z_layers"]
    g1 = T.z_flux(m, t, 0.5 * sum(z["glass1"]))
    lm = st["layers_mean"]
    p = m["p"]
    tc = p["t_cool"]
    out = {"tag": tag, "params": {k: v for k, v in prm.items()}, "design": design, "pkg": pkg, "scale": scale,
           "t_max": st["t_max"], "junction_max": st["junction_max"], "inductor_max": st["inductor_max"],
           "inductor_mean": st["inductor_mean"], "p_total_w": st["p_total_w"], "p_inductor_w": st["p_inductor_w"],
           "p_dies_w": st["p_dies_w"], "iterations": it, "energy_rel": 2 * sum(fh.values()) / st["p_total_w"] - 1,
           "glass1_flux_strip_share": g1["strip"] / (g1["strip"] + g1["columns"]),
           "hot_in": "inductor" if st["inductor_max"] >= st["t_max"] - 1e-9 else "elsewhere",
           "layers_mean": lm,
           # column-mean temperature steps from the coolant up to the inductor's hottest point
           "steps_k": {"convection": lm["spreader"] - tc, "spreader_die_bump": lm["bump"] - lm["spreader"],
                       "lower_buildup": lm["cu_g1b"] - lm["bump"], "glass1": lm["cu_g1t"] - lm["cu_g1b"],
                       "middle_buildup": lm["cu_g2b"] - lm["cu_g1t"], "inductor_body": st["inductor_max"] - lm["cu_g2b"]}}
    return out


def f_star(rows):
    """Smallest fill with t_max <= T_LIMIT, interpolated linearly in fill between the swept points (T_max(f) is convex,
    so the interpolation errs towards more copper); None if even the largest fill fails."""
    rows = sorted(rows, key=lambda r: r["params"]["f_g1"])
    f = [r["params"]["f_g1"] for r in rows]
    tm = [r["t_max"] for r in rows]
    if tm[0] <= T_LIMIT:
        return 0.0
    for i in range(1, len(f)):
        if tm[i] <= T_LIMIT:
            return f[i - 1] + (f[i] - f[i - 1]) * (tm[i - 1] - T_LIMIT) / (tm[i - 1] - tm[i])
    return None


def counts(f):
    if f is None:
        return None
    return {"d30um": float(T.via_count(f, COL_AREA, 30e-6)), "d100um": float(T.via_count(f, COL_AREA, 100e-6)),
            "cu_area_mm2": f * COL_AREA * 1e6}


def refine(base_job, rows):
    """Bisect between the bracketing swept fills to 2 % of f (5 extra solves)."""
    rows = sorted(rows, key=lambda r: r["params"]["f_g1"])
    lo = hi = None
    for a, b in zip(rows[:-1], rows[1:]):
        if a["t_max"] > T_LIMIT >= b["t_max"]:
            lo, hi = a["params"]["f_g1"], b["params"]["f_g1"]
    if lo is None:
        return f_star(rows)
    tag, prm, design, pkg, scale = base_job
    while hi - lo > 0.02 * hi:
        mid = 0.5 * (lo + hi)
        r = run((tag, dict(prm, f_g1=mid), design, pkg, scale))
        if r["t_max"] <= T_LIMIT:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    out = {"stack": {k: v for k, v in T.STACK.items()}, "t_limit_c": T_LIMIT, "fills": FILLS, "h_bot": H_BOT,
           "t_cool": T_COOL, "col_area_m2": COL_AREA, "sweep": [], "f_star": {}, "sensitivity": {}, "decomposition": {}}
    jobs = []
    for case, scale in CASES.items():
        for pkg in PKG_CU:
            for h in H_BOT:
                for tc in T_COOL:
                    for f in FILLS:
                        jobs.append((f"{case}|{pkg}|h{h:g}|T{tc:g}", {"f_g1": f, "h_bot": h, "t_cool": tc},
                                     "2.5MHz_N29", pkg, scale))
    base = {"h_bot": 2e4, "t_cool": 45.0}
    sens = {"baseline": {}, "k_glass_0.9": {"k_glass": 0.9}, "k_glass_1.4": {"k_glass": 1.4},
            "t_g1_100um": {"t_g1": 100e-6}, "t_g1_500um": {"t_g1": 500e-6}, "k_ind_z_1": {"k_ind_z": 1.0},
            "k_ind_z_5": {"k_ind_z": 5.0}, "k_ind_z_20": {"k_ind_z": 20.0}, "k_ind_xy_5": {"k_ind_xy": 5.0},
            "abf_not_stacked": {"mv_follow": False}, "abf_no_microvias": {"mv_follow": False, "f_mv": 0.0},
            "strip_no_vias": {"f_strip": 0.0}, "strip_full_vias": {"f_strip": 0.196}, "k_fill_0.3": {"k_fill": 0.3},
            "bump_frac_0.3": {"bump_frac": 0.3}, "cu_cov_0.4": {"cu_cov": 0.4},
            "top_cooled_1e4": {"h_top": 1e4, "t_top": 45.0}, "spreader_1mm": {"t_spreader": 1e-3},
            "design_N40": {}}
    for name, prm in sens.items():
        for f in FILLS:
            design = "2.5MHz_N40" if name == "design_N40" else "2.5MHz_N29"
            jobs.append((f"sens|{name}", dict(base, **prm, f_g1=f), design, "86um_150pH", 1.0))
    with ProcessPoolExecutor(args.jobs) as pool:
        results = list(pool.map(run, jobs, chunksize=2))
    groups = {}
    for job, r in zip(jobs, results):
        groups.setdefault(job[0], []).append((job, r))
    out["sweep"] = [{k: r[k] for k in ("tag", "pkg", "scale", "t_max", "junction_max", "inductor_max", "p_total_w",
                                       "p_inductor_w", "iterations", "energy_rel", "glass1_flux_strip_share", "hot_in")}
                    | {"f_g1": r["params"]["f_g1"], "h_bot": r["params"]["h_bot"], "t_cool": r["params"]["t_cool"]}
                    for r in results]
    print(f"{len(results)} coupled solves; worst energy balance {max(abs(r['energy_rel']) for r in results):.1e}, "
          f"iterations <= {max(r['iterations'] for r in results)}")
    with ProcessPoolExecutor(args.jobs) as pool:
        futs = {tag: pool.submit(refine, rows[0][0], [r for _, r in rows]) for tag, rows in groups.items()}
        fst = {tag: fu.result() for tag, fu in futs.items()}
    for tag, rows in groups.items():
        rs = sorted((r for _, r in rows), key=lambda r: r["params"]["f_g1"])
        out["f_star"][tag] = {"f_star": fst[tag], "f_star_interp": f_star(rs), "vias": counts(fst[tag]),
                              "t_max_f0": rs[0]["t_max"], "t_max_fmax": rs[-1]["t_max"],
                              "junction_max_f0": rs[0]["junction_max"], "inductor_max_f0": rs[0]["inductor_max"],
                              "inductor_max_f2pct": next(r["inductor_max"] for r in rs if r["params"]["f_g1"] == 0.02),
                              "junction_max_f2pct": next(r["junction_max"] for r in rs if r["params"]["f_g1"] == 0.02),
                              "inductor_max_fmax": rs[-1]["inductor_max"], "junction_max_fmax": rs[-1]["junction_max"],
                              "p_total_f0": rs[0]["p_total_w"], "p_total_fmax": rs[-1]["p_total_w"],
                              "strip_share_f0": rs[0]["glass1_flux_strip_share"]}
        if tag.startswith("sens|"):
            out["sensitivity"][tag[5:]] = out["f_star"][tag]
    out["abf_microvias"] = {}
    abf_jobs = [(f"abf|{fmv:g}|{f:g}", dict(base, mv_follow=False, f_mv=fmv, f_g1=f), "2.5MHz_N29", "86um_150pH", 1.0)
                for fmv in (0.0, 0.0025, 0.005, 0.01, 0.02, 0.05) for f in (0.02, 0.196)]
    with ProcessPoolExecutor(args.jobs) as pool:
        for job, r in zip(abf_jobs, pool.map(run, abf_jobs)):
            out["abf_microvias"][job[0][4:]] = {k: r[k] for k in ("t_max", "junction_max", "inductor_max", "steps_k")}
    for tc in T_COOL:
        for f in (0.0, 0.02, 0.196):
            r = run(("decomp", {"f_g1": f, "h_bot": 2e4, "t_cool": tc}, "2.5MHz_N29", "86um_150pH", 1.0))
            out["decomposition"][f"T{tc:g}_f{f:g}"] = {k: r[k] for k in ("t_max", "junction_max", "inductor_max",
                                                                          "steps_k", "layers_mean", "p_total_w",
                                                                          "glass1_flux_strip_share")}
    # report
    print("f* (glass-1 copper fill under the columns for T_max <= 85 C); vias of 30 um over 200 mm^2:")
    for case in CASES:
        for pkg in PKG_CU:
            print(f"  {case} {pkg}:")
            for tc in T_COOL:
                cells = []
                for h in H_BOT:
                    x = out["f_star"][f"{case}|{pkg}|h{h:g}|T{tc:g}"]
                    fs = x["f_star"]
                    cells.append(f"h{h:.0e}: " + ("none" if fs is None else f"{100 * fs:.2f}%")
                                 + f" (T0 {x['t_max_f0']:.0f}, Tmin {x['t_max_fmax']:.0f})")
                print(f"    T_cool {tc:.0f}: " + "; ".join(cells))
    print("Sensitivity (buildable, 86 um, h 2e4, T_cool 45): f*, T_max at f 0 / 2 % / 19.6 %, inductor - junction at 19.6 %")
    for name, x in out["sensitivity"].items():
        fs = x["f_star"]
        print(f"  {name:18s} f* {'none' if fs is None else f'{100 * fs:.2f}%':>7s}  T {x['t_max_f0']:.1f} / "
              f"{x['inductor_max_f2pct']:.1f} / {x['t_max_fmax']:.1f}  ind-junction {x['inductor_max_fmax'] - x['junction_max_fmax']:+.1f} K")
    print("ABF microvia fill (every dielectric, not stacked over the glass vias; h 2e4, T_cool 45): T_max at glass fill 2 % / 19.6 %")
    for fmv in (0.0, 0.0025, 0.005, 0.01, 0.02, 0.05):
        a2, a196 = out["abf_microvias"][f"{fmv:g}|0.02"], out["abf_microvias"][f"{fmv:g}|0.196"]
        print(f"  f_mv {100 * fmv:4.2f}%: {a2['t_max']:.1f} / {a196['t_max']:.1f} C (build-ups {a2['steps_k']['lower_buildup']:.1f} + "
              f"{a2['steps_k']['middle_buildup']:.1f} K)")
    for key, d in out["decomposition"].items():
        print(f"  steps {key}: " + ", ".join(f"{k} {v:.1f}" for k, v in d["steps_k"].items())
              + f" K; T_max {d['t_max']:.1f}, junction {d['junction_max']:.1f}, strip share {d['glass1_flux_strip_share']:.2f}")
    (DIAG / "D74_thermal_stack.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {(DIAG / 'D74_thermal_stack.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
