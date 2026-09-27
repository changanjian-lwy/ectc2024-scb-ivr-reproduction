"""A58 - regulate a continuation path of (d_rise, d_fall) points to 250 W and price them.

Usage:
    python3 run_a58.py --design zvs --seed-json <json> --path 2.15:2.15,2.0:2.15,...

Each point along ``--path`` (ns pairs rise:fall) is seeded from the previous
point's regulated z* and Ton_cmd (the first from ``--seed-json``, an A56 run
or an A58 point). Regulation reuses A56's declared outer policy
(``run_regulated_candidate.next_ton``, 15 trials, 1e-3, +/-250 A on orbits
and every probe) with A53's ``solve_fixed_point`` and A55's meter, all inside
``asym_schedule_context``. Accounting per BOUNDARY.md Section 2:

* P_A = A55 channel loss + missed hard/partial-hard capacitive energy
  (A56 event-window re-integration, Richardson 0.05/0.025 ps, both sides);
* P_B = P_A - Ron loss in natural-admission remainders + A57 datasheet VSD loss;
* recorded: turn-on recharge estimate, coarse source-side balance.

Output ``runs/<design>_r<rise>_f<fall>.json``; an existing point is never
overwritten -- it is reused as the continuation seed (resume).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import a58_schedule as S

sys.path.insert(0, str(S.A56_DIR))
sys.path.insert(0, str(S.A57_DIR))
import orbit_diagnostics as O  # noqa: E402  (A56)
import run_regulated_candidate as RR  # noqa: E402  (A56 outer policy)
import price_reverse_conduction as P57  # noqa: E402  (A57 pricing)

R = S.R
HERE = S.HERE
RUNS = HERE / "runs"
DESIGNS = {"zvs": 6.274059728342265e-10, "baseline": 1.4666667e-9}
FINE_RUNGS_S = (0.05e-12, 0.025e-12)
MODELS = ("fig8_25C", "fig8_125C", "table_floor_1p2V")
CURVES = P57.load_curves()


def point_path(design: str, rise_ns: float, fall_ns: float, suffix: str = "") -> Path:
    return RUNS / f"{design}_r{rise_ns:.3f}_f{fall_ns:.3f}{suffix}.json"


def regulate(b_of_ton, ton0, seed_z, coarse, sub, label):
    trials, regulated = [], None
    ton, seed, seed_ton, reason = ton0, np.array(seed_z, float), ton0, "replay of the seed"
    for iteration in range(RR.MAX_OUTER):
        b = b_of_ton(ton)
        trial = dict(iteration=iteration, ton_cmd_s=ton, choice_reason=reason,
                     seed_ton_cmd_s=seed_ton, outcome=None)
        started = time.time()
        try:
            with R.asymmetric_ron_context():
                solved = R.S.solve_fixed_point(b, seed.copy(), tolerance=RR.NEWTON_TOLERANCE,
                                               max_iterations=RR.NEWTON_MAX_ITERATIONS,
                                               coarse_step_s=coarse, sub_step_s=sub)
            trial.update(converged=bool(solved["converged"]), stalled_reason=solved["stalled_reason"],
                         relative_residual=solved["final_relative_residual"],
                         iterations_used=solved["iterations_used"],
                         solver_probe_safety=solved["safety"], z_star=solved["z_star"].tolist())
            if not solved["converged"]:
                trial["outcome"] = "periodic_closure_not_reached"
            else:
                metrics = R.meter_regulated(b, solved["z_star"], coarse_step_s=coarse,
                                            sub_step_s=sub, label=f"{label}_trial{iteration}")
                power = metrics["actual_load_power_w"]
                trial.update(metrics=metrics, power_relative_error=power / R.TARGET_POWER_W - 1.0,
                             h=math.sqrt(power / R.TARGET_POWER_W) - 1.0,
                             accepted_orbit_current_screen_pass=(
                                 metrics["maximum_abs_phase_current_a"] <= R.CURRENT_SCREEN_A))
                trial["outcome"] = ("success" if trial["accepted_orbit_current_screen_pass"]
                                    else "accepted_orbit_current_screen")
        except RuntimeError as error:
            match = RR.SAFETY_PATTERN.search(str(error))
            trial.update(outcome="probe_current_screen" if match else "solver_exception", error=str(error))
        except (ValueError, np.linalg.LinAlgError) as error:
            trial.update(outcome="solver_exception", error=str(error))
        trial["wall_time_s"] = time.time() - started
        trials.append(trial)
        m = trial.get("metrics", {})
        print(json.dumps(dict(point=label, it=iteration, ton_ns=round(ton * 1e9, 5), outcome=trial["outcome"],
                              P=m.get("actual_load_power_w"), hz=m.get("natural_zvs_flags"),
                              wall=round(trial["wall_time_s"], 1))), flush=True)
        if trial["outcome"] == "success" and abs(trial["power_relative_error"]) <= R.POWER_TOLERANCE:
            regulated = trial
            break
        ton, reason = RR.next_ton(trials, b.dead_time_s, b.period_s)
        if ton is None:
            return trials, None, reason
        good = [t for t in trials if t["outcome"] == "success"]
        nearest = min(good, key=lambda t: abs(t["ton_cmd_s"] - ton))
        seed, seed_ton = np.array(nearest["z_star"], float), nearest["ton_cmd_s"]
    if regulated is None:
        return trials, None, f"outer iteration cap ({RR.MAX_OUTER}) exhausted"
    return trials, regulated, None


def account(b, z, coarse, sub, metrics):
    result, steps, index = O.accepted_orbit(b, z, coarse_step_s=coarse, sub_step_s=sub)
    channel = O.channel_power_w(b, steps, index)
    if abs(channel - metrics["actual_branch_channel_loss_w"]) > 1e-9 * max(1.0, channel):
        raise RuntimeError("diagnostic meter differs from A55 meter")
    f_sw = 1.0 / b.period_s
    hard = []
    for event in O.hard_events(b, result, steps):
        state = steps[event.sample_position].state
        orbit_e = O.orbit_window_energy_j(b, steps, index, event)
        rung = {h: O.event_window_energy(b, state, event.window_end_s, h, index, event.branch,
                                         event.resistance_ohm)["energy_j"] for h in (coarse,) + FINE_RUNGS_S}
        limit = 2.0 * rung[FINE_RUNGS_S[1]] - rung[FINE_RUNGS_S[0]]
        hard.append(dict(side=event.side, phase_index=event.phase_index, residual_v=event.residual_v,
                         orbit_window_energy_j=orbit_e, coarse_rung_reproduces_orbit=bool(
                             abs(rung[coarse] - orbit_e) <= 1e-9 * max(abs(orbit_e), 1e-15)),
                         h_to_zero_energy_j=limit, missed_j=limit - orbit_e,
                         half_c_struct_v2_j=0.5 * O.structural_capacitance_f(b, event) * event.residual_v ** 2))
    missed_w = f_sw * sum(e["missed_j"] for e in hard)
    p_a = channel + missed_w
    exposure = O.dead_time_surrogate_exposure(b, result, steps, index)
    orbit = dict(dead_time_surrogate_exposure=exposure)
    priced = {m: P57.price_orbit(orbit, p_a, P57.vsd_model(m, CURVES)) for m in MODELS}
    transitions = []
    for v in result.turn_on:
        transitions.append(dict(side="high", phase_index=v.phase_index, natural=bool(v.natural_zvs),
                                window_s=v.window_end_s - v.window_start_s,
                                transition_s=(v.switch_on_time_s - v.window_start_s) if v.natural_zvs else None,
                                residual_reverse_s=(v.window_end_s - v.switch_on_time_s) if v.natural_zvs else 0.0,
                                residual_v=0.0 if v.natural_zvs else v.hard_switch_residual_v))
    for v in result.turn_off:
        transitions.append(dict(side="low", phase_index=v.phase_index, natural=bool(v.natural),
                                window_s=v.window_end_s - v.window_start_s,
                                transition_s=(v.switch_on_time_s - v.window_start_s) if v.natural else None,
                                residual_reverse_s=(v.window_end_s - v.switch_on_time_s) if v.natural else 0.0,
                                residual_v=0.0 if v.natural else v.hard_switch_residual_v))
    balance = O.energy_balance(b, steps, index)
    return dict(channel_loss_w=channel, missed_capacitive_w=missed_w, hard_events=hard,
                p_a_w=p_a, p_b_w={m: priced[m]["scenario_b_proxy_w"] for m in MODELS},
                recharge_estimate_w={m: priced[m]["turn_on_recharge_estimate_w"] for m in MODELS},
                ron_credit_in_remainders_w=priced[MODELS[0]]["channel_metered_in_intervals_w"],
                reverse_loss_w={m: priced[m]["reverse_loss_w"] for m in MODELS},
                reverse_events=priced[MODELS[0]]["events"], transitions=transitions,
                exposure_a=exposure["mean_abs_current_time_per_second_a"],
                source_minus_load_coarse_w=balance["source_w"] - balance["load_w"],
                energy_balance=balance)


def run_path(design, seed_json, path, coarse, sub, suffix=""):
    RUNS.mkdir(exist_ok=True)
    source = json.loads(Path(seed_json).read_text())
    reg = source["regulated"]
    seed_z, seed_ton = reg["z_star"], reg["ton_cmd_s"]
    seed_name = Path(seed_json).name
    inductance = DESIGNS[design]
    with S.asym_schedule_context():
        for rise_ns, fall_ns in path:
            out = point_path(design, rise_ns, fall_ns, suffix)
            if out.exists():
                done = json.loads(out.read_text())
                print(f"reuse {out.name} ({done['status']})", flush=True)
                if done.get("regulated"):
                    seed_z, seed_ton = done["regulated"]["z_star"], done["regulated"]["ton_cmd_s"]
                    seed_name = out.name
                continue
            label = out.stem

            def b_of_ton(ton, r=rise_ns * 1e-9, f=fall_ns * 1e-9):
                return S.build_asym_boundary(phase_inductance_h=inductance, dead_time_rise_s=r,
                                             dead_time_fall_s=f, ton_cmd_s=ton)

            record = dict(experiment="A58", classification="SENSITIVITY_ONLY", design=design,
                          phase_inductance_h=inductance, dead_time_rise_s=rise_ns * 1e-9,
                          dead_time_fall_s=fall_ns * 1e-9, coarse_step_s=coarse, sub_step_s=sub,
                          seed=seed_name, seed_ton_cmd_s=seed_ton, status="RUNNING")
            started = time.time()
            trials, regulated, stop = regulate(b_of_ton, seed_ton, seed_z, coarse, sub, label)
            record["trials"] = [{k: v for k, v in t.items() if k != "metrics"} | (
                {"power_w": t["metrics"]["actual_load_power_w"]} if "metrics" in t else {}) for t in trials]
            if regulated is None:
                record.update(status="NOT_REGULATED", stop_reason=stop)
            else:
                b = b_of_ton(regulated["ton_cmd_s"])
                z = np.array(regulated["z_star"], float)
                m = regulated["metrics"]
                record["full_boundary"] = R.boundary_record(b)
                record["regulated"] = dict(
                    ton_cmd_s=regulated["ton_cmd_s"], z_star=regulated["z_star"],
                    load_power_w=m["actual_load_power_w"], power_relative_error=regulated["power_relative_error"],
                    relative_residual=regulated["relative_residual"],
                    high_side_natural_zvs=list(m["natural_zvs_flags"]),
                    low_side_natural_zvs=[v["natural"] for v in m["low_side_turn_on_verdicts"]],
                    maximum_abs_phase_current_a=m["maximum_abs_phase_current_a"],
                    max_probe_abs_current_a=max(
                        (t.get("solver_probe_safety", {}).get("maximum_abs_phase_current_a") or 0.0)
                        for t in trials))
                record["accounting"] = account(b, z, coarse, sub, m)
                record["status"] = "REGULATED_TO_250W"
                seed_z, seed_ton, seed_name = regulated["z_star"], regulated["ton_cmd_s"], out.name
            record["wall_time_s"] = time.time() - started
            out.write_text(json.dumps(record, indent=1, default=str) + "\n")
            acc = record.get("accounting", {})
            print(json.dumps(dict(point=label, status=record["status"],
                                  ton_ns=record.get("regulated", {}).get("ton_cmd_s", 0) * 1e9,
                                  H=record.get("regulated", {}).get("high_side_natural_zvs"),
                                  L=record.get("regulated", {}).get("low_side_natural_zvs"),
                                  P_A=acc.get("p_a_w"), P_B=acc.get("p_b_w", {}).get("fig8_25C"),
                                  wall=round(record["wall_time_s"], 1))), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", choices=sorted(DESIGNS), required=True)
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--path", required=True, help="comma list of rise:fall in ns")
    parser.add_argument("--coarse", type=float, default=62.5e-12)
    parser.add_argument("--sub", type=float, default=5e-12)
    parser.add_argument("--suffix", default="", help="output name suffix, e.g. _step2p5ps")
    args = parser.parse_args()
    path = [tuple(float(x) for x in item.split(":")) for item in args.path.split(",")]
    run_path(args.design, args.seed_json, path, args.coarse, args.sub, args.suffix)


if __name__ == "__main__":
    main()
