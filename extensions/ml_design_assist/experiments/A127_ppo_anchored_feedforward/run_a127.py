"""A127: PPO with an anchored residual policy (the action is zero in a steady state by construction), a 240-period
horizon and reward v2 (ml_rl_ff), for a pure Vin feed-forward ("vin_ff") and Vin plus the controller's signals
("vin_fb"), 3 seeds each; the steady-state identity and long-horizon checks; then distillation.

    python3 .../run_a127.py baselines   # the fixed laws: scores and checks -> a127_baselines.json
    python3 .../run_a127.py train       # 2 sensor sets x 3 seeds in parallel; logs in tmp/logs/ -> a127_policy_*.npz
    python3 .../run_a127.py evaluate    # policies: scores and checks -> a127_summary.json

Checks (BOUNDARY Section 2): steady identity - 600 periods without a disturbance at every Cs factor, the last 300
against no feed-forward (Vo peak-to-peak + 0.5 mV, ladder 0.1 V, peak 1 A); long horizon - A124's rows over 1200
periods, the last 200 against no feed-forward's on the same row (Vo peak-to-peak + 0.5 mV, ladder 0.2 V, peak 2 A).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions import ml_rl_ff as F  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP  # noqa: E402
from scb_ivr.extensions.ml_ppo import train  # noqa: E402

spec = importlib.util.spec_from_file_location("run_a126", HERE.parent / "A126_ppo_line_feedforward" / "run_a126.py")
A126 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A126)
CFG = A126.CFG
VARIANTS = ("vin_ff", "vin_fb")
SEEDS = (0, 1, 2)
ITERS, EPISODES, LR, HORIZON = 600, 32, 3e-4, 240
LOGS = PROJECT / "tmp" / "logs"


def make_env(sensors):
    return F.Env(CFG, sensors, horizon=HORIZON, reward="v2")


def run(env, chooser, dist, cs, n):
    env.horizon = n
    o = env.reset(dist=dist, cs_factor=cs)
    done, scales = False, []
    while not done:
        if chooser[0] == "law":
            o, _, done, info = env.step_law(chooser[1])
        else:
            a = chooser[1](o)
            scales.append([min(max(1 + 0.25 * v, 0.5), 1.25) for v in a])
            o, _, done, info = env.step(a)
    env.horizon = HORIZON
    return env.recs, scales, bool(info.get("terminal"))


def tail_stats(recs, n):
    a = recs[-n:]
    vo = np.array([r["vo"] for r in a])
    return {"vo_pp_mv": float(1e3 * np.ptp(vo)), "ladder_v": float(max(max(abs(x - r["vin"] / 4) for x in r["rails"]) for r in a)),
            "peak_a": float(max(max(r["peak"]) for r in a))}


def checks(env, chooser, ref=None):
    out = {"steady": {}, "long": {}}
    for cs in F.CS_FACTORS:
        recs, scales, div = run(env, chooser, ("none",), cs, 600)
        st = tail_stats(recs, 300)
        st["max_action"] = float(np.max(np.abs(np.array(scales) - 1))) if scales else 0.0
        st["diverged"] = div
        if ref:
            r = ref["steady"][str(cs)]
            st["pass"] = (not div and st["vo_pp_mv"] <= r["vo_pp_mv"] + 0.5 and st["ladder_v"] <= 0.1
                          and abs(st["peak_a"] - r["peak_a"]) <= 1.0)
        out["steady"][str(cs)] = st
    for name, dist in F.A124_ROWS.items():
        recs, _, div = run(env, chooser, dist, 1.0, 1200)
        st = tail_stats(recs, 200)
        st["diverged"] = div
        if ref:
            r = ref["long"][name]
            st["pass"] = (not div and st["vo_pp_mv"] <= r["vo_pp_mv"] + 0.5 and st["ladder_v"] <= 0.2
                          and abs(st["peak_a"] - r["peak_a"]) <= 2.0)
        out["long"][name] = st
    if ref:
        out["pass"] = all(v["pass"] for v in out["steady"].values()) and all(v["pass"] for v in out["long"].values())
    return out


def line(name, r):
    a = r["a124"]
    c = r.get("checks", {})
    return (f"{name:12s} ret {r['mean_return']:8.2f} div {r['diverged']} worst {r['worst_peak_a']:4.0f} | +4.8V 1/5us "
            f"{a['p125_l_p48_1us']['peak_a']:.0f}/{a['p125_l_p48_5us']['peak_a']:.0f} -4.8V 1us {a['p125_l_m48_1us']['peak_a']:.0f} "
            f"load {a['p125_s_p62']['peak_a']:.0f}/{a['p125_s_m62']['peak_a']:.0f} | Vo " + "/".join(f"{v['extreme_mv']:+.0f}" for v in a.values())
            + (f" | checks {'PASS' if c.get('pass') else 'FAIL'}" if "pass" in c else ""))


def baselines():
    env = make_env("vin_ff")
    out = {}
    for name, law in F.LAWS.items():
        out[name] = A126.score(env, ("law", law))
    ref = checks(env, ("law", F.law_none))
    for name, law in F.LAWS.items():
        out[name]["checks"] = checks(env, ("law", law), ref)
        print(line(name, out[name]))
    out["reference"] = ref
    (HERE / "a127_baselines.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


def _train(args):
    sensors, seed = args
    env = make_env(sensors)
    LOGS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(LOGS / f"a127_{sensors}_s{seed}.log", "w") as f:
        pol, _, hist = train(env, env.n_obs, 4, iters=ITERS, episodes=EPISODES, lr=LR, log_std=-1.0, seed=seed,
                             anchor=env.anchor, log=lambda s: (f.write(s + "\n"), f.flush()))
    np.savez(HERE / f"a127_policy_{sensors}_s{seed}.npz", hist=np.array(hist), log_std=pol.log_std,
             **{f"W{i}": w for i, w in enumerate(pol.net.W)}, **{f"b{i}": b for i, b in enumerate(pol.net.b)})
    return f"{sensors} s{seed}: {time.time() - t0:.0f} s, return {np.mean(hist[:5]):.1f} -> {np.mean(hist[-10:]):.1f}"


def train_all():
    jobs = [(v, s) for v in VARIANTS for s in SEEDS]
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        for msg in ex.map(_train, jobs):
            print(msg)


def load_policy(sensors, seed, env):
    z = np.load(HERE / f"a127_policy_{sensors}_s{seed}.npz")
    n = sum(1 for k in z.files if k.startswith("W"))
    net = MLP.__new__(MLP); net.out = "linear"
    net.W = [z[f"W{i}"] for i in range(n)]; net.b = [z[f"b{i}"] for i in range(n)]

    def fn(o):
        o = np.atleast_2d(o)
        return (net.predict(o) - net.predict(env.anchor(o)))[0]
    return fn, z["hist"]


def evaluate():
    base = json.loads((HERE / "a127_baselines.json").read_text())
    ref = base["reference"]
    out = {"laws": {k: v for k, v in base.items() if k != "reference"}, "policies": {}}
    for name, r in out["laws"].items():
        print(line(name, r))
    for sensors in VARIANTS:
        env = make_env(sensors)
        for seed in SEEDS:
            fn, hist = load_policy(sensors, seed, env)
            r = A126.score(env, ("policy", fn))
            r["checks"] = checks(env, ("policy", fn), ref)
            r["train_curve"] = hist.tolist()
            out["policies"][f"{sensors}_s{seed}"] = r
            print(line(f"{sensors}_s{seed}", r))
    (HERE / "a127_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    {"baselines": baselines, "train": train_all, "evaluate": evaluate}[sys.argv[1]]()
