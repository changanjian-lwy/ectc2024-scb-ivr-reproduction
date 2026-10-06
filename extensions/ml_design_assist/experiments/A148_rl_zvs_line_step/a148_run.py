"""A148 D63 part: physics grid, PPO (anchored residual, asymmetric critic, 3 seeds), evaluation with the anti-gaming
checks, distillation. Usage: a148_run.py grid | train | evaluate | distill. Outputs a148_grid.json,
a148_policy_s{seed}.npz, a148_eval.json, a148_distill.json; logs in tmp/logs."""
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

from scb_ivr.extensions.ml_ppo import GaussianPolicy, train  # noqa: E402

PROJECT = HERE.parents[3]
LOGS = PROJECT / "tmp" / "logs"
SEEDS = (0, 1, 2)
W_VO = (1.0, 4.0)               # the registered weighting and the tight-Vo scenario
ITERS, EPISODES, LR, HORIZON = 600, 32, 3e-4, 200
EVAL_DRAWS, EVAL_SEED = 40, 999
A124 = {k: v for k, v in M.ROWS.items() if k != "n0"}
GRID = [("B0", None), ("S255", None), ("vr1", (1.0, None, True))] + [
    (f"vs{g}_{s or 'inf'}", (g, s, False)) for g in (0.5, 0.75, 1.0, 1.25) for s in (None, 20, 40)]


def eval_set():
    rng = np.random.default_rng(EVAL_SEED)
    return list(A124.values()) + [M.draw(rng) for _ in range(EVAL_DRAWS)]


def rollout(env, chooser, st, n=HORIZON):
    """chooser(env, o) -> ("a", action) or ("add", lo_add). Returns (records, total cost, diverged)."""
    o = env.reset(st=st)
    env.horizon = n
    total, done, info = 0.0, False, {}
    while not done:
        kind, x = chooser(env, o)
        o, r, done, info = env.step(x) if kind == "a" else env.step_add(x)
        total -= r
    return env.recs, total, bool(info.get("terminal"))


def law_chooser(spec):
    if spec is None:
        return lambda env, o: ("add", None)
    state = {}

    def make():
        return spec() if callable(spec) else M.VS(spec[0], spec[1], spec[2])

    def ch(env, o):
        if env.n == 0:
            state["law"] = make()
        return "add", state["law"](env.vff)
    return ch


def env_for(name, w_vo=1.0):
    return M.Env(HORIZON, M.design(255 if name == "S255" else 64), w_vo)


def _grid_one(args):
    name, spec, w = args
    env, ch = env_for(name, w), law_chooser(spec)
    return f"{name}|{w}", [rollout(env, ch, st)[1] for st in eval_set()]


def grid():
    with ProcessPoolExecutor(10) as ex:
        res = dict(ex.map(_grid_one, [(n, s, w) for w in W_VO for n, s in GRID]))
    out = {"best": {}, "arms": {}}
    for w in W_VO:
        arms = {k.split("|")[0]: {"mean": float(np.mean(v)), "a124": [float(x) for x in v[:len(A124)]],
                                  "draws_mean": float(np.mean(v[len(A124):]))} for k, v in res.items() if k.endswith(f"|{w}")}
        out["arms"][str(w)] = arms
        out["best"][str(w)] = min((k for k in arms if k.startswith("vs") or k == "vr1"), key=lambda k: arms[k]["mean"])
        print(f"w_vo {w}: " + " | ".join(f"{k} {v['mean']:.1f}" for k, v in sorted(arms.items(), key=lambda kv: kv[1]["mean"])[:5])
              + f" | B0 {arms['B0']['mean']:.1f}")
    (HERE / "a148_grid.json").write_text(json.dumps(out, indent=1) + "\n")


def tag(seed, w):
    return f"s{seed}" if w == 1.0 else f"s{seed}_w{w:g}"


def _train(args):
    seed, w = args
    env = M.Env(HORIZON, w_vo=w)
    LOGS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with open(LOGS / f"a148_{tag(seed, w)}.log", "w") as f:
        pol, _, hist = train(env, M.Env.N_OBS, 1, iters=ITERS, episodes=EPISODES, lr=LR, log_std=-1.0, seed=seed,
                             anchor=M.Env.anchor, critic_obs=lambda e, o: e.critic_obs(o), n_critic=M.Env.N_CRITIC,
                             log_std_max=-1.0, log=lambda s: (f.write(s + "\n"), f.flush()))
    np.savez(HERE / f"a148_policy_{tag(seed, w)}.npz", hist=np.array(hist), log_std=pol.log_std,
             **{f"W{i}": w for i, w in enumerate(pol.net.W)}, **{f"b{i}": b for i, b in enumerate(pol.net.b)})
    return f"{tag(seed, w)}: {time.time() - t0:.0f} s, return {np.mean(hist[:5]):.1f} -> {np.mean(hist[-10:]):.1f}"


