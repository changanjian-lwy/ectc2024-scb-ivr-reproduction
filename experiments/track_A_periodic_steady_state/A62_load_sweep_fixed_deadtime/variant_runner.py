"""A62/A63 - run A59's reference model at fixed dead times under boundary variants.

A "variant" is a label, a function that modifies the A59 boundary (via
``dataclasses.replace``), and the regulation target power. Points are run in
the given order, each seeded from the previous regulated point
(continuation). Regulation, metering and accounting are A58's unchanged
``regulate``/``account``, inside A58's schedule and A59's nonlinear-Coss
contexts. ``R.TARGET_POWER_W`` (read by ``regulate`` at call time) is scoped
to each variant's target.
"""
from __future__ import annotations

import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

TRACK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TRACK / "A59_nonlinear_coss_epc2067"))
import a59_nonlinear as N  # noqa: E402
import run_a58 as A58  # noqa: E402

S, R = N.S, N.R


@contextmanager
def target_power(watts: float):
    old = R.TARGET_POWER_W
    R.TARGET_POWER_W = float(watts)
    try:
        yield
    finally:
        R.TARGET_POWER_W = old


def run_variants(*, experiment, runs_dir: Path, design, seed_json, rise_ns, fall_ns, variants, coarse=62.5e-12,
                 sub=5e-12):
    runs_dir.mkdir(exist_ok=True)
    source = json.loads(Path(seed_json).read_text())
    seed_z, seed_ton, seed_name = source["regulated"]["z_star"], source["regulated"]["ton_cmd_s"], Path(seed_json).name
    inductance = A58.DESIGNS[design]
    with S.asym_schedule_context(), N.nonlinear_coss_context():
        for label, modify, power_w in variants:
            out = runs_dir / f"{design}_r{rise_ns:.3f}_f{fall_ns:.3f}_{label}.json"
            if out.exists():
                done = json.loads(out.read_text())
                print(f"reuse {out.name}", flush=True)
                if done.get("regulated"):
                    seed_z, seed_ton, seed_name = done["regulated"]["z_star"], done["regulated"]["ton_cmd_s"], out.name
                continue

            def b_of_ton(ton, r=rise_ns * 1e-9, f=fall_ns * 1e-9, modify=modify):
                return modify(N.build_nl_boundary(phase_inductance_h=inductance, dead_time_rise_s=r,
                                                  dead_time_fall_s=f, ton_cmd_s=ton))

            record = dict(experiment=experiment, classification="SENSITIVITY_ONLY", design=design, variant=label,
                          target_power_w=power_w, phase_inductance_h=inductance, dead_time_rise_s=rise_ns * 1e-9,
                          dead_time_fall_s=fall_ns * 1e-9, coarse_step_s=coarse, sub_step_s=sub, seed=seed_name,
                          status="RUNNING")
            started = time.time()
            with target_power(power_w):
                trials, regulated, stop = A58.regulate(b_of_ton, seed_ton, seed_z, coarse, sub, out.stem)
            record["trials"] = [{k: v for k, v in t.items() if k != "metrics"} | (
                {"power_w": t["metrics"]["actual_load_power_w"]} if "metrics" in t else {}) for t in trials]
            if regulated is None:
                record.update(status="NOT_REGULATED", stop_reason=stop)
            else:
                b = b_of_ton(regulated["ton_cmd_s"])
                m = regulated["metrics"]
                record["full_boundary"] = R.boundary_record(b)
                record["regulated"] = dict(
                    ton_cmd_s=regulated["ton_cmd_s"], z_star=regulated["z_star"],
                    load_power_w=m["actual_load_power_w"], power_relative_error=regulated["power_relative_error"],
                    high_side_natural_zvs=list(m["natural_zvs_flags"]),
                    low_side_natural_zvs=[v["natural"] for v in m["low_side_turn_on_verdicts"]],
                    maximum_abs_phase_current_a=m["maximum_abs_phase_current_a"],
                    max_probe_abs_current_a=max(
                        (t.get("solver_probe_safety", {}).get("maximum_abs_phase_current_a") or 0.0) for t in trials))
                record["accounting"] = A58.account(b, np.array(regulated["z_star"], float), coarse, sub, m)
                record["status"] = "REGULATED"
                seed_z, seed_ton, seed_name = regulated["z_star"], regulated["ton_cmd_s"], out.name
            record["wall_time_s"] = time.time() - started
            out.write_text(json.dumps(record, indent=1, default=str) + "\n")
            a = record.get("accounting", {})
            print(json.dumps(dict(point=out.stem, status=record["status"],
                                  ton_ns=record.get("regulated", {}).get("ton_cmd_s", 0) * 1e9,
                                  H=record.get("regulated", {}).get("high_side_natural_zvs"),
                                  L=record.get("regulated", {}).get("low_side_natural_zvs"),
                                  P_A=a.get("p_a_w"), P_B=a.get("p_b_w", {}).get("fig8_25C"),
                                  wall=round(record["wall_time_s"], 1))), flush=True)
