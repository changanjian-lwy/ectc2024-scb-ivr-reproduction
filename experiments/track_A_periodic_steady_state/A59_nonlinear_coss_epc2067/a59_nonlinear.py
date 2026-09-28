"""A59 - charge-based backward Euler with EPC2067's nonlinear Coss(V).

A50's ``_candidate_step`` solves ``(E/h + A) z1 = E z0/h + r`` with a constant
switch capacitance inside ``E``. For ``NonlinearCossBoundary`` only, this
module replaces it by a charge-conserving step: for every switch branch b
(incidence row B_b, n_b parallel devices, linear C_lin_b already in E)

    F(z1) = (E/h + A) z1 - E z0/h - r
            + sum_b B_b^T ( n_b [q(v_b1) - q(v_b0)] - C_lin_b [v_b1 - v_b0] ) / h = 0

solved by Newton from the linear predictor. Any other boundary goes to the
original function unchanged. ``nonlinear_coss_context`` swaps every loaded
namespace that holds the original ``_candidate_step`` (found by identity),
as A58 does for the schedule; single-thread-only.

Capacitor models are referenced by a string id (``coss_model_id``) so that
``dataclasses.asdict`` comparisons in A55/A56 metering still work.
"""
from __future__ import annotations

import csv
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

HERE = Path(__file__).resolve().parent
A58_DIR = HERE.parent / "A58_asymmetric_fixed_deadtime_tuning"
if str(A58_DIR) not in sys.path:
    sys.path.insert(0, str(A58_DIR))

import a58_schedule as S  # noqa: E402  (A58, read-only)

R, D, H, M = S.R, S.D, S.H, S.M
CURVE_CSV = HERE / "epc2067_coss_qoss_eoss_digitized.csv"
CO_TR_F = 1860e-12  # EPC2067 printed typ, 0-20 V (the linear model A50-A58 use)
V_MAX = 40.0
ORIGINAL_STEP = H._candidate_step
NEWTON_STATS = {"steps": 0, "iterations": 0, "max_iterations": 0}


class Fig5aCoss:
    """Per-device C(V) = PCHIP of Fig. 5a; q = exact antiderivative; C even, q odd."""

    def __init__(self, path=CURVE_CSV):
        pts = {}
        with open(path) as f:
            for row in csv.DictReader(f):
                if row["curve"] == "coss":
                    pts[round(float(row["vds_v"]), 4)] = float(row["value"]) * 1e-12
        v = np.array(sorted(pts))
        c = np.array([pts[x] for x in v])
        keep = v > 0
        v = np.concatenate([[0.0], v[keep]])
        c = np.concatenate([[c[keep][0]], c[keep]])
        # thin to ~0.1 V spacing: dense Bezier samples carry sub-pixel jitter
        grid = np.arange(0.0, V_MAX + 1e-9, 0.1)
        self.c_interp = PchipInterpolator(grid, np.interp(grid, v, c), extrapolate=False)
        self.q_interp = self.c_interp.antiderivative()
        self.c_end = float(self.c_interp(V_MAX))
        self.q_end = float(self.q_interp(V_MAX))

    def c(self, v):
        a = np.abs(np.asarray(v, float))
        inside = np.minimum(a, V_MAX)
        out = self.c_interp(inside)
        return np.where(a > V_MAX, self.c_end, out)

    def q(self, v):
        v = np.asarray(v, float)
        a = np.abs(v)
        out = np.where(a > V_MAX, self.q_end + self.c_end * (a - V_MAX), self.q_interp(np.minimum(a, V_MAX)))
        return np.sign(v) * out


class LinearCoss:
    """q = C0 * V: must reproduce the linear A50 step (test only)."""

    def __init__(self, c0=CO_TR_F):
        self.c0 = c0

    def c(self, v):
        return np.full(np.shape(v), self.c0)

    def q(self, v):
        return self.c0 * np.asarray(v, float)


MODELS = {"fig5a_pchip": Fig5aCoss(), "linear_cotr": LinearCoss()}


@dataclass(frozen=True)
class NonlinearCossBoundary(S.AsymDeadTimeBoundary):
    coss_model_id: str = "fig5a_pchip"

    def __post_init__(self) -> None:
        if self.coss_model_id not in MODELS:
            raise ValueError(f"unknown Coss model {self.coss_model_id!r}")
        if self.switch_capacitance is None:
            raise ValueError("the linear base capacitance must be present")
        super().__post_init__()


