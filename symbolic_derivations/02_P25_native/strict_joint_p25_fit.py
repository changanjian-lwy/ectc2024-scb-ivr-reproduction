"""Strict local joint feasibility audit for the reported P25 operating point.

The optimizer is only a search mechanism.  A candidate passes solely through
the separate hard acceptance checks defined below; scipy's success flag is
never interpreted as physical feasibility.
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from p25_native_fixed_slot_ring import VIN, SLOT, event_ring


HERE = Path(__file__).parent
OUT = HERE / "numerical_runs/02_strict_joint_fit"
IDEAL_PEAK_A = 2.0 * 200.0 / 9.0
TARGET_MODULE_CURRENT_A = 200.0 / 3.0

# Hard acceptance tolerances.  These also nondimensionalize the residual, so
# max(abs(residual)) is the largest acceptance violation factor.
V_RETURN_TOL = 1e-3
I_RETURN_TOL = 1e-2
SPACING_TOL_NS = 1.0
PEAK_TOL_A = 0.5
MODULE_CURRENT_TOL_A = 0.5
SCALE = np.r_[np.full(4, V_RETURN_TOL), np.full(3, I_RETURN_TOL),
              np.full(3, SPACING_TOL_NS), np.full(3, PEAK_TOL_A),
              MODULE_CURRENT_TOL_A]


def unpack(q):
    return np.r_[VIN, q[:7]], q[7] * IDEAL_PEAK_A


def physical_residual(q):
    initial, negative_target = unpack(q)
    result = event_ring(initial, negative_target)
    if not result.passed:
        return None, result, None
    period_ns = result.history[-1]["next_high_on_ns"]
    state_return = result.final[1:] - initial[1:]
    spacings = np.array([h["phase_spacing_ns"] for h in result.history])
    peaks = np.array([h["peak_a"] for h in result.history])
    module_current = float(np.sum(result.charge_a_ns) / period_ns)
    raw = np.r_[state_return,
                spacings - SLOT * 1e9,
                peaks - IDEAL_PEAK_A,
                module_current - TARGET_MODULE_CURRENT_A]
    metrics = {
        "period_ns": float(period_ns),
        "phase_spacings_ns": spacings.tolist(),
        "peaks_a": peaks.tolist(),
        "module_average_current_a": module_current,
        "state_return": (result.final - initial).tolist(),
    }
    return raw, result, metrics


def normalized_residual(q):
    raw, result, _ = physical_residual(q)
    if raw is None:
        # Fixed dimension, intentionally outside every acceptance boundary.
        return np.full(len(SCALE), 1e6)
    return raw / SCALE


def audit_candidate(label, fit):
    raw, result, metrics = physical_residual(fit.x)
    normalized = normalized_residual(fit.x)
    initial, target = unpack(fit.x)
    checks = {
        "event_ring": bool(result.passed),
        "voltage_return": bool(raw is not None and np.max(np.abs(raw[:4])) <= V_RETURN_TOL),
        "current_return": bool(raw is not None and np.max(np.abs(raw[4:7])) <= I_RETURN_TOL),
        "equal_spacing": bool(raw is not None and np.max(np.abs(raw[7:10])) <= SPACING_TOL_NS),
        "peak_current": bool(raw is not None and np.max(np.abs(raw[10:13])) <= PEAK_TOL_A),
        "module_power": bool(raw is not None and abs(raw[13]) <= MODULE_CURRENT_TOL_A),
        "negative_fraction_range": bool(0.05 <= fit.x[7] <= 0.10),
    }
    return {
        "label": label,
        "optimizer_success_flag": bool(fit.success),
        "optimizer_message": fit.message,
        "cost": float(fit.cost),
        "optimality": float(fit.optimality),
        "nfev": int(fit.nfev),
        "negative_fraction": float(fit.x[7]),
        "negative_target_a": float(target),
        "initial_state": initial.tolist(),
        "metrics": metrics,
        "raw_residual": None if raw is None else raw.tolist(),
        "normalized_residual": normalized.tolist(),
        "max_acceptance_violation_factor": float(np.max(np.abs(normalized))),
        "checks": checks,
        "strict_pass": bool(all(checks.values())),
        "history": result.history,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    old = HERE / "numerical_runs/01_full_ring_calibration"
    periodic = json.loads((old / "event_fixed_point.json").read_text())
    equal = json.loads((old / "equal_spacing_fit.json").read_text())
    starts = [
        ("periodic_seed", np.r_[periodic["initial_state"][1:], 0.05]),
        ("equal_spacing_seed", np.r_[equal["initial_state"][1:], equal["negative_fraction"]]),
    ]
    lower = np.r_[[3.0, 2.5, -0.5, -0.5, -10.0, 10.0, 35.0], 0.05]
    upper = np.r_[[5.0, 5.5, 0.5, 0.5, 20.0, 50.0, 85.0], 0.10]
    reports = []
    for label, q0 in starts:
        print("START", label, "initial max violation", np.max(np.abs(normalized_residual(q0))), flush=True)
        fit = least_squares(
            normalized_residual, q0, bounds=(lower, upper),
            x_scale="jac", diff_step=2e-5,
            ftol=1e-11, xtol=1e-11, gtol=1e-11,
            max_nfev=100, verbose=1,
        )
        report = audit_candidate(label, fit)
        reports.append(report)
        print("END", label, "strict_pass", report["strict_pass"],
              "max_violation", report["max_acceptance_violation_factor"], flush=True)
    best = min(reports, key=lambda r: r["max_acceptance_violation_factor"])
    payload = {
        "problem": {
            "fixed_L_nH": 22.0,
            "fixed_Ton_ns": 500.0,
            "fixed_frequency_Hz": 0.5e6,
            "target_spacing_ns": SLOT * 1e9,
            "target_peak_a": IDEAL_PEAK_A,
            "target_module_current_a": TARGET_MODULE_CURRENT_A,
            "negative_fraction_bounds": [0.05, 0.10],
            "acceptance_tolerances": {
                "voltage_return_V": V_RETURN_TOL,
                "current_return_A": I_RETURN_TOL,
                "spacing_ns": SPACING_TOL_NS,
                "peak_A": PEAK_TOL_A,
                "module_current_A": MODULE_CURRENT_TOL_A,
            },
        },
        "runs": reports,
        "best_label": best["label"],
        "strict_feasible_found": bool(any(r["strict_pass"] for r in reports)),
        "claim_limit": "two-start local search; failure is not a proof of global infeasibility",
    }
    (OUT / "strict_joint_fit.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
