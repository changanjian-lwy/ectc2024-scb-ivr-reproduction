"""D54: a timed phase-1 low-side turn-off against gate-driver jitter (src/scb_ivr/p24_jitter.py, option timed1).

    python3 scripts/p24_timed_modes.py [--jobs 4] [--reuse]

1. Phase 1's on-low interval at D51's orbit (the average and follow rules' orbit), from one cycle of the comparator
   map: turn-off time - (Ton + dl_1).
2. Gate: the timed map at that interval reproduces the comparator map's cycle (section, period, crossings, valleys,
   turn-off currents).
3. The per-edge Jacobian of the timed map at D51's orbit.
4. Average slots: linear covariance and Monte Carlo (exact rules, no trim) with the dlo gain 1/2, 1/4 and 1/8, at
   sigma = 0-100 ps, next to D53's comparator results.
Writes symbolic_derivations/03_P24_native/diagnostics/D54_timed_turnoff_5p0pct_m0p0.json; --reuse keeps its Jacobian.
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

from scb_ivr import p24_closed_loop as pcl  # noqa: E402
from scb_ivr import p24_jitter as pj  # noqa: E402
from scb_ivr.p24_exact_event_map import Circuit, section_full  # noqa: E402
from scb_ivr.p24_lowpred_event_map import ControlLP, LowPredEventMap  # noqa: E402
from scb_ivr.p24_orbit_solver import PEAK, T_RS  # noqa: E402
from scripts.p24_orbits import DIAG, R_DEV_25, VF_25, epc2067  # noqa: E402

PCT = 5.0
SIGMAS_PS = (0, 10, 20, 30, 50, 100)
SHIFTS = (1, 2, 3)                      # dlo gain 1/2, 1/4, 1/8
OUT = DIAG / "D54_timed_turnoff_5p0pct_m0p0.json"


def tlow1_of(rec):
    """Phase 1's on-low interval (ns) on the orbit: its turn-off minus its low-side turn-on (Ton + dl_1)."""
    ctl = ControlLP(ton=rec["ton_ns"] * 1e-9, i_target=-PCT / 100 * PEAK, d_high=tuple(x * 1e-9 for x in rec["d_ns"]),
                    t_restart_high=T_RS, d_low=tuple(x * 1e-9 for x in rec["d_low_ns"]), t0=rec["t0_ns"] * 1e-9)
    emap = LowPredEventMap(Circuit(), ctl, coss=epc2067(), vf=VF_25, r_dev=R_DEV_25)
    v, i = section_full(rec["section_free"], emap.ckt)
    _, _, lg = emap.run_cycle(v, i)
    t_lo1 = [x["t"] for x in lg["lowoff"] if x["phase"] == 1][0]
    return (t_lo1 - (rec["ton_ns"] + rec["d_low_ns"][0]) * 1e-9) * 1e9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--reuse", action="store_true")
    a = ap.parse_args()
    rec = json.loads((DIAG / "D51_orbit_5p0pct_m0p0.json").read_text())
    d53 = json.loads((DIAG / "D53_jitter_5p0pct_m0p0.json").read_text())
    t0 = rec["t0_ns"]
    tlow1 = tlow1_of(rec)
    out = {"pct": PCT, "tlow1_ns": tlow1, "sigmas_ps": SIGMAS_PS, "dlo_shifts": SHIFTS, "lo_tgt_lsb": 3, "lo_step_lsb": 2}

    # gate: the timed map reproduces the comparator map's cycle at the orbit
    pcl._init(epc2067, PCT, VF_25, R_DEV_25, extra={"t0_base": t0, "ton_base": rec["ton_ns"]})
    p_cmp = pj.p0_of(rec, t0)
    q_cmp = pj.core_edges(p_cmp)
    pcl._CTX["timed1"] = True
    p_tim = p_cmp.copy(); p_tim[pj.I_U] = tlow1
    q_tim = pj.core_edges(p_tim)
    out["gate_max_abs_diff"] = float(np.max(np.abs(q_tim - q_cmp)))
    print(f"tlow1 = {tlow1:.6f} ns; timed map against comparator map at the orbit: max |dq| = {out['gate_max_abs_diff']:.2e}")

    old = json.loads(OUT.read_text()) if a.reuse and OUT.exists() else None
    if old:
        p0, q0, J = np.array(old["p0"]), np.array(old["q0"]), np.array(old["jacobian"])
        out.update({k: old[k] for k in ("p0", "q0", "jacobian", "curvature_per_column", "wall_s")})
    else:
        t = time.time()
        p0, q0, J, curv = pj.edge_jacobian(rec, t0, epc2067, PCT, VF_25, R_DEV_25, jobs=a.jobs, tlow1_ns=tlow1)
        out.update(p0=p0.tolist(), q0=q0.tolist(), jacobian=J.tolist(),
                   curvature_per_column=dict(zip(pj.P_NAMES[:-1] + ["tlow1"], curv.tolist())), wall_s=time.time() - t)
        print(f"timed per-edge Jacobian in {time.time() - t:.0f} s; largest curvature {curv.max():.1e}", flush=True)
    q_names = [f"s{j}'" for j in range(pj.NS)] + ["T"] + [f"cross{k}" for k in range(1, 5)] + \
        [f"valley{k}" for k in range(1, 5)] + [f"ilo{k}" for k in range(1, 5)]
    out["dT_dtlow1"] = float(J[q_names.index("T"), pj.I_U]); out["dT_dton1"] = float(J[q_names.index("T"), pj.I_TON])
    out["dilo1_dton1"] = float(J[q_names.index("ilo1"), pj.I_TON])
    print(f"timed map: dT/dton1 = {out['dT_dton1']:+.3f} ns/ns (comparator map: +10.5); dT/dtlow1 = {out['dT_dtlow1']:+.3f}; "
          f"d i_off1/d ton1 = {out['dilo1_dton1']:+.3f} A/ns")

    out["linear"], out["monte_carlo"] = {}, {}
    for sh in SHIFTS:
        g = 1.0 / (1 << sh)
        A, Bw, Bu, C, Dw, Du = pj.linear_loop(J, "avg", timed1=True, g_lo=g)
        lin = {"eig_abs_max": float(np.max(np.abs(np.linalg.eigvals(A))))}
        for sig in SIGMAS_PS[1:]:
            lin[f"all_{sig}ps"] = dict(zip(pj.Y_NAMES, pj.covariance(A, Bw, C, Dw, sig * 1e-3).tolist()))
        out["linear"][f"shift{sh}"] = lin
        mc = {}
        for sig in SIGMAS_PS:
            r = pj.monte_carlo(p0, q0, J, "avg", sig * 1e-3, seed=1, timed1=True, lo_shift=sh)
            st = pj.mc_stats(r)
            st["elo_mean_sd_ns"] = [float(r["elo"].mean()), float(r["elo"].std())]
            st["elo_early_frac"] = float((r["elo"] < 0).mean())
            mc[f"all_{sig}ps"] = st
        out["monte_carlo"][f"shift{sh}"] = mc
        print(f"\ndlo gain 1/{1 << sh}: closed-loop |lambda|max {lin['eig_abs_max']:.4f}")
        for sig in SIGMAS_PS:
            s, c = mc[f"all_{sig}ps"], d53["monte_carlo"]["avg"][f"all_{sig}ps"]
            li = lin.get(f"all_{sig}ps")
            print(f"  {sig:3d} ps: ilo sd {[round(x, 3) for x in s['ilo_sd_a']]} (comparator {[round(x, 3) for x in c['ilo_sd_a']]}) "
                  f"T sd {s['period_sd_ns']:.3f} ({c['period_sd_ns']:.3f}) early_h {[round(x, 3) for x in s['early_high_frac'][1:]]} "
                  f"({[round(x, 3) for x in c['early_high_frac'][1:]]}) dither {s['dither_window_mean_sd_a'][0]:.2f} "
                  f"({c['dither_window_mean_sd_a'][0]:.2f}) elo {s['elo_mean_sd_ns'][0]:.3f}+-{s['elo_mean_sd_ns'][1]:.3f} ns"
                  + (f" | linear ilo {[round(li[f'ilo{k}'], 3) for k in (1, 2, 3, 4)]} T {li['T']:.3f}" if li else ""))
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
