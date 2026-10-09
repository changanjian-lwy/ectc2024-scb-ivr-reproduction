"""A182 runner: A180's switched clamp opened by a detector (threshold vth on max_k |V(d(4-k)) - Vcs_k|, delay td,
one-shot window t_win) instead of at the step (extension lscb_ladder).

Run from the project root:
    PYTHONPATH=src:scripts python3 extensions/lscb_ladder/experiments/A182_lscb_detector_clamp/a182_run.py [--jobs 4]
Two passes. Pass 1 runs the active variant with its window never open (so only the 3.0 V diode acts) and finds the
detector's firing time t_det for each threshold; until the switch first closes, pass 2 is the same circuit, so the
window [t_det + td, t_det + td + t_win] is what a detector of that threshold and delay would produce. The "ideal" rows
open the same overlap window at the step (A180's trigger with A182's gating). runs/<name>.json as in A180.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A180_lscb_ladder_open_loop"))
import a180_run as a180                                                   # noqa: E402  (run_lt, compact)
from scb_ivr.extensions import lscb_ladder as ll                          # noqa: E402

RUNS = HERE / "runs"
VTH = (0.75, 1.5)                    # V; A180 steady rail ripple 0.45 V p-p plus a 0.13 V offset on clamp 1
TD = (0.1e-6, 0.3e-6, 1.0e-6)       # detector + floating-driver delay
ROWS = ("up1", "up5", "dn1")
GRID = [("act_c20", vth, td) for vth in VTH for td in TD] + [("act_c60", 0.75, 0.3e-6)]


def tag(vth, td):
    return f"v{int(round(vth * 100)):03d}_t{int(round(td * 1e9)):04d}"


def run(name, var, row, p, extra):
    t0 = time.time()
    (names, arr), log, rp = a180.run_lt(f"a182_{name}", ll.netlist(var, row, p))
    res = ll.metrics(names, arr, row, p)
    res.update(variant=var, wall_s=round(time.time() - t0, 1), n_points=int(arr.shape[0]),
               params={k: p[k] for k in ("T", "ton0", "t_dead", "r_on", "t_step", "t_end", "t_win", "vo0", "il0")},
               win=p.get("win"), lt_warnings=[ln for ln in log.splitlines() if "arning" in ln or "rror" in ln][:5],
               trace=a180.compact(names, arr, p), **extra)
    if extra.get("pass") == 1:
        res["detect"] = {}
        for vth in VTH:
            t_det, pre = ll.detect(names, arr, vth, p["t_step"])
            res["detect"][str(vth)] = dict(t_det=t_det, pre_dev_max=pre)
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"{name}.json").write_text(json.dumps(res))
    rp.unlink(missing_ok=True)
    return name, res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--pass1-only", action="store_true")
    a = ap.parse_args()
    base = dict(ll.PARAMS, save_ls=True)
    never = (-2.0, -1.0)
    p1 = [(f"nowin_{v[4:]}_{r}", v, r, dict(base, win=never), {"pass": 1}) for v in ("act_c20", "act_c60") for r in ROWS]
    ideal = [(f"ideal_{v[4:]}_{r}", v, r, dict(base, win=(base["t_step"], base["t_step"] + base["t_win"])),
              {"pass": 2, "trigger": "ideal"}) for v in ("act_c20", "act_c60") for r in ROWS]
    with ThreadPoolExecutor(a.jobs) as ex:
        done = dict(ex.map(lambda x: run(*x), p1))
    for name, res in done.items():
        print(name, {k: (round(d["t_det"] * 1e6 - 40, 3) if d["t_det"] else None, round(d["pre_dev_max"], 3))
                     for k, d in res["detect"].items()}, flush=True)
    if a.pass1_only:
        return
    plan = list(ideal)
    for var, vth, td in GRID:
        for r in ROWS:
            d = done[f"nowin_{var[4:]}_{r}"]["detect"][str(vth)]
            if d["t_det"] is None:
                print("no detection", var, vth, r, flush=True)
                continue
            w0 = d["t_det"] + td
            plan.append((f"det_{var[4:]}_{tag(vth, td)}_{r}", var, r, dict(base, win=(w0, w0 + base["t_win"])),
                         {"pass": 2, "trigger": "detector", "vth": vth, "td": td, "t_det": d["t_det"]}))
    with ThreadPoolExecutor(a.jobs) as ex:
        for name, res in ex.map(lambda x: run(*x), plan):
            post = res["post"]
            print(f"{name:28s} {res['wall_s']:6.1f} s  rail1_exc {post['rail1_exc']:+.2f}  peak {max(post['il_peak']):.1f}"
                  f"  clamp {max(post['clamp_peak_a']):.0f} A  ls {max(post['ls_peak_a']):.0f} A", flush=True)


if __name__ == "__main__":
    sys.exit(main())
