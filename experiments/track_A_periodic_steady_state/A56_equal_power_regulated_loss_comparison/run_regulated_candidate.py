"""A56 - regulate ONE A55 grid candidate to mean(Vout^2/R) = 250 W via Ton_cmd.

BOUNDARY.md S3 steps 2-3 and 6. Outer 1-D root find on the command on-interval
``Ton_cmd`` (the only control degree of freedom); inner periodic fixed point by
A53's unchanged ``solve_fixed_point`` inside A55's ``asymmetric_ron_context``;
every converged state metered by A55's unchanged ``metered_orbit`` through the
scoped boundary override documented in ``regulated_boundary.py``.

Declared outer-search policy (fixed before any run; not tuned afterwards):

* residual ``h(Ton) = sqrt(P_load/250 W) - 1`` (P_load = mean(Vout^2/R) from
  the metered accepted orbit; h is ~linear in Ton because P ~ Vout^2);
* trial 0 replays A55's own point (Ton_cmd = nominal 16.6667 ns) from A55's
  committed z*; trial 1 uses ``Ton/(1+h)``; later trials use the secant on the
  two most recent successful trials, or regula falsi (Illinois) once 250 W is
  bracketed by successful trials;
* each step is clipped to 3 ns and Ton_cmd to [d+0.5 ns, T/4-d-0.5 ns];
* a trial that fails (periodic closure not reached, solver exception, or the
  +/-250 A screen tripped by any Newton/line-search probe or by the accepted
  orbit) is RECORDED, is never used as a regulated point, and the next trial
  bisects between it and the nearest successful Ton_cmd. If that gap falls
  below 5 ps, the search stops: the candidate cannot reach 250 W before that
  failure under this scheduler;
* each trial is seeded with the z* of the successful trial nearest in Ton_cmd
  (continuation; no raw A37 re-seeding);
* at most 15 outer trials (including the replay). Convergence:
  ``|P-250|/250 <= 1e-3`` (solver tolerance only, not a paper tolerance).

Output: ``runs/<label>[_<suffix>].json``; an existing file is never overwritten.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import regulated_boundary as R  # noqa: E402

MAX_OUTER = 15
MAX_STEP_S = 3e-9
MIN_FAIL_GAP_S = 5e-12
EDGE_MARGIN_S = 0.5e-9
NEWTON_TOLERANCE = 1e-6
NEWTON_MAX_ITERATIONS = 30
SAFETY_PATTERN = re.compile(r"SAFETY BOUND VIOLATED at (\S+): \|iL\| = ([0-9.eE+-]+) A")


def candidate_spec(label: str) -> tuple[str, float, float, float]:
    for row, inductance in R.L_ROWS:
        for factor, dead_time in R.DT_COLUMNS:
            if label == f"{row}_dt_x{factor:g}":
                return row, inductance, factor, dead_time
    raise SystemExit(f"unknown candidate label {label!r}")


def a55_seed(label: str) -> dict:
    grid = json.loads((R.A55_DIR / "joint_local_grid.json").read_text())
    probe = next(p for p in grid["probes"] if p["label"] == label)
    if not probe.get("converged"):
        raise SystemExit(f"A55 probe {label} has no converged z*")
    return probe


def next_ton(trials: list[dict], dead_time_s: float, period_s: float) -> tuple[float | None, str]:
    good = [t for t in trials if t["outcome"] == "success"]
    bad = [t for t in trials if t["outcome"] != "success"]
    low_edge = dead_time_s + EDGE_MARGIN_S
    high_edge = period_s / 4 - dead_time_s - EDGE_MARGIN_S
    last = trials[-1]
    if last["outcome"] != "success":
        if not good:
            return None, "first trial failed; no successful Ton_cmd to continue from"
        nearest = min(good, key=lambda t: abs(t["ton_cmd_s"] - last["ton_cmd_s"]))
        gap = abs(nearest["ton_cmd_s"] - last["ton_cmd_s"])
        if gap < MIN_FAIL_GAP_S:
            return None, ("failure boundary reached: failing Ton_cmd within 5 ps of a "
                          "successful one, 250 W not reached before it")
        return 0.5 * (nearest["ton_cmd_s"] + last["ton_cmd_s"]), "bisect toward nearest success after failure"

    below = [t for t in good if t["h"] < 0]
    above = [t for t in good if t["h"] > 0]
    if below and above:
        a = max(below, key=lambda t: t["ton_cmd_s"])
        b = min(above, key=lambda t: t["ton_cmd_s"])
        ha, hb = a["h"], b["h"]
        # Illinois modification: halve the stale end's residual when the same
        # end has been retained twice in a row.
        if len(good) >= 3:
            recent = good[-2:]
            if all(t["h"] < 0 for t in recent):
                hb *= 0.5
            elif all(t["h"] > 0 for t in recent):
                ha *= 0.5
        ton = a["ton_cmd_s"] - ha * (b["ton_cmd_s"] - a["ton_cmd_s"]) / (hb - ha)
        lo, hi = sorted((a["ton_cmd_s"], b["ton_cmd_s"]))
        if not (lo < ton < hi):
            ton, reason = 0.5 * (lo + hi), "bisection inside bracket"
        else:
            reason = "regula falsi (Illinois) inside successful bracket"
    elif len(good) >= 2:
        p, q = good[-2], good[-1]
        if q["h"] == p["h"]:
            return None, "flat residual between the last two successful trials"
        ton = q["ton_cmd_s"] - q["h"] * (q["ton_cmd_s"] - p["ton_cmd_s"]) / (q["h"] - p["h"])
        reason = "secant on last two successful trials"
    else:
        q = good[-1]
        ton = q["ton_cmd_s"] / (1.0 + q["h"])
        reason = "first step: Ton/(1+h) (Vout proportional to Ton model)"
    anchor = trials[-1]["ton_cmd_s"]
    ton = min(max(ton, anchor - MAX_STEP_S), anchor + MAX_STEP_S)
    # Never step beyond (or onto) a Ton_cmd that already failed.
    for failed in bad:
        f = failed["ton_cmd_s"]
        nearest = min(good, key=lambda t: abs(t["ton_cmd_s"] - f))["ton_cmd_s"]
        if (nearest < f <= ton) or (ton <= f < nearest):
            if abs(f - nearest) < MIN_FAIL_GAP_S:
                return None, ("failure boundary reached: the root lies beyond a failing "
                              "Ton_cmd that is within 5 ps of a successful one")
            ton = 0.5 * (nearest + f)
            reason += "; clipped to midpoint before a failed Ton_cmd"
    ton = min(max(ton, low_edge), high_edge)
    if any(abs(t["ton_cmd_s"] - ton) < 1e-16 for t in trials):
        return None, "next Ton_cmd repeats an already-evaluated value (edge clip or stall)"
    return ton, reason


def run(label: str, coarse_step_s: float, sub_step_s: float, suffix: str | None,
        seed_json: Path | None) -> None:
    row, inductance, factor, dead_time = candidate_spec(label)
    runs = HERE / "runs"
    runs.mkdir(exist_ok=True)
    out = runs / (f"{label}_{suffix}.json" if suffix else f"{label}.json")
    if out.exists():
        raise SystemExit(f"{out} exists; results are never overwritten")

    if seed_json is None:
        probe = a55_seed(label)
        seed_z = probe["z_star"]
        ton0 = R.NOMINAL_TON_S
        seed_source = f"A55 joint_local_grid.json probe {label} (Ton_cmd = nominal)"
        a55_reference = dict(
            actual_load_power_w=probe["metrics"]["actual_load_power_w"],
            actual_branch_channel_loss_w=probe["metrics"]["actual_branch_channel_loss_w"],
            natural_zvs_flags=probe["metrics"]["natural_zvs_flags"])
    else:
        source = json.loads(seed_json.read_text())
        reg = source.get("regulated")
        if not reg:
            raise SystemExit(f"{seed_json} has no regulated state to seed from")
        seed_z, ton0 = reg["z_star"], reg["ton_cmd_s"]
        seed_source = f"{seed_json.name} regulated state (step continuation)"
        a55_reference = None

    result = dict(
        experiment="A56", classification="SENSITIVITY_ONLY_EQUAL_POWER_REGULATION",
        label=label, row=row, deadtime_factor=factor, phase_inductance_h=inductance,
        dead_time_s=dead_time, coarse_step_s=coarse_step_s, sub_step_s=sub_step_s,
        regulated_variable="Ton_cmd (D01 command on-interval, all four phases)",
        load_resistance_ohm=R.RATED_LOAD_OHM, target_power_w=R.TARGET_POWER_W,
        power_tolerance_relative=R.POWER_TOLERANCE, nominal_ton_s=R.NOMINAL_TON_S,
        current_screen_a=R.CURRENT_SCREEN_A, newton_tolerance=NEWTON_TOLERANCE,
        newton_max_iterations=NEWTON_MAX_ITERATIONS, max_outer_iterations=MAX_OUTER,
        initial_seed_source=seed_source, a55_reference_metrics=a55_reference,
        objective_note="partial electrical-loss proxy, not total loss",
        trials=[], regulated=None, status="RUNNING")

    def save():
        tmp = out.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, indent=1, default=str) + "\n")
        tmp.replace(out)

    save()
    ton = ton0
    seed = np.array(seed_z, dtype=float)
    seed_ton = ton0
    seed_label = seed_source
    reason = "replay of the seed point"
    for iteration in range(MAX_OUTER):
        b = R.build_regulated_boundary(phase_inductance_h=inductance, dead_time_s=dead_time,
                                       ton_cmd_s=ton)
        trial = dict(iteration=iteration, ton_cmd_s=ton, choice_reason=reason,
                     ton_cmd_deviation_from_nominal_s=ton - R.NOMINAL_TON_S,
                     seed=seed_label, seed_ton_cmd_s=seed_ton,
                     full_boundary=R.boundary_record(b), outcome=None)
        started = time.time()
        try:
            with R.asymmetric_ron_context():
                solved = R.S.solve_fixed_point(
                    b, seed.copy(), tolerance=NEWTON_TOLERANCE,
                    max_iterations=NEWTON_MAX_ITERATIONS,
                    coarse_step_s=coarse_step_s, sub_step_s=sub_step_s)
            trial.update(converged=bool(solved["converged"]),
                         stalled_reason=solved["stalled_reason"],
                         relative_residual=solved["final_relative_residual"],
                         iterations_used=solved["iterations_used"],
                         jacobian_rebuilds=solved["jacobian_rebuilds"],
                         solver_probe_safety=solved["safety"], history=solved["history"],
                         z_star=solved["z_star"].tolist())
            if not solved["converged"]:
                trial["outcome"] = "periodic_closure_not_reached"
            else:
                metrics = R.meter_regulated(b, solved["z_star"], coarse_step_s=coarse_step_s,
                                            sub_step_s=sub_step_s, label=f"{label}_trial{iteration}")
                power = metrics["actual_load_power_w"]
                trial["metrics"] = metrics
                trial["power_relative_error"] = power / R.TARGET_POWER_W - 1.0
                trial["h"] = math.sqrt(power / R.TARGET_POWER_W) - 1.0
                trial["accepted_orbit_current_screen_pass"] = (
                    metrics["maximum_abs_phase_current_a"] <= R.CURRENT_SCREEN_A)
                trial["outcome"] = ("success" if trial["accepted_orbit_current_screen_pass"]
                                    else "accepted_orbit_current_screen")
        except RuntimeError as error:
            text = str(error)
            match = SAFETY_PATTERN.search(text)
            if match:
                trial.update(outcome="probe_current_screen", error=text,
                             tripping_probe=match.group(1),
                             tripping_probe_abs_current_a=float(match.group(2)))
            else:
                trial.update(outcome="solver_exception", error=text)
        except (ValueError, np.linalg.LinAlgError) as error:
            trial.update(outcome="solver_exception", error=str(error))
        trial["wall_time_s"] = time.time() - started
        result["trials"].append(trial)
        save()
        m = trial.get("metrics", {})
        print(json.dumps(dict(label=label, it=iteration, ton_ns=ton * 1e9, outcome=trial["outcome"],
                              P=m.get("actual_load_power_w"), loss=m.get("actual_branch_channel_loss_w"),
                              hz=m.get("natural_zvs_flags"),
                              lz=[v["natural"] for v in m.get("low_side_turn_on_verdicts", [])],
                              peak=m.get("maximum_abs_phase_current_a"),
                              probe=trial.get("solver_probe_safety", {}).get("maximum_abs_phase_current_a"),
                              wall=round(trial["wall_time_s"], 1))), flush=True)
        if trial["outcome"] == "success" and abs(trial["power_relative_error"]) <= R.POWER_TOLERANCE:
            result["regulated"] = dict(iteration=iteration, ton_cmd_s=ton, z_star=trial["z_star"],
                                       metrics=trial["metrics"],
                                       power_relative_error=trial["power_relative_error"],
                                       relative_residual=trial["relative_residual"])
            result["status"] = "REGULATED_TO_250W"
            save()
            return
        ton, reason = next_ton(result["trials"], dead_time, b.period_s)
        if ton is None:
            result["status"] = "NOT_REGULATED"
            result["stop_reason"] = reason
            save()
            return
        good = [t for t in result["trials"] if t["outcome"] == "success"]
        nearest = min(good, key=lambda t: abs(t["ton_cmd_s"] - ton))
        seed = np.array(nearest["z_star"], dtype=float)
        seed_ton = nearest["ton_cmd_s"]
        seed_label = f"trial {nearest['iteration']} of this run (continuation)"
    result["status"] = "NOT_REGULATED"
    result["stop_reason"] = f"outer iteration cap ({MAX_OUTER}) exhausted"
    save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("label")
    parser.add_argument("--coarse", type=float, default=62.5e-12)
    parser.add_argument("--sub", type=float, default=5e-12)
    parser.add_argument("--suffix", default=None)
    parser.add_argument("--seed-json", type=Path, default=None)
    args = parser.parse_args()
    run(args.label, args.coarse, args.sub, args.suffix, args.seed_json)


if __name__ == "__main__":
    main()
