"""Refine the negative-valley branch without changing acceptance limits."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from strict_joint_negative_corrected import HERE, OUT, raw, decode
from strict_joint_p25_fit import (
    SCALE, V_RETURN_TOL, I_RETURN_TOL, SPACING_TOL_NS, PEAK_TOL_A,
    MODULE_CURRENT_TOL_A,
)


def main():
    source = json.loads((OUT / "negative_corrected_joint_fit.json").read_text())
    q0 = np.r_[source["initial_state"][1:], source["negative_fraction"],
               source["inductance_nH"], source["ton_ns"]]
    # Search weights are tightened only for the voltage-return terms.  The
    # hard acceptance limits below remain exactly unchanged.
    search_scale = SCALE.copy()
    search_scale[:4] *= 0.25
    def objective(q):
        residual, _, _ = raw(q)
        return np.full(len(SCALE), 1e6) if residual is None else residual/search_scale
    lo = np.r_[[3, 2.5, -.5, -.5, -10, 5, 20], .05, 15., 250.]
    hi = np.r_[[5, 5.5, .5, .5, 20, 55, 90], .10, 50., 650.]
    fit = least_squares(objective, q0, bounds=(lo, hi), x_scale="jac", diff_step=1e-5,
                        ftol=1e-12, xtol=1e-12, gtol=1e-12,
                        max_nfev=160, verbose=2)
    residual, result, metrics = raw(fit.x)
    acceptance = residual / SCALE
    initial, alpha, peak, negative, inductance, ton = decode(fit.x)
    checks = {
        "event_ring": bool(result.passed),
        "voltage_return": bool(np.max(abs(residual[:4])) <= V_RETURN_TOL),
        "current_return": bool(np.max(abs(residual[4:7])) <= I_RETURN_TOL),
        "equal_spacing": bool(np.max(abs(residual[7:10])) <= SPACING_TOL_NS),
        "corrected_peak_current": bool(np.max(abs(residual[10:13])) <= PEAK_TOL_A),
        "module_power": bool(abs(residual[13]) <= MODULE_CURRENT_TOL_A),
        "negative_fraction_range": bool(.05 <= alpha <= .10),
    }
    payload = {
        "branch_status": "cross-paper mathematical correction; not P25 explicit",
        "acceptance_limits_unchanged": True,
        "optimizer_success_flag": bool(fit.success), "message": fit.message,
        "nfev": int(fit.nfev), "cost_in_refinement_metric": float(fit.cost),
        "negative_fraction": float(alpha), "negative_target_a": float(negative),
        "corrected_peak_target_a": float(peak),
        "inductance_nH": inductance*1e9, "ton_ns": ton*1e9,
        "initial_state": initial.tolist(), "metrics": metrics,
        "raw_residual": residual.tolist(),
        "acceptance_normalized_residual": acceptance.tolist(),
        "max_acceptance_violation_factor": float(np.max(abs(acceptance))),
        "checks": checks, "strict_pass": bool(all(checks.values())),
        "claim_limit": "single local refinement and assumed triangular average identity",
    }
    path = OUT / "negative_corrected_refined.json"
    path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