def build_nl_boundary(*, phase_inductance_h, dead_time_rise_s, dead_time_fall_s, ton_cmd_s,
                      coss_model_id="fig5a_pchip") -> NonlinearCossBoundary:
    base = S.build_asym_boundary(phase_inductance_h=phase_inductance_h, dead_time_rise_s=dead_time_rise_s,
                                 dead_time_fall_s=dead_time_fall_s, ton_cmd_s=ton_cmd_s)
    fields = {k: getattr(base, k) for k in base.__dataclass_fields__}
    return NonlinearCossBoundary(**fields, coss_model_id=coss_model_id)


_BRANCH_CACHE: dict = {}


def branch_matrix(boundary, node_names, size):
    key = (node_names, size, boundary.switch_capacitance)
    if key not in _BRANCH_CACHE:
        index = {name: i for i, name in enumerate(node_names)}
        rows, n, c_lin = [], [], []
        pop = R.B  # A54 boundary module: NHS/NLS population
        for pairs, count, total in ((D.HIGH_SIDE_BRANCHES, pop.NHS, boundary.switch_capacitance.high_total_f),
                                    (D.LOW_SIDE_BRANCHES, pop.NLS, boundary.switch_capacitance.low_total_f)):
            for first, second in pairs:
                row = np.zeros(size)
                row[index[first]] += 1.0
                if second is not None:
                    row[index[second]] -= 1.0
                rows.append(row)
                n.append(count)
                c_lin.append(total)
        _BRANCH_CACHE[key] = (np.array(rows), np.array(n, float), np.array(c_lin))
    return _BRANCH_CACHE[key]


def candidate_step(previous_state, time_s, next_time_s, boundary, high_side_on, low_side_on, diode_state):
    if not isinstance(boundary, NonlinearCossBoundary):
        return ORIGINAL_STEP(previous_state, time_s, next_time_s, boundary, high_side_on,
                             low_side_on, diode_state)
    model = MODELS[boundary.coss_model_id]
    mode = D.Mode(high_side_on, low_side_on, diode_state)
    system = H.assemble_descriptor(boundary, mode, next_time_s)
    dt = next_time_s - time_s
    matrix = system.e / dt + system.a
    vector = system.e @ previous_state / dt + system.rhs
    bmat, n, c_lin = branch_matrix(boundary, tuple(system.node_names), len(previous_state))
    v0 = bmat @ previous_state
    q0 = n * model.q(v0)
    try:
        z = np.linalg.solve(matrix, vector)
        for iteration in range(1, 31):
            v1 = bmat @ z
            corr = (n * model.q(v1) - q0) - c_lin * (v1 - v0)
            residual = matrix @ z - vector + bmat.T @ corr / dt
            jac = matrix + (bmat.T * ((n * model.c(v1) - c_lin) / dt)) @ bmat
            dz = np.linalg.solve(jac, residual)
            z = z - dz
            if np.max(np.abs(dz)) <= 1e-12 * max(1.0, np.max(np.abs(z))):
                break
        else:
            raise RuntimeError("nonlinear Coss Newton did not converge in 30 iterations")
    except np.linalg.LinAlgError as error:
        raise H.ComplementarityFailure("singular nonlinear descriptor step") from error
    NEWTON_STATS["steps"] += 1
    NEWTON_STATS["iterations"] += iteration
    NEWTON_STATS["max_iterations"] = max(NEWTON_STATS["max_iterations"], iteration)
    v1 = bmat @ z
    residual = matrix @ z - vector + bmat.T @ ((n * model.q(v1) - q0) - c_lin * (v1 - v0)) / dt
    residual_inf = float(np.max(np.abs(residual)))
    scale = float(np.linalg.norm(matrix, ord=np.inf) * np.linalg.norm(z, ord=np.inf)
                  + np.linalg.norm(vector, ord=np.inf))
    return H.HybridStep(time_s=next_time_s, state=z, mode=mode,
                        diode_observation=H.diode_observation(z, boundary, mode),
                        descriptor_residual_inf=residual_inf,
                        descriptor_relative_backward_error=residual_inf / max(scale, np.finfo(float).tiny))


def holders():
    return [(m, "_candidate_step") for m in list(sys.modules.values())
            if getattr(m, "_candidate_step", None) is ORIGINAL_STEP]


@contextmanager
def nonlinear_coss_context():
    swapped = holders()
    for module, name in swapped:
        setattr(module, name, candidate_step)
    try:
        yield swapped
    finally:
        for module, name in swapped:
            setattr(module, name, ORIGINAL_STEP)


__all__ = ["Fig5aCoss", "LinearCoss", "MODELS", "NonlinearCossBoundary", "build_nl_boundary",
           "candidate_step", "nonlinear_coss_context", "holders", "NEWTON_STATS", "S", "R", "D", "H", "M"]
