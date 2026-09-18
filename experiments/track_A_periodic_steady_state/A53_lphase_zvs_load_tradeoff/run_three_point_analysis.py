"""A53 step 4/5 -- the three-point comparison (nominal / critical / margin `L`)
and the net Watts tradeoff, `BOUNDARY.md` Section 2 steps 4-5.

Reads `bisection_search.json` and `key_states.json` (both written by
`run_bisection.py`, read-only from here) for the three `LPHASE` values and
their own already-converged fixed points, so this script warm-starts every
solve instead of re-deriving from A37's raw seed (unsafe near the critical/
margin region, per the bisection script's own diagnostic probe).

At each of the three points this computes, per `BOUNDARY.md` Section 2
step 4:

* convergence/residual (Newton, re-polished from the saved seed, plus a
  damped-Picard cross-check, mirroring A51's own practice);
* per-phase natural-ZVS verdicts, checked over a `{5, 2, 1, 0.5} ps`
  sub-step ladder (A50/A51's own established discipline) rather than trusted
  at a single sub-step;
* peak and RMS phase currents, the RMS integrated from the actual solved
  periodic waveform via `a53_solve.rms_and_peak_currents` (a genuine
  time integral, not an estimate from peak/average);
* a conduction-loss estimate, `sum_phase I_rms^2 * 0.007` (`Ron=7 mOhm`
  uniform, `BOUNDARY.md` Section 2.4);
* at the NOMINAL point only, a capacitive switching-loss estimate,
  `sum_phase 0.5 * C_phase * Vds_at_forced_turn_on^2 * f_sw`, using A51's
  own ALREADY-PUBLISHED `final_verification.json` measured capacitances and
  hard-switch residual voltages (read-only) -- not re-derived, per
  `BOUNDARY.md` Section 2 step 4's own instruction. `measure_node_
  capacitance_f` is also re-run at this experiment's own nominal `z*` purely
  as a consistency check against A51's published numbers (reported, not
  substituted).

Finally reports the net Watts comparison (Section 2 step 5): the conduction-
loss increase from nominal to critical/margin against the capacitive
switching-loss eliminated by reaching ZVS, plainly, without forcing a single
confident number the estimate cannot support (Section 5).

Run:  python3 run_three_point_analysis.py --output three_point_analysis.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import a53_boundary as B
import a53_solve as S
import a51_period_map as M

COARSE_STEP_S = 0.0625e-9
RMS_SUB_STEP_S = 1e-12  # fine sub-step for the RMS/peak integration itself
SUB_STEP_LADDER_S = (5e-12, 2e-12, 1e-12, 0.5e-12)
RON_OHM = 0.007  # BOUNDARY.md Section 2.4 -- uniform, matching A51's convention
A51_DIR = Path(__file__).resolve().parent.parent / "A51_four_phase_joint_zvs_solve"


def sub_step_ladder_check(boundary, z_star: np.ndarray, *, label: str) -> dict:
    rungs = []
    for sub_step_s in SUB_STEP_LADDER_S:
        result = M.evaluate_period_map(
            boundary, z_star, coarse_step_s=COARSE_STEP_S, sub_step_s=sub_step_s
        )
        rungs.append(
            {
                "sub_step_s": sub_step_s,
                "natural_zvs_flags": list(result.natural_zvs_flags),
                "minimum_abs_vds_v": [v.minimum_abs_vds_v for v in result.turn_on],
                "maximum_abs_phase_current_a": result.monitor.maximum_abs_phase_current_a,
            }
        )
    all_flags = [tuple(row["natural_zvs_flags"]) for row in rungs]
    converged_flags = len(set(all_flags)) == 1
    return {
        "label": label,
        "rungs": rungs,
        "identical_across_all_rungs": converged_flags,
        "finest_natural_zvs_flags": rungs[-1]["natural_zvs_flags"],
    }


def analyze_point(boundary, z_seed: np.ndarray, *, label: str, safety_log: list[dict]) -> dict:
    # Re-polish from the saved seed (should already be very close; a few
    # Newton iterations here just confirm/tighten, matching A51's own
    # single-point rigor rather than the faster search settings).
    polished = S.solve_fixed_point(
        boundary,
        z_seed,
        coarse_step_s=COARSE_STEP_S,
        sub_step_s=5e-12,
        max_iterations=30,
        picard_iterations=25,
        picard_damping=0.5,
    )
    z_star = polished["z_star"]
    safety_log.append(
        {
            "label": label,
            "maximum_abs_phase_current_a": polished["safety"]["maximum_abs_phase_current_a"],
        }
    )

    ladder = sub_step_ladder_check(boundary, z_star, label=label)

    rms_peak = S.rms_and_peak_currents(
        boundary, z_star, coarse_step_s=COARSE_STEP_S, sub_step_s=RMS_SUB_STEP_S
    )
    per_phase = rms_peak["per_phase"]
    conduction_loss_w_per_phase = [RON_OHM * row["rms_a"] ** 2 for row in per_phase]
    conduction_loss_w_total = float(sum(conduction_loss_w_per_phase))

    return {
        "label": label,
        "phase_inductance_h": boundary.phase_inductance_h,
        "module_power_w": boundary.module_power_w,
        "newton": {
            "converged": polished["converged"],
            "final_relative_residual": polished["final_relative_residual"],
            "iterations_used": polished["iterations_used"],
        },
        "picard": (
            {
                "damping": polished["picard"]["damping"],
                "iterations": polished["picard"]["iterations"],
                "final_relative_residual": polished["picard"]["history"][-1]["relative_residual"],
                "final_natural_zvs_flags": polished["picard"]["history"][-1]["natural_zvs_flags"],
            }
            if polished["picard"]
            else None
        ),
        "sub_step_ladder": ladder,
        "natural_zvs_flags": ladder["finest_natural_zvs_flags"],
        "all_four_zvs": all(ladder["finest_natural_zvs_flags"]),
        "per_phase_currents": per_phase,
        "conduction_loss_w_per_phase": conduction_loss_w_per_phase,
        "conduction_loss_w_total": conduction_loss_w_total,
        "average_output_v": polished["final_orbit_metrics"]["average_output_v"],
        "average_load_power_w": polished["final_orbit_metrics"]["average_load_power_w"],
        "maximum_abs_phase_current_a": polished["safety"]["maximum_abs_phase_current_a"],
        "z_star": z_star.tolist(),
    }


def capacitive_switching_loss_at_nominal(boundary, z_star_nominal: np.ndarray) -> dict:
    """`BOUNDARY.md` Section 2 step 4's capacitive switching-loss estimate.

    Uses A51's own ALREADY-PUBLISHED `final_verification.json` (read-only)
    for both the measured node capacitance and the hard-switch residual
    voltage at the boundary's own 250 W nominal-L point -- not re-derived.
    `measure_node_capacitance_f` is re-run here at THIS run's own nominal
    `z*` purely as a consistency check on the reused numbers.
    """
    published = json.loads((A51_DIR / "final_verification.json").read_text())
    switching_frequency_hz = 5e6  # A51's own boundary.switching_frequency_hz
    rows = []
    for phase_row in published["phases"]:
        phase = phase_row["phase"]
        capacitance_f = phase_row["measured_node_capacitance_f"]
        vds_v = phase_row["richardson"]["vds_at_commanded_window_end_v"]
        loss_w = 0.5 * capacitance_f * vds_v**2 * switching_frequency_hz
        rows.append(
            {
                "phase": phase,
                "measured_capacitance_f_a51_published": capacitance_f,
                "vds_at_forced_turn_on_v_a51_published": vds_v,
                "capacitive_switching_loss_w": loss_w,
            }
        )
    total_w = float(sum(row["capacitive_switching_loss_w"] for row in rows))

    # Consistency check: re-measure capacitance at THIS run's own nominal z*,
    # using each phase's own turn-on-window ENTRY step (`result.turn_on_entry`,
    # populated by `evaluate_period_map` right before it resolves that dead-
    # time window) -- the same state A51's own `run_final_verification.py`
    # feeds to `measure_node_capacitance_f`. Perturbing at the raw period-
    # start state instead (a different, non-dead-time switch mode) measures a
    # different node altogether, which was tried first and gave nonsense
    # (~500 pF vs ~1500 pF) -- recorded here as a caveat, not silently fixed
    # away.
    period_result = M.evaluate_period_map(boundary, z_star_nominal, coarse_step_s=0.0625e-9, sub_step_s=5e-12)
    cross_check = []
    for phase_index in range(4):
        entry_step = period_result.turn_on_entry[phase_index]
        measured = M.measure_node_capacitance_f(
            boundary, entry_step, phase_index=phase_index, step_s=0.25e-12
        )
        cross_check.append(
            {
                "phase": phase_index + 1,
                "measured_here_f": measured,
                "a51_published_f": rows[phase_index]["measured_capacitance_f_a51_published"],
                "relative_difference": (
                    abs(measured - rows[phase_index]["measured_capacitance_f_a51_published"])
                    / rows[phase_index]["measured_capacitance_f_a51_published"]
                ),
            }
        )

    return {
        "source": "A51_four_phase_joint_zvs_solve/final_verification.json (read-only, already published)",
        "switching_frequency_hz": switching_frequency_hz,
        "per_phase": rows,
        "total_w": total_w,
        "capacitance_cross_check_at_this_runs_own_nominal_z_star": cross_check,
        "caveat": (
            "node-capacitance charge/discharge energy only -- NOT a complete "
            "device switching-loss model (no gate-drive loss, no reverse "
            "recovery); BOUNDARY.md Section 5"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="three_point_analysis.json")
    parser.add_argument("--bisection-json", default="bisection_search.json")
    parser.add_argument("--key-states-json", default="key_states.json")
    args = parser.parse_args()

    started = time.time()
    bisection = json.loads(Path(args.bisection_json).read_text())
    key_states = json.loads(Path(args.key_states_json).read_text())
    module_power_w = bisection["module_power_w"]

    safety_log: list[dict] = []
    points = {}
    for name in ("nominal", "critical", "margin"):
        entry = key_states[name]
        boundary = B.build_boundary(
            phase_inductance_h=entry["phase_inductance_h"], module_power_w=module_power_w
        )
        seed = np.array(entry["z_star"], dtype=float)
        print(f"\n=== {name}: L={entry['phase_inductance_h']*1e9:.5f} nH ===")
        points[name] = analyze_point(boundary, seed, label=name, safety_log=safety_log)
        print(
            f"  converged={points[name]['newton']['converged']}  "
            f"residual={points[name]['newton']['final_relative_residual']:.3e}  "
            f"zvs={points[name]['natural_zvs_flags']}  "
            f"ladder_consistent={points[name]['sub_step_ladder']['identical_across_all_rungs']}"
        )
        for row in points[name]["per_phase_currents"]:
            print(
                f"    phase {row['phase']}: peak={row['peak_a']:.3f} A  rms={row['rms_a']:.3f} A"
            )
        print(f"  conduction loss total = {points[name]['conduction_loss_w_total']:.4f} W")

    nominal_boundary = B.build_boundary(
        phase_inductance_h=key_states["nominal"]["phase_inductance_h"], module_power_w=module_power_w
    )
    switching_loss = capacitive_switching_loss_at_nominal(
        nominal_boundary, np.array(points["nominal"]["z_star"], dtype=float)
    )
    print(f"\ncapacitive switching loss @ nominal L (hard-switching) = {switching_loss['total_w']:.4f} W")

    conduction_increase_critical_w = (
        points["critical"]["conduction_loss_w_total"] - points["nominal"]["conduction_loss_w_total"]
    )
    conduction_increase_margin_w = (
        points["margin"]["conduction_loss_w_total"] - points["nominal"]["conduction_loss_w_total"]
    )
    net_watts_critical = switching_loss["total_w"] - conduction_increase_critical_w
    net_watts_margin = switching_loss["total_w"] - conduction_increase_margin_w

    tradeoff = {
        "capacitive_switching_loss_eliminated_w": switching_loss["total_w"],
        "conduction_loss_increase_critical_w": conduction_increase_critical_w,
        "conduction_loss_increase_margin_w": conduction_increase_margin_w,
        "net_watts_critical": net_watts_critical,
        "net_watts_margin": net_watts_margin,
        "critical_all_four_zvs": points["critical"]["all_four_zvs"],
        "margin_all_four_zvs": points["margin"]["all_four_zvs"],
    }
    print("\n--- net Watts comparison ---")
    print(f"  capacitive switching loss eliminated (nominal, hard-switch) : {switching_loss['total_w']:.4f} W")
    print(f"  conduction loss increase, nominal->critical                : {conduction_increase_critical_w:.4f} W")
    print(f"  conduction loss increase, nominal->margin                  : {conduction_increase_margin_w:.4f} W")
    print(f"  net Watts (critical) = switching_saved - conduction_added  : {net_watts_critical:+.4f} W")
    print(f"  net Watts (margin)   = switching_saved - conduction_added  : {net_watts_margin:+.4f} W")

    safety_max = max(row["maximum_abs_phase_current_a"] for row in safety_log)
    payload = {
        "script": Path(__file__).name,
        "classification": "SENSITIVITY_ONLY",
        "module_power_w": module_power_w,
        "points": points,
        "capacitive_switching_loss_at_nominal": switching_loss,
        "tradeoff": tradeoff,
        "safety_log": safety_log,
        "safety_limit_a": M.PHASE_CURRENT_LIMIT_A,
        "safety_maximum_a": safety_max,
        "safety_within_limit": bool(safety_max <= M.PHASE_CURRENT_LIMIT_A),
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {args.output}  ({payload['wall_clock_s']:.1f} s)")
    print(f"safety: max |iL| = {safety_max:.4f} A (limit {M.PHASE_CURRENT_LIMIT_A} A)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
