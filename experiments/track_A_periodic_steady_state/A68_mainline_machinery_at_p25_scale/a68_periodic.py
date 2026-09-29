"""A68 - periodic-closure diagnostics of the main line's section map at P25 scale.

Uses a68_context (main-line code, read only) with the DIAGNOSTIC entry
override (tolerance-level outward reverse gaps released; logged).

1-2. Truncated-SVD Newton on G(z) = F(z) - z with a central-difference
   Jacobian and a backtracking line search that accepts only tested
   descent steps (max 15). Directions of J - I with singular value < 1e-3
   of the largest are dropped and recorded.
3. Section-map eigenvalues (central differences) at the final point.
4. Plain iteration z <- F(z) from the final point, until blocked or 60 cycles.

Writes results.json. Usage: python3 a68_periodic.py
"""
import json
import time
from pathlib import Path

import numpy as np

import a68_context as C

HERE = Path(__file__).resolve().parent
SC = C.P25
NAMES = ("a2_v", "x1_v", "out_v", "iL1_a", "iL2_a", "iL3_a")
SCALE = np.array([1, 1, .1, 1, 1, 1.])


def F(z):
    r, d = C.run(SC, seed=tuple(float(x) for x in z))
    if r.attempt.end is None:
        return None, d["failed_mode"]
    e = r.attempt.end.last_event
    return np.array([e.voltage_v[1], e.voltage_v[2], e.voltage_v[5], *e.current_a], float), e.time_s


def norms(g):
    return float(np.max(np.abs(g[:3]))), float(np.max(np.abs(g[3:])))


def jac_forward(z, f0, h0=1e-5):
    J = np.zeros((6, 6))
    for j in range(6):
        h = h0 * SCALE[j]
        zp = z.copy(); zp[j] += h
        fp, _ = F(zp)
        if fp is None:
            zp[j] -= 2 * h; fp, _ = F(zp); h = -h
        J[:, j] = (fp - f0) / h
    return J


def jac_central(z, h0=2e-6):
    J = np.zeros((6, 6))
    for j in range(6):
        h = h0 * SCALE[j]
        zp = z.copy(); zp[j] += h
        zm = z.copy(); zm[j] -= h
        fp, _ = F(zp); fm, _ = F(zm)
        J[:, j] = (fp - fm) / (2 * h)
    return J


def main():
    t0 = time.time()
    out = {"experiment": "A68", "classification": "DIAGNOSTIC (main-line machinery, read only, entry override on)",
           "source_hash": C.source_hashes(), "scenario": {k: (list(v) if isinstance(v, tuple) else v)
                                                           for k, v in SC.items()}}
    C.install_entry_override()
    z = np.array(SC["seed"], float)
    steps = []
    for it in range(15):
        f0, T = F(z)
        g = f0 - z
        J = jac_central(z)
        U, s, Vt = np.linalg.svd(J - np.eye(6))
        keep = s > 1e-3 * s[0]
        steps.append({"iter": it, "z": z.tolist(), "max_dV": norms(g)[0], "max_dI": norms(g)[1], "period_s": T,
                      "singular_values": s.tolist(), "kept": int(keep.sum()),
                      "dropped_directions": [dict(zip(NAMES, v)) for v in Vt[~keep].tolist()]})
        print(f"tsvd-newton {it}: |G| {norms(g)[0]:.3e} V {norms(g)[1]:.3e} A  T {T * 1e9:.4f} ns  "
              f"sv {np.array2string(s, precision=2)} kept {int(keep.sum())}", flush=True)
        step = -(Vt[keep].T @ ((U[:, keep].T @ g) / s[keep]))
        lam, accepted = 1.0, None
        while lam > 1e-4:
            trial = z + lam * step
            ft, _ = F(trial)
            if ft is not None and np.max(np.abs((ft - trial) / SCALE)) < np.max(np.abs(g / SCALE)):
                accepted = trial
                break
            lam /= 2
        if accepted is None:
            print("   no descent step found; stop", flush=True)
            break
        z = accepted
    out["tsvd_newton"] = steps

    f0, T = F(z)
    J = jac_central(z)
    w = np.linalg.eigvals(J)
    out["final"] = {"z": dict(zip(NAMES, z.tolist())), "period_s": T, "frequency_hz": 1 / T,
                    "max_dV": norms(f0 - z)[0], "max_dI": norms(f0 - z)[1],
                    "eigenvalues": [[float(x.real), float(x.imag)] for x in w]}
    print("eigenvalues:", np.round(w, 4), flush=True)

    picard, zz = [], z.copy()
    for k in range(60):
        fz, T = F(zz)
        if fz is None:
            picard.append({"iter": k, "blocked_at": T})
            break
        picard.append({"iter": k, "max_dV": norms(fz - zz)[0], "max_dI": norms(fz - zz)[1], "period_s": T})
        zz = fz
    out["plain_iteration"] = picard
    ov = C.OVERRIDE_LOG
    out["override"] = {"uses": len(ov), "max_abs_gap_v": max(abs(o["value_v"]) for o in ov),
                       "all_outward": all(o["rate_v_s"] > 0 for o in ov),
                       "gaps": sorted({o["gap"] for o in ov}), "modes": sorted({o["mode"] for o in ov})}
    out["wall_s"] = time.time() - t0
    (HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"plain iteration: {picard[-1]}")
    print(f"override: {out['override']}  wall {out['wall_s']:.0f} s")


if __name__ == "__main__":
    main()
