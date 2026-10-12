"""A202: design search by gradients through A120's surrogate (backpropagation to the inputs), against A120's
exhaustive random search on the same surrogate and against D63. Writes a202_summary.json; prints <= 15 lines.

    PYTHONPATH=src <python with torch> .../a202_inverse.py [--smoke]

A design is (pct, Cs, fc, rule, floor); the surrogate (A120's MLP, 11 inputs -> 5 outputs) predicts each of the 8
standard transients. Two objectives: f1 = the worst peak (A), f2 = the worst |Vo extreme| (mV). Feasible is A120's
rule: every peak <= 200 A and phase 1 inside D63's refitted rule.
port     the surrogate in PyTorch against numpy, and autograd's input gradient against central differences
margin   the smallest f1: Adam on the box-constrained design from random starts, per rule, against the best of
         A120's 100 000 random designs
front    the (f1, f2) Pareto front: a smoothed Chebyshev scalarisation over a grid of weights, against the
         non-dominated set of the 100 000; compared by hypervolume below (200 A, 100 mV)
d63      D63 runs the designs both searches return: are they feasible there, and how optimistic is the surrogate
--smoke runs short searches and prints timings only."""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
A120 = PROJECT / "extensions" / "ml_design_assist" / "experiments" / "A120_d63_surrogate_mlp"
sys.path.insert(0, str(HERE.parents[1]))                           # torch_mlp.py
sys.path.insert(0, str(A120))

from explore_a120 import STANDARD, verdict  # noqa: E402
from torch_mlp import forward, tensors  # noqa: E402

from scb_ivr.extensions import ml_d63_data as DD  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP, Scaler  # noqa: E402

torch.set_default_dtype(torch.float64)
REF = (200.0, 100.0)                                               # hypervolume reference: A, mV
BOX = {"pct": (5.0, 15.0), "log_cs": (math.log(3.0), math.log(20.0)), "fc": (20.0, 80.0), "floor": (1.0, 5.0)}    # DD.sample's ranges
TAU_A, TAU_MV, LAM = 2.0, 2.0, 10.0                                # smooth-max temperatures and the rule penalty's weight


class Surrogate:
    def __init__(self):
        self.net, z = MLP.load(A120 / "a120_mlp.npz")
        self.sx, self.sy = Scaler(z["x_mean"], z["x_sd"]), Scaler(z["y_mean"], z["y_sd"])
        self.Ws, self.bs = tensors(self.net)
        self.xm, self.xs, self.ym, self.ys = (torch.tensor(a) for a in (z["x_mean"], z["x_sd"], z["y_mean"], z["y_sd"]))
        self.tr = torch.tensor([[float(k == "load"), di, dv, math.log(sl)] for k, di, dv, sl in STANDARD])    # (8, 4)

    def numpy_outputs(self, designs):
        """A120's path: (n, 8, 5) predictions in the targets' units."""
        feats = DD.features([dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl) for d in designs for k, di, dv, sl in STANDARD])
        return self.sy.inv(self.net.predict(self.sx.fwd(feats))).reshape(len(designs), len(STANDARD), -1), feats

    def torch_outputs(self, v, rule):
        """v: (n, 4) = pct, log Cs, fc, floor (ignored unless the rule is floor) -> (n, 8, 5)."""
        hot = torch.tensor([float(rule == r) for r in DD.RULES]).expand(len(v), 3)
        fl = v[:, 3:4] if rule == "floor" else torch.zeros(len(v), 1)
        des = torch.cat([v[:, :3], hot, fl], dim=1)                # (n, 7), DD.FEATURES' first seven
        x = torch.cat([des[:, None, :].expand(-1, len(STANDARD), -1), self.tr[None].expand(len(v), -1, -1)], dim=2)
        return forward(self.Ws, self.bs, (x - self.xm) / self.xs) * self.ys + self.ym


