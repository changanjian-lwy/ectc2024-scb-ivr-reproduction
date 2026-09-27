"""A56 - expose the commanded high-side window width ``Ton_cmd`` (BOUNDARY.md S1).

``ZeroStartBoundary.on_time_s`` (A50 ``solver_copy``) is a derived property
``duty * period_s`` with ``duty = phases * vout_target_v / vin_target_v``. A56's
single declared control degree of freedom is the *command* on-interval of
``symbolic_derivations/D01_TIMING_DEFINITION_CONTRACT.md`` (command_on ->
command_off), identical for all four phases. This module subclasses A55's
``AsymmetricRonBoundary`` (imported read-only) and overrides ``on_time_s`` ONLY:

* ``vout_target_v`` and ``module_power_w`` are untouched, so
  ``load_resistance_ohm = 1**2 / 250 = 0.004 Ohm`` exactly;
* ``duty`` is untouched (it is read by no solve path -- see the test file);
* phase offsets stay ``T/4``; dead-time windows stay centred on the command
  edges ``p*T/4`` and ``p*T/4 + Ton_cmd`` exactly as A50/A51/A55 schedule them,
  because every scheduler reads ``boundary.on_time_s``.

Documented local override (the ONLY one): A55's ``audit_accepted_orbit.
metered_orbit(point)`` does not accept a boundary. It rebuilds one from
``point['phase_inductance_h']`` and ``point['dead_time_s']`` via
``build_epc2067_boundary``, which would silently re-derive ``on_time_s`` from
``duty`` and meter a regulated ``z*`` on the NOMINAL 16.6667 ns schedule.
``regulated_metering(boundary)`` therefore rebinds the name
``build_epc2067_boundary`` *inside the audit module's namespace only*, for the
duration of one call, to return exactly the regulated boundary (after checking
that L and dead time agree). A55's file is not edited; its metering code runs
unchanged. The rebinding is restored in ``finally`` and is single-thread-only,
like A55's own ``asymmetric_ron_context``.
"""
from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
ROOT = TRACK.parent.parent
A55_DIR = TRACK / "A55_joint_lphase_deadtime_total_loss_optimization"
A53_DIR = TRACK / "A53_lphase_zvs_load_tradeoff"
for _path in (ROOT / "src", A53_DIR, A55_DIR, HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import a53_solve as S  # noqa: E402  (A53, read-only)
import audit_accepted_orbit as A  # noqa: E402  (A55, read-only)
from asymmetric_ron_dynamics import (  # noqa: E402  (A55, read-only)
    AsymmetricRonBoundary,
    B,
    D,
    H,
    M,
    asymmetric_ron_context,
)

#: P24 nominal D*T = (4 * 1 V / 48 V) * 200 ns = 16.6667 ns, taken bitwise from
#: the inherited property so a Ton_cmd equal to it replays A55 exactly.
NOMINAL_TON_S = D.ZeroStartBoundary().on_time_s
#: Rated-point load, never retuned (BOUNDARY.md S1).
RATED_LOAD_OHM = 0.004
TARGET_POWER_W = 250.0
POWER_TOLERANCE = 1e-3
CURRENT_SCREEN_A = 250.0

#: A55's 3x3 local grid, unchanged (BOUNDARY.md S2).
L_ROWS = (
    ("new_passing", 6.215240418389056e-10),
    ("old_critical", 6.274059728342265e-10),
    ("nominal", 1.4666667e-9),
)
DT_COLUMNS = ((1.0, 2.15e-9), (0.5, 1.075e-9), (2.0, 4.3e-9))


@dataclass(frozen=True)
class RegulatedBoundary(AsymmetricRonBoundary):
    """A55 boundary whose command on-interval is an explicit field."""

    #: Command on-interval width (D01 "command_on -> command_off"). NaN means
    #: "not supplied" and is rejected, so no caller can silently inherit duty.
    ton_cmd_s: float = float("nan")

    def __post_init__(self) -> None:
        if not (isinstance(self.ton_cmd_s, float) and math.isfinite(self.ton_cmd_s)):
            raise ValueError("ton_cmd_s must be an explicit finite float")
        if self.ton_cmd_s <= 0:
            raise ValueError("ton_cmd_s must be positive")
        # The parent's checks (dead time shorter than both commanded conduction
        # intervals) run against the overridden on_time_s below.
        super().__post_init__()
        # Turn-off window of phase p must end before phase p+1's turn-on
        # window opens: Ton + d/2 < T/4 - d/2. period_intervals() would raise
        # anyway; fail earlier with a clearer message.
        if self.ton_cmd_s + self.dead_time_s >= self.period_s / self.phases:
            raise ValueError("Ton_cmd + dead time must stay below T/4 (window overlap)")

    @property
    def on_time_s(self) -> float:  # type: ignore[override]
        return self.ton_cmd_s


def build_regulated_boundary(
    *, phase_inductance_h: float, dead_time_s: float, ton_cmd_s: float
) -> RegulatedBoundary:
    """A55's ``build_epc2067_boundary`` field-for-field, plus ``ton_cmd_s``."""

    return RegulatedBoundary(
        phase_inductance_h=phase_inductance_h,
        flying_capacitances_f=(B.CFLY_F, B.CFLY_F, B.CFLY_F),
        module_power_w=250.0,
        dead_time_s=dead_time_s,
        switch_capacitance=B.SWITCH_CAPACITANCE,
        evidence=B.Evidence.CROSS_PAPER_EXTENSION,
        ton_cmd_s=float(ton_cmd_s),
    )


def boundary_record(boundary: RegulatedBoundary) -> dict:
    record = asdict(boundary)
    record["on_time_s_effective_property"] = boundary.on_time_s
    record["load_resistance_ohm"] = boundary.load_resistance_ohm
    record["duty_property_unused"] = boundary.duty
    return record


@contextmanager
def regulated_metering(boundary: RegulatedBoundary) -> Iterator[None]:
    """Make A55's unchanged ``metered_orbit`` meter exactly ``boundary``."""

    original = A.build_epc2067_boundary

    def _exact(*, phase_inductance_h, dead_time_s, **_ignored):
        if phase_inductance_h != boundary.phase_inductance_h:
            raise RuntimeError("metering L differs from the regulated boundary")
        if dead_time_s != boundary.dead_time_s:
            raise RuntimeError("metering dead time differs from the regulated boundary")
        return boundary

    A.build_epc2067_boundary = _exact
    try:
        yield
    finally:
        A.build_epc2067_boundary = original


def meter_regulated(boundary: RegulatedBoundary, z_star, *, coarse_step_s: float,
                    sub_step_s: float, label: str | None = None) -> dict:
    """A55 ``metered_orbit`` on the regulated boundary (scoped override above)."""

    point = dict(label=label, phase_inductance_h=boundary.phase_inductance_h,
                 dead_time_s=boundary.dead_time_s, z_star=list(map(float, z_star)),
                 coarse_step_s=coarse_step_s, sub_step_s=sub_step_s)
    with regulated_metering(boundary):
        metrics = A.metered_orbit(point)
    if metrics["full_boundary"].get("ton_cmd_s") != boundary.ton_cmd_s:
        raise RuntimeError("metered boundary lost Ton_cmd")
    if metrics["full_boundary"] != asdict(boundary):
        raise RuntimeError("metered boundary differs from the regulated boundary")
    metrics["ton_cmd_s"] = boundary.ton_cmd_s
    metrics["ton_cmd_deviation_from_nominal_s"] = boundary.ton_cmd_s - NOMINAL_TON_S
    metrics["ton_cmd_relative_deviation_from_nominal"] = boundary.ton_cmd_s / NOMINAL_TON_S - 1.0
    metrics["load_resistance_ohm"] = boundary.load_resistance_ohm
    return metrics


__all__ = [
    "A", "B", "D", "H", "M", "S", "NOMINAL_TON_S", "RATED_LOAD_OHM", "TARGET_POWER_W",
    "POWER_TOLERANCE", "CURRENT_SCREEN_A", "L_ROWS", "DT_COLUMNS", "RegulatedBoundary",
    "build_regulated_boundary", "boundary_record", "regulated_metering",
    "meter_regulated", "asymmetric_ron_context",
]
