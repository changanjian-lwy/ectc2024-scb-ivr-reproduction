"""D84: the thermal results of D73 / D74 / D77 / D78 / D80 rerun with D83's inductor losses (real IND048-HBS1 array,
[10] Eq. (1) core loss), everything else as those notes had it.

    PYTHONPATH=src python3 scripts/p24_thermal_d83.py [--jobs 8]

Inputs changed (2.5 MHz design A124 p125_n0, per 250 W module, 25 C values; diagnostics/D83_hbs1_units.json):
  inductor copper 27.33 W (IND048 2 x 41 per phase; D72 N29: 18.57 W), with D73's copper law (+0.393 %/K);
  core loss kappa x [10] Eq. (1) small-signal value at the embedded r_acx band edge lo / hi (34.48 / 44.12 W), kappa 1 or
  [10] Table V's 3.074 (2 MHz), held constant in temperature (as D74 / D76 / D83). D76 had 7.47 W x kappa 1 / 4.
Unchanged: die map, gate, Cs, loop, lateral copper (D73 / D75), the stack (scb_ivr.p24_thermal.STACK: 10 x 20 mm module,
phase columns 2.5 x 20 mm = 0.5 cm^2 per phase, glass 2 inductor body 300 um), h, coolers, coolant, processor-side
scenarios, the 85 C threshold. The copper and the core are split equally over the four phase columns (coupled()).
Method, no existing file edited:
  D73 (lumped): p24_electrothermal.p_at / dpdt / fixed_point on D73's N29 split with cu replaced and the core added to
    the temperature-independent part (as scripts/p24_core_loss.py does for D76's 85 C table).
  D74 / D77 / D78 / D80: every heat source of their job functions (p24_thermal_stack.run / refine, p24_coolant.run,
    p24_processor_side.run, p24_thermal_gate.stack / coolant) comes from p24_thermal_stack.sources(); each worker
    replaces that function (monkeypatch) by d83_sources(), which calls the original with the core at zero and sets
    inductor / core to D83's values. edge None runs the original (reproduction checks against the published JSONs).
  D78's 85 C crossing in T_proc is inline in p24_processor_side.main; it is copied here (t_proc_for_85).
Writes symbolic_derivations/03_P24_native/diagnostics/D84_thermal_d83.json.
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import p24_coolant as C  # noqa: E402
import p24_electrothermal as ET  # noqa: E402
import p24_processor_side as P  # noqa: E402
import p24_thermal_gate as G  # noqa: E402
import p24_thermal_stack as S  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
D83 = json.loads((DIAG / "D83_hbs1_units.json").read_text())["designs"]["2.5MHz"]
CU_D83 = D83["cases"]["steady"]["copper_w"]                     # W per module, 25 C (2 x 41 IND048; same for 200 A)
CORE_D83 = {e: D83["core"][e]["k1_eq1_w"] for e in ("lo", "hi")}  # W per module, kappa 1, [10] Eq. (1)
KAPPA_V = D83["kappa_nearest"]                                  # [10] Table V at 2 MHz
CORES = {"k1_lo": (1.0, "lo"), "k1_hi": (1.0, "hi"), "kV_lo": (KAPPA_V, "lo"), "kV_hi": (KAPPA_V, "hi")}
AREA_PHASE_CM2 = {"stack_column": 2.5e-3 * 20e-3 * 1e4, **D83["cases"]["steady"]["area_cm2_per_phase"]}
T_LIMIT = 85.0
_ORIG_SOURCES = S.sources


def d83_sources(design="2.5MHz_N29", pkg="86um_150pH", scale=1.0, kappa=1.0, edge="hi"):
    """D74's sources() with the inductor copper = D83's array and the core = kappa x D83's Eq. (1) value at edge."""
    src, a_sw, a_cu = _ORIG_SOURCES(design, pkg, scale, 0.0)
    return dict(src, inductor=scale * CU_D83, core=scale * kappa * CORE_D83[edge]), a_sw, a_cu


TASKS = {"d74": S.run, "d74_refine": lambda j: S.refine(*j), "d77": C.run, "d78": P.run, "d80_stack": G.stack,
         "d80_coolant": G.coolant}


