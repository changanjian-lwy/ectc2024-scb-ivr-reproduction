"""D30: conservative charge/flux obstruction, not a ZVS success certificate.

Exact zero winding R and zero other-phase ON nodes only. Constant linear
capacitor network, constant Vin, dynamic Co, constant load, no active reverse
branch. A trajectory leaving this mode earlier cannot use this certificate
to continue through the guard. No measured samples establish the premises.
"""
from dataclasses import dataclass
from math import isfinite
from .p25_cycle_modes import cycle_mode, commutation_target
from .p25_commutation_closed_form import normalized_capacitance


@dataclass(frozen=True)
class ChargeNecessity:
    status: str
    reason: str
    required_charge_c: float | None = None
    maximum_charge_c: float | None = None
    maximum_duration_s: float | None = None
    minimum_output_current_margin_a: float | None = None


def commutation_necessity(state, parts, mode, ports, *, charge_margin_c):
    """Necessary condition for reaching target Vds=0 before another current zero.

The explicit charge margin is a decision guard band, NOT interval arithmetic.
Failure to meet the sufficient monotone-Vo premise means NOT_APPLICABLE,
not an impossible orbit. Passing the charge inequality never proves ZVS.
"""
    cn = normalized_capacitance(state.boundary, parts, mode)
    spec = cycle_mode(mode)
    if state.gates != spec.gates:
        raise ValueError("mode/gates mismatch")
    if not isfinite(charge_margin_c) or charge_margin_c < 0:
        raise ValueError("explicit finite nonnegative charge margin required")
    if ports.other_modules_current_a != 0:
        raise ValueError("single-module boundary: no other module current")
    q = spec.next_phase - 1
    other = tuple(k for k in range(3) if k != q)
    if any(r != 0 for r in parts.winding_ohm):
        return ChargeNecessity("NOT_APPLICABLE", "requires exact zero winding resistance")
    if any(state.voltage_v[2+k] != 0 for k in other):
        return ChargeNecessity("NOT_APPLICABLE", "nonzero ON-node residual retained, not rounded away")
    i = state.current_a
    v0 = state.switch_voltage(commutation_target(mode))
    vo = state.voltage_v[5]
    if not (i[q] < 0 and all(i[k] > 0 for k in other)
            and vo > 0 and v0 > 0 and state.voltage_v[2+q] >= 0):
        return ChargeNecessity("NOT_APPLICABLE", "requires negative target-phase current, positive other currents/Vo/Vds, xq>=0")
    ls = parts.inductance_h
    flux = min(ls[k]*i[k] for k in other)
    output_margin = sum(i) - flux*sum(1/l for l in ls) - ports.load_current_a
    if output_margin < 0:
        return ChargeNecessity("NOT_APPLICABLE", "monotone output voltage not established by this bound",
                               minimum_output_current_margin_a=output_margin)
    duration = flux/vo
    maximum = (-i[q]+flux/ls[q])*duration
    required = cn*v0
    status = ("TARGET_BEFORE_OTHER_ZERO_IMPOSSIBLE" if required-maximum > charge_margin_c
              else "NOT_EXCLUDED_NOT_SUFFICIENT")
    return ChargeNecessity(status, "conditional fixed-mode analytic bound; floating-point evaluation",
                           required, maximum, duration, output_margin)
