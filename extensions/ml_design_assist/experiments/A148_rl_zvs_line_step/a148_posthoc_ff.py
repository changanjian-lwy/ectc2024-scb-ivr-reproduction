"""A148 post hoc (not registered): the registered policies failed the steady check because two observations are
feedback (phase 1's last valley report and hard-turn-on bit): the anchor zeroes the action only where the features
are zero, and the closed loop found a nonzero equilibrium (lo_add +300 ns, phase 1 on the floor every period). Here
the actor sees only the feed-forward features (rail excess, Vin slope, Ton vs its low-pass) and the context, as in
A127, so the action is exactly zero at constant Vin and load. Same cost (w_vo 1), PPO settings and eval set; then the
same distillation. Usage: a148_posthoc_ff.py train | evaluate. Writes a148_policy_ff_s{seed}.npz, a148_posthoc_ff.json."""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a148_d63 as M  # noqa: E402
import a148_run as R  # noqa: E402

from scb_ivr.extensions.ml_ppo import GaussianPolicy, train  # noqa: E402

KEEP = [0, 1, 2, 5]


class EnvFF(M.Env):
    N_OBS, N_TRANS = 4, 3

    @staticmethod
    def anchor(O):
        O = np.array(O, dtype=float, copy=True)
        O[:, :EnvFF.N_TRANS] = 0.0
        return O

    def obs(self):
        return M.Env.obs(self)[KEEP]

    def critic_obs(self, o=None):
        return M.Env.critic_obs(self, M.Env.obs(self))


def _train(seed):
    env = EnvFF(R.HORIZON)
    t0 = time.time()
    with open(R.LOGS / f"a148_ff_s{seed}.log", "w") as f:
        pol, _, hist = train(env, EnvFF.N_OBS, 1, iters=R.ITERS, episodes=R.EPISODES, lr=R.LR, log_std=-1.0, seed=seed,
                             anchor=EnvFF.anchor, critic_obs=lambda e, o: e.critic_obs(o), n_critic=M.Env.N_CRITIC,
                             log_std_max=-1.0, log=lambda s: (f.write(s + "\n"), f.flush()))
    np.savez(HERE / f"a148_policy_ff_s{seed}.npz", hist=np.array(hist), log_std=pol.log_std,
             **{f"W{i}": w for i, w in enumerate(pol.net.W)}, **{f"b{i}": b for i, b in enumerate(pol.net.b)})
    return f"ff s{seed}: {time.time() - t0:.0f} s, return {np.mean(hist[:5]):.1f} -> {np.mean(hist[-10:]):.1f}"


def chooser(seed):
    z = np.load(HERE / f"a148_policy_ff_s{seed}.npz")
    pol = GaussianPolicy(EnvFF.N_OBS, 1, anchor=EnvFF.anchor)
    pol.net.W = [z[f"W{i}"] for i in range(len(pol.net.W))]
    pol.net.b = [z[f"b{i}"] for i in range(len(pol.net.b))]
    return lambda env, o: ("a", pol.mean(np.asarray(o)[KEEP])[0])


def _eval(seed):
    return R.arm_eval(f"ff_s{seed}", chooser(seed), 1.0)


def distill(seed):
    ch, env = chooser(seed), M.Env(R.HORIZON)
    F, A = [], []
    for st in R.eval_set():
        o = env.reset(st=st)
        done = False
        while not done:
            F.append(R.features(env))
            a = float(np.clip(np.ravel(ch(env, o)[1])[0], -2, 3))
            A.append(M.Env.A_NS * a)
            o, _, done, _ = env.step(a)
    F, A = np.array(F), np.array(A)
    fits = {}
    for k, idx in R.SETS.items():
        w, *_ = np.linalg.lstsq(F[:, idx], A, rcond=None)
        fits[k] = {"idx": idx, "w": w.tolist(), "r2": float(1 - np.sum((A - F[:, idx] @ w) ** 2) / np.sum((A - A.mean()) ** 2))}
    return {"fits": fits, "corr_vs": float(np.corrcoef(F[:, 0], A)[0, 1]), "n": len(A),
            "action_ns": {"mean": float(A.mean()), "max": float(A.max()), "min": float(A.min())}}


def main(cmd):
    if cmd == "train":
        with ProcessPoolExecutor(3) as ex:
            for msg in ex.map(_train, R.SEEDS):
                print(msg)
        return
    ev = json.loads((HERE / "a148_eval.json").read_text())
    with ProcessPoolExecutor(3) as ex:
        res = dict(ex.map(_eval, R.SEEDS))
    for k in res:
        res[k]["checks"] = R.checks(res[k], ev["B0@1"])
    best = min(R.SEEDS, key=lambda s: res[f"ff_s{s}@1"]["mean_cost"])
    out = {"runs": res, "best": best, "distill": distill(best),
           "ref": {k: ev[k]["mean_cost"] for k in ("B0@1", "vs0.75_inf@1")}}
    (HERE / "a148_posthoc_ff.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in res.items():
        rw = v["rows"]
        print(f"{k:10s} cost {v['mean_cost']:7.1f} | p48_1us von1 {rw['l_p48_1us']['von1_max']:4.1f} pk {rw['l_p48_1us']['peak_max']:5.1f}"
              f" | p48_5us {rw['l_p48_5us']['von1_max']:4.1f} | s_p62 {max(rw['s_p62']['von_max']):4.1f}"
              f" | st {int(v['checks']['steady'])} lg {int(v['checks']['long'])} add {v['steady']['add_max_ns']:.2f}")
    d = out["distill"]
    print(f"refs: B0 {out['ref']['B0@1']:.1f}, law {out['ref']['vs0.75_inf@1']:.1f}; best ff_s{best}; corr(vs) {d['corr_vs']:.3f}; "
          + " ".join(f"{k} R2 {x['r2']:.2f} w {np.round(x['w'], 3).tolist()}" for k, x in d["fits"].items() if k in ("vs", "rail+ton")))


if __name__ == "__main__":
    main(sys.argv[1])
