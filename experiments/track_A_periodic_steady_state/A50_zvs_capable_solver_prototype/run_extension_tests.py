"""A50 extension self-tests for the local `solver_copy` package.

Checks, in order:

1. import isolation -- nothing under `src/scb_ivr/` is reachable or loaded;
2. `dead_time_s = 0` collapse -- `commanded_pwm_mode` returns BIT-IDENTICAL
   high-side booleans to the unmodified original function (transcribed
   verbatim below from the pre-A50 file, which is also kept byte-for-byte in
   this repository at `src/scb_ivr/zero_start_descriptor.py`), with the low
   side exactly complementary, i.e. the exact original two-state schedule;
3. `next_pwm_edge_s` collapse at `dead_time_s = 0`;
4. `switch_capacitance = None` collapse -- the assembled `E`, `A` and `r`
   matrices are bit-identical to the same descriptor assembled with the
   commutation-capacitance code path switched off;
5. the `dead_time_s > 0` schedule really is HIGH -> DEADTIME -> LOW -> DEADTIME,
   centered on the original edges, with the right durations;
6. `resolve_deadtime_window` runs and reports a monotone, physical transition.
"""

from __future__ import annotations

import sys
from math import floor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from solver_copy.commutation_capacitance import CommutationCapacitance  # noqa: E402
from solver_copy.zero_start_descriptor import (  # noqa: E402
    ZeroStartBoundary,
    assemble_descriptor,
    commanded_pwm_mode,
)
from solver_copy.zero_start_hybrid_solver import next_pwm_edge_s  # noqa: E402


def check_import_isolation() -> None:
    leaked = sorted(
        name for name in sys.modules if name == "scb_ivr" or name.startswith("scb_ivr.")
    )
    assert not leaked, f"solver_copy leaked src/scb_ivr imports: {leaked}"
    for name, module in list(sys.modules.items()):
        if not name.startswith("solver_copy"):
            continue
        origin = (getattr(module, "__file__", "") or "").replace("\\", "/")
        assert "src/scb_ivr" not in origin, f"{name} resolved to {origin}"
    print("1. import isolation .............. OK (no src/scb_ivr module loaded)")


def original_commanded_high_side_on(
    time_s: float, boundary: ZeroStartBoundary
) -> tuple[bool, ...]:
    """Verbatim transcription of the pre-A50 `commanded_pwm_mode` body."""
    period = boundary.period_s
    high = []
    for phase in range(boundary.phases):
        shifted = time_s - phase * period / boundary.phases
        local = shifted - floor(shifted / period) * period
        high.append(local < boundary.on_time_s)
    return tuple(high)


def original_next_pwm_edge_s(time_s: float, boundary: ZeroStartBoundary) -> float:
    """Verbatim transcription of the pre-A50 `next_pwm_edge_s` body."""
    period = boundary.period_s
    candidates: list[float] = []
    epsilon = max(1e-18, 1e-12 * period)
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        cycle = floor((time_s - start0) / period)
        for index in (cycle, cycle + 1, cycle + 2):
            start = start0 + index * period
            end = start + boundary.on_time_s
            if start > time_s + epsilon:
                candidates.append(start)
            if end > time_s + epsilon:
                candidates.append(end)
    if not candidates:
        raise RuntimeError("failed to locate the next PWM edge")
    return min(candidates)


def sample_times(boundary: ZeroStartBoundary) -> list[float]:
    """A dense grid plus every exact edge plus a reproducible random set."""
    period = boundary.period_s
    times = list(np.linspace(0.0, 3.0 * period, 60_001))
    times += list(np.linspace(23.0e-6, 23.0e-6 + 2.0 * period, 40_001))
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        for cycle in range(-1, 4):
            start = start0 + cycle * period
            times += [start, start + boundary.on_time_s]
    rng = np.random.default_rng(50)
    times += list(rng.uniform(-period, 120.0 * period, 40_000))
    return times


def check_dead_time_zero_collapse() -> None:
    boundary = ZeroStartBoundary()
    assert boundary.dead_time_s == 0.0
    assert boundary.switch_capacitance is None
    mismatches = 0
    for time_s in sample_times(boundary):
        mode = commanded_pwm_mode(float(time_s), boundary)
        reference = original_commanded_high_side_on(float(time_s), boundary)
        if mode.high_side_on != reference:
            mismatches += 1
        if mode.low_side_on != tuple(not value for value in reference):
            mismatches += 1
        if any(mode.dead_time_phases):
            mismatches += 1
    assert mismatches == 0, f"{mismatches} schedule mismatches at dead_time_s=0"
    print(
        "2. dead_time_s=0 Mode collapse ... OK "
        "(bit-identical high side, exactly complementary low side, "
        "zero dead-time phases, over 140k+ sampled instants)"
    )


def check_edge_collapse() -> None:
    boundary = ZeroStartBoundary()
    worst = 0.0
    for time_s in sample_times(boundary):
        got = next_pwm_edge_s(float(time_s), boundary)
        want = original_next_pwm_edge_s(float(time_s), boundary)
        assert got == want, (time_s, got, want)
        worst = max(worst, abs(got - want))
    assert worst == 0.0
    print("3. next_pwm_edge_s collapse ..... OK (bit-identical at dead_time_s=0)")


