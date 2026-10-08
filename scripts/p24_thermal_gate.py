"""D80: D74 / D77's thermal model with the final gate-level plant's switching losses (A171) in place of D73's
ideal-edge die terms, and the loop at the spec's 50 pH.

    PYTHONPATH=src python3 scripts/p24_thermal_gate.py [--jobs 3]

D74 / D77 take each high-side die's switching loss from D62's ideal-edge budget (hard turn-on at the energy balance's
minimum + turn-off overlap at t_f 0.75 ns; 0.94 W per module with reverse conduction, none on the low sides) and the
package loop from D70 at 150 pH (A145's loop-dependent loss = edge-power increase + damper, 6.6 W; 1.7 W at 50 pH).
The final plant (A172: every switch gate-driven, 50 pH, <= 0.3 ohm sink) records each switch's channel edge energy
and reverse-conduction energy. Their steady power (600-950 us, before the step) replaces the die terms (per die =
switch / devices). That power is the whole edge loss, so the loop keeps only the damper's ring energy: 1.81 W at
50 pH (A145 harness at instantaneous turn-off, an upper bound for the strong sink).
Variants (all 86 um copper, 2.5 MHz design, D73 conduction with its temperature coefficient):
  base       D74 / D77 as published (150 pH loop, D73 dies);
  loop50     base with the loop at 50 pH (D73's 1.7 W);
  gate_nom / gate_hot / gate_ss   50 pH damper + the final plant's edge power at nominal / 125 C / slow-corner devices
             (A171 S50 l_p48_1us; held constant in temperature - gate_hot bounds the edge loss's own rise).
Cases: D74's headline (kappa 1, h 2e4, 25 C, no vias); its 85 C fill f* at h 2e4, 25 / 45 C, kappa 1 / 4; D77's
coolant flow for 85 C (cu_100_400 cooler, 2 % fill; kappa 1 at 25 / 45 C, kappa 4 at 25 C).
Records: release records-a171 (run_S50_*_l_p48_1us.json); the powers used are written to the output.
Writes symbolic_derivations/03_P24_native/diagnostics/D80_thermal_gate.json.
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

import p24_coolant as C  # noqa: E402
import p24_thermal_stack as S  # noqa: E402
from scb_ivr import p24_thermal as T  # noqa: E402
from scb_ivr.p24_loss_budget import N_H, N_L  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
A171 = ROOT / "experiments" / "track_A_periodic_steady_state" / "A171_p24_gate_interlock_threshold" / "cosim"
D73_LOOP50 = 1.7            # D73 PKG["429um_50pH"]["loop"]
DAMPER50 = 1.81             # A145 a145_summary per.144_l50 damper_inst_w (W per module)
WINDOW = (600e-6, 950e-6)
GATE = {"gate_nom": "nom", "gate_hot": "hot", "gate_ss": "ss"}
VARIANTS = ("base", "loop50") + tuple(GATE)
FILLS = (0.0, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.1)
COOL_CASES = ((1.0, 25.0), (1.0, 45.0), (4.0, 25.0))


def edge_power(corner):
    """Per switch (high sides 1-4, low sides 1-4) steady channel edge + reverse-conduction power (W per module)."""
    r = json.loads((A171 / f"run_S50_{corner}_l_p48_1us.json").read_text())
    s = [q for q in r["sections"] if WINDOW[0] <= q["t_s"] <= WINDOW[1]]
    dt = s[-1]["t_s"] - s[0]["t_s"]
    e = np.sum([q["edge_energy_j"] for q in s[1:]], axis=0) / dt
    rv = np.sum([q["rev_energy_j"] for q in s[1:]], axis=0) / dt          # per switch, like edge_energy_j
    return {"edge_w": e.tolist(), "rev_w": rv.tolist()}


def sources(variant, kappa, edges):
    src, a_sw, a_cu = S.sources("2.5MHz_N29", "86um_150pH", 1.0, kappa)
    if variant == "base":
        return src, a_sw, a_cu
    src = dict(src, loop=D73_LOOP50)
    if variant in GATE:
        p = edges[GATE[variant]]
        w = np.add(p["edge_w"], p["rev_w"])
        n = len(src["die_fixed"])
        src = dict(src, loop=DAMPER50, die_fixed={k: (w[k - 1] / N_H, w[n + k - 1] / N_L) for k in src["die_fixed"]})
    return src, a_sw, a_cu


def stack(job):
    tag, variant, kappa, prm, edges = job
    src, a_sw, a_cu = sources(variant, kappa, edges)
    m = T.build(dict(prm, t_cu=S.PKG_CU["86um_150pH"]))
    t, st, _, it, fh = T.coupled(m, src, a_sw, a_cu, method="cg")
    return {"tag": tag, "variant": variant, "kappa": kappa, "params": prm, "t_max": st["t_max"],
            "junction_max": st["junction_max"], "inductor_max": st["inductor_max"], "p_total_w": st["p_total_w"],
            "p_dies_w": st["p_dies_w"], "iterations": it, "energy_rel": 2 * sum(fh.values()) / st["p_total_w"] - 1}


def coolant(job):
    tag, variant, kappa, t_in, m_dot, edges = job
    c = C.cooler_h("cu_100_400", m_dot)
    src, a_sw, a_cu = sources(variant, kappa, edges)
    m = T.build({"f_g1": 0.02, "h_bot": c["h_face"], "t_cool": t_in, "t_cu": 86e-6, "y_full": True})
    t, st, _, it, fh = T.coupled(m, src, a_sw, a_cu, method="cg", max_iter=300,
                                 coolant={"m_dot": m_dot, "t_in": t_in, "cp": C.M.WATER["cp"]})
    return {"tag": tag, "variant": variant, "kappa": kappa, "t_in": t_in, "m_dot_module": m_dot, "t_max": st["t_max"],
            "junction_max": st["junction_max"], "inductor_max": st["inductor_max"], "p_total_w": st["p_total_w"],
            "iterations": it, "energy_rel": st["coolant_heat_w"] / st["p_total_w"] - 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    args = ap.parse_args()
    edges = {c: edge_power(c) for c in GATE.values()}
    s_jobs = [(f"{v}|k{k:g}|T{tc:g}|f{f:g}", v, k, {"f_g1": f, "h_bot": 2e4, "t_cool": tc}, edges)
              for v in VARIANTS for k in (1.0, 4.0) for tc in S.T_COOL for f in FILLS]
    c_jobs = [(f"{v}|k{k:g}|T{ti:g}|m{m * 1e3:g}", v, k, ti, m, edges)
              for v in VARIANTS for k, ti in COOL_CASES for m in C.FLOWS]
    with ProcessPoolExecutor(args.jobs) as pool:
        s_rows = list(pool.map(stack, s_jobs))
        c_rows = list(pool.map(coolant, c_jobs))
    out = {"inputs": {"edges_w_per_module": edges, "window_s": WINDOW, "damper50_w": DAMPER50, "d73_loop50_w": D73_LOOP50,
                      "n_h": N_H, "n_l": N_L},
           "stack": s_rows, "coolant": c_rows, "headline": {}, "f_star": {}, "min_flow": {}}
    for v in VARIANTS:
        h = next(r for r in s_rows if r["tag"] == f"{v}|k1|T25|f0")
        out["headline"][v] = {k: h[k] for k in ("t_max", "junction_max", "inductor_max", "p_total_w", "p_dies_w")}
        for k in (1.0, 4.0):
            for tc in S.T_COOL:
                rs = [dict(r, params=dict(r["params"])) for r in s_rows if r["tag"].startswith(f"{v}|k{k:g}|T{tc:g}|")]
                out["f_star"][f"{v}|k{k:g}|T{tc:g}"] = S.f_star(rs)
        for k, ti in COOL_CASES:
            rs = [r for r in c_rows if r["tag"].startswith(f"{v}|k{k:g}|T{ti:g}|")]
            out["min_flow"][f"{v}|k{k:g}|T{ti:g}"] = C.min_flow(rs)[0]
    (DIAG / "D80_thermal_gate.json").write_text(json.dumps(out, indent=1, default=float))
    print("edge + rev W per module: " + ", ".join(f"{c} {sum(e['edge_w']) + sum(e['rev_w']):.2f}" for c, e in edges.items()))
    print(f"energy balance |rel| <= {max(abs(r['energy_rel']) for r in s_rows + c_rows):.1e}")
    for v in VARIANTS:
        h = out["headline"][v]
        fs = " ".join(f"{t}:{'-' if x is None else f'{100 * x:.2f}%'}" for t, x in out["f_star"].items() if t.startswith(v + "|"))
        mf = " ".join(f"{t[len(v) + 1:]}:{'-' if x is None else f'{x * 1e3:.2f}'}" for t, x in out["min_flow"].items()
                      if t.startswith(v + "|"))
        print(f"{v:9s} P {h['p_total_w']:5.1f} W dies {h['p_dies_w']:5.1f} W | T_max {h['t_max']:5.1f} ind {h['inductor_max']:5.1f} "
              f"jn {h['junction_max']:5.1f} C | f* {fs} | flow g/s {mf}")
    print(f"wrote {(DIAG / 'D80_thermal_gate.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
