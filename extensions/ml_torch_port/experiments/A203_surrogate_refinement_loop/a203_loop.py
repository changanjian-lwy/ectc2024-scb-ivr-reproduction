"""A203 loop: A202's gradient search on the surrogate, D63 on the designs it proposes, the surrogate fine-tuned on
those D63 runs, repeated. Writes a203_loop.json and a203_surrogate_final.npz (the fine-tuned weights); prints <= 15 lines.

    PYTHONPATH=src <python with torch> .../a203_loop.py [--rounds 10] [--smoke]

Per round: A202's two searches (margin and front) on the current surrogate; 16 new designs are picked (the 8 smallest
surrogate worst peaks, then 8 spread along the surrogate's front; a design within the rounding grid of one already
run is skipped); D63 runs them on the 8 standard transients; their rows join A120's training rows with weight
NEW_WEIGHT; the surrogate is fine-tuned (Adam, EPOCHS epochs, lr LR, A120's L2 and scalers)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A202_surrogate_inverse_design"))

import a202_inverse as A  # noqa: E402
from a203_d63_reference import A120, judge, run_design  # noqa: E402
from torch_mlp import forward  # noqa: E402

DD = A.DD
PICKS, NEW_WEIGHT, EPOCHS, LR, L2, BATCH = 16, 10.0, 100, 5e-4, 1e-5, 128
GRID = {"pct": 0.05, "cs_uf": 0.05, "fc_khz": 0.5, "floor_a": 0.1}     # two designs closer than this count as one


def key(d):
    return (d["rule"], *(round(d[k] / g) for k, g in GRID.items()))


def a120_rows():
    """A120's training and test rows, standardised with its scalers (its split: first 80 % / last 10 % of the
    runs that did not diverge)."""
    z = np.load(A120 / "a120_dataset.npz")
    ok = ~z["div"]
    xs, ys = z["x"][ok], z["y"][ok]
    n = len(xs)
    return xs[:int(0.8 * n)], ys[:int(0.8 * n)], xs[int(0.9 * n):], ys[int(0.9 * n):]


def finetune(sur, x, y, w, seed):
    """Adam on the weighted summed-square loss (ml_nn's loss), warm-started from the surrogate's weights."""
    Ws, bs = [a.clone().requires_grad_() for a in sur.Ws], [a.clone().requires_grad_() for a in sur.bs]
    opt = torch.optim.Adam([{"params": Ws, "weight_decay": L2}, {"params": bs}], lr=LR)
    X, Y, Wt = torch.tensor(sur.sx.fwd(x)), torch.tensor(sur.sy.fwd(y)), torch.tensor(w)
    gen = torch.Generator().manual_seed(seed)
    for _ in range(EPOCHS):
        perm = torch.randperm(len(X), generator=gen)
        for k in range(0, len(X), BATCH):
            j = perm[k:k + BATCH]
            opt.zero_grad()
            ((Wt[j, None] * (forward(Ws, bs, X[j]) - Y[j]) ** 2).sum() / len(j)).backward()
            opt.step()
    sur.Ws, sur.bs = [a.detach() for a in Ws], [a.detach() for a in bs]
    sur.net.W, sur.net.b = [a.numpy().copy() for a in sur.Ws], [a.numpy().copy() for a in sur.bs]    # numpy path = the same network


def pick(designs, f1, f2, feas, seen):
    """PICKS new designs: half by the smallest surrogate worst peak, half spread along the surrogate's front."""
    order = np.lexsort((f1, ~feas))                                # feasible first, then by f1
    new, keys = [], set(seen)
    for i in order:
        if len(new) == PICKS // 2:
            break
        if key(designs[i]) not in keys:
            new.append(int(i)); keys.add(key(designs[i]))
    fi = np.nonzero(feas)[0]
    fr = [int(fi[j]) for j in A.front(f1[fi], f2[fi])] if len(fi) else []
    fr = [i for i in fr if key(designs[i]) not in keys]
    for i in ([fr[j] for j in sorted(set(np.linspace(0, len(fr) - 1, PICKS // 2).astype(int)))] if fr else []):
        if key(designs[i]) not in keys:
            new.append(i); keys.add(key(designs[i]))
    for i in order:                                                # fill up if the front was short
        if len(new) == PICKS:
            break
        if key(designs[i]) not in keys:
            new.append(int(i)); keys.add(key(designs[i]))
    return new


def main():
    smoke = "--smoke" in sys.argv
    rounds = 2 if smoke else int(sys.argv[sys.argv.index("--rounds") + 1]) if "--rounds" in sys.argv else 10
    git = lambda *a: subprocess.run(["git", "-C", str(A.PROJECT), *a], capture_output=True, text=True).stdout.strip()
    prov = {"commit": git("rev-parse", "--short", "HEAD"), "modified": bool(git("status", "--porcelain", "--", "extensions/ml_torch_port/*.py"))}
    sur = A.Surrogate()
    xtr, ytr, xte, yte = a120_rows()
    mae = lambda: float(np.mean(np.abs(sur.sy.inv(sur.net.predict(sur.sx.fwd(xte)))[:, 0] - yte[:, 0])))
    n_s, steps = (8, 20) if smoke else (64, 400)
    ws = torch.linspace(0.02, 0.98, 5 if smoke else 21)
    wt = ws.repeat_interleave(2 if smoke else 16)

    def cheb(f1, f2, pen):                                         # A202's scalarisation
        a, b = wt * (f1 - 150.0) / 50.0, (1 - wt) * f2 / 100.0
        return 0.2 * torch.logsumexp(torch.stack([a, b]) / 0.2, dim=0) + 0.05 * (a + b) + A.LAM * pen + torch.relu(f1 - 200.0)

    seen, xn, yn, log, best = set(), [], [], [], None
    t0 = time.time()
    for r in range(1, rounds + 1):
        des = A.search(sur, lambda f1, f2, pen: f1 + A.LAM * pen, n_s, steps, seed=2020 + 10 * r) + A.search(sur, cheb, len(wt), steps, seed=2021 + 10 * r)
        p, _ = sur.numpy_outputs(des)
        s1, s2, sfeas = A.hard(p)
        idx = pick(des, s1, s2, sfeas, seen)
        chosen = [des[i] for i in idx]
        seen.update(key(d) for d in chosen)
        res = np.array([run_design(d) for d in chosen])
        d1, d2, dfeas, ddiv = judge(res)
        rows = []
        for j, d in enumerate(chosen):
            rows.append({"design": d, "kind": "margin" if j < PICKS // 2 else "front", "mlp_f1": float(s1[idx[j]]), "mlp_f2": float(s2[idx[j]]),
                         "mlp_feasible": bool(sfeas[idx[j]]), "d63_f1": float(d1[j]), "d63_f2": float(d2[j]), "d63_feasible": bool(dfeas[j]),
                         "d63_diverged": bool(ddiv[j])})
            if dfeas[j] and (best is None or d1[j] < best["d63_f1"]):
                best = dict(rows[-1], round=r)
            for t, (k, di, dv, sl) in enumerate(A.STANDARD):       # the new rows, in A120's features and targets
                if not res[j, t, 4]:
                    xn.append(DD.features([dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl)])[0])
                    yn.append([res[j, t, 0], res[j, t, 1], res[j, t, 2], np.log1p(res[j, t, 3]), np.log1p(res[j, t, 5])])
        m = [q for q in rows if q["kind"] == "margin" and not q["d63_diverged"]]
        log.append({"round": r, "surrogate_feasible_finals": int(sfeas.sum()), "picks": rows, "d63_feasible_picks": int(dfeas.sum()),
                    "margin_optimism_a": float(np.mean([q["d63_f1"] - q["mlp_f1"] for q in m])) if m else None,
                    "best_d63_f1": None if best is None else best["d63_f1"], "test_mae_before_a": mae(), "d63_designs_so_far": r * PICKS})
        finetune(sur, np.concatenate([xtr, np.array(xn)]), np.concatenate([ytr, np.array(yn)]),
                 np.concatenate([np.ones(len(xtr)), np.full(len(xn), NEW_WEIGHT)]), seed=r)
        log[-1]["test_mae_after_a"] = mae()
        if not smoke:
            o = log[-1]["margin_optimism_a"]
            print(f"round {r}: {int(sfeas.sum())} surrogate-feasible finals; D63 feasible {int(dfeas.sum())} of {PICKS}; margin optimism "
                  f"{'n/a' if o is None else format(o, '+.1f')} A; best so far {'none' if best is None else format(best['d63_f1'], '.2f')} A; "
                  f"test MAE {log[-1]['test_mae_after_a']:.2f} A", flush=True)
    if smoke:
        print(f"smoke ok: {rounds} rounds in {time.time() - t0:.0f} s, {len(xn)} new rows")
        return
    out = {"provenance": prov, "settings": {"picks": PICKS, "new_weight": NEW_WEIGHT, "epochs": EPOCHS, "lr": LR, "l2": L2, "rounds": rounds},
           "seconds": time.time() - t0, "best": best, "rounds": log}
    (HERE / "a203_loop.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    np.savez(HERE / "a203_surrogate_final.npz", **{f"W{i}": a for i, a in enumerate(sur.net.W)}, **{f"b{i}": a for i, a in enumerate(sur.net.b)})
    print(f"loop: {rounds} rounds, {rounds * PICKS} D63 designs, {out['seconds']:.0f} s, commit {prov['commit']}{' (MODIFIED)' if prov['modified'] else ''}")


if __name__ == "__main__":
    main()
