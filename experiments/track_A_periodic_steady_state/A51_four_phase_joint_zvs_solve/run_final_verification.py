"""A51 step 5 - independent per-phase verification at the final state.

`BOUNDARY.md` Section 4.4: at the final state, EVERY phase's own turn-on
dead-time window is checked independently, with step-size convergence, and all
four results are reported separately -- A44's own finding is that the phases are
not interchangeable, so no symmetry is assumed anywhere in this script.

Five things are measured, per phase, one phase at a time:

1. **A sub-step ladder** through A50's own unchanged `resolve_deadtime_window`,
   from `50 ps` down to `0.0625 ps`, plus a first-order Richardson
   extrapolation -- A50 Section 3.3 showed a single sub-step cannot answer a
   millivolt-margin ZVS question under backward Euler, and Section 5 of its
   RESULTS made showing this convergence mandatory for any later use.
2. **An extended-window probe.**  The same window is re-run with its end pushed
   out to `10 ns` -- far past a full resonant quarter period -- to answer
   directly whether a LONGER dead time could ever have produced the crossing,
   or whether the resonance simply lacks the amplitude.
3. **The implied participating capacitance** of each phase's own commutation
   node, back-solved from the measured resonant amplitude by
   `C_eff = L * I^2 / A^2`.  This is the quantitative form of A50's own
   observation that phase 4 sits at the bottom of the ladder and commutates
   `1155 pF` while phases 1-3 commutate more -- i.e. it is a direct measurement
   of how NOT interchangeable the phases are.
4. **The threshold negative current** at which each phase's own window would
   just cross zero, found by bisection on that phase's own inductor current at
   its window entry with every other coordinate held at the orbit value (the
   same deliberately-local construction A42 used).  Compared against the current
   the fixed point actually delivers, this is the quantitative size of the gap.
5. **An A44-style state sensitivity table**: the derivative of each phase's own
   minimum `|Vds|` with respect to `VC1`, `VC2`, `VC3` and its own phase
   current, at the window entry.

Run:  python3 run_final_verification.py --output final_verification.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import a51_period_map as M
from solver_copy.zero_start_hybrid_solver import resolve_deadtime_window

SUB_STEPS_PS = (50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5, 0.25, 0.125, 0.0625)


def _window(boundary, entry_step, phase_index, sub_step_s, window_end_s=None):
    return resolve_deadtime_window(
        boundary,
        entry_step,
        phase_index=phase_index,
        window_end_s=window_end_s,
        sub_step_s=sub_step_s,
        crossing_tolerance_v=1e-3,
        diode_state=(False, False, False),
        store_steps=False,
    )


def _entry_with_current(boundary, entry_step, phase_index, current_a, index):
    state = entry_step.state.copy()
    state[index[f"L{phase_index + 1}"]] = current_a
    return M._initial_step(boundary, state, entry_step.time_s, (False, False, False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", default="fixed_point_search.json")
    parser.add_argument("--output", default="final_verification.json")
    parser.add_argument("--extended-window-ns", type=float, default=10.0)
    parser.add_argument("--probe-sub-step-ps", type=float, default=1.0)
    args = parser.parse_args()

    search = json.loads(Path(args.search).read_text())
    boundary = M.build_boundary(
        dead_time_s=search["boundary"]["dead_time_s"],
        switch_on_resistance_ohm=search["boundary"]["switch_on_resistance_ohm"],
        module_power_w=search["boundary"]["module_power_w"],
    )
    names = M.variable_names(boundary)
    index = {name: position for position, name in enumerate(names)}
    z = np.array(search["newton"]["final_state"], dtype=float)
    started = time.time()

    result = M.evaluate_period_map(
        boundary,
        z,
        coarse_step_s=search["numerics"]["coarse_step_s"],
        sub_step_s=search["numerics"]["sub_step_s"],
    )
    if result.monitor.maximum_abs_phase_current_a > M.PHASE_CURRENT_LIMIT_A:
        raise RuntimeError("safety bound violated at the final state")

    phases: list[dict] = []
    for phase_index in range(boundary.phases):
        entry = result.turn_on_entry[phase_index]
        entry_current_a = float(entry.state[index[f"L{phase_index + 1}"]])

        # ---- 1. sub-step ladder --------------------------------------------
        ladder = []
        for sub_step_ps in SUB_STEPS_PS:
            window = _window(boundary, entry, phase_index, sub_step_ps * 1e-12)
            ladder.append(
                {
                    "sub_step_ps": sub_step_ps,
                    "step_count": window.step_count,
                    "commanded_dead_time_confirmed": window.commanded_dead_time_confirmed,
                    "initial_vds_v": window.initial_switch_voltage_v,
                    "minimum_abs_vds_v": window.minimum_abs_switch_voltage_v,
                    "minimum_abs_vds_time_s": window.minimum_abs_switch_voltage_time_s,
                    "minimum_signed_vds_v": window.minimum_signed_switch_voltage_v,
                    "vds_at_commanded_window_end_v": window.final_switch_voltage_v,
                    "crossed_1mv": window.crossed_tolerance,
                    "crossed_1mv_time_s": window.crossed_tolerance_time_s,
                    "sign_change_time_s": window.sign_change_time_s,
                    "maximum_relative_backward_error": (
                        window.maximum_descriptor_relative_backward_error
                    ),
                }
            )
        richardson = {
            key: 2.0 * ladder[-1][key] - ladder[-2][key]
            for key in ("minimum_abs_vds_v", "vds_at_commanded_window_end_v")
        }

        # ---- 2. free-resonance probe (would a LONGER dead time help?) ------
        def probe_from(step, *, sub_step_s=None, duration_s=None):
            return M.free_resonance_probe(
                boundary,
                step,
                phase_index=phase_index,
                duration_s=duration_s or args.extended_window_ns * 1e-9,
                sub_step_s=sub_step_s or args.probe_sub_step_ps * 1e-12,
            )

        free = probe_from(entry)
        free_ladder = [
            {
                "sub_step_ps": sub_step_ps,
                "minimum_signed_vds_v": probe_from(
                    entry, sub_step_s=sub_step_ps * 1e-12
                ).minimum_signed_vds_v,
            }
            for sub_step_ps in (4.0, 2.0, 1.0, 0.5)
        ]
        amplitude_v = free.downward_excursion_v

        # ---- 3. measured participating capacitance -------------------------
        capacitance_rows = [
            {
                "step_ps": step_ps,
                "capacitance_f": M.measure_node_capacitance_f(
                    boundary, entry, phase_index=phase_index, step_s=step_ps * 1e-12
                ),
            }
            for step_ps in (2.0, 1.0, 0.5, 0.25)
        ]
        measured_capacitance_f = capacitance_rows[-1]["capacitance_f"]

        # ---- 4. threshold negative current ---------------------------------
        def crosses(current_a: float, sub_step_ps: float | None = None) -> bool:
            step = _entry_with_current(boundary, entry, phase_index, current_a, index)
            return probe_from(
                step, sub_step_s=(sub_step_ps or args.probe_sub_step_ps) * 1e-12
            ).crossed_zero

        bound_a = -(M.PHASE_CURRENT_LIMIT_A - 1.0)
        threshold = {
            "search_lower_bound_a": bound_a,
            "free_probe_duration_ns": args.extended_window_ns,
            "reachable_within_safety_bound": crosses(bound_a),
        }
        if threshold["reachable_within_safety_bound"]:
            low, high = bound_a, 0.0  # crosses at `low`, does not at `high`
            for _ in range(40):
                middle = 0.5 * (low + high)
                if crosses(middle):
                    low = middle
                else:
                    high = middle
            threshold["threshold_current_a"] = low
            threshold["threshold_fraction_of_125a"] = abs(low) / M.IPEAK_P24_A
            threshold["deficit_vs_orbit_minimum_a"] = (
                result.monitor.phase_minimum_a[phase_index] - low
            )
            # Step-size convergence of the threshold itself.
            threshold["sub_step_convergence"] = []
            for sub_step_ps in (2.0, 1.0, 0.5):
                low_c, high_c = bound_a, 0.0
                for _ in range(32):
                    middle = 0.5 * (low_c + high_c)
                    if crosses(middle, sub_step_ps):
                        low_c = middle
                    else:
                        high_c = middle
                threshold["sub_step_convergence"].append(
                    {"sub_step_ps": sub_step_ps, "threshold_current_a": low_c}
                )
            # Does that threshold current cross inside the REAL 2.15 ns window?
            step = _entry_with_current(boundary, entry, phase_index, low, index)
            inside = probe_from(step)
            threshold["crosses_inside_commanded_dead_time"] = (
                inside.crossed_within_commanded_dead_time
            )
            threshold["crossing_time_after_window_start_s"] = (
                None
                if inside.sign_change_time_s is None
                else inside.sign_change_time_s - entry.time_s
            )
        else:
            threshold["threshold_current_a"] = None

        # ---- 5. A44-style state sensitivity --------------------------------
        # Measured on the FREE probe's own minimum signed `Vds`, because inside
        # the real 2.15 ns window almost nothing moves and the derivative would
        # degenerate to the trivial `d(blocking voltage)/d(coordinate) = -/+1`.
        sensitivity = []
        base_minimum = free.minimum_signed_vds_v
        probes = (
            ("VC1", "a1", 0.5),
            ("VC2", "a2", 0.5),
            ("VC3", "a3", 0.5),
            (f"iL{phase_index + 1}", f"L{phase_index + 1}", 1.0),
        )
        for label, target, delta in probes:
            state = entry.state.copy()
            state[index[target]] += delta
            probe_step = M._initial_step(
                boundary, state, entry.time_s, (False, False, False)
            )
            value = probe_from(probe_step).minimum_signed_vds_v
            sensitivity.append(
                {
                    "coordinate": label,
                    "perturbation": delta,
                    "d_minimum_signed_vds_v": value - base_minimum,
                    "derivative_per_unit": (value - base_minimum) / delta,
                }
            )

        verdict = next(
            item for item in result.turn_on if item.phase_index == phase_index
        )
        phases.append(
            {
                "phase": phase_index + 1,
                "high_side_branch": list(verdict.__dict__["high_side_branch"])
                if "high_side_branch" in verdict.__dict__
                else None,
                "window_start_s": entry.time_s,
                "window_end_s": entry.time_s + boundary.dead_time_s,
                "phase_current_at_window_entry_a": entry_current_a,
                "phase_current_minimum_over_orbit_a": result.monitor.phase_minimum_a[
                    phase_index
                ],
                "phase_current_maximum_over_orbit_a": result.monitor.phase_maximum_a[
                    phase_index
                ],
                "natural_zvs": verdict.natural_zvs,
                "sub_step_ladder": ladder,
                "richardson": richardson,
                "free_resonance_probe": {
                    "duration_ns": args.extended_window_ns,
                    "sub_step_ps": args.probe_sub_step_ps,
                    "initial_vds_v": free.initial_vds_v,
                    "minimum_signed_vds_v": free.minimum_signed_vds_v,
                    "minimum_abs_vds_v": free.minimum_abs_vds_v,
                    "delay_to_minimum_s": free.minimum_abs_vds_time_s - entry.time_s,
                    "crossed_zero": free.crossed_zero,
                    "crossed_within_commanded_dead_time": (
                        free.crossed_within_commanded_dead_time
                    ),
                    "sign_change_time_s": free.sign_change_time_s,
                    "downward_excursion_v": amplitude_v,
                    "sub_step_convergence": free_ladder,
                    "maximum_relative_backward_error": (
                        free.maximum_relative_backward_error
                    ),
                },
                "measured_node_capacitance_f": measured_capacitance_f,
                "measured_node_capacitance_step_ladder": capacitance_rows,
                "threshold_current": threshold,
                "state_sensitivity": sensitivity,
            }
        )

    payload = {
        "script": Path(__file__).name,
        "final_state": z.tolist(),
        "variable_names": list(names),
        "relative_residual_at_final_state": M.relative_residual(z, result.z_next),
        "natural_zvs_flags": list(result.natural_zvs_flags),
        "phases": phases,
        "safety": {
            "limit_a": M.PHASE_CURRENT_LIMIT_A,
            "maximum_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
            "within_limit": bool(
                result.monitor.maximum_abs_phase_current_a <= M.PHASE_CURRENT_LIMIT_A
            ),
        },
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {args.output}  ({payload['wall_clock_s']:.1f} s)\n")
    for entry in phases:
        print(f"phase {entry['phase']}:  natural ZVS = {entry['natural_zvs']}")
        print(
            f"  iL at window entry = {entry['phase_current_at_window_entry_a']:+.6f} A"
            f"   (orbit min {entry['phase_current_minimum_over_orbit_a']:+.4f} A,"
            f" max {entry['phase_current_maximum_over_orbit_a']:.4f} A)"
        )
        print("  sub-step ladder:  sub-step |  min|Vds| (V) |  Vds at window end (V) | crossed")
        for row in entry["sub_step_ladder"]:
            print(
                f"     {row['sub_step_ps']:>8} ps | {row['minimum_abs_vds_v']:>13.9f} |"
                f" {row['vds_at_commanded_window_end_v']:>21.9f} | {row['crossed_1mv']}"
            )
        print(
            f"     Richardson  | {entry['richardson']['minimum_abs_vds_v']:>13.9f} |"
            f" {entry['richardson']['vds_at_commanded_window_end_v']:>21.9f} |"
        )
        free_probe = entry["free_resonance_probe"]
        print(
            f"  free-resonance probe ({free_probe['duration_ns']} ns, dead-time mode held):"
            f" Vds start = {free_probe['initial_vds_v']:.6f} V ->"
            f" minimum {free_probe['minimum_signed_vds_v']:.6f} V at"
            f" {free_probe['delay_to_minimum_s']*1e9:.4f} ns;"
            f" crossed zero = {free_probe['crossed_zero']};"
            f" downward excursion = {free_probe['downward_excursion_v']:.6f} V"
        )
        print(
            "     sub-step convergence of the minimum: "
            + ", ".join(
                f"{row['sub_step_ps']} ps -> {row['minimum_signed_vds_v']:.6f} V"
                for row in free_probe["sub_step_convergence"]
            )
        )
        print(
            f"  measured participating capacitance = "
            f"{entry['measured_node_capacitance_f']*1e12:.4f} pF"
            "  (step ladder: "
            + ", ".join(
                f"{row['step_ps']} ps -> {row['capacitance_f']*1e12:.4f} pF"
                for row in entry["measured_node_capacitance_step_ladder"]
            )
            + ")"
        )
        threshold = entry["threshold_current"]
        if threshold.get("threshold_current_a") is None:
            print(
                f"  threshold current: NOT reachable within +/-"
                f"{M.PHASE_CURRENT_LIMIT_A} A"
            )
        else:
            print(
                f"  threshold current = {threshold['threshold_current_a']:.6f} A"
                f"  ({threshold['threshold_fraction_of_125a']*100:.4f}% of 125 A);"
                f" orbit minimum is {entry['phase_current_minimum_over_orbit_a']:+.4f} A,"
                f" deficit {threshold['deficit_vs_orbit_minimum_a']:.4f} A"
            )
            print(
                f"     crosses inside the commanded {boundary.dead_time_s*1e9:.2f} ns"
                f" dead time = {threshold['crosses_inside_commanded_dead_time']}"
                + (
                    ""
                    if threshold.get("crossing_time_after_window_start_s") is None
                    else f" (at {threshold['crossing_time_after_window_start_s']*1e9:.4f} ns)"
                )
            )
            print(
                "     threshold sub-step convergence: "
                + ", ".join(
                    f"{row['sub_step_ps']} ps -> {row['threshold_current_a']:.6f} A"
                    for row in threshold["sub_step_convergence"]
                )
            )
        print("  sensitivity of the free probe's minimum signed Vds (V per unit):")
        for row in entry["state_sensitivity"]:
            print(
                f"     d/d{row['coordinate']:<5} = {row['derivative_per_unit']:+.6f}"
            )
        print()
    print(
        f"safety at the final state: max |iL| = "
        f"{payload['safety']['maximum_abs_phase_current_a']:.4f} A"
        f" (limit {M.PHASE_CURRENT_LIMIT_A} A)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
