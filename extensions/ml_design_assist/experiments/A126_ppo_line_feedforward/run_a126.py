"""A126: deep reinforcement learning (PPO) of a per-phase Ton feed-forward in D63's environment at A124's 2.5 MHz design,
against fixed physics laws, for three sensor sets (ml_rl_ff).

    python3 .../run_a126.py setup       # A124's design with D57's thresholds -> a126_design.json (~1 min)
    python3 .../run_a126.py baselines   # the fixed laws on the held-out set and A124's rows -> a126_baselines.json
    python3 .../run_a126.py train       # PPO, 3 sensor sets x 3 seeds, in parallel -> a126_policy_<sensors>_s<seed>.npz
    python3 .../run_a126.py evaluate    # every policy (greedy) and law on the same disturbances -> a126_summary.json
    python3 .../run_a126.py distill     # a few-parameter rule fitted to the best policy -> a126_distill.json

Held-out set: 64 disturbances from sample_dist (seed 12345) at random Cs factors, and A124's seven step rows at Cs x 1.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions import ml_rl_ff as F  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP  # noqa: E402
from scb_ivr.extensions.ml_ppo import GaussianPolicy, train  # noqa: E402

CFG = HERE / "a126_design.json"
VARIANTS = ("rtl", "vin", "rails")
SEEDS = (0, 1, 2)
ITERS, EPISODES, LR = 600, 32, 3e-4


def setup():
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import node_model
    from scb_ivr.p24_valley_map import thresholds
    pred = json.loads((PROJECT / "experiments" / "track_A_periodic_steady_state" / "A124_p24_two_point_five_mhz" / "a124_predictions.json").read_text())
    lf = 7.3333333e-9 / 2.5
    e = EdgeCircuit()
    t1 = node_model(replace(e, lf=lf)).valley_free(15.625, t_max=200e-9)[0]
    t4 = node_model(replace(e, lf=lf, v_rail=12.0, dv_cs=0.0, n_next=0)).valley_free(15.625, t_max=200e-9)[0]
    out = {"lf": lf, "i_tgt": -15.625, "kp_ns": pred["loop"]["kp_ns_per_v"], "ki_ns": pred["loop"]["ki_ns_per_v"],
           "t_tr": [t1, t1, t1, t4], "ith": [list(x) for x in thresholds(lf)]}
    CFG.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", CFG.name)


def held_out():
    rng = np.random.default_rng(12345)
    return [(F.sample_dist(rng), float(rng.choice(F.CS_FACTORS))) for _ in range(64)]


def score(env, chooser):
    """Returns and summaries on the held-out set and A124's rows."""
    res = {"held_out": [], "a124": {}}
    for dist, cs in held_out():
        ret, recs, div = F.episode(env, chooser, dist, cs)
        res["held_out"].append({"dist": list(dist), "cs": cs, "return": ret, "diverged": div, **F.summarise(recs)})
    for name, dist in F.A124_ROWS.items():
        ret, recs, div = F.episode(env, chooser, dist, 1.0)
        res["a124"][name] = {"return": ret, "diverged": div, **F.summarise(recs)}
    h = res["held_out"]
    res["mean_return"] = float(np.mean([x["return"] for x in h]))
    res["diverged"] = int(sum(x["diverged"] for x in h))
    res["worst_peak_a"] = float(max(x["peak_a"] for x in h))
    res["share_peak_le_ilim"] = float(np.mean([x["peak_a"] <= F.I_LIM for x in h]))
    return res


def show(name, r):
    a = r["a124"]
    print(f"{name:16s}: held-out return {r['mean_return']:8.2f}, diverged {r['diverged']}, worst peak {r['worst_peak_a']:5.0f} A, "
          f"peak <= {F.I_LIM:.0f} A {r['share_peak_le_ilim']:.0%} | A124 rows peak " + " ".join(f"{k[5:]} {v['peak_a']:.0f}" for k, v in a.items())
          + " | Vo " + " ".join(f"{v['extreme_mv']:+.1f}" for v in a.values()))


def baselines():
    env = F.Env(CFG, "vin")
    out = {}
    for name, law in F.LAWS.items():
        out[name] = score(env, ("law", law))
        show(name, out[name])
    (HERE / "a126_baselines.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


def _train(args):
    sensors, seed = args
    env = F.Env(CFG, sensors)
    log = []
    t0 = time.time()
    pol, critic, hist = train(env, env.n_obs, 4, iters=ITERS, episodes=EPISODES, lr=LR, log_std=-1.0, seed=seed,
                              log=lambda s: log.append(s))
    np.savez(HERE / f"a126_policy_{sensors}_s{seed}.npz", hist=np.array(hist), log_std=pol.log_std,
             **{f"W{i}": w for i, w in enumerate(pol.net.W)}, **{f"b{i}": b for i, b in enumerate(pol.net.b)})
    return sensors, seed, hist, log, time.time() - t0


def train_all():
    jobs = [(v, s) for v in VARIANTS for s in SEEDS]
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        for sensors, seed, hist, log, dt in ex.map(_train, jobs):
            print(f"{sensors} seed {seed}: {dt:.0f} s; return {np.mean(hist[:5]):.1f} -> {np.mean(hist[-10:]):.1f}")
            for line in log[::4] + log[-1:]:
                print("   ", line)


def load_policy(sensors, seed):
    z = np.load(HERE / f"a126_policy_{sensors}_s{seed}.npz")
    n = sum(1 for k in z.files if k.startswith("W"))
    net = MLP.__new__(MLP); net.out = "linear"
    net.W = [z[f"W{i}"] for i in range(n)]; net.b = [z[f"b{i}"] for i in range(n)]
    return lambda o: net.predict(np.atleast_2d(o))[0], z["hist"]


def evaluate():
    base = json.loads((HERE / "a126_baselines.json").read_text())
    out = {"laws": base, "policies": {}}
    for name, r in base.items():
        show(name, r)
    for sensors in VARIANTS:
        env = F.Env(CFG, sensors)
        for seed in SEEDS:
            fn, hist = load_policy(sensors, seed)
            r = score(env, ("policy", fn))
            r["train_curve"] = hist.tolist()
            out["policies"][f"{sensors}_s{seed}"] = r
            show(f"PPO {sensors} s{seed}", r)
    (HERE / "a126_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")


if __name__ == "__main__":
    {"setup": setup, "baselines": baselines, "train": train_all, "evaluate": evaluate}[sys.argv[1]]()
