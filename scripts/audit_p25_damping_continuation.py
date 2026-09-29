"""D42: series-resistance continuation of the D41 P25-scale orbit (stability vs damping).

Run from the project root: python3 -m scripts.audit_p25_damping_continuation
Writes symbolic_derivations/02_P25_native/diagnostics/D42_damping_continuation.json.

Series resistance per phase (Components.winding_ohm) is stepped 0 -> 4.9 mOhm.
Each step's Newton starts from the previous converged section state.
PROJECT_DECISION: 4.9 mOhm lumps P25's switch Ron into the phase path,
duty-weighted:
    0.25 * 7 mOhm (1 GS61008T high side) + 0.75 * 3.5 mOhm (2 low sides)
    + 0.5 mOhm (Coilcraft DCR).
The native model's ON switches are ideal, and every phase current flows
through exactly one of its switches, so this is a first-order equivalent,
not a device model.
Load current, Ton, alpha and the phase shifts stay at D41's values: open
loop, so Vo sags as R rises.
"""
import json
import time
from pathlib import Path

import numpy as np

from scripts import audit_p25_single_sensor_closure as A

OUT = Path(__file__).resolve().parents[1] / "symbolic_derivations" / "02_P25_native" / "diagnostics" / "D42_damping_continuation.json"
R_STEPS = (0.0, 0.5e-3, 1e-3, 2e-3, 3e-3, 4e-3, 4.9e-3)


def run():
    out = {"scope": "P25-scale orders of magnitude; D41 single-sensor control; series R lumps Ron+DCR (first order)",
           "R_steps_ohm": list(R_STEPS), "points": []}
    z = np.array(A.SEED0, float)
    for R in R_STEPS:
        t0 = time.time()
        contract, options = A.context(A.P25_SCALE["phase_shift_s"], winding_ohm=(R,) * 3)
        z_new, rows, r = A.newton(contract, options, z.copy(), iterations=15)
        if r.attempt.end is None:
            out["points"].append({"R_ohm": R, "blocked_at": r.attempt.failed_mode, "newton": rows})
            print(f"R={R * 1e3:.1f} mOhm: blocked at {r.attempt.failed_mode}", flush=True)
            break
        J = A.jacobian(contract, options, z_new)
        w = np.linalg.eigvals(J)
        best = min((x for x in rows if "max_dI" in x), key=lambda x: x["max_dI"] + x["max_dV"])
        out["points"].append({"R_ohm": R, "z_star": dict(zip(A.NAMES, z_new.tolist())),
                              "period_s": r.attempt.end.last_event.time_s, "status": r.status,
                              "residual_max_dV": best["max_dV"], "residual_max_dI": best["max_dI"],
                              "eigenvalues": [[float(x.real), float(x.imag)] for x in w],
                              "max_abs_eigenvalue": float(np.max(np.abs(w))), "newton": rows})
        print(f"R={R * 1e3:.1f} mOhm: |eig|max {np.max(np.abs(w)):.4f}  Vo {z_new[2]:.4f} V  "
              f"T {r.attempt.end.last_event.time_s * 1e9:.3f} ns  residual {best['max_dV']:.1e} V {best['max_dI']:.1e} A  "
              f"wall {time.time() - t0:.0f}s", flush=True)
        z = z_new
        OUT.write_text(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    run()
