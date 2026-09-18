"""A54 step 4/5 -- the three-point comparison (nominal / critical / margin `L`)
and the net Watts tradeoff, under EPC2067's own device parameters.
`BOUNDARY.md` Section 3 steps 4-5.

Structurally identical to `A53`'s own `run_three_point_analysis.py` (a NEW
file in this experiment's own directory, not an edit to A53's file), with
ONE material difference beyond the device swap itself: A53 could reuse A51's
own ALREADY-PUBLISHED `final_verification.json` measured capacitance and
hard-switch residual voltage for its capacitive switching-loss estimate,
because A53 kept GS61008T's own device parameters unchanged (only `LPHASE`
moved) -- that published file's numbers are GS61008T-specific (`385/770 pF`)
and DO NOT apply to EPC2067's `3720/5580 pF`. `BOUNDARY.md` Section 3 step 4
explicitly says to use "EPC2067's own measured participating capacitance and
hard-switch residual voltages" -- so this script measures BOTH directly at
THIS run's own nominal (hard-switching) fixed point, via `measure_node_
capacitance_f` fed the correct turn-on-window ENTRY state (`result.turn_on_
entry[phase]`, the same state A53 found necessary -- the raw period-start
state sits in a different switch-mode branch and gives nonsense) and the
solver's own `hard_switch_residual_v` verdict from that same evaluation, no
external published reference file involved.

At each of the three points this computes, per `BOUNDARY.md` Section 3 step 4:
* convergence/residual (Newton, re-polished from the saved seed, plus a
  damped-Picard cross-check);
* per-phase natural-ZVS verdicts, checked over a `{5, 2, 1, 0.5} ps` sub-step
  ladder;
* peak and RMS phase currents (RMS integrated from the actual solved
  periodic waveform via `a53_solve.rms_and_peak_currents`, imported
  read-only from A53's own directory -- generic, device-agnostic);
* a conduction-loss estimate, `sum_phase I_rms^2 * 0.00155` (EPC2067's own
  raw single-device `Ron=1.55 mOhm`, uniform, NOT population-divided --
  `BOUNDARY.md` Section 2's explicit instruction to mirror A51/A53's own
  simplification);
* at the NOMINAL point only, a capacitive switching-loss estimate,
  `sum_phase 0.5 * C_phase * Vds_at_forced_turn_on^2 * f_sw`, using EPC2067's
  own measured participating capacitance and hard-switch residual voltage.

Finally reports the net Watts comparison (Section 3 step 5): the conduction-
loss increase from nominal to critical/margin against the capacitive
switching-loss eliminated by reaching ZVS.

Run:  python3 run_three_point_analysis.py --output three_point_analysis.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A53_DIR = HERE.parent / "A53_lphase_zvs_load_tradeoff"
if str(A53_DIR) not in sys.path:
    sys.path.insert(0, str(A53_DIR))

import a54_boundary as B  # noqa: E402
import a53_solve as S  # noqa: E402  (A53's own generic, device-agnostic solve machinery, read-only)
import a51_period_map as M  # noqa: E402

COARSE_STEP_S = 0.0625e-9
RMS_SUB_STEP_S = 1e-12  # fine sub-step for the RMS/peak integration itself
SUB_STEP_LADDER_S = (5e-12, 2e-12, 1e-12, 0.5e-12)
RON_OHM = 1.55e-3  # BOUNDARY.md Section 2 -- EPC2067's own raw single-device Ron, uniform
SWITCHING_FREQUENCY_HZ = 5e6  # A51's own boundary.switching_frequency_hz


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
    """`BOUNDARY.md` Section 3 step 4's capacitive switching-loss estimate,
    using EPC2067's OWN measured participating capacitance and hard-switch
    residual voltage -- measured directly at THIS run's own nominal `z*`,
    NOT reused from A51's own published (GS61008T-specific) numbers, per the
    module docstring's own explanation of why A53's exact reuse pattern does
    not carry over unchanged.
    """
    period_result = M.evaluate_period_map(
        boundary, z_star_nominal, coarse_step_s=COARSE_STEP_S, sub_step_s=5e-12
    )
    rows = []
    for phase_index in range(4):
        entry_step = period_result.turn_on_entry[phase_index]
        capacitance_f = M.measure_node_capacitance_f(
            boundary, entry_step, phase_index=phase_index, step_s=0.25e-12
        )
        verdict = period_result.turn_on[phase_index]
        assert verdict.phase_index == phase_index
        if verdict.natural_zvs:
            vds_v = 0.0
        else:
            vds_v = verdict.hard_switch_residual_v
        loss_w = 0.5 * capacitance_f * vds_v**2 * SWITCHING_FREQUENCY_HZ
        rows.append(
            {
                "phase": phase_index + 1,
                "natural_zvs": verdict.natural_zvs,
                "measured_capacitance_f": capacitance_f,
                "vds_at_forced_turn_on_v": vds_v,
                "capacitive_switching_loss_w": loss_w,
            }
        )
    total_w = float(sum(row["capacitive_switching_loss_w"] for row in rows))
    return {
        "source": (
            "measured directly at this run's own EPC2067 nominal z* via "
            "M.measure_node_capacitance_f (A51's own function, read-only), "
            "fed each phase's own turn-on-window ENTRY state -- NOT reused "
            "from A51's own published (GS61008T-specific) final_verification.json"
        ),
        "switching_frequency_hz": SWITCHING_FREQUENCY_HZ,
        "per_phase": rows,
        "total_w": total_w,
        "caveat": (
            "node-capacitance charge/discharge energy only -- NOT a complete "
            "device switching-loss model (no gate-drive loss, no reverse "
            "recovery); BOUNDARY.md Section 6. Also inherits the EPC2067 "
            "Co(tr) 0-20V-vs-~12V-actual extrapolation caveat, BOUNDARY.md "
            "Section 1."
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
        "ron_ohm_epc2067": RON_OHM,
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
