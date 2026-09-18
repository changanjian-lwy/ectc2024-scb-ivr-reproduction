"""A53 - assembles `results.json` from `bisection_search.json` and
`three_point_analysis.json` (both already written by the two run scripts in
this directory). Read-only with respect to every other experiment's files.

Run:  python3 build_results.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    bisection = json.loads((HERE / "bisection_search.json").read_text())
    three_point = json.loads((HERE / "three_point_analysis.json").read_text())

    points = three_point["points"]
    tradeoff = three_point["tradeoff"]

    summary = {
        "script": Path(__file__).name,
        "classification": "SENSITIVITY_ONLY",
        "not_a_p24_reproduction": True,
        "module_power_w": bisection["module_power_w"],
        "search": {
            "outcome": bisection["outcome"],
            "nominal_lphase_h": bisection["nominal_lphase_h"],
            "critical_lphase_h": bisection.get("critical_lphase_h"),
            "critical_lphase_bracket_h": bisection.get("critical_lphase_bracket_h"),
            "reduction_from_nominal_pct": bisection.get("reduction_from_nominal_pct"),
            "margin_lphase_h": bisection.get("margin_lphase_h"),
            "margin_reduction_from_nominal_pct": bisection.get("margin_reduction_from_nominal_pct"),
            "bracket_was_widened_past_proposed_start": bisection.get(
                "bracket_was_widened_past_proposed_start"
            ),
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

    verdict_bits = []
    if tradeoff["critical_all_four_zvs"] and tradeoff["net_watts_critical"] > 0:
        verdict_bits.append(
            "at the critical LPHASE, the capacitive switching-loss eliminated exceeds the "
            "conduction-loss increase under this partial loss model (net Watts positive)"
        )
    elif tradeoff["critical_all_four_zvs"] and tradeoff["net_watts_critical"] <= 0:
        verdict_bits.append(
            "at the critical LPHASE, the conduction-loss increase meets or exceeds the "
            "capacitive switching-loss eliminated under this partial loss model (net Watts "
            "non-positive) -- achieving ZVS this way is not shown to be a net efficiency win"
        )
    else:
        verdict_bits.append("no critical LPHASE with all-four ZVS was confirmed at report time")
    summary["plain_verdict"] = " ".join(verdict_bits)

    (HERE / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote results.json")
    print(json.dumps(summary["three_point_table"], indent=2))
    print("\ntradeoff:", json.dumps(tradeoff, indent=2))
    print("\nverdict:", summary["plain_verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
