"""Machine-readable synchronized state export for model-building consumers."""

from __future__ import annotations

from dataclasses import asdict

from scb_ivr.periodic_affine_solver import PeriodicFixedPoint, periodic_orbit_metrics
from scb_ivr.zero_start_descriptor import ZeroStartBoundary, assemble_descriptor
from scb_ivr.zero_start_hybrid_solver import HybridStep


HIGH_SIDE_PAIRS = (
    ("vin", "a1"),
    ("a1", "a2"),
    ("a2", "a3"),
    ("a3", "x4"),
)
LOW_SIDE_PAIRS = (("x1", None), ("x2", None), ("x3", None), ("x4", None))
INDUCTOR_PAIRS = (
    ("x1", "out"),
    ("x2", "out"),
    ("x3", "out"),
    ("x4", "out"),
)
FLYING_CAPACITOR_PAIRS = (("a1", "x1"), ("a2", "x2"), ("a3", "x3"))
SLOW_COORDINATES = frozenset(("tap3", "tap2", "tap1"))


def _named_state(step: HybridStep, boundary: ZeroStartBoundary) -> dict[str, float]:
    system = assemble_descriptor(boundary, step.mode, step.time_s)
    return {
        name: float(value)
        for name, value in zip(system.variable_names, step.state, strict=True)
    }


def _node(state: dict[str, float], name: str | None) -> float:
    return 0.0 if name is None else state[name]


def synchronized_snapshot(
    step: HybridStep,
    boundary: ZeroStartBoundary,
    *,
    label: str,
    relative_time_s: float,
    transition_phase: int,
    transition: str,
) -> dict[str, object]:
    """Return one same-time four-phase left-limit snapshot."""
    state = _named_state(step, boundary)
    phases = []
    for phase_index, (high_pair, low_pair, inductor_pair) in enumerate(
        zip(HIGH_SIDE_PAIRS, LOW_SIDE_PAIRS, INDUCTOR_PAIRS), start=1
    ):
        high_on = step.mode.high_side_on[phase_index - 1]
        switch_node = f"x{phase_index}"
        phase = {
            "phase": phase_index,
            "high_side_pair": list(high_pair),
            "low_side_pair": [low_pair[0], "ground"],
            "inductor_pair": list(inductor_pair),
            "high_side_on_left_limit": high_on,
            "low_side_on_left_limit": not high_on,
            "switch_node_v": state[switch_node],
            "high_side_voltage_first_minus_second_v": (
                _node(state, high_pair[0]) - _node(state, high_pair[1])
            ),
            "low_side_voltage_first_minus_ground_v": state[switch_node],
            "inductor_current_first_to_second_a": state[f"L{phase_index}"],
            "inductor_voltage_first_minus_second_v": (
                state[switch_node] - state["out"]
            ),
            "flying_capacitor_voltage_first_minus_second_v": None,
        }
        if phase_index <= 3:
            first, second = FLYING_CAPACITOR_PAIRS[phase_index - 1]
            phase["flying_capacitor_pair"] = [first, second]
            phase["flying_capacitor_voltage_first_minus_second_v"] = (
                state[first] - state[second]
            )
        phases.append(phase)

    diode_pairs = (("tap3", "a1"), ("tap2", "a2"), ("tap1", "a3"))
    return {
        "label": label,
        "absolute_time_s": step.time_s,
        "relative_time_s": relative_time_s,
        "sampling_side": "left_limit",
        "transition_phase": transition_phase,
        "transition": transition,
        "global": {
            "input_source_v": state["src"],
            "input_bus_v": state["vin"],
            "output_v": state["out"],
            "input_inductor_current_a": state["LPAR_IN"],
            "output_load_current_a": state["out"] / boundary.load_resistance_ohm,
            "sum_phase_currents_a": sum(state[f"L{i}"] for i in range(1, 5)),
            "source_current_variable_a": state["I_VSTEP"],
        },
        "precharge_diodes": [
            {
                "diode": index,
                "pair": list(pair),
                "on_left_limit": step.mode.precharge_diode_on[index - 1],
                "anode_minus_cathode_v": state[pair[0]] - state[pair[1]],
                "reliability": "INVALID_WITHOUT_PHYSICAL_SLOW_COORDINATES",
            }
            for index, pair in enumerate(diode_pairs, start=1)
        ],
        "phases": phases,
        "raw_state_by_variable": state,
    }


def _event_specs(boundary: ZeroStartBoundary) -> list[tuple[float, int, str]]:
    specs: list[tuple[float, int, str]] = [(0.0, 1, "high_side_turn_on")]
    for phase in range(1, boundary.phases + 1):
        start = (phase - 1) * boundary.period_s / boundary.phases
        specs.append((start + boundary.on_time_s, phase, "high_side_turn_off"))
        if phase < boundary.phases:
            specs.append(
                (
                    phase * boundary.period_s / boundary.phases,
                    phase + 1,
                    "high_side_turn_on",
                )
            )
    specs.append((boundary.period_s, 1, "next_period_high_side_turn_on"))
    return sorted(specs, key=lambda item: item[0])


