"""A51 diagnostic - WHERE does the four-phase joint ZVS state start to exist?

`BOUNDARY.md` Section 6's second bullet asks, for a fixed point whose phases
hard-switch, which state coordinates the failure is most sensitive to, "if that
can be characterized cheaply".  The per-phase work in `run_final_verification.py`
answers that locally.  This script answers the global version, because the fast
solver makes it cheap.

The mechanism the final state exhibits is a ripple/load balance, not a device
limitation.  Over one period the phase current ramps from its own minimum
`i_min` up to `i_peak` and back, so

    i_avg = (i_min + i_peak) / 2   and   i_peak - i_min = dI,

hence `i_min = i_avg - dI/2`.  `dI` is set by `L`, the switching-node voltage
and the effective on-time; `i_avg` is set by the LOAD.  Natural ZVS needs
`i_min` at least as negative as the phase's own threshold current.  At the rated
250 W the two terms nearly cancel and `i_min` lands near zero.  Reducing the
load raises `-i_min`.

So: re-solve the whole fixed point at a ladder of nominal module powers and
report, per phase, whether it achieves natural ZVS -- i.e. locate the load at
which a self-consistent four-phase joint ZVS periodic state DOES exist for this
boundary, if one exists at all.

This is `SENSITIVITY_ONLY`.  P24's own rated operating point is 250 W per
module; no row other than 250 W is a P24 operating point, and none of this is a
P24/P25 reproduction claim.

Run:  python3 run_load_sweep.py --output load_sweep.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEARCH = HERE / "run_fixed_point_search.py"
POWERS_W = (250.0, 225.0, 200.0, 190.0, 185.0, 180.0, 175.0, 150.0, 100.0, 50.0)


def run_case(power_w: float, scratch: Path) -> dict:
    output = scratch / f"load_{power_w:g}w.json"
    command = [
        sys.executable,
        str(SEARCH),
        "--output",
        str(output),
        "--picard-iterations",
        "0",
        "--module-power-w",
        f"{power_w:g}",
    ]
    started = time.time()
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        return {
            "module_power_w": power_w,
            "failed": True,
            "command": command,
            "stderr_tail": completed.stderr[-4000:],
        }
    payload = json.loads(output.read_text())
    metrics = payload["newton"]["final_orbit_metrics"]
    verdicts = payload["newton"]["final_verdicts"]["turn_on"]
    minima = metrics["minimum_phase_currents_a"]
    maxima = metrics["maximum_phase_currents_a"]
    return {
        "module_power_w": power_w,
        "failed": False,
        "command": command,
        "wall_clock_s": time.time() - started,
        "converged": payload["newton"]["converged"],
        "final_relative_residual": payload["newton"]["final_relative_residual"],
        "natural_zvs_flags": payload["newton"]["final_natural_zvs_flags"],
        "average_output_v": metrics["average_output_v"],
        "average_load_power_w": metrics["average_load_power_w"],
        "phase_current_minima_a": minima,
        "phase_current_maxima_a": maxima,
        "phase_current_ripple_a": [
            maxima[phase] - minima[phase] for phase in range(4)
        ],
        "minimum_abs_vds_v": [item["minimum_abs_vds_v"] for item in verdicts],
        "hard_switch_residual_v": [item["hard_switch_residual_v"] for item in verdicts],
        "flying_capacitor_v": metrics["flying_capacitor_v_at_z_star"],
        "maximum_abs_phase_current_a": payload["safety"][
            "maximum_abs_phase_current_a"
        ],
        "safety_within_limit": payload["safety"]["within_limit"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="load_sweep.json")
    parser.add_argument("--scratch", default="_load_sweep")
    args = parser.parse_args()
    scratch = Path(args.scratch)
    scratch.mkdir(exist_ok=True)
    started = time.time()
    rows = [run_case(power_w, scratch) for power_w in POWERS_W]

    good = [row for row in rows if not row["failed"]]
    all_four = [row for row in good if all(row["natural_zvs_flags"])]
    any_one = [row for row in good if any(row["natural_zvs_flags"])]
    payload = {
        "script": Path(__file__).name,
        "classification": "SENSITIVITY_ONLY",
        "rated_module_power_w": 250.0,
        "rows": rows,
        "highest_power_with_all_four_phases_zvs_w": (
            max(row["module_power_w"] for row in all_four) if all_four else None
        ),
        "highest_power_with_any_phase_zvs_w": (
            max(row["module_power_w"] for row in any_one) if any_one else None
        ),
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {args.output}  ({payload['wall_clock_s']:.1f} s)\n")
    header = (
        f"{'P_nom(W)':>9} {'P_act(W)':>9} {'Vout(V)':>8} {'ZVS 1/2/3/4':<16} "
        f"{'iL minima (A)':<40} {'ripple (A)':<38} {'residual':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        if row["failed"]:
            print(f"{row['module_power_w']:>9g}  FAILED")
            continue
        print(
            f"{row['module_power_w']:>9g} {row['average_load_power_w']:>9.3f} "
            f"{row['average_output_v']:>8.5f} "
            f"{str([int(v) for v in row['natural_zvs_flags']]):<16} "
            f"{str([round(v, 4) for v in row['phase_current_minima_a']]):<40} "
            f"{str([round(v, 3) for v in row['phase_current_ripple_a']]):<38} "
            f"{row['final_relative_residual']:>10.2e}"
        )
    print(
        f"\nhighest nominal power at which ALL FOUR phases achieve natural ZVS: "
        f"{payload['highest_power_with_all_four_phases_zvs_w']}"
    )
    print(
        f"highest nominal power at which ANY phase achieves natural ZVS: "
        f"{payload['highest_power_with_any_phase_zvs_w']}"
    )
    print("\nsafety:")
    for row in good:
        print(
            f"  {row['module_power_w']:>6g} W  max |iL| = "
            f"{row['maximum_abs_phase_current_a']:.4f} A   within limit = "
            f"{row['safety_within_limit']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
