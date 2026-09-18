"""A51 - two checks that decide how much a recovered fixed point is worth.

**1. Local stability.**  `F(z*) = z*` says an orbit closes; it does NOT say the
converter would ever sit on it.  The eigenvalues of `dF/dz` at `z*` do: a
spectral radius above 1 means the orbit is a repeller and no real converter
settles there, which would change how a positive ZVS finding must be reported.
The Jacobian is rebuilt by the same finite differences the search used.  The
three precharge-divider tap directions are excluded, because `F` is the identity
on them to `~3e-13` per period (measured in the search) and they would otherwise
contribute three spurious eigenvalues at exactly 1.

**2. Divider admissibility.**  The whole experiment freezes the three precharge
diodes OFF (`diode_state = (False, False, False)`), which is `advance_fixed_
diode_step`'s own contract.  That is only physically honest while every off
diode stays reverse-biased.  The search's own audit found `0.40 V` of forward
bias at the `2.15 ns` fixed point but `43-46 V` at the long-dead-time ones, so
this script re-solves each case with the taps moved far enough down that NO
diode is forward-biased anywhere on the orbit, and reports how much the STAGE
part of `z*` moved.  If it does not move, the divider -- which A37's own netlist
does not contain at all -- is confirmed irrelevant to the four-phase result.

Run:  python3 run_stability_and_divider_checks.py --output stability_and_divider.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

import a51_period_map as M

HERE = Path(__file__).resolve().parent
SEARCH = HERE / "run_fixed_point_search.py"
PINNED = ("tap3", "tap2", "tap1")
STAGE_VARIABLES = (
    "src", "src_r", "vin", "a1", "a2", "a3", "x1", "x2", "x3", "x4",
    "out", "LPAR_IN", "L1", "L2", "L3", "L4", "I_VSTEP",
)


def boundary_from(payload: dict):
    return M.build_boundary(
        dead_time_s=payload["boundary"]["dead_time_s"],
        switch_on_resistance_ohm=payload["boundary"]["switch_on_resistance_ohm"],
        module_power_w=payload["boundary"]["module_power_w"],
    )


def spectral_analysis(payload: dict, increment: float = 1e-4) -> dict:
    boundary = boundary_from(payload)
    names = M.variable_names(boundary)
    z = np.array(payload["newton"]["final_state"], dtype=float)
    coarse = payload["numerics"]["coarse_step_s"]
    sub = payload["numerics"]["sub_step_s"]
    base = M.evaluate_period_map(boundary, z, coarse_step_s=coarse, sub_step_s=sub)
    size = len(names)
    jacobian = np.empty((size, size), dtype=float)
    for column in range(size):
        probe = z.copy()
        probe[column] += increment
        image = M.evaluate_period_map(
            boundary, probe, coarse_step_s=coarse, sub_step_s=sub
        ).z_next
        jacobian[:, column] = (image - base.z_next) / increment
    free = [position for position, name in enumerate(names) if name not in PINNED]
    reduced = jacobian[np.ix_(free, free)]
    eigenvalues = np.linalg.eigvals(reduced)
    order = np.argsort(-np.abs(eigenvalues))
    eigenvalues = eigenvalues[order]
    return {
        "dead_time_s": boundary.dead_time_s,
        "module_power_w": boundary.module_power_w,
        "relative_residual": M.relative_residual(z, base.z_next),
        "natural_zvs_flags": list(base.natural_zvs_flags),
        "finite_difference_increment": increment,
        "excluded_directions": list(PINNED),
        "spectral_radius": float(np.max(np.abs(eigenvalues))),
        "locally_stable": bool(np.max(np.abs(eigenvalues)) < 1.0),
        "eigenvalue_magnitudes": [float(value) for value in np.abs(eigenvalues)],
        "eigenvalues_real": [float(value.real) for value in eigenvalues],
        "eigenvalues_imag": [float(value.imag) for value in eigenvalues],
    }


def divider_check(payload: dict, label: str, scratch: Path) -> dict:
    """Re-solve with the taps pushed below every ladder node on the orbit."""
    margin = payload["precharge_diode_audit"]["maximum_off_diode_forward_voltage_v"]
    drop = max(5.0, margin + 5.0)
    taps = [36.0 - drop, 24.0 - drop, 12.0 - drop]
    output = scratch / f"divider_{label}.json"
    command = [
        sys.executable,
        str(SEARCH),
        "--output",
        str(output),
        "--picard-iterations",
        "0",
        "--dead-time-ns",
        f"{payload['boundary']['dead_time_s'] * 1e9:g}",
        "--switch-on-resistance-ohm",
        f"{payload['boundary']['switch_on_resistance_ohm']:g}",
        "--module-power-w",
        f"{payload['boundary']['module_power_w']:g}",
        "--tap-voltages",
        ",".join(f"{value:g}" for value in taps),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        return {"label": label, "failed": True, "command": command,
                "stderr_tail": completed.stderr[-4000:]}
    other = json.loads(output.read_text())
    names = payload["variable_names"]
    a = np.array(payload["newton"]["final_state"], dtype=float)
    b = np.array(other["newton"]["final_state"], dtype=float)
    return {
        "label": label,
        "failed": False,
        "command": command,
        "tap_voltages_v": taps,
        "original_maximum_off_diode_forward_voltage_v": margin,
        "new_maximum_off_diode_forward_voltage_v": other["precharge_diode_audit"][
            "maximum_off_diode_forward_voltage_v"
        ],
        "all_diodes_reverse_biased": bool(
            other["precharge_diode_audit"]["maximum_off_diode_forward_voltage_v"] <= 0.0
        ),
        "converged": other["newton"]["converged"],
        "final_relative_residual": other["newton"]["final_relative_residual"],
        "natural_zvs_flags": other["newton"]["final_natural_zvs_flags"],
        "stage_state_inf_difference": max(
            abs(a[names.index(name)] - b[names.index(name)])
            for name in STAGE_VARIABLES
        ),
        "average_output_v": other["newton"]["final_orbit_metrics"]["average_output_v"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="stability_and_divider.json")
    parser.add_argument("--scratch", default="_checks")
    parser.add_argument(
        "--cases",
        nargs="*",
        default=[
            "baseline=fixed_point_search.json",
            "deadtime_5p00ns=_sweeps/sweep_deadtime_5p00ns.json",
            "deadtime_10p0ns=_sweeps/sweep_deadtime_10p0ns.json",
        ],
    )
    args = parser.parse_args()
    scratch = Path(args.scratch)
    scratch.mkdir(exist_ok=True)
    started = time.time()

    results = []
    for item in args.cases:
        label, _, path = item.partition("=")
        payload = json.loads(Path(path).read_text())
        results.append(
            {
                "label": label,
                "source": path,
                "stability": spectral_analysis(payload),
                "divider": divider_check(payload, label, scratch),
            }
        )

    out = {
        "script": Path(__file__).name,
        "cases": results,
        "wall_clock_s": time.time() - started,
    }
    Path(args.output).write_text(json.dumps(out, indent=2) + "\n")

    print(f"wrote {args.output}  ({out['wall_clock_s']:.1f} s)\n")
    for case in results:
        stability = case["stability"]
        divider = case["divider"]
        print(f"{case['label']}  (d = {stability['dead_time_s']*1e9:g} ns)")
        print(
            f"  residual {stability['relative_residual']:.3e},"
            f" natural ZVS {stability['natural_zvs_flags']}"
        )
        print(
            f"  spectral radius of dF/dz = {stability['spectral_radius']:.6f}"
            f"  -> locally stable = {stability['locally_stable']}"
        )
        print(
            "  five largest |eigenvalue|: "
            + ", ".join(f"{value:.6f}" for value in stability["eigenvalue_magnitudes"][:5])
        )
        if divider["failed"]:
            print("  divider check FAILED")
        else:
            print(
                f"  divider check: taps -> {divider['tap_voltages_v']},"
                f" max off-diode forward "
                f"{divider['original_maximum_off_diode_forward_voltage_v']:.4f} V ->"
                f" {divider['new_maximum_off_diode_forward_voltage_v']:.4f} V"
                f" (all reverse-biased = {divider['all_diodes_reverse_biased']})"
            )
            print(
                f"                  stage |z*| difference = "
                f"{divider['stage_state_inf_difference']:.3e} V/A,"
                f" natural ZVS {divider['natural_zvs_flags']},"
                f" Vout {divider['average_output_v']:.5f} V"
            )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