def check_capacitance_none_collapse() -> None:
    boundary_none = ZeroStartBoundary()
    boundary_zero = ZeroStartBoundary(
        switch_capacitance=CommutationCapacitance(
            high_device_f=0.0, low_device_f=0.0
        )
    )
    for time_s in (0.0, 1e-8, 23.0e-6, 23.0e-6 + 137e-9):
        mode = commanded_pwm_mode(time_s, boundary_none)
        left = assemble_descriptor(boundary_none, mode, time_s)
        right = assemble_descriptor(boundary_zero, mode, time_s)
        assert np.array_equal(left.e, right.e)
        assert np.array_equal(left.a, right.a)
        assert np.array_equal(left.rhs, right.rhs)
        assert left.variable_names == right.variable_names
    # and the E matrix really has no switch-branch capacitance when None
    mode = commanded_pwm_mode(23.0e-6, boundary_none)
    system = assemble_descriptor(boundary_none, mode, 23.0e-6)
    index = {name: i for i, name in enumerate(system.node_names)}
    assert system.e[index["vin"], index["a1"]] == 0.0
    assert system.e[index["a1"], index["a2"]] == 0.0
    charged = ZeroStartBoundary(
        switch_capacitance=CommutationCapacitance(
            high_device_f=385e-12, low_device_f=770e-12
        )
    )
    loaded = assemble_descriptor(charged, mode, 23.0e-6)
    assert loaded.e[index["vin"], index["a1"]] == -385e-12
    assert loaded.e[index["a1"], index["a2"]] == -385e-12
    assert loaded.e[index["a2"], index["a3"]] == -385e-12
    assert loaded.e[index["a3"], index["x4"]] == -385e-12
    for node in ("x1", "x2", "x3", "x4"):
        assert loaded.e[index[node], index[node]] - system.e[index[node], index[node]] > 0
    print(
        "4. switch_capacitance collapse .. OK "
        "(None and 0 F give bit-identical E/A/r; 385 pF / 770 pF land on all "
        "eight switch branches)"
    )


def check_dead_time_schedule() -> None:
    dead_time_s = 10e-9
    boundary = ZeroStartBoundary(dead_time_s=dead_time_s)
    period = boundary.period_s
    on_time = boundary.on_time_s
    half = 0.5 * dead_time_s
    grid = np.linspace(0.0, period, 2_000_001, endpoint=False)
    for phase in range(boundary.phases):
        start0 = phase * period / boundary.phases
        high = np.zeros(grid.size, dtype=bool)
        low = np.zeros(grid.size, dtype=bool)
        for i, time_s in enumerate(grid):
            mode = commanded_pwm_mode(float(time_s), boundary)
            high[i] = mode.high_side_on[phase]
            low[i] = mode.low_side_on[phase]
        assert not np.any(high & low), "commanded shoot-through"
        dt = period / grid.size
        high_duration = high.sum() * dt
        low_duration = low.sum() * dt
        dead_duration = (~high & ~low).sum() * dt
        assert abs(high_duration - (on_time - dead_time_s)) < 2 * dt, high_duration
        assert abs(low_duration - (period - on_time - dead_time_s)) < 2 * dt
        assert abs(dead_duration - 2 * dead_time_s) < 4 * dt
        # dead-time windows centered on the ORIGINAL edges
        for edge in (start0, start0 + on_time):
            before = commanded_pwm_mode(edge - half - 1e-13, boundary)
            inside_low = commanded_pwm_mode(edge - half + 1e-13, boundary)
            inside_high = commanded_pwm_mode(edge + half - 1e-13, boundary)
            after = commanded_pwm_mode(edge + half + 1e-13, boundary)
            assert not inside_low.high_side_on[phase]
            assert not inside_low.low_side_on[phase]
            assert not inside_high.high_side_on[phase]
            assert not inside_high.low_side_on[phase]
            assert before.high_side_on[phase] or before.low_side_on[phase]
            assert after.high_side_on[phase] or after.low_side_on[phase]
    print(
        "5. dead-time schedule ........... OK "
        "(HIGH/DEADTIME/LOW/DEADTIME, durations Ton-d and T-Ton-d, "
        "both windows centered on the original T/4-shifted edges)"
    )


def check_resolve_runs() -> None:
    from a42_local_validation import build_case, resolve_case  # noqa: PLC0415

    case = build_case(negative_fraction=0.0777)
    result = resolve_case(case, sub_step_s=50e-12)
    window = result["window"]
    assert window.commanded_dead_time_confirmed
    assert window.step_count > 100
    assert window.high_side_branch == ("a3", "x4")
    assert window.initial_switch_voltage_v > 11.0
    print(
        "6. resolve_deadtime_window ...... OK "
        f"({window.step_count} sub-steps, branch V({window.high_side_branch[0]},"
        f"{window.high_side_branch[1]}) started at "
        f"{window.initial_switch_voltage_v:.6f} V, "
        f"min |Vds| {window.minimum_abs_switch_voltage_v:.6e} V)"
    )


def main() -> None:
    check_import_isolation()
    check_dead_time_zero_collapse()
    check_edge_collapse()
    check_capacitance_none_collapse()
    check_dead_time_schedule()
    check_resolve_runs()
    check_import_isolation()
    print("\nall A50 extension self-tests passed")


if __name__ == "__main__":
    main()
