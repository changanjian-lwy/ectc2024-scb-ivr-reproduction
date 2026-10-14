"""A218 runner: LSCB's idle state on one P24 module - stage shedding and restart after idle (extension lscb_ladder).

Run from the project root:
    PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A218_lscb_idle_restart_shedding/a218_run.py [--jobs 2]
Netlists, logs and .raw files stay in the LTspice work folder (p24_ltspice.WORK); runs/<variant>_<row>.json holds the
metrics (scb_ivr.extensions.lscb_ladder) and a compact trace for the figures. a219_run.py imports run_lt / compact.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

import p24_ltspice as lt
from scb_ivr.extensions import lscb_ladder as ll

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
OPTIONS = ".options plotwinsize=0 numdgt=15 reltol=1e-4"           # linear parts only, as A180
LIGHT = dict(rload=16e-3)                                           # restart rows: 25 % load, 62.5 A at 1 V
DRIFT = {"rs0": 0.0, "rsv": ll.PARAMS["vo0"], "rs2": 2.0, "rs4": 4.0}
PLAN = [("base", "shed4"), ("actall_c20", "shed4")] + [("base", r) for r in ("rs0", "rsv", "rs2", "rs4")] + \
       [("d07_c20", "rs4"), ("act_c20", "rs4")]


def cs_ic(var, row, p):
    """Cs after the idle: drift below nominal on all three; a diode clamp stops it at vf + Vout below the ladder, a
    switched clamp (closed through the idle) holds it at ladder - Vout."""
    d, v = DRIFT[row], ll.VARIANTS[var]
    if v is not None and v["kind"] == "diode":
        d = min(d, v["vf"] + p["vo0"])
    elif v is not None and v["kind"] == "active":
        d = p["vo0"]
    return [f * p["vin"] - d for f in (0.75, 0.5, 0.25)]


def run_lt(name, text, timeout=7200):
    """LTspice in batch; stdout / stderr to DEVNULL (wine keeps inherited pipes open, scb-experiment lesson 18)."""
    lt.WORK.mkdir(parents=True, exist_ok=True)
    net = lt.WORK / f"{name}.net"
    net.write_text(text.rstrip() + "\n" + OPTIONS + "\n.end\n")
    for ext in (".log", ".raw"):
        (lt.WORK / f"{name}{ext}").unlink(missing_ok=True)
    env = dict(os.environ, CX_ROOT=str(lt.CX))
    subprocess.run([str(lt.CX / "bin" / "wine"), "--bottle", "ltspice", "--cx-app", lt.EXE, "-b", lt._winpath(net)],
                   cwd=lt.WORK, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
    log = (lt.WORK / f"{name}.log").read_text(errors="replace") if (lt.WORK / f"{name}.log").exists() else ""
    rp = lt.WORK / f"{name}.raw"
    if not rp.exists():
        raise RuntimeError(f"LTspice produced no .raw for {name}: {log[-400:]}")
    return lt.read_raw(rp), log, rp


def compact(names, arr, p, dt=20e-9):
    """Rails, Vin, Vo, the ladder and the switch voltages on a grid of dt; each phase's per-period current peak."""
    w = ll.waves(names, arr)
    t = w["t"]
    grid = np.arange(0.0, t[-1], dt)
    f = lambda y, n=4: np.interp(grid, t, y).round(n).tolist()
    tr = {"t_us": (grid * 1e6).round(4).tolist(), "vin": f(w["vin"]), "vo": f(w["vo"], 5),
          "rails": [f(r) for r in w["rails"]], "sw": [f(s, 3) for s in ll.sw_volts(w)]}
    if w["ladder"] is not None:
        tr["ladder"] = [f(x) for x in w["ladder"]]
    if dt <= p["T"]:
        edges = np.arange(0.0, t[-1] + p["T"], p["T"])
        idx = np.searchsorted(t, edges)
        tr["period_peak"] = [[round(float(i[a:b].max()), 2) if b > a else None for a, b in zip(idx[:-1], idx[1:])]
                             for i in w["il"]]
    return tr


def one(var, row, p, name, tag=None, dt=20e-9):
    t0 = time.time()
    (names, arr), log, rp = run_lt(name, ll.netlist(var, row, p))
    res = ll.metrics(names, arr, row, p)
    res.update(variant=var, row_label=tag or row, wall_s=round(time.time() - t0, 1), n_points=int(arr.shape[0]),
               params={k: p[k] for k in ("T", "ton0", "rload", "vo0", "il0", "t_shed", "t_rs", "t_win") if k in p},
               cs_ic=p.get("cs_ic"), ic=p.get("ic"),
               lt_warnings=[ln for ln in log.splitlines() if "arning" in ln or "rror" in ln][:5],
               trace=compact(names, arr, p, dt))
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{var}_{tag or row}.json").write_text(json.dumps(res))
    rp.unlink(missing_ok=True)
    return res


def job(x):
    var, row = x
    p = dict(ll.PARAMS, **(LIGHT if row.startswith("rs") else {}))
    if row.startswith("rs"):
        p["cs_ic"] = cs_ic(var, row, p)
    return var, row, one(var, row, p, f"a218_{var}_{row}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("only", nargs="*", help="variant_row names (default: the whole plan)")
    a = ap.parse_args()
    plan = [x for x in PLAN if not a.only or f"{x[0]}_{x[1]}" in a.only]
    with ThreadPoolExecutor(a.jobs) as ex:
        for var, row, res in ex.map(job, plan):
            print(f"{var:11s} {row:6s} {res['wall_s']:6.1f} s  rail_dev_max {res['rail_dev_max']:.2f}  "
                  f"peaks {[round(x) for x in res['il_peak']]}  settle {res['t_settle_us']:.2f} us", flush=True)


if __name__ == "__main__":
    sys.exit(main())
