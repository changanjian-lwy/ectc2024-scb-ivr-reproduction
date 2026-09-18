"""Paper-labelled analytical feasibility relations for Track A.

No SPICE model is called here.  The functions separate the P24 lossless
current-ramp check from the P25 device-augmented ramp and Mode-5 commutation
relations.  Capacitance participation remains an explicit caller choice.
"""

from __future__ import annotations

from math import exp, sqrt


def ideal_current_endpoint_a(
    admission_current_a: float,
    drive_voltage_v: float,
    inductance_h: float,
    on_time_s: float,
) -> float:
    """P24 lossless ramp: I(Ton) = Iadmit + Vdrive*Ton/L."""
    if inductance_h <= 0 or on_time_s < 0:
        raise ValueError("inductance must be positive and on-time non-negative")
    return admission_current_a + drive_voltage_v * on_time_s / inductance_h


def rl_current_endpoint_a(
    admission_current_a: float,
    drive_voltage_v: float,
    inductance_h: float,
    path_resistance_ohm: float,
    on_time_s: float,
) -> float:
    """Constant-drive RL endpoint for the P25 device-augmented layer."""
    if inductance_h <= 0 or path_resistance_ohm < 0 or on_time_s < 0:
        raise ValueError("invalid L, R, or on-time")
    if path_resistance_ohm == 0:
        return ideal_current_endpoint_a(
            admission_current_a, drive_voltage_v, inductance_h, on_time_s
        )
    steady_a = drive_voltage_v / path_resistance_ohm
    alpha = exp(-path_resistance_ohm * on_time_s / inductance_h)
    return steady_a + (admission_current_a - steady_a) * alpha


def p25_mode5_commutation_time_s(
    participating_capacitance_f: float,
    voltage_step_v: float,
    negative_current_a: float,
) -> float:
    """P25 Eq. (13) rearranged: tcomm = 2*C*DeltaV/|Ineg|.

    The factor two is retained exactly from the coefficient printed in P25
    Eq. (13).  The paper does not publish a separate fixed Mode-5 deadline.
    """
    if participating_capacitance_f < 0 or voltage_step_v < 0:
        raise ValueError("capacitance and voltage step must be non-negative")
    if negative_current_a == 0:
        raise ValueError("negative-current magnitude must be nonzero")
    return 2 * participating_capacitance_f * voltage_step_v / abs(negative_current_a)


def maximum_capacitance_for_time_f(
    negative_current_a: float,
    voltage_step_v: float,
    available_time_s: float,
) -> float:
    """P25 Eq. (13) ceiling after an external time budget is supplied."""
    if voltage_step_v <= 0 or available_time_s < 0:
        raise ValueError("voltage step must be positive and time non-negative")
    return abs(negative_current_a) * available_time_s / (2 * voltage_step_v)


def isolated_lc_capacitance_ceiling_f(
    inductance_h: float,
    negative_current_a: float,
    voltage_step_v: float,
) -> float:
    """General-physics isolated-LC energy ceiling, not a P25 equation."""
    if inductance_h <= 0 or voltage_step_v <= 0:
        raise ValueError("inductance and voltage step must be positive")
    return inductance_h * abs(negative_current_a) ** 2 / voltage_step_v**2


def isolated_lc_minimum_current_a(
    inductance_h: float,
    participating_capacitance_f: float,
    voltage_step_v: float,
) -> float:
    """General-physics envelope 0.5*L*I^2 >= 0.5*C*dV^2.

    This applies only if L and the selected C form the isolated commutating
    energy pair.  It must not be labelled as P25 Eq. (13).
    """
    if inductance_h <= 0 or participating_capacitance_f < 0:
        raise ValueError("inductance must be positive and capacitance non-negative")
    if voltage_step_v < 0:
        raise ValueError("invalid voltage boundary")
    return voltage_step_v * sqrt(participating_capacitance_f / inductance_h)