def train_all():
    jobs = [(s, w) for w in W_VO for s in SEEDS]
    with ProcessPoolExecutor(len(jobs)) as ex:
        for msg in ex.map(_train, jobs):
            print(msg)


def load_policy(name):
    z = np.load(HERE / f"a148_policy_{name}.npz")
    pol = GaussianPolicy(M.Env.N_OBS, 1, anchor=M.Env.anchor)
    pol.net.W = [z[f"W{i}"] for i in range(len(pol.net.W))]
    pol.net.b = [z[f"b{i}"] for i in range(len(pol.net.b))]
    return lambda env, o: ("a", pol.mean(o)[0])


def tail(recs, n):
    t = recs[-n:]
    vo = [r["vo"] for r in t]
    return {"vo_pp_mv": 1e3 * (max(vo) - min(vo)), "vo_mean_mv": float(1e3 * (np.mean(vo) - M.VO)),
            "peak_a": max(max(r["peak"]) for r in t), "ton_ns": float(1e9 * np.mean([r["ton"] for r in t])),
            "rail_dev_v": max(abs(x - r["vin"] / 4) for r in t for x in r["rails"]),
            "von1_v": float(np.mean([r["von"][0] for r in t])), "add_max_ns": 1e9 * max(abs(r["lo_add"] or 0.0) for r in t)}


def arm_eval(name, ch, w):
    """Eval-set costs, A124 rows (L0 and L x 0.7 / 1.3), steady identity (600 periods), long horizon (1000)."""
    env = M.Env(HORIZON, M.design(255 if name.startswith("S255") else 64), w)
    out = {"costs": [], "rows": {}, "long": {}, "corners": {}}
    for st in eval_set():
        recs, c, div = rollout(env, ch, st)
        out["costs"].append(c)
    for row, st in A124.items():
        recs, c, div = rollout(env, ch, st)
        out["rows"][row] = {"cost": c, **M.stats(recs, t_step=M.Env.T_ENV)}
        recs, c, div = rollout(env, ch, st, 5 * HORIZON)
        out["long"][row] = {"diverged": div, **tail(recs, 200)}
    out["steady"] = tail(rollout(env, ch, ("none",), 600)[0], 300)
    for m in (0.7, 1.3):
        e = M.Env(HORIZON, M.design(64, m=m), w)
        out["corners"][str(m)] = {row: {"cost": (x := rollout(e, ch, st))[1], **M.stats(x[0], t_step=M.Env.T_ENV)}
                                  for row, st in A124.items()}
    out["mean_cost"] = float(np.mean(out["costs"]))
    return f"{name}@{w:g}", out


def _arm(args):
    name, w = args
    if name == "B0":
        return arm_eval(name, law_chooser(None), w)
    if name.startswith("rl_"):
        return arm_eval(name, load_policy(name[3:]), w)
    if name.startswith("distilled"):
        return arm_eval(name, rule_chooser(json.loads((HERE / "a148_distill.json").read_text())[f"{w:g}"]["rule"]), w)
    return arm_eval(name, law_chooser(dict(GRID)[name]), w)


def checks(a, b0):
    """The scb-ml-run checks against B0: steady identity and long-horizon settling."""
    s, r = a["steady"], b0["steady"]
    steady = (s["vo_pp_mv"] <= r["vo_pp_mv"] + 0.5 and abs(s["peak_a"] - r["peak_a"]) <= 1.0
              and s["rail_dev_v"] <= r["rail_dev_v"] + 0.1 and abs(s["ton_ns"] - r["ton_ns"]) <= 0.2)
    long = all(not x["diverged"] and x["vo_pp_mv"] <= b0["long"][k]["vo_pp_mv"] + 0.5
               and x["rail_dev_v"] <= b0["long"][k]["rail_dev_v"] + 0.2 for k, x in a["long"].items())
    return {"steady": steady, "long": long}


