"""A50 gate 2 driver - phase-4 dead-time commutation at A42's own targets.

Runs `resolve_deadtime_window` at 7.76% and 7.77% of the 125 A phase peak,
at `../BOUNDARY.md`'s stated 50 ps default sub-step and at a refinement ladder
down to 0.25 ps, because backward Euler is only first-order accurate and its
numerical damping is itself a voltage error on the same scale as the millivolt
quantity being measured.  Both are reported; neither is hidden.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import a42_local_validation as a42  # noqa: E402

SUB_STEPS_S = (
    50e-12,
    10e-12,
    5e-12,
    2e-12,
    1e-12,
    0.5e-12,
    0.25e-12,
    0.125e-12,
    0.0625e-12,
)
FRACTIONS = (0.0776, 0.0777)


def assert_import_isolation() -> None:
    leaked = sorted(
        name for name in sys.modules if name == "scb_ivr" or name.startswith("scb_ivr.")
    )
    if leaked:
        raise RuntimeError(f"leaked src/scb_ivr imports: {leaked}")


def one_run(fraction: float, sub_step_s: float) -> dict[str, object]:
    case = a42.build_case(negative_fraction=fraction)
    out = a42.resolve_case(case, sub_step_s=sub_step_s)
    window = out["window"]
    start = window.start_time_s
    return {
        "negative_fraction": fraction,
        "negative_current_a": case["negative_current_a"],
        "release_switch_node_v": case["release_switch_node_v"],
        "sub_step_s": sub_step_s,
        "step_count": window.step_count,
        "commanded_dead_time_confirmed": window.commanded_dead_time_confirmed,
        "high_side_branch": list(window.high_side_branch),
        "initial_switch_voltage_v": window.initial_switch_voltage_v,
        "minimum_abs_vds_v": window.minimum_abs_switch_voltage_v,
        "minimum_signed_vds_v": window.minimum_signed_switch_voltage_v,
        "time_of_minimum_after_release_s": (
            window.minimum_abs_switch_voltage_time_s - start
        ),
        "crossed_tolerance": window.crossed_tolerance,
        "crossing_tolerance_v": window.crossing_tolerance_v,
        "crossed_tolerance_after_release_s": (
            None
            if window.crossed_tolerance_time_s is None
            else window.crossed_tolerance_time_s - start
        ),
        "sign_change_after_release_s": (
            None
            if window.sign_change_time_s is None
            else window.sign_change_time_s - start
        ),
        "phase_current_at_crossing_a": window.switch_current_at_crossing_a,
        "idle_phase_reference_drift_v": out["idle_phase_reference_drift_v"],
        "output_rail_drift_v": out["output_rail_drift_v"],
        "maximum_descriptor_relative_backward_error": (
            window.maximum_descriptor_relative_backward_error
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    assert_import_isolation()

    report: dict[str, object] = {
        "classification": "A50_PROTOTYPE_LOCAL_ZVS_VALIDATION",
        "a42_published": a42.A42_PUBLISHED,
        "device_plug_in": {
            "part_number": "GS61008T",
            "high_side_parallel": 1,
            "low_side_parallel": 2,
            "high_total_f": a42.A42_SWITCH_CAPACITANCE.high_total_f,
            "low_total_f": a42.A42_SWITCH_CAPACITANCE.low_total_f,
            "rhs_ohm": a42.A42_RHS_OHM,
            "rls_ohm": a42.A42_RLS_OHM,
        },
        "cell": {
            "test_phase_index": a42.TEST_PHASE_INDEX,
            "high_side_branch": ["a3", "x4"],
            "dead_time_s": a42.DEAD_TIME_S,
            "phase_inductance_h": a42.LPHASE_H,
            "vds_to_remove_v": a42.A42_VDS_HIGH_AT_T2_V,
            "window_start_s": a42.dead_time_window_start_s(a42.build_boundary()),
        },
        "analytic_lossless_reference": {},
        "runs": [],
    }

    for fraction in FRACTIONS:
        current = fraction * a42.IPEAK_P24_A
        drop = current * a42.A42_RLS_OHM
        report["analytic_lossless_reference"][f"{fraction:.4f}"] = (
            a42.analytic_lossless_commutation(
                negative_current_a=current, switch_node_v=drop
            )
        )
    report["analytic_threshold_current_a"] = a42.threshold_current_a(
        switch_node_v=0.0776 * a42.IPEAK_P24_A * a42.A42_RLS_OHM
    )
    report["analytic_threshold_fraction"] = (
        report["analytic_threshold_current_a"] / a42.IPEAK_P24_A
    )

    for sub_step_s in SUB_STEPS_S:
        for fraction in FRACTIONS:
            row = one_run(fraction, sub_step_s)
            report["runs"].append(row)
            print(
                f"sub-step {sub_step_s * 1e12:8.4f} ps  "
                f"{fraction * 100:.2f}%  "
                f"min Vds(signed) {row['minimum_signed_vds_v'] * 1e3:12.6f} mV  "
                f"min|Vds| {row['minimum_abs_vds_v'] * 1e3:10.6f} mV  "
                f"crossed={str(row['crossed_tolerance']):5s}  "
                f"t_sign_change="
                + (
                    "      n/a   "
                    if row["sign_change_after_release_s"] is None
                    else f"{row['sign_change_after_release_s'] * 1e9:9.5f} ns"
                )
                + f"  steps={row['step_count']}"
            )

    # First-order Richardson extrapolation from the two finest sub-steps, which
    # is the correct limit statement for a backward-Euler result.
    extrapolated: dict[str, dict[str, float | None]] = {}
    for fraction in FRACTIONS:
        rows = [row for row in report["runs"] if row["negative_fraction"] == fraction]
        fine, coarse = rows[-1], rows[-2]
        entry: dict[str, float | None] = {
            "finest_sub_step_s": fine["sub_step_s"],
            "minimum_signed_vds_v": 2 * fine["minimum_signed_vds_v"]
            - coarse["minimum_signed_vds_v"],
        }
        for key in (
            "sign_change_after_release_s",
            "phase_current_at_crossing_a",
        ):
            if fine[key] is not None and coarse[key] is not None:
                entry[key] = 2 * fine[key] - coarse[key]
            else:
                entry[key] = None
        entry["crossed"] = bool(fine["crossed_tolerance"])
        extrapolated[f"{fraction:.4f}"] = entry
    report["richardson_extrapolated"] = extrapolated
    print("\nfirst-order Richardson extrapolation (two finest sub-steps):")
    for key, entry in extrapolated.items():
        crossing = entry["sign_change_after_release_s"]
        print(
            f"  {float(key) * 100:.2f}%  min Vds -> "
            f"{entry['minimum_signed_vds_v'] * 1e3:.6f} mV"
            + (
                ""
                if crossing is None
                else f"   crossing -> {crossing * 1e9:.6f} ns after release"
            )
        )

    print("\npre-window low-side ramp (phase 4, iL4: 0 -> -INEG):")
    ramps = {}
    for fraction in FRACTIONS:
        ramp = a42.ramp_to_release(negative_fraction=fraction, sub_step_s=1e-12)
        ramps[f"{fraction:.4f}"] = {
            "ramp_duration_s": ramp["ramp_duration_s"],
            "current_at_window_start_a": ramp["current_at_window_start_a"],
            "negative_current_a": ramp["negative_current_a"],
            "sub_step_s": ramp["sub_step_s"],
        }
        print(
            f"  {fraction * 100:.2f}%  ramp {ramp['ramp_duration_s'] * 1e9:.6f} ns  "
            f"iL4(window start) = {ramp['current_at_window_start_a']:.6f} A  "
            f"(A42 release {a42.A42_PUBLISHED['cross_release_time_s'] * 1e9:.4f} ns)"
        )
    report["pre_window_ramp"] = ramps

    # ---- gate-2 comparison against A42's own published outcome -------------
    published = a42.A42_PUBLISHED
    cross = extrapolated[f"{FRACTIONS[1]:.4f}"]
    no_cross = extrapolated[f"{FRACTIONS[0]:.4f}"]
    commutation_s = cross["sign_change_after_release_s"]
    own_ramp_s = ramps[f"{FRACTIONS[1]:.4f}"]["ramp_duration_s"]
    comparison = {
        "no_cross_target_pct": 100 * FRACTIONS[0],
        "a50_crossed_at_no_cross_target": no_cross["crossed"],
        "a50_minimum_vds_v": no_cross["minimum_signed_vds_v"],
        "a42_minimum_vds_v": published["no_cross_minimum_vds_v"],
        "minimum_vds_difference_v": (
            no_cross["minimum_signed_vds_v"] - published["no_cross_minimum_vds_v"]
        ),
        "cross_target_pct": 100 * FRACTIONS[1],
        "a50_crossed_at_cross_target": cross["crossed"],
        "a50_commutation_after_release_s": commutation_s,
        "a42_commutation_after_release_s": published["cross_commutation_time_s"],
        "commutation_difference_pct": 100
        * (commutation_s - published["cross_commutation_time_s"])
        / published["cross_commutation_time_s"],
        "a50_own_ramp_absolute_zvs_time_s": own_ramp_s + commutation_s,
        "a50_on_a42_release_absolute_zvs_time_s": (
            published["cross_release_time_s"] + commutation_s
        ),
        "a42_absolute_zvs_time_s": published["cross_absolute_time_s"],
        "absolute_time_difference_own_ramp_pct": 100
        * (own_ramp_s + commutation_s - published["cross_absolute_time_s"])
        / published["cross_absolute_time_s"],
        "absolute_time_difference_a42_release_pct": 100
        * (
            published["cross_release_time_s"]
            + commutation_s
            - published["cross_absolute_time_s"]
        )
        / published["cross_absolute_time_s"],
        "a50_phase_current_at_crossing_a": cross["phase_current_at_crossing_a"],
        "a42_phase_current_at_crossing_a": published["cross_current_at_zvs_a"],
    }
    report["gate_2_comparison"] = comparison
    print("\ngate-2 comparison against A42:")
    print(
        f"  7.76%: A50 crossed={comparison['a50_crossed_at_no_cross_target']}  "
        f"min Vds {comparison['a50_minimum_vds_v'] * 1e3:.4f} mV  "
        f"(A42 {published['no_cross_minimum_vds_v'] * 1e3:.4f} mV, "
        f"difference {comparison['minimum_vds_difference_v'] * 1e3:+.4f} mV)"
    )
    print(
        f"  7.77%: A50 crossed={comparison['a50_crossed_at_cross_target']}  "
        f"commutation {commutation_s * 1e9:.4f} ns "
        f"(A42 {published['cross_commutation_time_s'] * 1e9:.4f} ns, "
        f"{comparison['commutation_difference_pct']:+.3f}%)"
    )
    print(
        f"         absolute ZVS time with A50's own ramp "
        f"{comparison['a50_own_ramp_absolute_zvs_time_s'] * 1e9:.4f} ns "
        f"(A42 {published['cross_absolute_time_s'] * 1e9:.4f} ns, "
        f"{comparison['absolute_time_difference_own_ramp_pct']:+.3f}%); "
        f"on A42's own release instant "
        f"{comparison['a50_on_a42_release_absolute_zvs_time_s'] * 1e9:.4f} ns "
        f"({comparison['absolute_time_difference_a42_release_pct']:+.3f}%)"
    )

    assert_import_isolation()
    if args.output is not None:
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(f"\nwrote {args.output}" if args.output else "")


if __name__ == "__main__":
    main()
