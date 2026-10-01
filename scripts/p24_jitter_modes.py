"""D53: gate-driver jitter in the P24 closed loop (src/scb_ivr/p24_jitter.py).

    python3 scripts/p24_jitter_modes.py [--jobs 4] [--reuse]

1. Per-edge core Jacobians at D50's m = 0 orbit (fixed slots, t0 = 200 ns) and D51's (slots at k T/4: the follow and
   average rules' orbit). Check: their on-time and slot columns summed as D52's single ton and t0 inputs reproduce
   D52's Jacobian.
2. Linear covariance for fixed / follow / avg at sigma = 10-100 ps, all edges and high-side / low-side edges only.
3. Monte Carlo (linearised circuit, exact controller) at sigma = 0-100 ps, and high-only / low-only at 30 ps.
4. The co-simulation's statistics of the same runs (A98's a98_summary.json) next to them.
Writes symbolic_derivations/03_P24_native/diagnostics/D53_jitter_5p0pct_m0p0.json. --reuse takes the Jacobians from
that file instead of recomputing them.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

from scb_ivr import p24_jitter as pj  # noqa: E402
from scripts.p24_orbits import DIAG, R_DEV_25, VF_25, epc2067  # noqa: E402

PCT = 5.0
SIGMAS_PS = (0, 10, 20, 30, 50, 100)
HIGH = ["eta", "hoff1"] + [f"{e}{k}" for k in range(2, 5) for e in ("hon", "hoff")]
LOW = ["lon1", "loff1"] + [f"{e}{k}" for k in range(2, 5) for e in ("lon", "loff")]
POINT_OF = {"fixed": "D50", "follow": "D51", "avg": "D51"}
COSIM = ROOT / "experiments" / "track_A_periodic_steady_state" / "A98_jitter_amplification" / "a98_summary.json"
OUT = DIAG / "D53_jitter_5p0pct_m0p0.json"


def d52_check(J_edge, d52):
    """Largest difference between D52's Jacobian and the per-edge one with its on-time columns summed (= ton) and its
    slot columns weighted (k-1)/N (= t0), relative to the column's largest entry."""
    J52 = np.array(d52["points"]["D51"]["jacobian"])
    cols = {"ton": J_edge[:, pj.I_TON:pj.I_TON + pj.N].sum(axis=1),
            "t0": sum(J_edge[:, pj.I_SL + j - 1] * j / pj.N for j in range(1, pj.N))}
    p52 = d52["p_names"]
    out = {}
    for name, col in cols.items():
        ref = J52[:, p52.index(name)]
        out[name] = float(np.max(np.abs(col - ref)) / np.max(np.abs(ref)))
    for j in range(pj.NS):                                       # the section columns are the same inputs
        ref = J52[:, j]
        out[f"s{j}"] = float(np.max(np.abs(J_edge[:, j] - ref)) / np.max(np.abs(ref)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    out = {"pct": PCT, "sigmas_ps": SIGMAS_PS, "p_names": pj.P_NAMES, "w_names": pj.W_NAMES, "y_names": pj.Y_NAMES,
           "high_edges": HIGH, "low_edges": LOW, "points": {}, "linear": {}, "monte_carlo": {}}
    old = json.loads(OUT.read_text()) if a.reuse and OUT.exists() else None
    pts = {}
    for tag in ("D50", "D51"):
        rec = json.loads((DIAG / f"{tag}_orbit_5p0pct_m0p0.json").read_text())
        t0 = 200.0 if tag == "D50" else rec["t0_ns"]
        if old:
            o = old["points"][tag]
            p0, q0, J = np.array(o["p0"]), np.array(o["q0"]), np.array(o["jacobian"])
            out["points"][tag] = o
        else:
            t = time.time()
            p0, q0, J, curv = pj.edge_jacobian(rec, t0, epc2067, PCT, VF_25, R_DEV_25, jobs=a.jobs)
            out["points"][tag] = {"p0": p0.tolist(), "q0": q0.tolist(), "jacobian": J.tolist(),
                                  "curvature_per_column": dict(zip(pj.P_NAMES, curv.tolist())), "wall_s": time.time() - t}
            print(f"{tag}: per-edge Jacobian in {time.time() - t:.0f} s; largest curvature {curv.max():.1e}", flush=True)
        pts[tag] = (p0, q0, J)
    d52 = json.loads((DIAG / "D52_closed_loop_5p0pct_m0p0.json").read_text())
    out["d52_consistency"] = d52_check(pts["D51"][2], d52)
    print("consistency with D52 (largest relative column difference):",
          {k: f"{v:.1e}" for k, v in out["d52_consistency"].items()})

    for rule in ("fixed", "follow", "avg"):
        p0, q0, J = pts[POINT_OF[rule]]
        A, Bw, Bu, C, Dw, Du = pj.linear_loop(J, rule)
        lin = {"eig_abs_max": float(np.max(np.abs(np.linalg.eigvals(A))))}
        for sig in SIGMAS_PS[1:]:
            for edges, inp in (("all", None), ("high", HIGH), ("low", LOW)):
                sd = pj.covariance(A, Bw, C, Dw, sig * 1e-3, inp)
                lin[f"{edges}_{sig}ps"] = dict(zip(pj.Y_NAMES, sd.tolist()))
        h1 = C @ np.linalg.solve(-np.eye(len(A)) - A, Bu) + Du
        lin["trim_two_cycle_a"] = dict(zip(pj.Y_NAMES, (np.abs(h1) * 0.125).tolist()))
        out["linear"][rule] = lin
        mc = {}
        for sig in SIGMAS_PS:
            mc[f"all_{sig}ps"] = pj.mc_stats(pj.monte_carlo(p0, q0, J, rule, sig * 1e-3, seed=1))
        for edges, inp in (("high", HIGH), ("low", LOW)):
            mc[f"{edges}_30ps"] = pj.mc_stats(pj.monte_carlo(p0, q0, J, rule, 0.030, seed=1, jitter_inputs=inp))
        out["monte_carlo"][rule] = mc
        print(f"\n{rule}: closed-loop |lambda|max {lin['eig_abs_max']:.4f}")
        for sig in SIGMAS_PS:
            s = mc[f"all_{sig}ps"]
            li = lin.get(f"all_{sig}ps")
            lin_txt = (f" | linear ilo sd {[round(li[f'ilo{k}'], 3) for k in (1, 2, 3, 4)]} valley sd "
                       f"{[round(li[f'valley{k}'], 3) for k in (2, 3, 4)]} eh sd {[round(li[f'eh{k}'], 3) for k in (2, 3, 4)]}"
                       if li else "")
            print(f"  MC {sig:3d} ps: ilo sd {[round(x, 3) for x in s['ilo_sd_a']]} early_h "
                  f"{[round(x, 3) for x in s['early_high_frac']]} eh sd {[round(x[1], 3) for x in s['eh_mean_sd_ns']]} "
                  f"valley sd {[round(x, 3) for x in s['valley_sd_ns']]} early_l {[round(x, 3) for x in s['early_low_frac']]} "
                  f"T sd {s['period_sd_ns']:.3f} dither {s['dither_window_mean_sd_a'][0]:.2f}{lin_txt}")
        for edges in ("high", "low"):
            s = mc[f"{edges}_30ps"]
            print(f"  MC 30 ps {edges:4s} only: ilo sd {[round(x, 3) for x in s['ilo_sd_a']]} early_h "
                  f"{[round(x, 3) for x in s['early_high_frac']]}")
    if COSIM.exists():
        out["cosim"] = json.loads(COSIM.read_text())
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
