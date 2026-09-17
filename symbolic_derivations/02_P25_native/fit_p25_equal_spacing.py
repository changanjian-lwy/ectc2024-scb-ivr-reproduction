"""Local joint fit of P25 periodic return and nominal 120-degree spacing.

This is a feasibility audit, not a proof of global infeasibility.  The
negative-current fraction is allowed only inside P25's published 5%-10% band.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, SLOT, event_ring


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/01_full_ring_calibration"
STATE_SCALE = np.array([0.1, 0.1, 0.1, 0.1, 1.0, 1.0, 1.0])
SPACING_SCALE_NS = 10.0
IDEAL_PEAK = 2.0 * 200.0 / 9.0


def unpack(q):
    initial = np.r_[VIN, q[:7]]
    target = q[7] * IDEAL_PEAK
    return initial, target


def residual(q):
    initial, target = unpack(q)
    result = event_ring(initial, target)
    if not result.passed:
        return np.full(10, 1e3)
    state = (result.final[1:] - initial[1:]) / STATE_SCALE
    spacings = np.array([h["phase_spacing_ns"] for h in result.history])
    timing = (spacings - SLOT * 1e9) / SPACING_SCALE_NS
    return np.r_[state, timing]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    previous = json.loads((OUT / "event_fixed_point.json").read_text())
    x = np.asarray(previous["initial_state"])[1:]
    q0 = np.r_[x, 0.05]
    lower = np.r_[[3.0, 2.5, -0.5, -0.5, -5.0, 15.0, 40.0], 0.05]
    upper = np.r_[[5.0, 5.5, 0.5, 0.5, 15.0, 45.0, 80.0], 0.10]
    print("initial residual", residual(q0).tolist(), flush=True)
    fit = least_squares(residual, q0, bounds=(lower, upper),
                        x_scale="jac", diff_step=2e-5,
                        ftol=1e-10, xtol=1e-10, gtol=1e-10,
                        max_nfev=80, verbose=2)
    initial, target = unpack(fit.x)
    result = event_ring(initial, target)
    payload = {
        "optimizer_success_flag": bool(fit.success),
        "message": fit.message,
        "cost": float(fit.cost),
        "optimality": float(fit.optimality),
        "nfev": int(fit.nfev),
        "negative_fraction": float(fit.x[7]),
        "negative_target_a": float(target),
        "initial_state": initial.tolist(),
        "ring_passed": result.passed,
        "history": result.history,
        "return_error": (result.final - initial).tolist(),
    }
    if result.passed:
        spacings = [h["phase_spacing_ns"] for h in result.history]
        payload["phase_spacings_ns"] = spacings
        payload["max_spacing_error_ns"] = max(abs(np.asarray(spacings) - SLOT * 1e9))
        payload["period_ns"] = result.history[-1]["next_high_on_ns"]
    (OUT / "equal_spacing_fit.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
