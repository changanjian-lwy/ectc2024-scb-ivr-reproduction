"""A219 runner: LSCB's resistor pre-charge on one P24 module, then a soft start from the pre-charged state.

Run from the project root (after A218's runner exists; it provides run_lt / compact):
    PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A219_lscb_precharge_startup/a219_run.py [--jobs 2]
Stage 1: the six pre-charge rows (every switch off). Stage 2: soft starts from the rdiv_pc pre_slow end state and from
the exact nominal state, and A180's base su row again with the switch-voltage metric.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A218_lscb_idle_restart_shedding"))
import a218_run as a218                                                     # noqa: E402
from scb_ivr.extensions import lscb_ladder as ll                            # noqa: E402

a218.RUNS = HERE / "runs"
PRE = [(v, r) for r in ("pre_fast", "pre_slow") for v in ("base", "rdiv_pc", "lad_pc")]


def pre_job(x):
    var, row = x
    return var, row, a218.one(var, row, dict(ll.PARAMS), f"a219_{var}_{row}", dt=20e-6)


def soft_ic(rec):
    """Node voltages at the end of a pre-charge record (output at 0 V, no current), for the soft start."""
    pc = rec["precharge"]
    ic = {f"a{k}": pc["vcs_end"][k - 1] + pc["x_end"][k - 1] for k in (1, 2, 3)}
    ic.update({f"x{k}": pc["x_end"][k - 1] for k in (1, 2, 3, 4)}, out=0.0)
    return ic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--stage", type=int, default=0, help="1 or 2 only (default both)")
    a = ap.parse_args()
    if a.stage in (0, 1):
        with ThreadPoolExecutor(a.jobs) as ex:
            for var, row, res in ex.map(pre_job, PRE):
                pc = res["precharge"]
                print(f"{var:8s} {row:8s} {res['wall_s']:6.1f} s  sw_max {[round(x, 1) for x in pc['sw_max']]}  "
                      f"SH1>40V {pc['sh1_over_40v_s'] * 1e3:.2f} ms  Vcs dev end {[round(x, 2) for x in pc['vcs_dev_end']]}", flush=True)
    if a.stage in (0, 2):
        rec = json.loads((a218.RUNS / "rdiv_pc_pre_slow.json").read_text())
        nominal = {"a1": 36.0, "a2": 24.0, "a3": 12.0, "x1": 0.0, "x2": 0.0, "x3": 0.0, "x4": 0.0, "out": 0.0}
        jobs = [("base", "soft", dict(ll.PARAMS, ic=soft_ic(rec)), "soft_rdiv"),
                ("base", "soft", dict(ll.PARAMS, ic=nominal), "soft_nominal"),
                ("base", "su", dict(ll.PARAMS), "su")]
        with ThreadPoolExecutor(a.jobs) as ex:
            for res in ex.map(lambda j: a218.one(j[0], j[1], j[2], f"a219_{j[0]}_{j[3]}", tag=j[3]), jobs):
                su = res["startup"]
                print(f"{res['row_label']:13s} {res['wall_s']:6.1f} s  peaks {[round(x) for x in su['il_peak']]}  "
                      f"sw_max {[round(x, 1) for x in su['sw_max']]}  rail_dev_end {su['rail_dev_end']:.2f}  vo_end {su['vo_end']:.3f}",
                      flush=True)


if __name__ == "__main__":
    sys.exit(main())
