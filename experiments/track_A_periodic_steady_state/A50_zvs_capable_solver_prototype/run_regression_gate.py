"""A50 gate 1 - reproduce the published affine-period fixed point via solver_copy.

Reproduces `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`'s own published
0.0625 ns numbers (map residual `2.6e-11`, one-period closure `2.3e-8`) using
ONLY this experiment's local `solver_copy` package, with the boundary left at
`ZeroStartBoundary`'s own dataclass defaults -- which are exactly the frozen
boundary that document states (one 250 W module, four phases, 48 V -> 1 V,
5 MHz, `Lphase=1.4666667 nH`, `Cfly=3 uF`, `Cdiv=300 uF`, 22.87 us input ramp).

The start time and step size are taken from `scripts/solve_zero_start_affine_
period.py`, the script that produced the published numbers: the first whole PWM
period boundary at or after the end of the input ramp, and `--step-ns 0.0625`.

Nothing here writes to, or imports from, `src/scb_ivr/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from solver_copy.periodic_affine_solver import (  # noqa: E402
    build_affine_period_map,
    periodic_orbit_metrics,
    solve_periodic_fixed_point,
)
from solver_copy.zero_start_descriptor import ZeroStartBoundary  # noqa: E402

PUBLISHED_MAP_RESIDUAL = 2.6e-11
PUBLISHED_ORBIT_CLOSURE = 2.3e-8
PUBLISHED_AVERAGE_OUTPUT_V = 1.00601
PUBLISHED_AVERAGE_LOAD_POWER_W = 253.013
PUBLISHED_AVERAGE_FLYING_V = (35.8448, 23.8863, 11.9278)
PUBLISHED_PHASE_MAXIMA_A = (125.879, 125.554, 125.554, 125.891)
PUBLISHED_PHASE_MINIMA_A = (0.111, -0.214, -0.214, 0.123)
PUBLISHED_AVERAGE_INPUT_CURRENT_A = 5.298


def assert_import_isolation() -> list[str]:
    """Fail loudly if anything under `src/scb_ivr/` was pulled in."""
    leaked = sorted(
        name for name in sys.modules if name == "scb_ivr" or name.startswith("scb_ivr.")
    )
    if leaked:
        raise RuntimeError(f"solver_copy leaked an import of src/scb_ivr/: {leaked}")
    loaded = sorted(
        name for name in sys.modules if name.startswith("solver_copy")
    )
    for name in loaded:
        origin = getattr(sys.modules[name], "__file__", "") or ""
        if "src/scb_ivr" in origin.replace("\\", "/"):
            raise RuntimeError(f"{name} resolved to {origin}")
    return loaded


def run(step_ns: float) -> dict[str, object]:
    boundary = ZeroStartBoundary()
    start_time_s = (
        int(boundary.input_ramp_s / boundary.period_s) + 1
    ) * boundary.period_s
    period_map = build_affine_period_map(
        boundary,
        start_time_s=start_time_s,
        maximum_step_s=step_ns * 1e-9,
    )
    fixed = solve_periodic_fixed_point(boundary, period_map)
    metrics = periodic_orbit_metrics(boundary, fixed)
    return {
        "maximum_step_ns": step_ns,
        "start_time_us": start_time_s * 1e6,
        "map_size": int(period_map.matrix.shape[0]),
        "least_squares_rank": fixed.least_squares_rank,
        "numerical_nullity": int(
            period_map.matrix.shape[0] - fixed.least_squares_rank
        ),
        "fixed_point_residual_inf": fixed.fixed_point_residual_inf,
        "orbit_closure_inf": fixed.orbit_closure_inf,
        "diode_complementarity_valid": fixed.diode_complementarity_valid,
        "maximum_off_diode_forward_voltage_v": (
            fixed.maximum_off_diode_forward_voltage_v
        ),
        "average_output_v": metrics.average_output_v,
        "average_load_power_w": metrics.average_load_power_w,
        "average_flying_capacitor_v": list(metrics.average_flying_capacitor_v),
        "average_phase_currents_a": list(metrics.average_phase_currents_a),
        "maximum_phase_currents_a": list(metrics.maximum_phase_currents_a),
        "minimum_phase_currents_a": list(metrics.minimum_phase_currents_a),
        "average_input_inductor_current_a": (
            metrics.average_input_inductor_current_a
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-ns", type=float, default=0.0625)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    loaded = assert_import_isolation()
    result = run(args.step_ns)
    result["imported_solver_copy_modules"] = loaded
    assert_import_isolation()

    result["published_reference"] = {
        "map_residual_inf": PUBLISHED_MAP_RESIDUAL,
        "orbit_closure_inf": PUBLISHED_ORBIT_CLOSURE,
        "average_output_v": PUBLISHED_AVERAGE_OUTPUT_V,
        "average_load_power_w": PUBLISHED_AVERAGE_LOAD_POWER_W,
        "average_flying_capacitor_v": list(PUBLISHED_AVERAGE_FLYING_V),
        "maximum_phase_currents_a": list(PUBLISHED_PHASE_MAXIMA_A),
        "minimum_phase_currents_a": list(PUBLISHED_PHASE_MINIMA_A),
        "average_input_inductor_current_a": PUBLISHED_AVERAGE_INPUT_CURRENT_A,
    }
    print(json.dumps(result, indent=2))
    if args.output is not None:
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
