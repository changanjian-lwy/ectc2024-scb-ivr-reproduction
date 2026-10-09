"""A180 runner: open-loop LTspice power stage of one P24 module with and without the LSCB ladder (extension lscb_ladder).

Run from the project root:
    PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_run.py [--jobs 2]
    ... a180_run.py --smoke [--param T=4.52e-7]      (base, steady state only: Vo, rails, phase currents)
Netlists, logs and .raw files stay in the LTspice work folder (p24_ltspice.WORK, outside the repository); a .raw is
deleted once its metrics are written. runs/<variant>_<row>.json holds the metrics (scb_ivr.extensions.lscb_ladder) and
a compact trace (rails, Vin, Vo on a 20 ns grid; each phase's per-period current peak) for the figures.
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
# p24_ltspice.OPTIONS is tuned for EPC's charge-defined capacitances; this circuit has linear parts only
OPTIONS = ".options plotwinsize=0 numdgt=15 reltol=1e-4"
PLAN = [(v, r) for r in ("up1", "up5", "dn1") for v in ll.VARIANTS] + \
       [(v, "su") for v in ("base", "d07_c20", "d30_c20", "act_c20")]


def run_lt(name, text, timeout=7200):
    lt.WORK.mkdir(parents=True, exist_ok=True)
    net = lt.WORK / f"{name}.net"
    net.write_text(text.rstrip() + "\n" + OPTIONS + "\n.end\n")
    for ext in (".log", ".raw"):
        (lt.WORK / f"{name}{ext}").unlink(missing_ok=True)
    env = dict(os.environ, CX_ROOT=str(lt.CX))
    subprocess.run([str(lt.CX / "bin" / "wine"), "--bottle", "ltspice", "--cx-app", lt.EXE, "-b", lt._winpath(net)],
                   cwd=lt.WORK, env=env, capture_output=True, timeout=timeout)
    log = (lt.WORK / f"{name}.log").read_text(errors="replace") if (lt.WORK / f"{name}.log").exists() else ""
    rp = lt.WORK / f"{name}.raw"
    if not rp.exists():
        raise RuntimeError(f"LTspice produced no .raw for {name}: {log[-400:]}")
    return lt.read_raw(rp), log, rp


def compact(names, arr, p):
    w = ll.waves(names, arr)
    t = w["t"]
    grid = np.arange(0.0, t[-1], 20e-9)
    tr = {"t_us": (grid * 1e6).round(4).tolist(), "vin": np.interp(grid, t, w["vin"]).round(4).tolist(),
          "vo": np.interp(grid, t, w["vo"]).round(5).tolist(),
          "rails": [np.interp(grid, t, r).round(4).tolist() for r in w["rails"]]}
    edges = np.arange(0.0, t[-1] + p["T"], p["T"])
    pk = []
    for i in w["il"]:
        idx = np.searchsorted(t, edges)
        pk.append([round(float(i[a:b].max()), 2) if b > a else None for a, b in zip(idx[:-1], idx[1:])])
    tr["period_peak"] = {"t0_us": (edges[:-1] * 1e6).round(4).tolist(), "il": pk}
    return tr


def one(var, row, p, keep_raw=False):
    name = f"a180_{var}_{row}"
    t0 = time.time()
    (names, arr), log, rp = run_lt(name, ll.netlist(var, row, p))
    res = ll.metrics(names, arr, row, p)
    res.update(variant=var, wall_s=round(time.time() - t0, 1), n_points=int(arr.shape[0]),
               params={k: p[k] for k in ("T", "ton0", "t_dead", "r_on", "t_step", "t_end", "t_win", "vo0", "il0")},
               lt_warnings=[ln for ln in log.splitlines() if "arning" in ln or "rror" in ln][:5],
               trace=compact(names, arr, p))
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{var}_{row}.json").write_text(json.dumps(res))
    if not keep_raw:
        rp.unlink(missing_ok=True)
    return var, row, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--param", action="append", default=[])
    ap.add_argument("only", nargs="*", help="variant_row names (default: the whole plan)")
    a = ap.parse_args()
    p = dict(ll.PARAMS)
    for kv in a.param:
        k, v = kv.split("=")
        p[k] = float(v)
    if a.smoke:
        q = dict(p, t_end=p["t_step"])
        (names, arr), log, rp = run_lt("a180_smoke_base", ll.netlist("base", "up1", q))
        w = ll.waves(names, arr)
        t = w["t"]
        for a0, b0 in ((10e-6, 20e-6), (30e-6, 40e-6)):
            m = (t >= a0) & (t < b0)
            avg = lambda y: float(np.trapezoid(y[m], t[m]) / (t[m][-1] - t[m][0]))
            print(f"{a0 * 1e6:.0f}-{b0 * 1e6:.0f} us: Vo {avg(w['vo']):.4f}  rails {[round(avg(r), 3) for r in w['rails']]}"
                  f"  IL avg {[round(avg(i), 1) for i in w['il']]}  peak {[round(float(i[m].max()), 1) for i in w['il']]}"
                  f"  min {[round(float(i[m].min()), 1) for i in w['il']]}  loss {avg(w['pin'] - w['vo'] ** 2 / p['rload']):.2f} W")
        print("points", arr.shape[0], "warnings", [ln for ln in log.splitlines() if "arning" in ln][:3])
        rp.unlink(missing_ok=True)
        return
    plan = [x for x in PLAN if not a.only or f"{x[0]}_{x[1]}" in a.only]
    with ThreadPoolExecutor(a.jobs) as ex:
        for var, row, res in ex.map(lambda x: one(x[0], x[1], p), plan):
            post = res.get("post") or res.get("startup")
            print(f"{var:11s} {row}: {res['wall_s']:6.1f} s  spread {res['pre']['spread_pct']:.2f} %  "
                  f"rail1_exc {post.get('rail1_exc', float('nan')):.2f}  peaks {[round(x) for x in post['il_peak']]}",
                  flush=True)


if __name__ == "__main__":
    sys.exit(main())