def call(task):
    """Worker entry: install the D83 sources (or the original for edge None), then run the existing job function."""
    name, edge, job = task
    S.sources = _ORIG_SOURCES if edge is None else functools.partial(d83_sources, edge=edge)
    return TASKS[name](job)


# ---------------------------------------------------------------- D73: lumped node
def lumped_case(l25, cu, core, pkg):
    l = dict(l25, cu=cu, fixed=l25["fixed"] + core)
    p = {t: ET.p_at(l, t, pkg) for t in (25.0, 85.0, 125.0)}
    k = ET.dpdt(l, pkg)
    return {"cu_25c_w": cu, "core_w": core, "p_w": {f"{t:.0f}C": v for t, v in p.items()},
            "eff": {f"{t:.0f}C": 100 * l["p_out"] / (l["p_out"] + v) for t, v in p.items()},
            "r_th_max": {f"Tmax{tm:.0f}_Tin{ti:.0f}": (tm - ti) / p[tm] for tm in (85.0, 125.0) for ti in (25.0, 45.0)},
            "r_th_runaway": 1.0 / k, "dpdt_w_per_k": k, "p85_over_p25": p[85.0] / p[25.0], "_l": l}


def lumped():
    d73 = json.loads((DIAG / "D73_electrothermal.json").read_text())
    d75 = json.loads((DIAG / "D75_footprint.json").read_text())
    d76 = json.loads((DIAG / "D76_core_loss.json").read_text())
    l25 = d73["designs"]["2.5MHz_N29"]["split_25c"]
    core76 = d76["designs"]["2.5MHz"]["core_w"]["k1"]
    pkgs = {"converter": None, **{pk: {"lat_cu": d75["lateral"][ck]["w_20mm"], "loop": lp}
                                  for pk, (ck, lp) in {"429um_50pH": ("429um", 1.7), "86um_150pH": ("86um", 6.6)}.items()}}
    out = {"basis": "D73 N29 split, D75 20 mm lateral copper, core constant in T (D76 85 C table method)", "old": {}, "new": {}}
    for k in (0.0, 1.0, 4.0):                                    # reproduction of D76's 85 C table (N29)
        for pk, pkg in pkgs.items():
            c = lumped_case(l25, l25["cu"], k * core76, pkg)
            ref = d76["designs"]["2.5MHz"]["by_n"]["N29"]["hot"][f"k{k:g}_{pk}"]
            assert abs(c["eff"]["85C"] / ref["eff_85C"] - 1) < 1e-12 and abs(c["r_th_max"]["Tmax85_Tin25"] /
                                                                             ref["r_th_max_tin25"] - 1) < 1e-12
            out["old"][f"k{k:g}_{pk}"] = {kk: v for kk, v in c.items() if kk != "_l"}
    cases = {"k0": (0.0, "hi"), **CORES}
    for cn, (kap, edge) in cases.items():
        for pk, pkg in pkgs.items():
            c = lumped_case(l25, CU_D83, kap * CORE_D83[edge], pkg)
            l = c.pop("_l")
            # the fixed point at the R_th that held 85 C with the old losses (D76: kappa 1 for k0 / k1, kappa 4 for kV)
            old = out["old"][f"k{4 if cn.startswith('kV') else 1}_{pk}"]
            c["t_at_old_r_th"] = {}
            for ti in (25.0, 45.0):
                r_old = old["r_th_max"][f"Tmax85_Tin{ti:.0f}"]
                t = ET.fixed_point(l, r_old, ti, pkg)
                c["t_at_old_r_th"][f"Tin{ti:.0f}"] = {"r_th_old": r_old, "t_c": t,
                                                       "eff": None if t is None else
                                                       100 * l["p_out"] / (l["p_out"] + ET.p_at(l, t, pkg))}
            out["new"][f"{cn}_{pk}"] = c
    return out


# ---------------------------------------------------------------- helpers copied / adapted
def t_proc_for_85(sub):
    """Copied from p24_processor_side.main: the T_proc at which T_max crosses 85 C (linear), 'all' / 'none'."""
    sub = sorted(sub, key=lambda r: r["t_proc"])
    tp = None
    for a, b in zip(sub[:-1], sub[1:]):
        if (a["t_max"] - T_LIMIT) * (b["t_max"] - T_LIMIT) <= 0 and a["t_max"] != b["t_max"]:
            tp = a["t_proc"] + (T_LIMIT - a["t_max"]) * (b["t_proc"] - a["t_proc"]) / (b["t_max"] - a["t_max"])
    if tp is None:
        tp = "all" if sub[-1]["t_max"] <= T_LIMIT else "none"
    return tp


