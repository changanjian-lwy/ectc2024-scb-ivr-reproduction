"""Release one reported P25 parameter at a time in the strict joint audit."""
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
OUT = HERE / "numerical_runs/03_one_parameter_release"


def decode(q, branch):
    initial = np.r_[VIN, q[:7]]
    target = q[7] * IDEAL_PEAK_A
    if branch == "L":
        return initial, target, q[8] * 1e-9, 500e-9
    if branch == "TON":
        return initial, target, 22e-9, q[8] * 1e-9
    raise ValueError(branch)


def raw_residual(q, branch):
    initial, target, inductance, ton = decode(q, branch)
    result = event_ring(initial, target, lphase=inductance, ton=ton)
    if not result.passed:
        return None, result, None
    period_ns = result.history[-1]["next_high_on_ns"]
    spacings = np.array([h["phase_spacing_ns"] for h in result.history])
    peaks = np.array([h["peak_a"] for h in result.history])
    module_current = float(np.sum(result.charge_a_ns) / period_ns)
    raw = np.r_[result.final[1:] - initial[1:],
                spacings - SLOT * 1e9,
                peaks - IDEAL_PEAK_A,
                module_current - TARGET_MODULE_CURRENT_A]
    metrics = {
        "period_ns": period_ns,
        "spacings_ns": spacings.tolist(),
        "peaks_a": peaks.tolist(),
        "module_average_current_a": module_current,
        "state_return": (result.final - initial).tolist(),
    }
    return raw, result, metrics


def norm_residual(q, branch):
    raw, _, _ = raw_residual(q, branch)
    return np.full(len(SCALE), 1e6) if raw is None else raw / SCALE


def report(branch, fit):
    raw, result, metrics = raw_residual(fit.x, branch)
    norm = norm_residual(fit.x, branch)
    initial, target, inductance, ton = decode(fit.x, branch)
    checks = {
        "event_ring": bool(result.passed),
        "voltage_return": bool(raw is not None and np.max(abs(raw[:4])) <= V_RETURN_TOL),
        "current_return": bool(raw is not None and np.max(abs(raw[4:7])) <= I_RETURN_TOL),
        "equal_spacing": bool(raw is not None and np.max(abs(raw[7:10])) <= SPACING_TOL_NS),
        "peak_current": bool(raw is not None and np.max(abs(raw[10:13])) <= PEAK_TOL_A),
        "module_power": bool(raw is not None and abs(raw[13]) <= MODULE_CURRENT_TOL_A),
        "negative_fraction_range": bool(0.05 <= fit.x[7] <= 0.10),
    }
    return {
        "branch": branch,
        "optimizer_success_flag": bool(fit.success),
        "message": fit.message,
        "nfev": int(fit.nfev),
        "cost": float(fit.cost),
        "negative_fraction": float(fit.x[7]),
        "inductance_nH": inductance * 1e9,
        "ton_ns": ton * 1e9,
        "initial_state": initial.tolist(),
        "metrics": metrics,
        "raw_residual": None if raw is None else raw.tolist(),
        "normalized_residual": norm.tolist(),
        "max_acceptance_violation_factor": float(np.max(abs(norm))),
        "checks": checks,
        "strict_pass": bool(all(checks.values())),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fixed = json.loads((HERE / "numerical_runs/02_strict_joint_fit/strict_joint_fit.json").read_text())
    best = next(r for r in fixed["runs"] if r["label"] == fixed["best_label"])
    base = np.r_[best["initial_state"][1:], best["negative_fraction"]]
    configs = {
        "L": (np.r_[base, 22.0],
              np.r_[[3, 2.5, -.5, -.5, -10, 10, 35], .05, 15.0],
              np.r_[[5, 5.5, .5, .5, 20, 50, 85], .10, 45.0]),
        "TON": (np.r_[base, 500.0],
                np.r_[[3, 2.5, -.5, -.5, -10, 10, 35], .05, 250.0],
                np.r_[[5, 5.5, .5, .5, 20, 50, 85], .10, 600.0]),
    }
    reports = []
    for branch, (q0, lo, hi) in configs.items():
        print("START", branch, "max violation", np.max(abs(norm_residual(q0, branch))), flush=True)
        fit = least_squares(lambda q: norm_residual(q, branch), q0,
                            bounds=(lo, hi), x_scale="jac", diff_step=2e-5,
                            ftol=1e-11, xtol=1e-11, gtol=1e-11,
                            max_nfev=120, verbose=1)
        item = report(branch, fit)
        reports.append(item)
        print("END", branch, "strict_pass", item["strict_pass"],
              "L_nH", item["inductance_nH"], "Ton_ns", item["ton_ns"],
              "max_violation", item["max_acceptance_violation_factor"], flush=True)
    payload = {
        "fixed_other_boundaries": "P25 topology, 12/1 V, 0.5 MHz target spacing, 5%-10%, device abstraction",
        "runs": reports,
        "strict_feasible_found": any(r["strict_pass"] for r in reports),
        "claim_limit": "one local start per release branch; not a global proof",
    }
    (OUT / "one_parameter_release.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
