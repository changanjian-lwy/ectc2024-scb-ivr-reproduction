"""A58 - two fixed dead times (rising / falling edge) on A56's regulated boundary.

The A50/A51 scheduler has one scalar ``dead_time_s`` read by
``commanded_pwm_mode`` (imported by name into several modules),
``next_pwm_edge_s``, ``period_intervals`` and ``period_start_s``. Those files
are not edited. This module provides asymmetric versions that act only on
``AsymDeadTimeBoundary`` and pass every other boundary to the original function
unchanged. ``asym_schedule_context`` installs them in EVERY loaded module
namespace that holds one of the original function objects (found by identity,
not by a hand-kept list) and restores them in ``finally``. Single-thread-only,
like A55's ``asymmetric_ron_context``; A58 processes are standalone.

Window placement is A50's: each window is centered on its commanded edge,

    local in [0, dr/2)                 DEADTIME (turn-on window, rising edge)
    local in [dr/2, Ton - df/2)        HIGH
    local in [Ton - df/2, Ton + df/2)  DEADTIME (turn-off window, falling edge)
    local in [Ton + df/2, T - dr/2)    LOW
    local in [T - dr/2, T)             DEADTIME

so ``dr == df`` reproduces A56's schedule with the same floating-point
operations. The inherited scalar ``dead_time_s`` is forced to ``(dr + df)/2``:
the inherited checks (``Ton + d < T/4``, ``d < min(Ton, T - Ton)``) are then
exactly the asymmetric non-overlap conditions. No solve path may read it
otherwise (``test_a58_schedule.py`` proves this).
"""
from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from math import floor
from pathlib import Path
from typing import Iterator

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
A56_DIR = TRACK / "A56_equal_power_regulated_loss_comparison"
A57_DIR = TRACK / "A57_datasheet_reverse_conduction_pricing"
for _path in (A56_DIR, HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import regulated_boundary as R  # noqa: E402  (A56, read-only)

D, H, M = R.D, R.H, R.M

ORIGINALS = {
    "commanded_pwm_mode": D.commanded_pwm_mode,
    "next_pwm_edge_s": H.next_pwm_edge_s,
    "period_intervals": M.period_intervals,
    "period_start_s": M.period_start_s,
}


@dataclass(frozen=True)
class AsymDeadTimeBoundary(R.RegulatedBoundary):
    """A56 regulated boundary with separate rising/falling-edge dead times."""

    #: low-side off -> high-side on window (the high-side ZVS edge)
    dead_time_rise_s: float = float("nan")
    #: high-side off -> low-side on window (the low-side edge)
    dead_time_fall_s: float = float("nan")

    def __post_init__(self) -> None:
        for name in ("dead_time_rise_s", "dead_time_fall_s"):
            value = getattr(self, name)
            if not (isinstance(value, float) and math.isfinite(value) and value > 0):
                raise ValueError(f"{name} must be an explicit positive finite float")
        if self.dead_time_s != 0.5 * (self.dead_time_rise_s + self.dead_time_fall_s):
            raise ValueError("dead_time_s must equal the mean of the two dead times")
        super().__post_init__()


def build_asym_boundary(*, phase_inductance_h: float, dead_time_rise_s: float,
                        dead_time_fall_s: float, ton_cmd_s: float) -> AsymDeadTimeBoundary:
    """A56's ``build_regulated_boundary`` field-for-field, plus the two dead times."""
    rise, fall = float(dead_time_rise_s), float(dead_time_fall_s)
    return AsymDeadTimeBoundary(
        phase_inductance_h=phase_inductance_h,
        flying_capacitances_f=(R.B.CFLY_F, R.B.CFLY_F, R.B.CFLY_F),
        module_power_w=250.0,
        dead_time_s=0.5 * (rise + fall),
        switch_capacitance=R.B.SWITCH_CAPACITANCE,
        evidence=R.B.Evidence.CROSS_PAPER_EXTENSION,
        ton_cmd_s=float(ton_cmd_s),
        dead_time_rise_s=rise,
        dead_time_fall_s=fall,
    )


def commanded_pwm_mode(time_s, boundary, *, precharge_diode_on=(False, False, False)):
    if not isinstance(boundary, AsymDeadTimeBoundary):
        return ORIGINALS["commanded_pwm_mode"](time_s, boundary, precharge_diode_on=precharge_diode_on)
    period = boundary.period_s
    half_rise = 0.5 * boundary.dead_time_rise_s
    half_fall = 0.5 * boundary.dead_time_fall_s
    on_time = boundary.on_time_s
    high = []
    low = []
    for phase in range(boundary.phases):
        shifted = time_s - phase * period / boundary.phases
        local = shifted - floor(shifted / period) * period
        high.append(half_rise <= local < on_time - half_fall)
        low.append(on_time + half_fall <= local < period - half_rise)
    return D.Mode(tuple(high), tuple(low), precharge_diode_on)


def next_pwm_edge_s(time_s, boundary):
    if not isinstance(boundary, AsymDeadTimeBoundary):
        return ORIGINALS["next_pwm_edge_s"](time_s, boundary)
    period = boundary.period_s
    half_rise = 0.5 * boundary.dead_time_rise_s
    half_fall = 0.5 * boundary.dead_time_fall_s
    candidates = []
    epsilon = max(1e-18, 1e-12 * period)
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        cycle = floor((time_s - start0) / period)
        for index in (cycle, cycle + 1, cycle + 2):
            start = start0 + index * period
            end = start + boundary.on_time_s
            for edge in (start - half_rise, start + half_rise, end - half_fall, end + half_fall):
                if edge > time_s + epsilon:
                    candidates.append(edge)
    if not candidates:
        raise RuntimeError("failed to locate the next PWM edge")
    return min(candidates)


def period_start_s(boundary):
    if not isinstance(boundary, AsymDeadTimeBoundary):
        return ORIGINALS["period_start_s"](boundary)
    return M.BASE_PERIOD_INDEX * boundary.period_s + 0.5 * boundary.dead_time_rise_s


def period_intervals(boundary, t0):
    if not isinstance(boundary, AsymDeadTimeBoundary):
        return ORIGINALS["period_intervals"](boundary, t0)
    period = boundary.period_s
    halves = {"turn_on": 0.5 * boundary.dead_time_rise_s,
              "turn_off": 0.5 * boundary.dead_time_fall_s}
    windows = []
    for phase in range(boundary.phases):
        nominal_on = M.BASE_PERIOD_INDEX * period + phase * period / boundary.phases
        nominal_off = nominal_on + boundary.on_time_s
        for center, kind in ((nominal_on, "turn_on"), (nominal_off, "turn_off")):
            half = halves[kind]
            shifted = center
            while shifted - half < t0 - 1e-18:
                shifted += period
            while shifted - half >= t0 + period - 1e-18:
                shifted -= period
            windows.append((kind, shifted, phase, half))
    windows.sort(key=lambda item: item[1] - item[3])  # by window start

    intervals = []
    cursor = t0
    for kind, center, phase, half in windows:
        start = center - half
        end = center + half
        if start < cursor - 1e-18:
            raise RuntimeError("dead-time windows overlap; reduce the dead times")
        if start > cursor + 1e-18:
            intervals.append(M.Interval("normal", cursor, start, None))
        intervals.append(M.Interval(kind, start, min(end, t0 + period), phase))
        cursor = min(end, t0 + period)
    if cursor < t0 + period - 1e-18:
        intervals.append(M.Interval("normal", cursor, t0 + period, None))
    return tuple(intervals)


REPLACEMENTS = {
    "commanded_pwm_mode": commanded_pwm_mode,
    "next_pwm_edge_s": next_pwm_edge_s,
    "period_intervals": period_intervals,
    "period_start_s": period_start_s,
}


def holders() -> list[tuple[object, str]]:
    """Every (module, name) currently bound to one of the original functions."""
    found = []
    for module in list(sys.modules.values()):
        for name, original in ORIGINALS.items():
            if getattr(module, name, None) is original:
                found.append((module, name))
    return found


@contextmanager
def asym_schedule_context() -> Iterator[list[tuple[object, str]]]:
    swapped = holders()
    for module, name in swapped:
        setattr(module, name, REPLACEMENTS[name])
    try:
        yield swapped
    finally:
        for module, name in swapped:
            setattr(module, name, ORIGINALS[name])


__all__ = ["AsymDeadTimeBoundary", "build_asym_boundary", "asym_schedule_context", "holders",
           "ORIGINALS", "REPLACEMENTS", "R", "D", "H", "M"]
