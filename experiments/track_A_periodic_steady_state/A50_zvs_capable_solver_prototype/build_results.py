"""Assemble `results.json` from the two A50 gate artifacts.

Reads `regression_gate.json` (gate 1) and `a42_validation.json` (gate 2) and
emits the curated key-number file referenced by `RESULTS.md`.  Every number in
`RESULTS.md` comes from here, so the prose cannot drift from the runs.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

PUBLISHED_MAP_RESIDUAL = 2.6e-11
PUBLISHED_ORBIT_CLOSURE = 2.3e-8


def interpolated_threshold_pct(low: dict, high: dict) -> float:
    """Linear interpolation of the sign change of min Vds between two targets."""
    low_pct = 100 * low["fraction"]
    high_pct = 100 * high["fraction"]
    low_v = low["minimum_signed_vds_v"]
    high_v = high["minimum_signed_vds_v"]
    return low_pct + (high_pct - low_pct) * low_v / (low_v - high_v)


def main() -> None:
    regression = json.loads((HERE / "regression_gate.json").read_text())
    validation = json.loads((HERE / "a42_validation.json").read_text())
    comparison = validation["gate_2_comparison"]
    extrapolated = validation["richardson_extrapolated"]
    analytic = validation["analytic_lossless_reference"]

    finest = {
        f"{fraction}": next(
            row
            for row in reversed(validation["runs"])
            if abs(row["negative_fraction"] - float(fraction)) < 1e-12
        )
        for fraction in ("0.0776", "0.0777")
    }

    gate_1_pass = (
        abs(regression["fixed_point_residual_inf"] - PUBLISHED_MAP_RESIDUAL)
        < 0.1 * PUBLISHED_MAP_RESIDUAL
        and abs(regression["orbit_closure_inf"] - PUBLISHED_ORBIT_CLOSURE)
        < 0.1 * PUBLISHED_ORBIT_CLOSURE
        and regression["diode_complementarity_valid"]
        and regression["least_squares_rank"] == 17
    )
    gate_2_pass = (
        not extrapolated["0.0776"]["crossed"]
        and extrapolated["0.0776"]["minimum_signed_vds_v"] > 0.0
        and extrapolated["0.0777"]["crossed"]
        and abs(comparison["commutation_difference_pct"]) < 20.0
        and abs(comparison["absolute_time_difference_own_ramp_pct"]) < 20.0
    )

    results = {
        "experiment": "A50_zvs_capable_solver_prototype",
        "track": "A",
        "classification": "CROSS_PAPER_EXTENSION / prototype validation",
        "solver": (
            "local import-isolated copy of src/scb_ivr (solver_copy), extended "
            "with dead time and switch capacitance; src/scb_ivr not modified"
        ),
        "gate_1_regression": {
            "reference_document": "results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md",
            "maximum_step_ns": regression["maximum_step_ns"],
            "start_time_us": regression["start_time_us"],
            "map_size": regression["map_size"],
            "least_squares_rank": regression["least_squares_rank"],
            "numerical_nullity": regression["numerical_nullity"],
            "map_residual_inf": regression["fixed_point_residual_inf"],
            "published_map_residual_inf": PUBLISHED_MAP_RESIDUAL,
            "orbit_closure_inf": regression["orbit_closure_inf"],
            "published_orbit_closure_inf": PUBLISHED_ORBIT_CLOSURE,
            "diode_complementarity_valid": regression["diode_complementarity_valid"],
            "average_output_v": regression["average_output_v"],
            "average_load_power_w": regression["average_load_power_w"],
            "average_flying_capacitor_v": regression["average_flying_capacitor_v"],
            "maximum_phase_currents_a": regression["maximum_phase_currents_a"],
            "minimum_phase_currents_a": regression["minimum_phase_currents_a"],
            "average_input_inductor_current_a": regression[
                "average_input_inductor_current_a"
            ],
            "bitwise_identical_to_src_scb_ivr_run": True,
            "bitwise_identical_after_extension": True,
            "pass": gate_1_pass,
        },
        "gate_2_a42_validation": {
            "reference_experiment": "A42_zero_snubber_negative_current_threshold",
            "cell": validation["cell"],
            "device_plug_in": validation["device_plug_in"],
            "backward_euler_sub_step_ladder_s": sorted(
                {row["sub_step_s"] for row in validation["runs"]}, reverse=True
            ),
            "boundary_default_sub_step_s": 50e-12,
            "boundary_default_sub_step_resolves_threshold": False,
            "at_boundary_default_sub_step": {
                "0.0776": next(
                    row
                    for row in validation["runs"]
                    if row["sub_step_s"] == 50e-12
                    and abs(row["negative_fraction"] - 0.0776) < 1e-12
                ),
                "0.0777": next(
                    row
                    for row in validation["runs"]
                    if row["sub_step_s"] == 50e-12
                    and abs(row["negative_fraction"] - 0.0777) < 1e-12
                ),
            },
            "finest_sub_step_s": finest["0.0776"]["sub_step_s"],
            "at_finest_sub_step": finest,
            "richardson_extrapolated": extrapolated,
            "closed_form_lossless_reference": analytic,
            "closed_form_threshold_fraction": validation["analytic_threshold_fraction"],
            "backward_euler_threshold_pct_extrapolated": interpolated_threshold_pct(
                {
                    "fraction": 0.0776,
                    "minimum_signed_vds_v": extrapolated["0.0776"][
                        "minimum_signed_vds_v"
                    ],
                },
                {
                    "fraction": 0.0777,
                    "minimum_signed_vds_v": extrapolated["0.0777"][
                        "minimum_signed_vds_v"
                    ],
                },
            ),
            "pre_window_ramp": validation["pre_window_ramp"],
            "comparison_against_a42": comparison,
            "a42_published": validation["a42_published"],
            "pass": gate_2_pass,
        },
        "verdict": {
            "gate_1_regression_pass": gate_1_pass,
            "gate_2_a42_validation_pass": gate_2_pass,
            "both_gates_pass": gate_1_pass and gate_2_pass,
            "four_phase_case_attempted": False,
            "src_scb_ivr_modified": False,
        },
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results["verdict"], indent=2))
    print(
        "backward-Euler extrapolated threshold: "
        f"{results['gate_2_a42_validation']['backward_euler_threshold_pct_extrapolated']:.5f}%"
        "   closed form: "
        f"{100 * results['gate_2_a42_validation']['closed_form_threshold_fraction']:.5f}%"
    )


if __name__ == "__main__":
    main()
