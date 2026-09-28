"""A59 - A58's regulated (d_rise, d_fall) continuation path with nonlinear EPC2067 Coss(V).

Identical to A58's ``run_a58.py`` (its ``regulate`` and ``account`` are
imported unchanged) except that every boundary is a
``NonlinearCossBoundary`` and everything runs inside the nonlinear-Coss
context as well as A58's schedule context.

Usage:
    python3 run_a59.py --design zvs --seed-json <json> --path 2.15:2.15,2.0:2.15 [--coarse ..] [--suffix ..]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import a59_nonlinear as N

import run_a58 as A58  # noqa: E402  (A58 dir is on sys.path via a59_nonlinear)

S, R = N.S, N.R
HERE = N.HERE
RUNS = HERE / "runs"


def run_path(design, seed_json, path, coarse, sub, suffix="", model_id="fig5a_pchip"):
    RUNS.mkdir(exist_ok=True)
    source = json.loads(Path(seed_json).read_text())
    seed_z, seed_ton = source["regulated"]["z_star"], source["regulated"]["ton_cmd_s"]
    seed_name = Path(seed_json).name
    inductance = A58.DESIGNS[design]
    with S.asym_schedule_context(), N.nonlinear_coss_context():
        for rise_ns, fall_ns in path:
            out = RUNS / f"{design}_r{rise_ns:.3f}_f{fall_ns:.3f}{suffix}.json"
            if out.exists():
                done = json.loads(out.read_text())
                print(f"reuse {out.name} ({done['status']})", flush=True)
                if done.get("regulated"):
                    seed_z, seed_ton, seed_name = done["regulated"]["z_star"], done["regulated"]["ton_cmd_s"], out.name
                continue

            def b_of_ton(ton, r=rise_ns * 1e-9, f=fall_ns * 1e-9):
                return N.build_nl_boundary(phase_inductance_h=inductance, dead_time_rise_s=r,
                                           dead_time_fall_s=f, ton_cmd_s=ton, coss_model_id=model_id)

            record = dict(experiment="A59", classification="SENSITIVITY_ONLY", design=design,
                          coss_model_id=model_id, phase_inductance_h=inductance,
                          dead_time_rise_s=rise_ns * 1e-9, dead_time_fall_s=fall_ns * 1e-9,
                          coarse_step_s=coarse, sub_step_s=sub, seed=seed_name, seed_ton_cmd_s=seed_ton,
                          status="RUNNING")
            started = time.time()
            N.NEWTON_STATS.update(steps=0, iterations=0, max_iterations=0)
            trials, regulated, stop = A58.regulate(b_of_ton, seed_ton, seed_z, coarse, sub, out.stem)
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
                record["accounting"] = A58.account(b, z, coarse, sub, m)
                record["status"] = "REGULATED_TO_250W"
                seed_z, seed_ton, seed_name = regulated["z_star"], regulated["ton_cmd_s"], out.name
            record["newton_stats"] = dict(N.NEWTON_STATS)
            record["wall_time_s"] = time.time() - started
            out.write_text(json.dumps(record, indent=1, default=str) + "\n")
            acc = record.get("accounting", {})
            print(json.dumps(dict(point=out.stem, status=record["status"],
                                  ton_ns=record.get("regulated", {}).get("ton_cmd_s", 0) * 1e9,
                                  H=record.get("regulated", {}).get("high_side_natural_zvs"),
                                  L=record.get("regulated", {}).get("low_side_natural_zvs"),
                                  P_A=acc.get("p_a_w"), P_B=acc.get("p_b_w", {}).get("fig8_25C"),
                                  newton_max=N.NEWTON_STATS["max_iterations"],
                                  wall=round(record["wall_time_s"], 1))), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", choices=sorted(A58.DESIGNS), required=True)
    parser.add_argument("--seed-json", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--coarse", type=float, default=62.5e-12)
    parser.add_argument("--sub", type=float, default=5e-12)
    parser.add_argument("--suffix", default="")
    parser.add_argument("--model", default="fig5a_pchip")
    args = parser.parse_args()
    path = [tuple(float(x) for x in item.split(":")) for item in args.path.split(",")]
    run_path(args.design, args.seed_json, path, args.coarse, args.sub, args.suffix, args.model)


if __name__ == "__main__":
    main()