def evaluate(extra=False):
    best = json.loads((HERE / "a148_grid.json").read_text())["best"]
    arms = ([("distilled", w) for w in W_VO] if extra else
            [(n, w) for w in W_VO for n in ["B0", best[f"{w:g}"]] + [f"rl_{tag(s, w)}" for s in SEEDS]])
    with ProcessPoolExecutor(len(arms)) as ex:
        res = dict(ex.map(_arm, arms))
    path = HERE / "a148_eval.json"
    old = json.loads(path.read_text()) if path.exists() and extra else {}
    old.update(res)
    for k in res:
        res[k]["checks"] = old[k]["checks"] = checks(res[k], old[f"B0@{k.split('@')[1]}"])
    path.write_text(json.dumps(old, indent=1, default=float) + "\n")
    for k, v in res.items():
        rw = v["rows"]
        print(f"{k:16s} cost {v['mean_cost']:7.1f} | p48_1us von1 {rw['l_p48_1us']['von1_max']:4.1f} pk {rw['l_p48_1us']['peak_max']:5.1f}"
              f" | p48_5us {rw['l_p48_5us']['von1_max']:4.1f} | s_p62 {max(rw['s_p62']['von_max']):4.1f}"
              f" | pk {max(x['peak_max'] for x in rw.values()):5.1f} | st {int(v['checks']['steady'])} lg {int(v['checks']['long'])}"
              f" add {v['steady']['add_max_ns']:.2f}")


# ---- distillation ----
def features(env):
    """The offset's candidate inputs before the period (ns), from the controller's own signals."""
    v = env.vff
    tref, re, rs = (v.tlp >> 8) * M.LSB, v.volts(v.rail), v.volts(v.rss)
    p = env.prev
    rep = (p["valley"][0] - M.I_TGT) if p else 0.0
    return np.array([1e9 * (env.ton * re - tref * rs) / M.VO, 1e9 * tref * (re - rs) / M.VO,
                     1e9 * (env.ton - tref) * rs / M.VO, rep * env.d.lf / M.VO * 1e9,
                     env.vin - env.vin_prev, float(p["von"][0] > M.V_HARD) if p else 0.0])


FEATS = ["vs", "rail", "ton", "report", "slope", "dep"]
SETS = {"vs": [0], "rail+ton": [1, 2], "rail+ton+report": [1, 2, 3], "all": [1, 2, 3, 4, 5]}


def rule_chooser(rule):
    w, idx = np.array(rule["w"]), rule["idx"]
    return lambda env, o: ("add", float(np.clip(features(env)[idx] @ w, -200, 300)) * 1e-9)


def distill_one(w):
    ev = json.loads((HERE / "a148_eval.json").read_text())
    name = min((tag(s, w) for s in SEEDS), key=lambda t: ev[f"rl_{t}@{w:g}"]["mean_cost"])
    ch, env = load_policy(name), M.Env(HORIZON, w_vo=w)
    F, A = [], []
    for st in eval_set():
        o = env.reset(st=st)
        done = False
        while not done:
            F.append(features(env))
            _, a = ch(env, o)
            a = float(np.clip(a, -2, 3))
            A.append(M.Env.A_NS * a)
            o, _, done, _ = env.step(a)
    F, A = np.array(F), np.array(A)
    out = {"policy": name, "n": len(A), "fits": {}}
    for k, idx in SETS.items():
        wt, *_ = np.linalg.lstsq(F[:, idx], A, rcond=None)
        r2 = 1 - np.sum((A - F[:, idx] @ wt) ** 2) / np.sum((A - A.mean()) ** 2)
        out["fits"][k] = {"idx": idx, "w": wt.tolist(), "r2": float(r2), "feats": [FEATS[i] for i in idx]}
    full = out["fits"]["all"]["r2"]
    pick = next(k for k in SETS if out["fits"][k]["r2"] >= full - 0.05)
    out["rule"] = {"name": pick, **out["fits"][pick]}
    out["corr_vs"] = float(np.corrcoef(F[:, 0], A)[0, 1])
    for k, v in out["fits"].items():
        print(f"w_vo {w:g} {k:16s} R2 {v['r2']:.3f} w {np.round(v['w'], 3).tolist()}")
    print(f"w_vo {w:g}: policy {name}; corr(action, vs law) {out['corr_vs']:.3f}; rule {pick}")
    return out


def distill():
    out = {f"{w:g}": distill_one(w) for w in W_VO}
    (HERE / "a148_distill.json").write_text(json.dumps(out, indent=1) + "\n")
    evaluate(extra=True)


if __name__ == "__main__":
    {"grid": grid, "train": train_all, "evaluate": evaluate, "distill": distill}[sys.argv[1]]()
