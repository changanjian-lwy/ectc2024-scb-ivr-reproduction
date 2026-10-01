"""D52: closed-loop modes of the P24 timed-low-side map with the error-based correctors, for three slot rules
(src/scb_ivr/p24_closed_loop.py).

    python3 scripts/p24_closed_loop_modes.py [--jobs 4]

Core Jacobians at D50's m = 0 orbit (fixed slots, t0 = 200 ns) and D51's (slots at k T/4; also the average rule's
orbit, since T_avg = T on a period-1 orbit). Closed loops: fixed (D50), fixed_at_T (D51's orbit with t0 held at
its period: the like-for-like reference), follow and avg (D51). For each: eigenvalues, the gain at the two-cycle
frequency (z = -1) from phase 1's current threshold to every output, and the gain over the band. The two-cycle
amplitude for the trim's +-1 LSB alternation is the gain times 0.125 A. Writes
symbolic_derivations/03_P24_native/diagnostics/D52_closed_loop_5p0pct_m0p0.json.
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

from scb_ivr.p24_closed_loop import NS, P_NAMES, Q_NAMES, Y_NAMES, closed_loop, core_jacobian, response  # noqa: E402
from scripts.p24_orbits import DIAG, R_DEV_25, VF_25, epc2067  # noqa: E402

PCT, U_AMP = 5.0, 0.125          # load (%), trim alternation amplitude (A): +-1 LSB of 0.25 A around the mean
OMEGA = np.linspace(0.0, np.pi, 61)


def p0_of(rec, t0_ns):
    return np.concatenate([rec["section_free"], rec["d_ns"], rec["d_low_ns"], [rec["ton_ns"], t0_ns, 0.0]])


def describe(A, B, C, D):
    ev = np.linalg.eigvals(A)
    ev = ev[np.argsort(-np.abs(ev))]
    h1 = response(A, B, C, D, -1.0 + 0j)
    band = np.array([np.abs(response(A, B, C, D, np.exp(1j * w))) for w in OMEGA])
    near_m1 = [complex(x) for x in ev if x.real < 0 and abs(x) > 0.5]
    return {"eig": [[float(x.real), float(x.imag)] for x in ev], "eig_abs_max": float(np.abs(ev[0])),
            "eig_near_minus1": [[x.real, x.imag, abs(x)] for x in near_m1],
            "gain_z_minus1": {n: float(abs(g)) for n, g in zip(Y_NAMES, h1)},
            "two_cycle_amp_for_trim": {n: float(abs(g)) * U_AMP for n, g in zip(Y_NAMES, h1)},
            "band_gain": {n: band[:, j].tolist() for j, n in enumerate(Y_NAMES)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--step-check", action="store_true",
                    help="also D51 with half and twice the steps; compares the two-cycle gains of fixed_at_T, follow and "
                         "avg on the currents, the period and the high-side errors (the low-side errors, about 0.001 ns, "
                         "are at the noise level)")
    a = ap.parse_args()
    d50 = json.loads((DIAG / "D50_orbit_5p0pct_m0p0.json").read_text())
    d51 = json.loads((DIAG / "D51_orbit_5p0pct_m0p0.json").read_text())
    out = {"pct": PCT, "u_amp_a": U_AMP, "omega_rad_per_cycle": OMEGA.tolist(), "p_names": P_NAMES, "q_names": Q_NAMES,
           "y_names": Y_NAMES, "g": 0.5, "ki_ns_per_v": 0.25, "e_ps": 93.75, "points": {}, "rules": {}}
    J = {}
    for tag, rec, t0 in (("D50", d50, 200.0), ("D51", d51, d51["t0_ns"])):
        t = time.time()
        p0 = p0_of(rec, t0)
        q0, J[tag], curv = core_jacobian(p0, epc2067, PCT, VF_25, R_DEV_25, jobs=a.jobs)
        res = {"section": float(np.max(np.abs(q0[:NS] - p0[:NS]))),
               "period_minus_t0_ns": float(q0[NS] - t0) if tag == "D51" else None}
        out["points"][tag] = {"p0": p0.tolist(), "q0": q0.tolist(), "jacobian": J[tag].tolist(),
                              "curvature_per_column": dict(zip(P_NAMES, curv.tolist())), "fixed_point_residual": res,
                              "wall_s": time.time() - t}
        print(f"{tag}: core Jacobian in {time.time() - t:.0f} s; section residual {res['section']:.2e}; "
              f"largest curvature ratio {curv.max():.2e} ({P_NAMES[int(np.argmax(curv))]})", flush=True)
    for rule, tag, r in (("fixed", "D50", "fixed"), ("fixed_at_T", "D51", "fixed"), ("follow", "D51", "follow"),
                         ("avg", "D51", "avg")):
        out["rules"][rule] = describe(*closed_loop(J[tag], r))
        x = out["rules"][rule]
        amp = x["two_cycle_amp_for_trim"]
        print(f"\n{rule:10s} |lambda|max {x['eig_abs_max']:.4f}; near -1: "
              f"{[(round(e[0], 4), round(e[1], 4)) for e in x['eig_near_minus1']]}")
        print(f"   two-cycle amplitude for +-{U_AMP} A trim: ilo1-4 {[round(amp[f'ilo{k}'], 3) for k in (1, 2, 3, 4)]} A, "
              f"T {amp['T']:.4f} ns, eh {[round(amp[f'eh{k}'], 4) for k in (1, 2, 3, 4)]} ns, "
              f"el {[round(amp[f'el{k}'], 4) for k in (1, 2, 3, 4)]} ns")
    if a.step_check:
        p0 = np.array(out["points"]["D51"]["p0"])
        keep = [j for j, n in enumerate(Y_NAMES) if not n.startswith("el")]
        chk = {}
        for scale in (0.5, 2.0):
            _, Js, _ = core_jacobian(p0, epc2067, PCT, VF_25, R_DEV_25, jobs=a.jobs, scale=scale)
            for rule, r in (("fixed_at_T", "fixed"), ("follow", "follow"), ("avg", "avg")):
                gs = np.abs(response(*closed_loop(Js, r), -1.0 + 0j))[keep]
                g1 = np.array([out["rules"][rule]["gain_z_minus1"][n] for n in Y_NAMES])[keep]
                chk[f"{rule}_step_x{scale}"] = float(np.max(np.abs(gs - g1) / g1))
        out["step_check_max_rel_change_gain_z_minus1"] = chk
        print("step check, largest relative change of the z = -1 gains (currents, period, high-side errors):", chk)
    path = DIAG / "D52_closed_loop_5p0pct_m0p0.json"
    path.write_text(json.dumps(out, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
