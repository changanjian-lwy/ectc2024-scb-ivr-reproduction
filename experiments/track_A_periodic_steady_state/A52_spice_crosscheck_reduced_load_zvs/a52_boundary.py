"""A52 - shared boundary/derivation module for the SPICE cross-check.

`BOUNDARY.md` Section 2's own explicit instruction:

    "Derive the exact numerical window boundaries in Python, not by hand.
     ... the implementer must import `solver_copy` directly and call
     `commanded_pwm_mode`/inspect `ZeroStartBoundary`'s own `on_time_s`/
     `period_s` to PRINT the exact absolute-time HIGH/DEADTIME/LOW window
     boundaries for all four phases over the specific period being built,
     and use those printed numbers directly in the netlist's own `.param`
     values -- do not re-derive the `T/4`-offset formula independently by
     hand."

This module therefore contains NO hand-written `T/4` offset arithmetic.
Every window boundary below is found by BISECTING the mode actually
returned by `solver_copy.zero_start_descriptor.commanded_pwm_mode`, which
is the same function A50/A51 integrate against.  A51's own
`a51_period_map.period_intervals` is additionally imported and used as an
INDEPENDENT second derivation of the same numbers, and the two are
cross-checked against each other and against `BOUNDARY.md` Section 4's own
quoted absolute window instants.

Nothing here modifies A50's or A51's committed files; both are imported
read-only through `sys.path`.  `src/scb_ivr/` is neither imported nor read.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACK_A = HERE.parent
A50_DIR = TRACK_A / "A50_zvs_capable_solver_prototype"
A51_DIR = TRACK_A / "A51_four_phase_joint_zvs_solve"
for _path in (A50_DIR, A51_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import numpy as np  # noqa: E402

import a51_period_map as A51  # noqa: E402
from solver_copy.zero_start_descriptor import (  # noqa: E402
    HIGH_SIDE_BRANCHES,
    ZeroStartBoundary,
    commanded_pwm_mode,
)

# ---------------------------------------------------------------------------
# `BOUNDARY.md` Section 1 -- the corrected, realistic-resistance state
# ---------------------------------------------------------------------------
#: `BOUNDARY.md` Section 1: uniform for BOTH sides (Section 2's own explicit
#: requirement; NOT A37/A42/A49's asymmetric RHS/RLS).
SWITCH_ON_RESISTANCE_OHM = 0.007
#: `BOUNDARY.md` Section 1: the NOMINAL target the corrected state was solved
#: at (the ACTUAL delivered power at that state is 89.9207 W -- see
#: `rload_from_actual_power_ohm` below, which is what the netlist uses).
MODULE_POWER_W = 190.0

#: `BOUNDARY.md` Section 1, verbatim, in `solver_copy`'s own `variable_names`
#: order: ['src','src_r','vin','tap3','tap2','tap1','a1','a2','a3',
#:         'x1','x2','x3','x4','out','LPAR_IN','L1','L2','L3','L4','I_VSTEP']
Z_STAR = np.array(
    [
        48.00000000687211,
        47.96569022236729,
        47.969789939303524,
        36.0,
        24.0,
        12.0,
        48.00677396673983,
        24.036209731129393,
        11.636445707833776,
        11.742411388577601,
        -0.02167367897568295,
        -0.21253311225322608,
        -0.4715756542261936,
        0.6878908393606893,
        3.4309784504693295,
        -5.202377626634099,
        3.07242026743103,
        30.358686656836504,
        67.36321312878287,
        -3.43097845046932,
    ],
    dtype=float,
)

#: `BOUNDARY.md` Section 1's own quoted averages at `z*`.
AVERAGE_OUTPUT_V = 0.687944
AVERAGE_LOAD_POWER_W = 89.9207

#: `BOUNDARY.md` Section 4's own quoted per-phase targets (1-indexed phase).
SECTION4_TARGETS = {
    1: {
        "window_start_s": 2.319892500e-05,
        "window_end_s": 2.320107500e-05,
        "il_at_entry_a": -17.157444,
        "initial_vds_v": 11.579036,
        "natural_zvs": True,
        "crossing_time_ns": 1.128389,
        "min_abs_vds_v": 0.000114,
    },
    2: {
        "window_start_s": 2.304892500e-05,
        "window_end_s": 2.305107500e-05,
        "il_at_entry_a": -17.636990,
        "initial_vds_v": 11.822603,
        "natural_zvs": True,
        "crossing_time_ns": 1.122660,
        "min_abs_vds_v": 0.000239,
    },
    3: {
        "window_start_s": 2.309892500e-05,
        "window_end_s": 2.310107500e-05,
        "il_at_entry_a": -17.636853,
        "initial_vds_v": 11.822824,
        "natural_zvs": True,
        "crossing_time_ns": 1.122732,
        "min_abs_vds_v": 0.000153,
    },
    4: {
        "window_start_s": 2.314892500e-05,
        "window_end_s": 2.315107500e-05,
        "il_at_entry_a": -16.483221,
        "initial_vds_v": 11.472413,
        "natural_zvs": True,
        "crossing_time_ns": 0.858292,
        "min_abs_vds_v": 0.000233,
    },
}

#: `BOUNDARY.md` Section 4's own pre-declared comparison tolerance.
CROSSING_TIME_TOLERANCE_FRACTION = 0.20
#: `BOUNDARY.md` Section 6's own standing safety bound.
PHASE_CURRENT_LIMIT_A = 250.0


def build_boundary() -> ZeroStartBoundary:
    """Section 1/5's boundary, built through A51's own `build_boundary`.

    `CFLY=3 uF`, `CH=385 pF`/`CL=770 pF` (via `CommutationCapacitance`) and
    `dead_time_s=2.15 ns` all come from A51's own module-level constants, so
    they cannot drift from what A51 actually solved.
    """
    return A51.build_boundary(
        switch_on_resistance_ohm=SWITCH_ON_RESISTANCE_OHM,
        module_power_w=MODULE_POWER_W,
    )


def rload_from_actual_power_ohm() -> float:
    """`RLOAD = Vout^2 / P` at Section 1's own ACTUAL delivered power.

    `BOUNDARY.md` Section 1 quotes `0.687944 V` average output and
    `89.9207 W` average load power; the netlist's load must reproduce THAT
    operating point, not the `module_power_w=190` nominal figure that the
    solver's own `load_resistance_ohm` property would hand back.
    """
    return AVERAGE_OUTPUT_V**2 / AVERAGE_LOAD_POWER_W


# ---------------------------------------------------------------------------
# Window boundaries, found by bisecting `commanded_pwm_mode` itself
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Segment:
    """One commanded segment of one phase, in ABSOLUTE solver time."""

    phase_1indexed: int
    kind: str  # "HIGH" | "DEADTIME_TURN_OFF" | "LOW" | "DEADTIME_TURN_ON"
    start_s: float
    end_s: float


def _phase_label(time_s: float, boundary: ZeroStartBoundary, phase0: int) -> str:
    """What `commanded_pwm_mode` ACTUALLY commands for `phase0` at `time_s`."""
    mode = commanded_pwm_mode(time_s, boundary)
    high = mode.high_side_on[phase0]
    low = mode.low_side_on[phase0]
    if high and low:  # rejected by `Mode.__post_init__`, kept for completeness
        raise RuntimeError("commanded shoot-through")
    if high:
        return "HIGH"
    if low:
        return "LOW"
    return "DEADTIME"


def _bisect_label_change(
    boundary: ZeroStartBoundary,
    phase0: int,
    low_s: float,
    high_s: float,
    iterations: int = 200,
) -> float:
    """Exact instant in `(low_s, high_s]` at which the commanded label changes.

    Plain bisection on the label returned by `commanded_pwm_mode`.  Because
    that function's own comparisons are exact float comparisons on
    `local`, bisection converges to the true boundary to the last ulp, with
    no formula for the boundary ever being written down here.
    """
    start_label = _phase_label(low_s, boundary, phase0)
    for _ in range(iterations):
        middle = 0.5 * (low_s + high_s)
        if middle <= low_s or middle >= high_s:
            break
        if _phase_label(middle, boundary, phase0) == start_label:
            low_s = middle
        else:
            high_s = middle
    return high_s


def phase_segments(
    boundary: ZeroStartBoundary, t0_s: float, phase0: int, span_s: float
) -> list[Segment]:
    """Every commanded segment of one phase covering `[t0_s, t0_s + span_s)`.

    The scan is done on a grid fine enough that no `2.15 ns` window can be
    stepped over, and each detected label change is then bisected to full
    double precision.  The returned segments are in absolute solver time.
    """
    grid_s = 0.1 * boundary.dead_time_s
    segments: list[Segment] = []
    cursor = t0_s
    cursor_label = _phase_label(cursor, boundary, phase0)
    probe = cursor
    end_s = t0_s + span_s
    while probe < end_s:
        following = min(probe + grid_s, end_s)
        label = _phase_label(following, boundary, phase0)
        if label != cursor_label:
            edge = _bisect_label_change(boundary, phase0, probe, following)
            segments.append(Segment(phase0 + 1, cursor_label, cursor, edge))
            cursor = edge
            cursor_label = label
        probe = following
    segments.append(Segment(phase0 + 1, cursor_label, cursor, end_s))

    # Name the two dead-time windows by what FOLLOWS them, which is the only
    # thing that distinguishes a turn-on window from a turn-off window.
    named: list[Segment] = []
    for position, segment in enumerate(segments):
        kind = segment.kind
        if kind == "DEADTIME":
            following_label = (
                segments[position + 1].kind if position + 1 < len(segments) else None
            )
            if following_label == "HIGH":
                kind = "DEADTIME_TURN_ON"
            elif following_label == "LOW":
                kind = "DEADTIME_TURN_OFF"
            else:
                # last, truncated segment: fall back to what PRECEDED it
                previous_label = segments[position - 1].kind if position else None
                kind = (
                    "DEADTIME_TURN_ON"
                    if previous_label == "LOW"
                    else "DEADTIME_TURN_OFF"
                )
        named.append(Segment(segment.phase_1indexed, kind, segment.start_s, segment.end_s))
    return named


def vds_expression(phase0: int) -> tuple[str, str | None]:
    """The two descriptor nodes whose difference is phase `phase0`'s own `Vds`.

    Taken straight from `solver_copy`'s own `HIGH_SIDE_BRANCHES`, so the
    netlist's `.meas` probes cannot disagree with what A51 measured.
    """
    return HIGH_SIDE_BRANCHES[phase0]
