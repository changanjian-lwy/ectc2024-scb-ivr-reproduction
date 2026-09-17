"""Replaceable predictive current-limited pulse policy.

The policy changes no power-stage definition.  Its first use is restricted to
P24's explicit phase-1 QH1+QS2 state.  Rotation to other phases requires a
separately labelled sequence branch.
"""

from __future__ import annotations

from dataclasses import dataclass

from scb_ivr.evidence import Evidence


@dataclass(frozen=True)
class PredictivePulseRequest:
    inductance_h: float
    available_segment_v: float
    output_v: float
    allowed_delta_current_a: float
    maximum_pulse_s: float
    n_p: int


@dataclass(frozen=True)
class PredictivePulse:
    enabled: bool
    pulse_width_s: float
    predicted_inductor_voltage_v: float
    predicted_delta_current_a: float
    evidence: Evidence = Evidence.EXPLORATORY_ASSUMPTION


def calculate_predictive_pulse(request: PredictivePulseRequest) -> PredictivePulse:
    if request.n_p < 1:
        raise ValueError("n_p must be explicit and positive")
    if request.inductance_h <= 0 or request.maximum_pulse_s <= 0:
        raise ValueError("inductance and maximum pulse must be positive")
    if request.allowed_delta_current_a <= 0:
        raise ValueError("allowed current increment must be positive")

    v_l = request.available_segment_v - request.output_v
    if v_l <= 0:
        return PredictivePulse(False, 0.0, v_l, 0.0)

    pulse = min(
        request.maximum_pulse_s,
        request.inductance_h * request.allowed_delta_current_a / v_l,
    )
    return PredictivePulse(
        enabled=True,
        pulse_width_s=pulse,
        predicted_inductor_voltage_v=v_l,
        predicted_delta_current_a=v_l * pulse / request.inductance_h,
    )

