"""Strict joint fit with a labelled negative-valley current-balance identity.

This branch does not overwrite P25's printed peak-current expression.  It
tests the mathematically consistent triangular-wave alternative
Ipk = 2*Iphase_avg/(1-alpha) when Imin = -alpha*Ipk.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, SLOT, event_ring
from strict_joint_p25_fit import (
    TARGET_MODULE_CURRENT_A, SCALE,
    V_RETURN_TOL, I_RETURN_TOL, SPACING_TOL_NS, PEAK_TOL_A,
    MODULE_CURRENT_TOL_A,
)


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/05_negative_valley_corrected"
ZERO_VALLEY_PEAK = 2.0 * 200.0 / 9.0


def decode(q):
    alpha = q[7]
    peak = ZERO_VALLEY_PEAK / (1.0 - alpha)
    return (np.r_[VIN, q[:7]], alpha, peak, alpha * peak,
            q[8] * 1e-9, q[9] * 1e-9)


def raw(q):
    initial, alpha, peak_target, negative_target, inductance, ton = decode(q)
    result = event_ring(initial, negative_target, lphase=inductance, ton=ton)
    if not result.passed:
        return None, result, None
    period = result.history[-1]["next_high_on_ns"]
    spacings = np.array([h["phase_spacing_ns"] for h in result.history])
    peaks = np.array([h["peak_a"] for h in result.history])
    module_current = float(result.charge_a_ns.sum() / period)
    residual = np.r_[result.final[1:] - initial[1:],
                     spacings - SLOT * 1e9,
                     peaks - peak_target,
                     module_current - TARGET_MODULE_CURRENT_A]
    metrics = dict(period_ns=period, spacings_ns=spacings.tolist(),
                   peak_target_a=peak_target, negative_target_a=negative_target,
                   peaks_a=peaks.tolist(), module_average_current_a=module_current,
                   state_return=(result.final-initial).tolist())
    return residual, result, metrics


def norm(q):
    residual, _, _ = raw(q)
    return np.full(len(SCALE), 1e6) if residual is None else residual / SCALE


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((HERE / "numerical_runs/04_L_ton_joint_release/L_ton_joint_release.json").read_text())
    q0 = np.r_[prior["initial_state"][1:], prior["negative_fraction"],
               prior["inductance_nH"], prior["ton_ns"]]
    lo = np.r_[[3, 2.5, -.5, -.5, -10, 5, 20], .05, 15., 250.]
    hi = np.r_[[5, 5.5, .5, .5, 20, 55, 90], .10, 50., 650.]
    print("initial max violation", np.max(abs(norm(q0))), flush=True)
    fit = least_squares(norm, q0, bounds=(lo, hi), x_scale="jac", diff_step=2e-5,
                        ftol=1e-12, xtol=1e-12, gtol=1e-12,
                        max_nfev=180, verbose=2)
    residual, result, metrics = raw(fit.x)
    normalized = norm(fit.x)
    initial, alpha, peak, negative, inductance, ton = decode(fit.x)
    checks = {
        "event_ring": bool(result.passed),
        "voltage_return": bool(residual is not None and np.max(abs(residual[:4])) <= V_RETURN_TOL),
        "current_return": bool(residual is not None and np.max(abs(residual[4:7])) <= I_RETURN_TOL),
        "equal_spacing": bool(residual is not None and np.max(abs(residual[7:10])) <= SPACING_TOL_NS),
        "corrected_peak_current": bool(residual is not None and np.max(abs(residual[10:13])) <= PEAK_TOL_A),
        "module_power": bool(residual is not None and abs(residual[13]) <= MODULE_CURRENT_TOL_A),
        "negative_fraction_range": bool(.05 <= alpha <= .10),
    }
    payload = {
        "branch_status": "cross-paper mathematical correction; not P25 explicit",
        "identity": "Ipk=2*Io/(nP*nM)/(1-alpha), Imin=-alpha*Ipk",
        "optimizer_success_flag": bool(fit.success), "message": fit.message,
        "nfev": int(fit.nfev), "cost": float(fit.cost),
        "negative_fraction": float(alpha), "negative_target_a": float(negative),
        "corrected_peak_target_a": float(peak),
        "inductance_nH": inductance*1e9, "ton_ns": ton*1e9,
        "initial_state": initial.tolist(), "metrics": metrics,
        "raw_residual": None if residual is None else residual.tolist(),
        "normalized_residual": normalized.tolist(),
        "max_acceptance_violation_factor": float(np.max(abs(normalized))),
        "checks": checks, "strict_pass": bool(all(checks.values())),
        "claim_limit": "single local start and assumed triangular average identity",
    }
    (OUT / "negative_corrected_joint_fit.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
