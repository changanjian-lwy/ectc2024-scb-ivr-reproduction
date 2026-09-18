"""A51 robustness sweeps - is the A51 verdict an artifact of any single choice?

The main search (`run_fixed_point_search.py`) fixes four things that were
engineering choices rather than paper values, so each is varied here and the
whole fixed-point solve is redone from the same A37 seed:

1. **Dead time.**  `BOUNDARY.md` Section 4.2 inherits `2.15 ns` from A48's own
   single-phase bracket and says explicitly to "report plainly if a different
   dead time turns out to be needed for the coupled case".  So the solve is
   repeated at `1.0 / 2.15 / 5.0 / 10.0 ns`.
2. **Sub-step.**  The search runs at `5 ps`; it is redone at `20 ps` and `1 ps`
   to show the recovered `z*` and its ZVS verdicts do not depend on that.
3. **Divider-tap voltages.**  The taps are pinned (they are the map's own
   three-dimensional identity subspace); the solve is redone with them `1 V`
   lower each, which strictly reverse-biases every precharge diode, to confirm
   the stage part of `z*` is unaffected.
4. **Switch on-resistance.**  The framework carries a single global value and
   the search uses its `1 uOhm` default (A50's own validated configuration).
   A42's own GS61008T numbers are `RHS = 7 mOhm` / `RLS = 3.5 mOhm`, so the
   solve is redone at both, which is the closest this framework can come to the
   device value.

Each sweep is a full, independent re-run of `run_fixed_point_search.py` as a
subprocess, so every row is reproducible on its own from the printed command.

Run:  python3 run_robustness_sweeps.py --output robustness_sweeps.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEARCH = HERE / "run_fixed_point_search.py"
STAGE_VARIABLES = (
    "src", "src_r", "vin", "a1", "a2", "a3", "x1", "x2", "x3", "x4",
    "out", "LPAR_IN", "L1", "L2", "L3", "L4", "I_VSTEP",
)


def run_case(label: str, extra: list[str], scratch: Path) -> dict:
    output = scratch / f"sweep_{label}.json"
    command = [
        sys.executable,
        str(SEARCH),
        "--output",
        str(output),
        "--picard-iterations",
        "0",
        *extra,
    ]
    started = time.time()
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        return {
            "label": label,
            "command": command,
            "failed": True,
            "stderr_tail": completed.stderr[-4000:],
        }
    payload = json.loads(output.read_text())
    names = payload["variable_names"]
    z = np.array(payload["newton"]["final_state"], dtype=float)
    verdicts = payload["newton"]["final_verdicts"]["turn_on"]
    return {
        "label": label,
        "command": command,
        "failed": False,
        "wall_clock_s": time.time() - started,
        "dead_time_s": payload["boundary"]["dead_time_s"],
        "sub_step_s": payload["numerics"]["sub_step_s"],
        "switch_on_resistance_ohm": payload["boundary"]["switch_on_resistance_ohm"],
        "converged": payload["newton"]["converged"],
        "iterations_used": payload["newton"]["iterations_used"],
        "final_relative_residual": payload["newton"]["final_relative_residual"],
        "natural_zvs_flags": payload["newton"]["final_natural_zvs_flags"],
        "minimum_abs_vds_v": [item["minimum_abs_vds_v"] for item in verdicts],
        "hard_switch_residual_v": [item["hard_switch_residual_v"] for item in verdicts],
        "phase_current_minima_a": payload["newton"]["final_orbit_metrics"][
            "minimum_phase_currents_a"
        ],
        "phase_current_maxima_a": payload["newton"]["final_orbit_metrics"][
            "maximum_phase_currents_a"
        ],
        "average_output_v": payload["newton"]["final_orbit_metrics"]["average_output_v"],
        "flying_capacitor_v": payload["newton"]["final_orbit_metrics"][
            "flying_capacitor_v_at_z_star"
        ],
        "maximum_abs_phase_current_a": payload["safety"]["maximum_abs_phase_current_a"],
        "safety_within_limit": payload["safety"]["within_limit"],
        "stage_state": {
            name: float(z[names.index(name)]) for name in STAGE_VARIABLES
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="robustness_sweeps.json")
    parser.add_argument("--scratch", default="_sweeps")
    args = parser.parse_args()
    scratch = Path(args.scratch)
    scratch.mkdir(exist_ok=True)
    started = time.time()

    cases: list[tuple[str, list[str]]] = [
        ("deadtime_1p00ns", ["--dead-time-ns", "1.0"]),
        ("deadtime_2p15ns", ["--dead-time-ns", "2.15"]),
        ("deadtime_5p00ns", ["--dead-time-ns", "5.0"]),
        ("deadtime_10p0ns", ["--dead-time-ns", "10.0"]),
        ("substep_20ps", ["--sub-step-ps", "20"]),
        ("substep_1ps", ["--sub-step-ps", "1"]),
        ("taps_lowered_1v", ["--tap-voltages", "35,23,11"]),
        ("rds_3p5mohm", ["--switch-on-resistance-ohm", "3.5e-3"]),
        ("rds_7mohm", ["--switch-on-resistance-ohm", "7e-3"]),
    ]
    rows = [run_case(label, extra, scratch) for label, extra in cases]

    reference = next(row for row in rows if row["label"] == "deadtime_2p15ns")
    for row in rows:
        if row["failed"]:
            continue
        row["stage_state_inf_difference_from_reference"] = max(
            abs(row["stage_state"][name] - reference["stage_state"][name])
            for name in STAGE_VARIABLES
        )

    payload = {
        "script": Path(__file__).name,
        "reference_case": "deadtime_2p15ns",
        "rows": rows,
        "any_natural_zvs_anywhere": bool(
            any(any(row.get("natural_zvs_flags") or []) for row in rows)
        ),
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {args.output}  ({payload['wall_clock_s']:.1f} s)\n")
    header = (
        f"{'case':<18} {'conv':<5} {'residual':>11} {'ZVS 1/2/3/4':<24} "
        f"{'min|Vds| per phase (V)':<44} {'iL minima (A)':<40} {'Vout(V)':>9}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        if row["failed"]:
            print(f"{row['label']:<18} FAILED  {row['stderr_tail'][-200:]}")
            continue
        print(
            f"{row['label']:<18} {str(row['converged']):<5} "
            f"{row['final_relative_residual']:>11.3e} "
            f"{str([int(v) for v in row['natural_zvs_flags']]):<24} "
            f"{str([round(v, 5) for v in row['minimum_abs_vds_v']]):<44} "
            f"{str([round(v, 4) for v in row['phase_current_minima_a']]):<40} "
            f"{row['average_output_v']:>9.5f}"
        )
    print(
        f"\nany natural ZVS at any fixed point in any sweep: "
        f"{payload['any_natural_zvs_anywhere']}"
    )
    print("\nstage-state inf difference from the reference case:")
    for row in rows:
        if not row["failed"]:
            print(
                f"  {row['label']:<18} "
                f"{row['stage_state_inf_difference_from_reference']:.6e}"
            )
    print("\nsafety:")
    for row in rows:
        if not row["failed"]:
            print(
                f"  {row['label']:<18} max |iL| = "
                f"{row['maximum_abs_phase_current_a']:.4f} A   within limit = "
                f"{row['safety_within_limit']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
