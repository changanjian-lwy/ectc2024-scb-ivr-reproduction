"""Release L and Ton together while retaining all strict P25 constraints."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, SLOT, event_ring
from strict_joint_p25_fit import (
    IDEAL_PEAK_A, TARGET_MODULE_CURRENT_A, SCALE,
    V_RETURN_TOL, I_RETURN_TOL, SPACING_TOL_NS, PEAK_TOL_A,
    MODULE_CURRENT_TOL_A,
)


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/04_L_ton_joint_release"


def decode(q):
    return np.r_[VIN, q[:7]], q[7] * IDEAL_PEAK_A, q[8] * 1e-9, q[9] * 1e-9


def raw(q):
    initial, target, inductance, ton = decode(q)
    result = event_ring(initial, target, lphase=inductance, ton=ton)
    if not result.passed:
        return None, result, None
    period = result.history[-1]["next_high_on_ns"]
    spacings = np.array([h["phase_spacing_ns"] for h in result.history])
    peaks = np.array([h["peak_a"] for h in result.history])
    module_current = float(result.charge_a_ns.sum() / period)
    residual = np.r_[result.final[1:] - initial[1:],
                     spacings - SLOT * 1e9,
                     peaks - IDEAL_PEAK_A,
                     module_current - TARGET_MODULE_CURRENT_A]
    metrics = dict(period_ns=period, spacings_ns=spacings.tolist(),
                   peaks_a=peaks.tolist(), module_average_current_a=module_current,
                   state_return=(result.final-initial).tolist())
    return residual, result, metrics


def norm(q):
    residual, _, _ = raw(q)
    return np.full(len(SCALE), 1e6) if residual is None else residual / SCALE


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    previous = json.loads((HERE / "numerical_runs/03_one_parameter_release/one_parameter_release.json").read_text())
    lcase = next(x for x in previous["runs"] if x["branch"] == "L")
    q0 = np.r_[lcase["initial_state"][1:], lcase["negative_fraction"],
               lcase["inductance_nH"], 554.6357179160397]
    lo = np.r_[[3, 2.5, -.5, -.5, -10, 5, 20], .05, 15., 250.]
    hi = np.r_[[5, 5.5, .5, .5, 20, 55, 90], .10, 50., 650.]
    print("initial max violation", np.max(abs(norm(q0))), flush=True)
    fit = least_squares(norm, q0, bounds=(lo, hi), x_scale="jac", diff_step=2e-5,
                        ftol=1e-11, xtol=1e-11, gtol=1e-11,
                        max_nfev=150, verbose=2)
    residual, result, metrics = raw(fit.x)
    normalized = norm(fit.x)
    initial, target, inductance, ton = decode(fit.x)
    checks = {
        "event_ring": bool(result.passed),
        "voltage_return": bool(residual is not None and np.max(abs(residual[:4])) <= V_RETURN_TOL),
        "current_return": bool(residual is not None and np.max(abs(residual[4:7])) <= I_RETURN_TOL),
        "equal_spacing": bool(residual is not None and np.max(abs(residual[7:10])) <= SPACING_TOL_NS),
        "peak_current": bool(residual is not None and np.max(abs(residual[10:13])) <= PEAK_TOL_A),
        "module_power": bool(residual is not None and abs(residual[13]) <= MODULE_CURRENT_TOL_A),
        "negative_fraction_range": bool(.05 <= fit.x[7] <= .10),
    }
    payload = {
        "optimizer_success_flag": bool(fit.success), "message": fit.message,
        "nfev": int(fit.nfev), "cost": float(fit.cost),
        "negative_fraction": float(fit.x[7]),
        "inductance_nH": inductance*1e9, "ton_ns": ton*1e9,
        "initial_state": initial.tolist(), "metrics": metrics,
        "raw_residual": None if residual is None else residual.tolist(),
        "normalized_residual": normalized.tolist(),
        "max_acceptance_violation_factor": float(np.max(abs(normalized))),
        "checks": checks, "strict_pass": bool(all(checks.values())),
        "claim_limit": "single local start; not a global feasibility proof",
    }
    (OUT / "L_ton_joint_release.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
