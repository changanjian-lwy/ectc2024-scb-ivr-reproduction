"""D32: independent energy accounting; explicit numerical quadrature errors.

Finite ON-voltage residual work is retained separately, not called MOS loss.
No gate/state changes, failed trial intervals, or periodicity conclusions.
"""
from dataclasses import dataclass
from math import isfinite
import numpy as np
from scipy.integrate import quad_vec
from .p25_local_flow import LocalFlow
from .p25_nodal_contract import incidence, instantaneous_rates
from .p25_trace_balance import trace_balance


@dataclass(frozen=True)
class SegmentEnergy:
    mode: str
    input_j: float
    load_j: float
    winding_j: float
    on_residual_work_j: float
    stored_change_j: float
    balance_residual_j: float
    quadrature_error_estimate_j: float


def stored_energy(state, parts):
    vc = incidence().T @ np.r_[state.vin_v, state.voltage_v]
    return float(.5*(parts.capacitances() @ (vc*vc)
                     + np.array(parts.inductance_h) @ np.square(state.current_a)))


def segment_energy(flow, end, *, voltage_tolerance_v, quadrature_abs_j, quadrature_rel):
    """End must be the accepted endpoint; discrepancy is exposed, not reset.

Error estimate is from adaptive quadrature, NOT a rigorous enclosure or an
error bound on matrix exponentials, event roots, or the preceding trajectory.
"""
    if not all(isfinite(x) and x>0 for x in (quadrature_abs_j, quadrature_rel)):
        raise ValueError("explicit positive finite quadrature tolerances required")
    if end.time_s <= flow.start.time_s or end.vin_v != flow.start.vin_v:
        raise ValueError("forward constant-Vin segment required")
    if flow.start.boundary.nM != 1 or flow.ports.other_modules_current_a != 0:
        raise ValueError("native single-module energy ledger only")

    def power(t):
        s = flow.at(t)
        r = instantaneous_rates(s.boundary, flow.parts, flow.mode,
            voltage_v=s.voltage_v, current_a=s.current_a, vin_v=s.vin_v, dvin_v_s=0.,
            load_current_a=flow.ports.load_current_a, other_modules_current_a=0.,
            constraint_tolerance_v=voltage_tolerance_v,
            reverse_path_regime="off_reverse_channels_excluded_until_admission")
        vds = (incidence().T @ np.r_[s.vin_v, s.voltage_v])[:6]
        return np.array((s.vin_v*r.input_current_a,
            s.voltage_v[5]*flow.ports.load_current_a,
            np.array(flow.parts.winding_ohm) @ np.square(s.current_a),
            vds @ r.channel_current_a))

    z, error, info = quad_vec(power, flow.start.time_s, end.time_s,
                            epsabs=quadrature_abs_j, epsrel=quadrature_rel,
                            norm="max", full_output=True)
    if not info.success or not np.all(np.isfinite(z)):
        raise ArithmeticError("energy quadrature did not converge")
    change = stored_energy(end, flow.parts)-stored_energy(flow.start, flow.parts)
    residual = change-(z[0]-z[1]-z[2]-z[3])
    return SegmentEnergy(flow.mode, *map(float,z), change, float(residual), float(error))


def accepted_energy_ledger(attempt, parts, ports, *, voltage_tolerance_v,
                           quadrature_abs_j, quadrature_rel):
    """Validate connected accepted-prefix coverage using D28; exclude failed M5 etc."""
    ledger = trace_balance(attempt, parts, ports, voltage_tolerance_v=voltage_tolerance_v)
    rows = []
    for step in attempt.steps[:len(ledger.segments)]:
        flow = LocalFlow(step.before.last_event, parts, step.mode, ports,
                         voltage_tolerance_v=voltage_tolerance_v)
        rows.append(segment_energy(flow, step.outcome.memory.last_event,
            voltage_tolerance_v=voltage_tolerance_v, quadrature_abs_j=quadrature_abs_j,
            quadrature_rel=quadrature_rel))
    return ledger.coverage, tuple(rows)