def slim(r, keys=("t_max", "junction_max", "inductor_max", "p_total_w", "iterations", "energy_rel")):
    return {k: r[k] for k in keys if k in r}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()
    t0 = time.time()
    old74 = json.loads((DIAG / "D74_thermal_stack.json").read_text())
    old77 = json.loads((DIAG / "D77_coolant.json").read_text())
    old78 = json.loads((DIAG / "D78_processor_side.json").read_text())
    old80 = json.loads((DIAG / "D80_thermal_gate.json").read_text())
    edges = {c: G.edge_power(c) for c in ("nom", "ss")}
    for c in edges:
        assert edges[c] == old80["inputs"]["edges_w_per_module"][c], c
    out = {"inputs": {"copper_w_25c": CU_D83, "copper_w_25c_d72_n29": None, "core_k1_eq1_w": CORE_D83,
                      "kappa_table_v": KAPPA_V, "core_cases_w": {k: kap * CORE_D83[e] for k, (kap, e) in CORES.items()},
                      "d76_core_k1_w": D83["d76_core_w"]["k1"], "area_cm2_per_phase": AREA_PHASE_CM2,
                      "footprint_note": "all stack runs keep D74's 0.5 cm^2 phase column and one 300 um glass-2 body"},
           "lumped_d73": lumped()}
    out["inputs"]["copper_w_25c_d72_n29"] = out["lumped_d73"]["old"]["k1_converter"]["cu_25c_w"]

    tasks = []
    # reproduction checks with the original sources (edge None)
    tasks += [("d74", None, ("chk74", {"f_g1": 0.0, "h_bot": 2e4, "t_cool": 25.0}, "2.5MHz_N29", "86um_150pH", 1.0, 1.0)),
              ("d77", None, ("chk77", "cu_100_400", 1e-3, 25.0, 1.0, 0.02)),
              ("d78", None, ("chk78", 1e4 / 1.2, 85.0, 2e4, 45.0, 4.0)),
              ("d80_stack", None, ("chk80", "gate_nom", 1.0, {"f_g1": 0.0, "h_bot": 2e4, "t_cool": 25.0}, edges))]
    # D74: decomposition (h 2e4, 86 um) incl. copper only (core 0), and the f* grid
    for cn in ("k0",) + tuple(CORES):
        kap, edge = (0.0, "hi") if cn == "k0" else CORES[cn]
        for tc in S.T_COOL:
            for f in (0.0, 0.02, 0.196):
                tasks.append(("d74", edge, (f"dec|{cn}|T{tc:g}|f{f:g}", {"f_g1": f, "h_bot": 2e4, "t_cool": tc},
                                            "2.5MHz_N29", "86um_150pH", 1.0, kap)))
    for cn, (kap, edge) in CORES.items():
        for pkg in S.PKG_CU:
            for h in S.H_BOT:
                for tc in S.T_COOL:
                    for f in S.FILLS:
                        tasks.append(("d74", edge, (f"grid|{cn}|{pkg}|h{h:g}|T{tc:g}", {"f_g1": f, "h_bot": h, "t_cool": tc},
                                                    "2.5MHz_N29", pkg, 1.0, kap)))
    # D77: baseline cooler, fills 2 / 19.6 %, inlet 25 / 45 C, D77's flows
    for cn, (kap, edge) in CORES.items():
        for fill in (0.02, 0.196):
            for ti in C.T_IN:
                for m in C.FLOWS:
                    tasks.append(("d77", edge, (f"cool|{cn}|f{fill:g}|T{ti:g}", "cu_100_400", m, ti, kap, fill)))
    # D78: D78's full grid
    for cn, (kap, edge) in CORES.items():
        for hb in P.H_BOT:
            for tc in P.T_COOL:
                for ht in P.H_TOP:
                    for tp in (P.T_PROC if ht > 0 else (0.0,)):
                        tasks.append(("d78", edge, (f"proc|{cn}|hb{hb:g}|Tc{tc:g}", ht, tp, hb, tc, kap)))
    # D80: the final-spec variants (50 pH damper + gate-level edges, nominal / slow corner)
    for v in ("gate_nom", "gate_ss"):
        for cn, (kap, edge) in CORES.items():
            for tc in S.T_COOL:
                for f in G.FILLS:
                    tasks.append(("d80_stack", edge, (f"g80|{v}|{cn}|T{tc:g}|f{f:g}", v, kap,
                                                      {"f_g1": f, "h_bot": 2e4, "t_cool": tc}, edges)))
                for m in C.FLOWS:
                    tasks.append(("d80_coolant", edge, (f"c80|{v}|{cn}|T{tc:g}|m{m * 1e3:g}", v, kap, tc, m, edges)))
    print(f"{len(tasks)} solves on {args.jobs} workers", flush=True)
    with ProcessPoolExecutor(args.jobs) as pool:
        res = list(pool.map(call, tasks, chunksize=1))
    print(f"solves done in {time.time() - t0:.0f} s", flush=True)
    rows = [dict(r, _task=t[0], _edge=t[1], _tag=t[2][0]) for t, r in zip(tasks, res)]

    # convergence and energy balance
    cap = {"d74": 80, "d78": 80, "d80_stack": 80, "d77": 300, "d80_coolant": 300}
    nc = [r["_tag"] for r in rows if r["iterations"] >= cap[r["_task"]]]
    out["solver"] = {"n_solves": len(rows), "max_iterations": max(r["iterations"] for r in rows),
                     "not_converged": nc, "max_abs_energy_rel": max(abs(r["energy_rel"]) for r in rows)}

    # reproduction checks
    chk = {r["_tag"]: r for r in rows if r["_tag"].startswith("chk")}
    ref77 = next(x["t_max"] for x in old77["rows"] if x["tag"] == "cu_100_400|k1|f0.02|T25" and x["m_dot_module"] == 1e-3)
    ref78 = next(x["t_max"] for x in old78["rows"] if x["tag"] == "k4|hb20000|Tc45" and abs(x["h_top"] - 1e4 / 1.2) < 1e-6
                 and x["t_proc"] == 85.0)
    out["reproduction"] = {"d74_headline": [chk["chk74"]["t_max"], old74["decomposition"]["T25_f0"]["t_max"]],
                           "d77_k1_f2_T25_1gs": [chk["chk77"]["t_max"], ref77],
                           "d78_k4_hb2e4_Tc45_R1.2_Tp85": [chk["chk78"]["t_max"], ref78],
                           "d80_gate_nom_headline": [chk["chk80"]["t_max"], old80["headline"]["gate_nom"]["t_max"]]}
    for k, (a, b) in out["reproduction"].items():
        assert abs(a - b) < 1e-6, (k, a, b)

    # D74 decomposition
    out["d74_decomposition"] = {r["_tag"][4:]: slim(r, ("t_max", "junction_max", "inductor_max", "p_total_w",
                                                         "p_inductor_w", "steps_k", "iterations", "glass1_flux_strip_share"))
                                for r in rows if r["_tag"].startswith("dec|")}
    out["d74_decomposition_old"] = {k: slim(v, ("t_max", "junction_max", "inductor_max", "steps_k"))
                                    for k, v in old74["decomposition"].items()}
    # D74 f* grid, refined by bisection as D74 does
    groups = {}
    for t, r in zip(tasks, res):
        if t[2][0].startswith("grid|"):
            groups.setdefault(t[2][0], []).append((t, r))
    ref_tasks = [("d74_refine", g[0][0][1], (g[0][0][2], [r for _, r in g])) for g in groups.values()]
    with ProcessPoolExecutor(args.jobs) as pool:
        fst = list(pool.map(call, ref_tasks, chunksize=1))
    out["d74_f_star"] = {}
    for (tag, g), fs in zip(groups.items(), fst):
        rs = sorted((r for _, r in g), key=lambda r: r["params"]["f_g1"])
        _, cn, pkg, hh, tc = tag.split("|")
        okey = f"buildable_k{{}}|{pkg}|{hh}|{tc}"
        out["d74_f_star"][tag[5:]] = {
            "f_star": fs, "f_star_interp": S.f_star(rs), "t_max_f0": rs[0]["t_max"],
            "t_max_f2pct": next(r["t_max"] for r in rs if r["params"]["f_g1"] == 0.02), "t_max_fmax": rs[-1]["t_max"],
            "junction_max_f0": rs[0]["junction_max"], "p_total_f0": rs[0]["p_total_w"],
            "old_k1": {k: old74["f_star"][okey.format(1)][k] for k in ("f_star", "t_max_f0", "t_max_fmax")},
            "old_k4": {k: old74["f_star"][okey.format(4)][k] for k in ("f_star", "t_max_f0", "t_max_fmax")}}
    # D77 minimum flow
    out["d77_min_flow"] = {}
    cg = {}
    for r in rows:
        if r["_tag"].startswith("cool|"):
            cg.setdefault(r["_tag"][5:], []).append(r)
    for tag, rs in cg.items():
        mf, note = C.min_flow(rs)
        cn, ff, tt = tag.split("|")
        okey = f"cu_100_400|k{{}}|{ff}|{tt}"
        rs = sorted(rs, key=lambda r: r["m_dot_module"])
        out["d77_min_flow"][tag] = {"m_dot_module": mf, "note": note, "t_max_by_flow": [r["t_max"] for r in rs],
                                    "t_out_mean_by_flow": [r["t_out_mean"] for r in rs],
                                    "old_k1": old77["min_flow"][okey.format(1)], "old_k4": old77["min_flow"][okey.format(4)]}
    # D78 processor side
    out["d78"] = {}
    pg = {}
    for r in rows:
        if r["_tag"].startswith("proc|"):
            pg.setdefault(r["_tag"][5:], []).append(r)
    for tag, rs in pg.items():
        cn, hb, tc = tag.split("|")
        adi = next(r for r in rs if r["h_top"] == 0)
        okey = f"k{{}}|{hb}|{tc}"
        e = {"adiabatic_t_max": adi["t_max"], "adiabatic_top_face": adi["top_face_mean"], "p_total_w": adi["p_total_w"],
             "t_proc_max": {}, "rows": [slim(r, ("h_top", "t_proc", "t_max", "q_top_w")) for r in rs]}
        for ht in P.H_TOP[1:]:
            e["t_proc_max"][f"htop{ht:.0f}"] = t_proc_for_85([r for r in rs if r["h_top"] == ht])
            e.setdefault("old_k1", {})[f"htop{ht:.0f}"] = old78["t_proc_max"][f"{okey.format(1)}|htop{ht:.0f}"]
            e.setdefault("old_k4", {})[f"htop{ht:.0f}"] = old78["t_proc_max"][f"{okey.format(4)}|htop{ht:.0f}"]
        for kk in (1, 4):
            e[f"old_k{kk}"]["adiabatic_t_max"] = next(r["t_max"] for r in old78["rows"]
                                                      if r["tag"] == okey.format(kk) and r["h_top"] == 0)
        out["d78"][tag] = e
    # D80 final variants
    out["d80"] = {}
    for v in ("gate_nom", "gate_ss"):
        for cn in CORES:
            e = {}
            for tc in S.T_COOL:
                rs = [dict(r) for r in rows if r["_tag"].startswith(f"g80|{v}|{cn}|T{tc:g}|")]
                h0 = next(r for r in rs if r["params"]["f_g1"] == 0.0)
                e[f"T{tc:g}"] = {"f0": slim(h0, ("t_max", "junction_max", "inductor_max", "p_total_w", "p_dies_w")),
                                 "f2pct_t_max": next(r["t_max"] for r in rs if r["params"]["f_g1"] == 0.02),
                                 "fmax_t_max": max(rs, key=lambda r: r["params"]["f_g1"])["t_max"],
                                 "f_star_interp": S.f_star(rs)}
                cr = [r for r in rows if r["_tag"].startswith(f"c80|{v}|{cn}|T{tc:g}|")]
                mf, note = C.min_flow(cr)
                e[f"T{tc:g}"]["min_flow"] = {"m_dot_module": mf, "note": note,
                                             "t_max_by_flow": [r["t_max"] for r in sorted(cr, key=lambda r: r["m_dot_module"])]}
            out["d80"][f"{v}|{cn}"] = e
        out["d80"][f"{v}|old"] = {"headline": old80["headline"][v],
                                  "f_star": {k: x for k, x in old80["f_star"].items() if k.startswith(v + "|")},
                                  "min_flow": {k: x for k, x in old80["min_flow"].items() if k.startswith(v + "|")}}
    out["runtime_s"] = time.time() - t0
    (DIAG / "D84_thermal_d83.json").write_text(json.dumps(out, indent=1, default=float) + "\n")

    # ------------------------------------------------------------ report
    L = out["lumped_d73"]
    print(f"copper {CU_D83:.2f} W (D72 N29 {out['inputs']['copper_w_25c_d72_n29']:.2f}); core k1 "
          f"{CORE_D83['lo']:.2f}-{CORE_D83['hi']:.2f} W, kV {KAPPA_V * CORE_D83['lo']:.1f}-{KAPPA_V * CORE_D83['hi']:.1f} W")
    print(f"solver: {out['solver']['n_solves']} solves, max it {out['solver']['max_iterations']}, not converged "
          f"{len(nc)}, |energy| <= {out['solver']['max_abs_energy_rel']:.1e}; reproduction ok")
    for pk in ("converter", "429um_50pH", "86um_150pH"):
        o1, o4 = L["old"][f"k1_{pk}"], L["old"][f"k4_{pk}"]
        print(f"D73 {pk}: old k1/k4 eff85 {o1['eff']['85C']:.1f}/{o4['eff']['85C']:.1f} %, R_th85 Tin25 "
              f"{o1['r_th_max']['Tmax85_Tin25']:.2f}/{o4['r_th_max']['Tmax85_Tin25']:.2f}")
        for cn in ("k0",) + tuple(CORES):
            x = L["new"][f"{cn}_{pk}"]
            fp = x["t_at_old_r_th"]
            print(f"   {cn:6s} eff 25/85/125 {x['eff']['25C']:.1f}/{x['eff']['85C']:.1f}/{x['eff']['125C']:.1f} %; R_th85 Tin25/45 "
                  f"{x['r_th_max']['Tmax85_Tin25']:.3f}/{x['r_th_max']['Tmax85_Tin45']:.3f}; runaway {x['r_th_runaway']:.1f}; "
                  f"T at old R_th Tin25/45 {fp['Tin25']['t_c']:.1f}/{fp['Tin45']['t_c']:.1f} C")
    for k, d in out["d74_decomposition"].items():
        print(f"D74 dec {k:16s} T_max {d['t_max']:6.1f} jn {d['junction_max']:5.1f} P {d['p_total_w']:6.1f} W  "
              + ", ".join(f"{a} {b:.1f}" for a, b in d["steps_k"].items()))
    for k, d in out["d74_f_star"].items():
        if "86um" in k:
            fs = d["f_star"]
            print(f"D74 f* {k:32s} {'none' if fs is None else f'{100 * fs:.2f}%':>7s} (T {d['t_max_f0']:.0f}/{d['t_max_f2pct']:.0f}/"
                  f"{d['t_max_fmax']:.0f}); old k1 {d['old_k1']['f_star']}, k4 {d['old_k4']['f_star']}")
    for k, d in out["d77_min_flow"].items():
        print(f"D77 {k:18s} min flow {d['m_dot_module']} {d['note']}; T_max " + "/".join(f"{x:.0f}" for x in d["t_max_by_flow"]))
    for k, d in out["d78"].items():
        print(f"D78 {k:22s} adiabatic {d['adiabatic_t_max']:.1f} C; T_proc max {d['t_proc_max']}")
    for k, d in out["d80"].items():
        if not k.endswith("old"):
            print(f"D80 {k:16s} " + "; ".join(f"{tc}: T_max {x['f0']['t_max']:.1f} jn {x['f0']['junction_max']:.1f} f* "
                                             f"{x['f_star_interp']} flow {x['min_flow']['m_dot_module']} {x['min_flow']['note']}"
                                             for tc, x in d.items()))
    print(f"wrote {(DIAG / 'D84_thermal_d83.json').relative_to(ROOT)} in {out['runtime_s']:.0f} s")


if __name__ == "__main__":
    main()
