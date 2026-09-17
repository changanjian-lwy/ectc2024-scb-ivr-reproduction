"""Periodic shooting for the P25-native event-controlled three-phase ring."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, documented_seed, event_ring


OUT = Path(__file__).parent / "numerical_runs/01_full_ring_calibration"
TARGET = 2.2222222222
SCALE = np.array([0.1, 0.1, 0.1, 0.1, 1.0, 1.0, 1.0])


def unpack(x):
    return np.r_[VIN, x]


def residual(x, verbose=False):
    initial = unpack(x)
    result = event_ring(initial, TARGET)
    if not result.passed:
        # Keep an explicit infeasible return rather than fabricating a map.
        out = np.full(7, 1e3)
        out[:min(len(result.history), 3)] += np.arange(min(len(result.history), 3))
        if verbose:
            print("infeasible", result.history[-1])
        return out
    raw = result.final[1:] - initial[1:]
    if verbose:
        print("period_ns", result.history[-1]["next_high_on_ns"],
              "raw_return", raw.tolist())
    return raw / SCALE


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    x0 = documented_seed(TARGET)[1:]
    lower = np.array([3.0, 2.5, -0.5, -0.5, -5.0, 15.0, 45.0])
    upper = np.array([5.0, 5.5, 0.5, 0.5, 10.0, 40.0, 75.0])
    print("initial normalized residual", residual(x0, True).tolist(), flush=True)
    fit = least_squares(residual, x0, bounds=(lower, upper),
                        x_scale="jac", diff_step=2e-5,
                        ftol=1e-10, xtol=1e-10, gtol=1e-10,
                        max_nfev=80, verbose=2)
    initial = unpack(fit.x)
    result = event_ring(initial, TARGET)
    payload = {
        "success_flag": bool(fit.success),
        "message": fit.message,
        "cost": float(fit.cost),
        "optimality": float(fit.optimality),
        "nfev": int(fit.nfev),
        "initial_state": initial.tolist(),
        "ring_passed": result.passed,
        "history": result.history,
        "return_error": (result.final - initial).tolist(),
    }
    if result.passed:
        period_ns = result.history[-1]["next_high_on_ns"]
        payload["period_ns"] = period_ns
        payload["frequency_hz"] = 1e9 / period_ns
    (OUT / "event_fixed_point.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