def export_model_dataset(
    boundary: ZeroStartBoundary,
    fixed: PeriodicFixedPoint,
) -> dict[str, object]:
    """Build the complete synchronized model-interface dataset."""
    orbit = fixed.orbit
    start = orbit.steps[0].time_s
    tolerance = max(1e-18, boundary.period_s * 1e-10)
    snapshots = []
    for relative_time, phase, transition in _event_specs(boundary):
        target = start + relative_time
        matches = [step for step in orbit.steps if abs(step.time_s - target) <= tolerance]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected one orbit state at event t={relative_time:.9e}, "
                f"found {len(matches)}"
            )
        snapshots.append(
            synchronized_snapshot(
                matches[0],
                boundary,
                label=f"P{phase}_{transition}_{relative_time * 1e9:.6f}ns",
                relative_time_s=relative_time,
                transition_phase=phase,
                transition=transition,
            )
        )

    system = assemble_descriptor(
        boundary, orbit.steps[0].mode, orbit.steps[0].time_s
    )
    metrics = periodic_orbit_metrics(boundary, fixed)
    units = {
        name: ("A" if name.startswith("L") or name == "I_VSTEP" else "V")
        for name in system.variable_names
    }
    reliability = {
        name: (
            "NONUNIQUE_SLOW_COORDINATE_DO_NOT_USE_AS_PHYSICAL_STARTUP_STATE"
            if name in SLOW_COORDINATES
            else "FAST_PERIODIC_MANIFOLD_STATE"
        )
        for name in system.variable_names
    }
    boundary_data = asdict(boundary)
    boundary_data["evidence"] = boundary.evidence.value
    return {
        "schema": "scb_ivr.synchronized_four_phase_period.v1",
        "classification": "THEORETICAL_FIXED_DIODE_FAST_PERIODIC_MANIFOLD",
        "scope": {
            "topology": "P24-connected single-module four-phase stage",
            "control": "fixed 5 MHz interleaved PWM",
            "diode_branch": "three precharge diodes forced off and audited",
            "modules_simulated": 1,
            "nominal_module_power_w": boundary.module_power_w,
            "not_claimed": [
                "P24/P25 event-driven ZVS sequence",
                "four-module coupling or current sharing",
                "hardware loss or device-level ZVS",
                "unique full zero-start asymptotic state",
            ],
        },
        "boundary": boundary_data,
        "topology": {
            "high_side_pairs": [list(pair) for pair in HIGH_SIDE_PAIRS],
            "low_side_pairs": [[pair[0], "ground"] for pair in LOW_SIDE_PAIRS],
            "inductor_pairs": [list(pair) for pair in INDUCTOR_PAIRS],
            "flying_capacitor_pairs": [
                list(pair) for pair in FLYING_CAPACITOR_PAIRS
            ],
            "precharge_diode_pairs": [
                ["tap3", "a1"],
                ["tap2", "a2"],
                ["tap1", "a3"],
            ],
        },
        "state_schema": {
            "variable_order": list(system.variable_names),
            "units": units,
            "reliability": reliability,
            "sampling_side": "left_limit_at_each_pwm_event",
        },
        "solver_audit": {
            "maximum_step_s": fixed.period_map.maximum_step_s,
            "map_size": int(fixed.period_map.matrix.shape[0]),
            "least_squares_rank": fixed.least_squares_rank,
            "numerical_nullity": int(
                fixed.period_map.matrix.shape[0] - fixed.least_squares_rank
            ),
            "fixed_point_residual_inf": fixed.fixed_point_residual_inf,
            "orbit_closure_inf": fixed.orbit_closure_inf,
            "diode_complementarity_valid_for_minimum_norm_slow_coordinates": (
                fixed.diode_complementarity_valid
            ),
        },
        "affine_period_map": {
            "equation": "z_next = matrix_M @ z_current + offset_c",
            "variable_order": list(system.variable_names),
            "discretization": "backward_euler",
            "maximum_step_s": fixed.period_map.maximum_step_s,
            "matrix_M": fixed.period_map.matrix.tolist(),
            "offset_c": fixed.period_map.offset.tolist(),
            "warning": (
                "This is the selected discrete one-period map, not a "
                "continuous-time state matrix."
            ),
        },
        "period_metrics": asdict(metrics),
        "event_snapshots": snapshots,
        "warnings": [
            "tap3/tap2/tap1 are numerically nonunique slow coordinates; their "
            "minimum-norm values and derived diode voltages are not physical "
            "zero-start initial conditions.",
            "Each event row is the left limit. Stored-energy states are "
            "continuous, but algebraic switch-node right limits are not "
            "invented by this export.",
        ],
    }