def box(u):
    """Unconstrained u -> the design box (a sigmoid per variable)."""
    lo = torch.tensor([b[0] for b in BOX.values()])
    hi = torch.tensor([b[1] for b in BOX.values()])
    return lo + (hi - lo) * torch.sigmoid(u)


def smooth_objectives(p):
    """Smooth f1, f2 and the rule's penalty from (n, 8, 5) predictions."""
    f1 = TAU_A * torch.logsumexp(p[:, :, 0] / TAU_A, dim=1)
    f2 = TAU_MV * torch.logsumexp(torch.sqrt(p[:, :, 1] ** 2 + 1.0) / TAU_MV, dim=1)
    pen = (torch.nn.functional.softplus(p[:, :, 2] - 12.0) * torch.sigmoid((torch.expm1(p[:, :, 3]) - 25.0) / 3.0)).sum(dim=1)
    return f1, f2, pen


def hard(p):
    """f1, f2 and A120's verdict from (n, 8, 5) numpy predictions."""
    f1, f2 = p[:, :, 0].max(axis=1), np.abs(p[:, :, 1]).max(axis=1)
    feas = np.array([verdict(p[i, :, 0], p[i, :, 2], np.expm1(p[i, :, 3])) for i in range(len(p))])
    return f1, f2, feas


def as_designs(v, rule):
    v = v.detach().numpy()
    return [{"pct": float(a[0]), "cs_uf": float(math.exp(a[1])), "fc_khz": float(a[2]), "rule": rule,
             "floor_a": float(a[3]) if rule == "floor" else 0.0} for a in v]


def search(sur, loss_fn, n, steps, seed, lr=0.05):
    """Adam on n random starts per rule; returns the final designs of all rules."""
    out = []
    for r, rule in enumerate(DD.RULES):
        u = (torch.randn(n, 4, generator=torch.Generator().manual_seed(seed + r)) * 1.5).requires_grad_()
        opt = torch.optim.Adam([u], lr=lr)
        for _ in range(steps):
            opt.zero_grad()
            loss_fn(*smooth_objectives(sur.torch_outputs(box(u), rule))).sum().backward()    # the starts do not interact
            opt.step()
        out += as_designs(box(u), rule)
    return out


def front(f1, f2):
    """Indices of the non-dominated points (both minimised), by increasing f1."""
    keep, best = [], math.inf
    for i in np.lexsort((f2, f1)):
        if f2[i] < best:
            keep.append(int(i)); best = f2[i]
    return keep


def hypervolume(f1, f2):
    hv, idx = 0.0, [i for i in front(f1, f2) if f1[i] < REF[0] and f2[i] < REF[1]]
    for a, i in enumerate(idx):
        nxt = f1[idx[a + 1]] if a + 1 < len(idx) else REF[0]
        hv += (nxt - f1[i]) * (REF[1] - f2[i])
    return hv


def d63_check(designs, mlp_f1, mlp_f2, ith, ttr):
    rows = []
    for d, a, b in zip(designs, mlp_f1, mlp_f2):
        res = [DD.evaluate((dict(d, kind=k, di_a=di, dv_v=dv, slew_us=sl), ith, ttr)) for k, di, dv, sl in STANDARD]
        ok = all(not r["diverged"] for r in res)
        pk, ex = max(r["peak_a"] for r in res), max(abs(r["extreme_mv"]) for r in res)
        feas = ok and verdict(np.array([r["peak_a"] for r in res]), np.array([r["ph1_depth_a"] for r in res]), np.array([r["ph1_periods"] for r in res]))
        rows.append({"design": d, "mlp_f1": float(a), "mlp_f2": float(b), "d63_f1": float(pk) if ok else None, "d63_f2": float(ex) if ok else None,
                     "d63_diverged": not ok, "d63_feasible": bool(feas)})
    return rows


