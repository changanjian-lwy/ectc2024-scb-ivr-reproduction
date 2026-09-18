"""Independent device-Coss and external-snubber parameter module."""

from __future__ import annotations

from dataclasses import dataclass

from .device_library import CapacitanceView, GaNDevice
from .evidence import Evidence


@dataclass(frozen=True)
class CommutationCapacitance:
    """Capacitance attached to one high-/low-side switching position.

    Device capacitance and added snubber capacitance deliberately remain
    separate.  A control threshold may consume the resulting commutation
    requirement, but it must not silently change either capacitance.
    """

    high_device_f: float
    low_device_f: float
    high_snubber_f: float = 0.0
    low_snubber_f: float = 0.0
    device_evidence: Evidence = Evidence.EXTERNAL_DEVICE_DATA
    snubber_evidence: Evidence = Evidence.EXPLORATORY_ASSUMPTION

    @property
    def high_total_f(self) -> float:
        return self.high_device_f + self.high_snubber_f

    @property
    def low_total_f(self) -> float:
        return self.low_device_f + self.low_snubber_f


def from_device_population(
    device: GaNDevice,
    *,
    high_parallel: int,
    low_parallel: int,
    view: CapacitanceView = CapacitanceView.TIME_EQUIVALENT,
    high_snubber_f: float = 0.0,
    low_snubber_f: float = 0.0,
) -> CommutationCapacitance:
    if high_snubber_f < 0 or low_snubber_f < 0:
        raise ValueError("snubber capacitance cannot be negative")
    return CommutationCapacitance(
        high_device_f=device.capacitance(view, high_parallel),
        low_device_f=device.capacitance(view, low_parallel),
        high_snubber_f=high_snubber_f,
        low_snubber_f=low_snubber_f,
    )
