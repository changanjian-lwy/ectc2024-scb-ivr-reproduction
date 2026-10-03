"""A122: REINFORCE on phase 1's turn-off rule in D63's environment (A118's f6 design), against the fixed rules, on
held-out disturbances; the policy's choices distilled. Writes a122_policy.npz and a122_summary.json.

    python3 extensions/ml_design_assist/experiments/A122_rl_turn_off_policy/run_a122.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.ml_rl import RULES, Env, rollout, sample_dist, train  # noqa: E402
from scb_ivr.p24_valley_map import Design  # noqa: E402

D63 = PROJECT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D63_valley_map.json"
A118_SET = [("load", -62.5), ("load", 62.5)] + [("line", dv, s) for s in (1.0, 5.0, 20.0) for dv in (4.8, -4.8)]


def evaluate(env, dists, chooser):
    out = []
    for dist in dists:
        R, acts, obs, rews, recs = rollout(env, dist, chooser)
        out.append({"dist": dist, "return": R, "peak": max(max(r["peak"]) for r in recs),
                    "ph1_depth": max(r["depth"][0] for r in recs), "acts": acts, "obs": [o.tolist() for o in obs]})
    return out


def main():
    ith = json.loads(D63.read_text())["thresholds"]["7.3333333e-09"]
    d = Design(cs=6e-6, ith=tuple(tuple(x) for x in ith), t_tr=(16.904e-9,) * 3 + (15.082e-9,))
    env = Env(d)
    pol, hist = train(env, log=print)
    np.savez(HERE / "a122_policy.npz", W=pol.W, hist=np.array(hist))
    rng = np.random.default_rng(99)
    held = [sample_dist(rng) for _ in range(64)]
    res = {"train_hist": hist, "W": pol.W.tolist(), "eval": {}, "a118_set": {}}
    choosers = {name: (lambda o, a=a: a) for a, name in enumerate(RULES)}
    choosers["learned"] = lambda o: pol.act(o)
    for name, ch in choosers.items():
        ev = evaluate(env, held, ch)
        res["eval"][name] = {"mean_return": float(np.mean([e["return"] for e in ev])), "worst_peak": float(max(e["peak"] for e in ev)),
                             "share_peak_le_200": float(np.mean([e["peak"] <= 200 for e in ev])),
                             "max_ph1_depth": float(max(e["ph1_depth"] for e in ev))}
        a1 = evaluate(env, A118_SET, ch)
        res["a118_set"][name] = [{"dist": e["dist"], "return": e["return"], "peak": e["peak"]} for e in a1]
        if name == "learned":
            res["learned_actions"] = dict(Counter(RULES[a] for e in ev for a in e["acts"]))
            learned_ev = ev
        print(f"{name:8s}: held-out mean return {res['eval'][name]['mean_return']:8.1f}, worst peak {res['eval'][name]['worst_peak']:5.0f} A, "
              f"peak <= 200 A in {res['eval'][name]['share_peak_le_200']:.0%}, max phase-1 crossing {res['eval'][name]['max_ph1_depth']:.1f} A")
    print("learned policy's choices on the held-out set:", res["learned_actions"])
    # distillation: the best rule with up to two thresholds on single observations (choose among the three rules)
    X = np.array([o for e in learned_ev for o in e["obs"]]); A = np.array([a for e in learned_ev for a in e["acts"]])
    names = ["e_vo", "d_ton", "dd_ton", "ph1_valley"]
    best = (np.mean(A == Counter(A.tolist()).most_common(1)[0][0]), "constant", None)
    for j in range(4):
        for q in np.quantile(X[:, j], np.linspace(0.02, 0.98, 49)):
            for lo_a in range(3):
                for hi_a in range(3):
                    acc = float(np.mean(np.where(X[:, j] <= q, lo_a, hi_a) == A))
                    if acc > best[0]:
                        best = (acc, f"{names[j]} <= {q:.3f} -> {RULES[lo_a]}, else {RULES[hi_a]}", (j, float(q), lo_a, hi_a))
    res["distilled"] = {"accuracy": best[0], "rule": best[1]}
    print(f"distilled (one threshold): {best[1]}, reproduces {best[0]:.1%} of the choices")
    f = res["eval"]
    best_fixed = max(("timed", "cmp", "floor"), key=lambda k: f[k]["mean_return"])
    res["criteria"] = {"return_within_5pct_of_best_fixed": f["learned"]["mean_return"] >= f[best_fixed]["mean_return"] * (1.05 if f[best_fixed]["mean_return"] < 0 else 0.95),
                       "worst_peak_floor_plus_5A": f["learned"]["worst_peak"] <= f["floor"]["worst_peak"] + 5.0,
                       "distilled_90pct": best[0] >= 0.90}
    res["best_fixed"] = best_fixed
    print(f"best fixed rule: {best_fixed}; criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in res["criteria"].items()))
    (HERE / "a122_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