def group_stats(rows):
    ok = [r for r in rows if not r["d63_diverged"]]
    return {"n": len(rows), "d63_feasible": int(sum(r["d63_feasible"] for r in rows)), "d63_diverged": len(rows) - len(ok),
            "peak_optimism_a": float(np.mean([r["d63_f1"] - r["mlp_f1"] for r in ok])) if ok else None,
            "extreme_optimism_mv": float(np.mean([r["d63_f2"] - r["mlp_f2"] for r in ok])) if ok else None}


def main():
    smoke = "--smoke" in sys.argv
    t0 = time.time()
    sur = Surrogate()
    designs = DD.sample(2000 if smoke else 100_000, 2024)
    p, feats = sur.numpy_outputs(designs)
    b1, b2, bfeas = hard(p)
    # port: the same numbers from PyTorch, and the input gradient against central differences
    x = torch.tensor(sur.sx.fwd(feats[:800]), requires_grad=True)
    y = forward(sur.Ws, sur.bs, x)
    port_fwd = float(np.max(np.abs(y.detach().numpy() - sur.net.predict(sur.sx.fwd(feats[:800])))))
    y[:, 0].sum().backward()
    xn, h = sur.sx.fwd(feats[:800]), 1e-5
    num = np.stack([(sur.net.predict(xn + h * e)[:, 0] - sur.net.predict(xn - h * e)[:, 0]) / (2 * h) for e in np.eye(xn.shape[1])], axis=1)
    port_grad = float(np.max(np.abs(x.grad.numpy() - num)) / np.max(np.abs(num)))
    t_brute = time.time() - t0
    # margin: the smallest worst peak
    n, steps = (8, 20) if smoke else (64, 400)
    t1 = time.time()
    dm = search(sur, lambda f1, f2, pen: f1 + LAM * pen, n, steps, seed=2020)
    pm, _ = sur.numpy_outputs(dm)
    m1, m2, mfeas = hard(pm)
    # front: a smoothed Chebyshev scalarisation, 21 weights x 16 starts per rule
    ws = torch.linspace(0.02, 0.98, 5 if smoke else 21)
    k = 2 if smoke else 16
    wt = ws.repeat_interleave(k)

    def cheb(f1, f2, pen):
        a, b = wt * (f1 - 150.0) / 50.0, (1 - wt) * f2 / 100.0
        return 0.2 * torch.logsumexp(torch.stack([a, b]) / 0.2, dim=0) + 0.05 * (a + b) + LAM * pen + torch.relu(f1 - 200.0)

    df = search(sur, cheb, len(wt), steps, seed=2021)
    pf, _ = sur.numpy_outputs(df)
    g1, g2, gfeas = hard(pf)
    t_grad = time.time() - t1
    if smoke:
        print(f"smoke ok: brute {len(designs)} designs {t_brute:.1f} s; gradient searches {len(dm)} + {len(df)} designs x {steps} steps {t_grad:.1f} s")
        return
    # all gradient designs together form the gradient front
    a1, a2, af = np.concatenate([m1, g1]), np.concatenate([m2, g2]), np.concatenate([mfeas, gfeas])
    alld = dm + df
    hv_b, hv_g = hypervolume(b1[bfeas], b2[bfeas]), hypervolume(a1[af], a2[af])
    fb = [int(np.nonzero(bfeas)[0][i]) for i in front(b1[bfeas], b2[bfeas])]
    fg = [int(np.nonzero(af)[0][i]) for i in front(a1[af], a2[af])]
    # D63 on: the 12 best margins of each search, and up to 12 designs spread along each front
    ith = tuple(tuple(v) for v in json.loads(DD.D63_DIAG.read_text())["thresholds"][str(DD.L1)])
    ttr = json.loads(str(np.load(A120 / "a120_dataset.npz")["ttr"]))
    pick = lambda idx: [idx[i] for i in sorted(set(np.linspace(0, len(idx) - 1, min(12, len(idx))).astype(int)))]
    bi, gi = np.nonzero(bfeas)[0], np.nonzero(af)[0]
    groups = {"brute_margin": [int(i) for i in bi[np.argsort(b1[bi])[:12]]], "brute_front": pick(fb),
              "grad_margin": [int(i) for i in gi[np.argsort(a1[gi])[:12]]], "grad_front": pick(fg)}
    checks = {}
    for nm, idx in groups.items():
        src = (designs, b1, b2) if nm.startswith("brute") else (alld, a1, a2)
        checks[nm] = d63_check([src[0][i] for i in idx], src[1][idx], src[2][idx], ith, ttr)
    stats = {nm: group_stats(rows) for nm, rows in checks.items()}
    best_b, best_g = float(b1[bfeas].min()), float(a1[af].min())
    gm = stats["grad_margin"]
    crit = {"c1_port": {"forward_max_abs": port_fwd, "input_grad_rel": port_grad, "pass": bool(port_fwd <= 1e-9 and port_grad <= 1e-6)},
            "c2_margin": {"brute_best_a": best_b, "grad_best_a": best_g, "pass": bool(best_g <= best_b + 0.5)},
            "c3_front": {"hv_brute": float(hv_b), "hv_grad": float(hv_g), "ratio": float(hv_g / hv_b), "pass": bool(hv_g >= 0.98 * hv_b)},
            "c4_d63": {**gm, "pass": bool(gm["d63_feasible"] >= 0.8 * gm["n"] and gm["peak_optimism_a"] is not None and gm["peak_optimism_a"] <= 4.0)}}
    out = {"reference": REF, "n_brute": len(designs), "brute_feasible": int(bfeas.sum()), "grad_designs": len(alld), "grad_feasible": int(af.sum()),
           "grad_evaluations": len(alld) * steps, "seconds": {"brute": t_brute, "grad": t_grad},
           "criteria": crit, "passed": int(sum(c["pass"] for c in crit.values())), "of": len(crit), "d63": stats,
           "front_brute": [{"f1": float(b1[i]), "f2": float(b2[i]), **designs[i]} for i in fb],
           "front_grad": [{"f1": float(a1[i]), "f2": float(a2[i]), **alld[i]} for i in fg], "checks": checks}
    (HERE / "a202_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    ok = lambda c: "PASS" if crit[c]["pass"] else "FAIL"
    print(f"A202: {out['passed']} of {out['of']} criteria pass")
    print(f"C1 {ok('c1_port')} port: forward {port_fwd:.1e}, input gradient vs differences {port_grad:.1e}")
    print(f"brute force: {int(bfeas.sum())} of {len(designs)} feasible, {t_brute:.1f} s; gradient: {int(af.sum())} of {len(alld)} final designs feasible, "
          f"{out['grad_evaluations']} design evaluations, {t_grad:.1f} s")
    print(f"C2 {ok('c2_margin')} smallest worst peak: brute {best_b:.2f} A, gradient {best_g:.2f} A")
    print(f"C3 {ok('c3_front')} hypervolume below {REF}: brute {hv_b:.1f} ({len(fb)} points), gradient {hv_g:.1f} ({len(fg)} points), ratio {hv_g / hv_b:.3f}")
    for nm, s in stats.items():
        o = "n/a" if s["peak_optimism_a"] is None else f"{s['peak_optimism_a']:+.1f} A, {s['extreme_optimism_mv']:+.1f} mV"
        print(f"  D63 on {nm}: {s['d63_feasible']} of {s['n']} feasible ({s['d63_diverged']} diverged); D63 - surrogate {o}")
    print(f"C4 {ok('c4_d63')} gradient max-margin designs in D63")
    f = lambda r: f"({r['f1']:.1f} A, {r['f2']:.1f} mV: {r['rule']} pct {r['pct']:.1f} Cs {r['cs_uf']:.1f} fc {r['fc_khz']:.0f})"
    print("front ends, brute: " + f(out["front_brute"][0]) + " .. " + f(out["front_brute"][-1]))
    print("front ends, grad:  " + f(out["front_grad"][0]) + " .. " + f(out["front_grad"][-1]))


if __name__ == "__main__":
    main()
