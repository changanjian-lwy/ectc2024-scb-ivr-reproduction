"""D31: D30-type bound retaining constant ON-node offsets of LocalFlow.

This certifies neither ideal-switch algebraic admissibility nor the numerical
error in the preceding trajectory. It studies the residual-bearing affine
continuation exactly as initialized; no state is projected or altered.
"""
from math import isfinite
from .p25_cycle_modes import cycle_mode, commutation_target
from .p25_commutation_closed_form import normalized_capacitance
from .p25_commutation_necessity import ChargeNecessity


def residual_charge_bound(state, parts, mode, ports, *, charge_margin_c):
    cn = normalized_capacitance(state.boundary, parts, mode)
    spec = cycle_mode(mode)
    if state.gates != spec.gates:
        raise ValueError("mode/gates mismatch")
    if not isfinite(charge_margin_c) or charge_margin_c < 0:
        raise ValueError("explicit finite nonnegative charge margin required")
    if ports.other_modules_current_a != 0:
        raise ValueError("single-module boundary: no other module current")
    if any(r != 0 for r in parts.winding_ohm):
        return ChargeNecessity("NOT_APPLICABLE", "requires exact zero winding resistance")
    q = spec.next_phase-1
    other = tuple(k for k in range(3) if k != q)
    ls, i = parts.inductance_h, state.current_a
    x = state.voltage_v[2:5]
    vo = state.voltage_v[5]
    v0 = state.switch_voltage(commutation_target(mode))
    if not (i[q] < 0 and all(i[k] > 0 for k in other) and v0 > 0
            and vo > max(0., *(x[k] for k in other))):
        return ChargeNecessity("NOT_APPLICABLE", "current/voltage entry signs or Vo>other ON nodes not satisfied")
    duration = min(ls[k]*i[k]/(vo-x[k]) for k in other)
    flux_upper = min(ls[k]*i[k]+max(x[k], 0.)*duration for k in other)
    lower_i = tuple(i[k]+(min(x[k], 0.)*duration-flux_upper)/ls[k] for k in range(3))
    output_margin = sum(lower_i)-ports.load_current_a
    if output_margin < 0:
        return ChargeNecessity("NOT_APPLICABLE", "monotone output voltage not established by this bound",
                               minimum_output_current_margin_a=output_margin)
    maximum = -lower_i[q]*duration
    required = cn*v0
    status = ("TARGET_BEFORE_OTHER_ZERO_IMPOSSIBLE" if required-maximum > charge_margin_c
              else "NOT_EXCLUDED_NOT_SUFFICIENT")
    return ChargeNecessity(status, "residual-bearing affine continuation only; not ideal-state/error certification",
                           required, maximum, duration, output_margin)
