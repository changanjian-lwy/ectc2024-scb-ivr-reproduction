"""A60 - A59's tuned points at typical RDS(on)(Tj) from EPC2067 Fig. 9.

Usage:
    python3 run_a60.py --design zvs --seed-json <A59 tuned point json> --rise 1.95 --fall 0.65 \
        --points 1.55mohm,25,60,100,125 [--fall-offsets 0]

Each temperature point is regulated with A58's unchanged ``regulate`` and
priced with A58's unchanged ``account``, inside A58's schedule and A59's
nonlinear-Coss contexts. A57's pricing Ron (``price_reverse_conduction.RON``)
is scoped to the boundary's actual Ron for the call, so the Ron credit inside
reverse-conduction remainders uses the same Ron as the dynamics. The
reverse-conduction loss is then re-priced with VSD(I) linearly interpolated
in temperature between Fig. 8's 25 C and 125 C curves (BOUNDARY.md S1).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A59_DIR = HERE.parent / "A59_nonlinear_coss_epc2067"
sys.path.insert(0, str(A59_DIR))
import a59_nonlinear as N  # noqa: E402
import run_a58 as A58  # noqa: E402

P57 = A58.P57
S, R = N.S, N.R
RUNS = HERE / "runs"
RDS_TYP_25C = 1.3e-3
RDS_A59 = 1.55e-3
NHS, NLS = R.B.NHS, R.B.NLS
F_SW = 5e6


def k_of_tj(tj_c: float) -> float:
    rows = list(csv.DictReader(open(HERE / "epc2067_fig9_ron_vs_tj.csv")))
    t = np.array([float(r["tj_c"]) for r in rows])
    k = np.array([float(r["normalized_rds_on"]) for r in rows])
    return float(np.interp(tj_c, t, k))


def vsd_at(tj_c: float):
    v25, v125 = P57.vsd_model("fig8_25C", A58.CURVES), P57.vsd_model("fig8_125C", A58.CURVES)
    w = min(max((tj_c - 25.0) / 100.0, 0.0), 1.0)
    return lambda i: (1 - w) * v25(i) + w * v125(i)


@contextmanager
def pricing_ron(boundary):
    old = dict(P57.RON)
    P57.RON.update(high=boundary.high_side_on_resistance_ohm, low=boundary.low_side_on_resistance_ohm)
    try:
        yield
    finally:
        P57.RON.clear()
        P57.RON.update(old)


def with_ron(b, rds_device):
    high, low = rds_device / NHS, rds_device / NLS
    return replace(b, switch_on_resistance_ohm=high, high_side_on_resistance_ohm=high,
                   low_side_on_resistance_ohm=low)


def point_spec(token):
    if token.endswith("mohm"):
        return dict(label=f"R{token}", tj_c=None, rds_device=float(token[:-4]) * 1e-3)
    tj = float(token)
    return dict(label=f"T{tj:g}C", tj_c=tj, rds_device=RDS_TYP_25C * k_of_tj(tj))


def run(design, seed_json, rise_ns, fall_ns, tokens, coarse, sub):
    RUNS.mkdir(exist_ok=True)
    source = json.loads(Path(seed_json).read_text())
    seed_z, seed_ton, seed_name = source["regulated"]["z_star"], source["regulated"]["ton_cmd_s"], Path(seed_json).name
    inductance = A58.DESIGNS[design]
    with S.asym_schedule_context(), N.nonlinear_coss_context():
        for token in tokens:
            spec = point_spec(token)
            out = RUNS / f"{design}_r{rise_ns:.3f}_f{fall_ns:.3f}_{spec['label']}.json"
            if out.exists():
                done = json.loads(out.read_text())
                print(f"reuse {out.name}", flush=True)
                if done.get("regulated"):
                    seed_z, seed_ton, seed_name = done["regulated"]["z_star"], done["regulated"]["ton_cmd_s"], out.name
                continue

            def b_of_ton(ton, r=rise_ns * 1e-9, f=fall_ns * 1e-9, rds=spec["rds_device"]):
                return with_ron(N.build_nl_boundary(phase_inductance_h=inductance, dead_time_rise_s=r,
                                                    dead_time_fall_s=f, ton_cmd_s=ton), rds)

            record = dict(experiment="A60", classification="SENSITIVITY_ONLY", design=design,
                          phase_inductance_h=inductance, dead_time_rise_s=rise_ns * 1e-9,
                          dead_time_fall_s=fall_ns * 1e-9, tj_c=spec["tj_c"],
                          rds_on_device_ohm=spec["rds_device"],
                          k_tj=None if spec["tj_c"] is None else spec["rds_device"] / RDS_TYP_25C,
                          coarse_step_s=coarse, sub_step_s=sub, seed=seed_name, status="RUNNING")
            started = time.time()
            trials, regulated, stop = A58.regulate(b_of_ton, seed_ton, seed_z, coarse, sub, out.stem)
            record["trials"] = [{k: v for k, v in t.items() if k != "metrics"} | (
                {"power_w": t["metrics"]["actual_load_power_w"]} if "metrics" in t else {}) for t in trials]
            if regulated is None:
                record.update(status="NOT_REGULATED", stop_reason=stop)
            else:
                b = b_of_ton(regulated["ton_cmd_s"])
                m = regulated["metrics"]
                with pricing_ron(b):
                    acc = A58.account(b, np.array(regulated["z_star"], float), coarse, sub, m)
                tj = 25.0 if spec["tj_c"] is None else spec["tj_c"]
                vsd = vsd_at(tj)
                rev_t = sum(vsd(e["per_device_current_a"]) * e["branch_mean_current_a"] * e["duration_ns"] * 1e-9 * F_SW
                            for e in acc["reverse_events"])
                acc["p_b_temperature_interpolated_w"] = acc["p_a_w"] - acc["ron_credit_in_remainders_w"] + rev_t
                acc["reverse_loss_temperature_interpolated_w"] = rev_t
                acc["vsd_interpolation_tj_c"] = tj
                record["full_boundary"] = R.boundary_record(b)
                record["regulated"] = dict(
                    ton_cmd_s=regulated["ton_cmd_s"], z_star=regulated["z_star"],
                    load_power_w=m["actual_load_power_w"], power_relative_error=regulated["power_relative_error"],
                    high_side_natural_zvs=list(m["natural_zvs_flags"]),
                    low_side_natural_zvs=[v["natural"] for v in m["low_side_turn_on_verdicts"]],
                    maximum_abs_phase_current_a=m["maximum_abs_phase_current_a"],
                    max_probe_abs_current_a=max(
                        (t.get("solver_probe_safety", {}).get("maximum_abs_phase_current_a") or 0.0) for t in trials))
                record["accounting"] = acc
                record["status"] = "REGULATED_TO_250W"
                seed_z, seed_ton, seed_name = regulated["z_star"], regulated["ton_cmd_s"], out.name
            record["wall_time_s"] = time.time() - started
            out.write_text(json.dumps(record, indent=1, default=str) + "\n")
            a = record.get("accounting", {})
            print(json.dumps(dict(point=out.stem, status=record["status"], rds_mohm=spec["rds_device"] * 1e3,
                                  ton_ns=record.get("regulated", {}).get("ton_cmd_s", 0) * 1e9,
                                  P_A=a.get("p_a_w"), P_B_T=a.get("p_b_temperature_interpolated_w"),
                                  wall=round(record["wall_time_s"], 1))), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--design", choices=sorted(A58.DESIGNS), required=True)
    p.add_argument("--seed-json", required=True)
    p.add_argument("--rise", type=float, required=True)
    p.add_argument("--fall", type=float, required=True)
    p.add_argument("--points", required=True, help="comma list: '<x>mohm' or a junction temperature in C")
    p.add_argument("--coarse", type=float, default=62.5e-12)
    p.add_argument("--sub", type=float, default=5e-12)
    a = p.parse_args()
    run(a.design, a.seed_json, a.rise, a.fall, a.points.split(","), a.coarse, a.sub)


if __name__ == "__main__":
    main()
