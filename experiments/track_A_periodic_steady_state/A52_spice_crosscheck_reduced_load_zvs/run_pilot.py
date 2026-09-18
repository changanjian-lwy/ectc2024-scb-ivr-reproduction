"""A52 pilot runner -- run every pilot netlist and judge it against closed form.

Blocking: each LTspice batch run is waited on to completion and its `.log`
is parsed only afterwards, so nothing here can report a number from a
still-running or stale process (each `.log` is deleted before its run).

Pass bars, fixed BEFORE the runs (they are properties of the mechanism,
not of the result):

* `TIMING_TOLERANCE_S = 2 ps`.  BOUNDARY.md Section 4's tightest target is
  phase 4's `0.858292 ns` crossing, and Section 4's pre-declared comparison
  tolerance is `20%` of that = `171.7 ps`.  A mechanism accurate to 2 ps is
  86x finer than the comparison it has to support, so 2 ps is a bar the
  mechanism must clear with room to spare rather than a bar tuned to the
  answer.
* `BRANCH_MARGIN_S = 10 ps`: how far before the window end a transition
  must land to count as "natural" rather than "the timeout fired".
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import build_pilot as P
import meas_log

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parents[2] / "tools" / "ltspice_runner.sh"

TIMING_TOLERANCE_S = 2e-12
VOLTAGE_TOLERANCE_V = 1e-2
BRANCH_MARGIN_S = 10e-12


def run_one(netlist: Path) -> None:
    subprocess.run(
        ["bash", str(RUNNER), "run", str(netlist)], check=False, capture_output=True
    )


def main() -> int:
    results = []
    all_pass = True
    for case, (current_a, branch, expected_s) in P.CASES.items():
        for mechanism in P.MECHANISMS:
            for step_name in P.MAX_STEPS_S:
                name = f"A52_pilot_{case}_{mechanism}_{step_name}"
                netlist = P.PILOT_DIR / f"{name}.cir"
                log = P.PILOT_DIR / f"{name}.log"
                if log.exists():
                    log.unlink()
                run_one(netlist)
                if not log.exists():
                    print(f"{name}: NO LOG PRODUCED")
                    all_pass = False
                    continue
                meas = meas_log.parse(log)
                t_on = meas.get("t_gh_on")
                vds_on = meas.get("vds_at_on")
                t_cross = meas.get("t_vds_cross")
                vds_before_end = meas.get("vds_before_wend")
                vds_at_start = meas.get("vds_at_wstart")
                t_enter = meas.get("t_dt_enter")

                analytic_cross_s = (
                    P.WINDOW_START_S + P.INITIAL_V * P.NODE_CAPACITANCE_F / current_a
                )
                natural = branch == "natural_crossing"

                # --- criterion 1: the transition lands on the right instant
                timing_ok = (
                    t_on is not None and abs(t_on - expected_s) <= TIMING_TOLERANCE_S
                )
                # --- criterion 2: the DIRECT physical crossing (no gate-ramp
                #     latency at all) lands on the closed-form instant
                direct_cross_ok = (
                    t_cross is not None
                    and abs(t_cross - analytic_cross_s) <= TIMING_TOLERANCE_S
                    if natural
                    else True
                )
                # --- criterion 3: the correct BRANCH won.  Presence of a
                #     zero crossing is not enough on its own: in the timeout
                #     case the forced turn-on itself drives the node through
                #     zero, so the discriminator is whether the node is still
                #     materially positive immediately BEFORE the window end.
                if natural:
                    branch_ok = bool(
                        t_cross is not None
                        and t_cross < P.WINDOW_END_S - BRANCH_MARGIN_S
                        and t_on is not None
                        and t_on < P.WINDOW_END_S - BRANCH_MARGIN_S
                        and vds_before_end is not None
                        and vds_before_end <= 0.0
                    )
                    residual_ok = True
                else:
                    expected_residual = P.expected_residual_v(current_a)
                    branch_ok = bool(
                        vds_before_end is not None
                        and vds_before_end > 0.0
                        and (t_cross is None or t_cross >= P.WINDOW_END_S - BRANCH_MARGIN_S)
                    )
                    residual_ok = bool(
                        vds_before_end is not None
                        and abs(vds_before_end - expected_residual) <= VOLTAGE_TOLERANCE_V
                    )
                # --- criterion 4: the window itself opened when commanded
                window_entry_ok = bool(
                    t_enter is not None
                    and abs(t_enter - P.WINDOW_START_S) <= TIMING_TOLERANCE_S
                )
                ok = bool(
                    not meas.netlist_error
                    and timing_ok
                    and direct_cross_ok
                    and branch_ok
                    and residual_ok
                    and window_entry_ok
                )
                all_pass = all_pass and ok
                results.append(
                    {
                        "name": name,
                        "case": case,
                        "mechanism": mechanism,
                        "max_step": step_name,
                        "expected_branch": branch,
                        "expected_transition_s": expected_s,
                        "analytic_cross_s": analytic_cross_s,
                        "netlist_error": meas.netlist_error,
                        "t_dt_enter_s": t_enter,
                        "t_dt_enter_error_s": (
                            None if t_enter is None else t_enter - P.WINDOW_START_S
                        ),
                        "t_gh_on_s": t_on,
                        "t_gh_on_error_s": None if t_on is None else t_on - expected_s,
                        "vds_at_on_v": vds_on,
                        "t_vds_cross_s": t_cross,
                        "t_vds_cross_error_s": (
                            None if t_cross is None else t_cross - analytic_cross_s
                        ),
                        "vds_at_window_start_v": vds_at_start,
                        "vds_before_window_end_v": vds_before_end,
                        "expected_vds_before_window_end_v": (
                            P.expected_residual_v(current_a)
                        ),
                        "timing_ok": bool(timing_ok),
                        "direct_cross_ok": bool(direct_cross_ok),
                        "branch_ok": bool(branch_ok),
                        "residual_ok": bool(residual_ok),
                        "window_entry_ok": window_entry_ok,
                        "pass": ok,
                    }
                )
                print(
                    f"{name:<34} "
                    f"gate_on={'FAIL' if t_on is None else f'{t_on * 1e9:.9f}ns'} "
                    f"({'n/a' if t_on is None else f'{(t_on - expected_s) * 1e12:+.3f}ps'})  "
                    f"vds_x0="
                    f"{'none' if t_cross is None else f'{t_cross * 1e9:.9f}ns'} "
                    f"({'n/a' if t_cross is None or not natural else f'{(t_cross - analytic_cross_s) * 1e12:+.3f}ps'})  "
                    f"Vds@wend-="
                    f"{'n/a' if vds_before_end is None else f'{vds_before_end:+.6f}V'}  "
                    f"-> {'PASS' if ok else 'FAIL'}"
                )

    payload = {
        "timing_tolerance_s": TIMING_TOLERANCE_S,
        "voltage_tolerance_v": VOLTAGE_TOLERANCE_V,
        "branch_margin_s": BRANCH_MARGIN_S,
        "window_start_s": P.WINDOW_START_S,
        "window_end_s": P.WINDOW_END_S,
        "dead_time_s": P.DEAD_TIME_S,
        "initial_v": P.INITIAL_V,
        "node_capacitance_f": P.NODE_CAPACITANCE_F,
        "runs": results,
        "all_pass": all_pass,
    }
    (HERE / "pilot_results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print()
    print(f"ALL PILOT RUNS PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
