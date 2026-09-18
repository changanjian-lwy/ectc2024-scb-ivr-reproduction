"""A54 - assembles `results.json` from `bisection_search.json` and
`three_point_analysis.json` (both already written by the two run scripts in
this directory), and adds the explicit side-by-side comparison against A53's
own already-published GS61008T numbers (`BOUNDARY.md` Section 3 step 5).
Read-only with respect to every other experiment's files.

Run:  python3 build_results.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
A53_DIR = HERE.parent / "A53_lphase_zvs_load_tradeoff"

#: A53's own already-published GS61008T numbers (RESULTS.md Sections 0/2/4),
#: quoted verbatim, not re-derived -- read-only reference values for the
#: side-by-side comparison BOUNDARY.md Section 3 step 5 asks for.
A53_GS61008T_REFERENCE = {
    "device": "GS61008T",
    "ron_ohm": 0.007,
    "ch_total_f": 385e-12,
    "cl_total_f": 770e-12,
    "critical_lphase_h": 1.19625e-9,
    "critical_reduction_from_nominal_pct": 18.44,
    "margin_lphase_h": 1.07663e-9,
    "margin_reduction_from_nominal_pct": 26.59,
    "conduction_loss_w_nominal": 113.09,
    "conduction_loss_w_critical": 153.61,
    "conduction_loss_w_margin": 171.63,
    "capacitive_switching_loss_eliminated_w": 2.087,
    "conduction_loss_increase_critical_w": 40.513,
    "conduction_loss_increase_margin_w": 58.540,
    "net_watts_critical": -38.426,
    "net_watts_margin": -56.453,
    "safety_maximum_a": 150.13,
}


def main() -> int:
    bisection = json.loads((HERE / "bisection_search.json").read_text())
    three_point = json.loads((HERE / "three_point_analysis.json").read_text())

    points = three_point["points"]
    tradeoff = three_point["tradeoff"]

    summary = {
        "script": Path(__file__).name,
        "classification": "SENSITIVITY_ONLY",
        "not_a_p24_reproduction": True,
        "device": "EPC2067",
        "ron_ohm": three_point["ron_ohm_epc2067"],
        "ch_total_f": 3720e-12,
        "cl_total_f": 5580e-12,
        "nhs": 2,
        "nls": 3,
        "module_power_w": bisection["module_power_w"],
        "search": {
            "outcome": bisection["outcome"],
            "nominal_lphase_h": bisection["nominal_lphase_h"],
            "nominal_hard_switch_confirmed": not bisection["nominal"]["all_four_zvs"],
            "critical_lphase_h": bisection.get("critical_lphase_h"),
            "critical_lphase_bracket_h": bisection.get("critical_lphase_bracket_h"),
            "reduction_from_nominal_pct": bisection.get("reduction_from_nominal_pct"),
            "margin_lphase_h": bisection.get("margin_lphase_h"),
            "margin_reduction_from_nominal_pct": bisection.get("margin_reduction_from_nominal_pct"),
            "bracket_was_widened_past_proposed_start": bisection.get(
                "bracket_was_widened_past_proposed_start"
            ),
            "floor_lphase_h": bisection.get("floor_lphase_h"),
            "ladder_step_count": len(bisection.get("ladder", [])),
            "bisection_step_count": len(bisection.get("bisection", [])),
            "safety_maximum_over_whole_search_a": bisection.get("safety_maximum_over_whole_search_a"),
            "safety_limit_a": bisection.get("safety_limit_a"),
        },
        "three_point_table": {
            name: {
                "phase_inductance_h": points[name]["phase_inductance_h"],
                "converged": points[name]["newton"]["converged"],
                "final_relative_residual": points[name]["newton"]["final_relative_residual"],
                "natural_zvs_flags": points[name]["natural_zvs_flags"],
                "all_four_zvs": points[name]["all_four_zvs"],
                "sub_step_ladder_consistent": points[name]["sub_step_ladder"][
                    "identical_across_all_rungs"
                ],
                "peak_currents_a": [row["peak_a"] for row in points[name]["per_phase_currents"]],
                "rms_currents_a": [row["rms_a"] for row in points[name]["per_phase_currents"]],
                "conduction_loss_w_total": points[name]["conduction_loss_w_total"],
                "maximum_abs_phase_current_a": points[name]["maximum_abs_phase_current_a"],
            }
            for name in ("nominal", "critical", "margin")
        },
        "capacitive_switching_loss_at_nominal_w": three_point["capacitive_switching_loss_at_nominal"][
            "total_w"
        ],
        "tradeoff": tradeoff,
        "safety": {
            "limit_a": three_point["safety_limit_a"],
            "maximum_a_three_point_analysis": three_point["safety_maximum_a"],
            "maximum_a_whole_bisection_search": bisection.get("safety_maximum_over_whole_search_a"),
            "within_limit": three_point["safety_within_limit"]
            and bool(
                (bisection.get("safety_maximum_over_whole_search_a") or 0)
                <= three_point["safety_limit_a"]
            ),
        },
    }

    # --- BOUNDARY.md Section 3 step 5: explicit side-by-side vs A53's own
    # already-published GS61008T numbers. ---
    a53 = A53_GS61008T_REFERENCE
    comparison = {
        "gs61008t_a53_reference": a53,
        "epc2067_a54_result": {
            "critical_lphase_h": bisection.get("critical_lphase_h"),
            "critical_reduction_from_nominal_pct": bisection.get("reduction_from_nominal_pct"),
            "margin_lphase_h": bisection.get("margin_lphase_h"),
            "margin_reduction_from_nominal_pct": bisection.get("margin_reduction_from_nominal_pct"),
            "conduction_loss_w_nominal": points["nominal"]["conduction_loss_w_total"],
            "conduction_loss_w_critical": points["critical"]["conduction_loss_w_total"],
            "conduction_loss_w_margin": points["margin"]["conduction_loss_w_total"],
            "capacitive_switching_loss_eliminated_w": tradeoff["capacitive_switching_loss_eliminated_w"],
            "conduction_loss_increase_critical_w": tradeoff["conduction_loss_increase_critical_w"],
            "conduction_loss_increase_margin_w": tradeoff["conduction_loss_increase_margin_w"],
            "net_watts_critical": tradeoff["net_watts_critical"],
            "net_watts_margin": tradeoff["net_watts_margin"],
            "safety_maximum_a": bisection.get("safety_maximum_over_whole_search_a"),
        },
    }
    if bisection.get("critical_lphase_h") is not None:
        comparison["net_watts_critical_delta_epc2067_minus_gs61008t"] = (
            tradeoff["net_watts_critical"] - a53["net_watts_critical"]
        )
        comparison["net_watts_margin_delta_epc2067_minus_gs61008t"] = (
            tradeoff["net_watts_margin"] - a53["net_watts_margin"]
        )
        comparison["epc2067_less_bad_at_critical"] = (
            tradeoff["net_watts_critical"] > a53["net_watts_critical"]
        )
        comparison["epc2067_less_bad_at_margin"] = (
            tradeoff["net_watts_margin"] > a53["net_watts_margin"]
        )
    summary["comparison_vs_a53_gs61008t"] = comparison

    verdict_bits = []
    if bisection["outcome"] != "CRITICAL_LPHASE_FOUND":
        verdict_bits.append(
            "no critical LPHASE with all-four ZVS was found within the searched bracket "
            f"(floor {bisection.get('floor_lphase_h')} H) -- BOUNDARY.md Section 5's third "
            "named outcome."
        )
    elif tradeoff["critical_all_four_zvs"] and tradeoff["net_watts_critical"] > 0:
        verdict_bits.append(
            "at the critical LPHASE, the capacitive switching-loss eliminated exceeds the "
            "conduction-loss increase under this partial loss model (net Watts positive) -- "
            "BOUNDARY.md Section 5's first named outcome."
        )
    elif tradeoff["critical_all_four_zvs"]:
        if tradeoff["net_watts_critical"] > a53["net_watts_critical"]:
            verdict_bits.append(
                "net Watts is still negative, but LESS negative than A53's own GS61008T result -- "
                "the joint EPC2067+LPHASE change is a genuine (partial) improvement, "
                "BOUNDARY.md Section 5's first named outcome (the 'less bad' case)."
            )
        else:
            verdict_bits.append(
                "net Watts is negative AND worse than (or equal to) A53's own GS61008T result -- "
                "EPC2067, despite its much lower resistance, is NOT a better choice for this "
                "specific tradeoff -- BOUNDARY.md Section 5's second named outcome."
            )
    summary["plain_verdict"] = " ".join(verdict_bits)

    (HERE / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote results.json")
    print(json.dumps(summary["three_point_table"], indent=2))
    print("\ntradeoff:", json.dumps(tradeoff, indent=2))
    print("\ncomparison vs A53:", json.dumps(comparison, indent=2))
    print("\nverdict:", summary["plain_verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
