"""A200: every hand-written gradient left in ml_design_assist against PyTorch's autograd, in float64 on the CPU.
Writes a200_audit.json; prints <= 15 lines.

    PYTHONPATH=src <python with torch> .../a200_audit.py [--smoke]

mlp    ml_nn.MLP.loss_grads: the linear output with sample weights (A120's stored network and data, and the initial
       weights) and the sigmoid output with cross-entropy
fit    ml_nn.MLP.fit: 20 Adam steps with its L2 term against torch.optim.Adam(weight_decay on the weights only)
cnn    ml_cnn's layers A199 left out: A147's autoencoder (up) at its stored weights, and a network with tanh,
       unflatten and up
ppo    ml_ppo.update: the actor's clipped-surrogate gradient (plain and anchored policy) and the critic's, taken
       from the function itself through a recording optimiser
pg     ml_rl.train: one REINFORCE step on synthetic episodes; its gradient is the change of W at lr 1
gp     ml_gp.GP: the negative log marginal likelihood (value; autograd against central differences), and whether
       its finite-difference L-BFGS-B fits of A150's four outputs had converged (refit with the exact gradient)
A gradient difference is max |autograd - hand| / max |hand| per tensor (see gdiff)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
ML = PROJECT / "extensions" / "ml_design_assist" / "experiments"
sys.path.insert(0, str(HERE.parents[1]))                           # torch_cnn.py
sys.path.insert(0, str(ML / "A150_gpbo_vo_priced_package"))

import scb_ivr.extensions.ml_rl as RL  # noqa: E402
from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402
from scb_ivr.extensions.ml_gp import GP  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP  # noqa: E402
from scb_ivr.extensions.ml_ppo import GaussianPolicy, update  # noqa: E402
from torch_cnn import build_model, load_numpy, sse  # noqa: E402
from torch_mlp import forward as mlp_forward  # noqa: E402

torch.set_default_dtype(torch.float64)


def t(x, grad=False):
    return torch.tensor(np.asarray(x, dtype=float), requires_grad=grad)


def gdiff(auto, hand):
    """Per tensor max |auto - hand| / max |hand|; the absolute difference where the hand gradient is identically zero
    (the anchored policy's output bias: it cancels in net(o) - net(anchor(o)))."""
    out = []
    for a, h in zip(auto, hand):
        d, m = float(np.max(np.abs(a - h))), float(np.max(np.abs(h)))
        out.append(d / m if m > 0 else d)
    return out


def mlp_case(net, x, y, w):
    loss_n, gW, gb = net.loss_grads(x, y, w)
    Ws, bs = [t(a, True) for a in net.W], [t(a, True) for a in net.b]
    z = mlp_forward(Ws, bs, t(x))
    wt = t(w).reshape(-1, 1)
    if net.out == "sigmoid":                                       # cross-entropy on the logits, summed over the outputs
        loss = torch.nn.functional.binary_cross_entropy_with_logits(z, t(y), weight=wt.expand_as(z), reduction="sum") / len(x)
    else:
        loss = (wt * (z - t(y)) ** 2).sum() / len(x)
    loss.backward()
    return {"loss_rel": abs(loss.item() - loss_n) / abs(loss_n), "grad_rel": max(gdiff([p.grad.numpy() for p in Ws + bs], gW + gb))}


def check_mlp():
    rng = np.random.default_rng(200)
    net, z = MLP.load(ML / "A120_d63_surrogate_mlp" / "a120_mlp.npz")
    ds = np.load(ML / "A120_d63_surrogate_mlp" / "a120_dataset.npz")
    ok = np.all(np.isfinite(ds["y"]), axis=1)
    x = ((ds["x"][ok] - z["x_mean"]) / z["x_sd"])[:256]
    y = ((ds["y"][ok] - z["y_mean"]) / z["y_sd"])[:256]
    w = rng.uniform(0.5, 2.0, len(x))
    sizes = [net.W[0].shape[0]] + [a.shape[1] for a in net.W]
    sig = MLP([6, 16, 3], out="sigmoid", seed=1)
    for a in sig.W:
        a *= 3.0                                                   # away from p = 1/2 everywhere
    xs = rng.normal(size=(64, 6))
    return {"a120_trained": mlp_case(net, x, y, w), "a120_initial": mlp_case(MLP(sizes, seed=0), x, y, w), "sizes": sizes,
            "sigmoid": mlp_case(sig, xs, (rng.uniform(size=(64, 3)) < 0.4).astype(float), rng.uniform(0.5, 2.0, 64))}


def check_fit(steps=20, batch=128, lr=2e-3, l2=1e-5):
    rng = np.random.default_rng(201)
    x = rng.normal(size=(steps * batch, 11))
    y = np.tanh(x @ rng.normal(size=(11, 5))) + 0.1 * rng.normal(size=(len(x), 5))
    net = MLP([11, 32, 5], seed=3)
    Ws, bs = [t(a, True) for a in net.W], [t(a, True) for a in net.b]
    net.fit(x, y, x[:batch], y[:batch], epochs=1, batch=batch, lr=lr, l2=l2, patience=40, seed=0)    # one epoch = `steps` steps
    opt = torch.optim.Adam([{"params": Ws, "weight_decay": l2}, {"params": bs}], lr=lr)     # L2 on the weights only, as fit
    idx = np.random.default_rng(0).permutation(len(x))
    for k in range(steps):
        j = idx[k * batch:(k + 1) * batch]
        opt.zero_grad()
        (((mlp_forward(Ws, bs, t(x[j])) - t(y[j])) ** 2).sum() / len(j)).backward()
        opt.step()
    return {"steps": steps, "param_max_abs": max(float(np.max(np.abs(p.detach().numpy() - a))) for p, a in zip(Ws + bs, net.W + net.b))}


def cnn_case(net, x, y):
    loss_n, g_n = net.loss_grads(x, y)
    out_n = net.forward(x)
    model = load_numpy(build_model(net.specs), net)
    out_t = model(t(x))
    loss = sse(out_t, t(y))
    loss.backward()
    g_t = [p.grad.numpy().T if p.ndim == 2 else p.grad.numpy() for p in model.parameters()]
    return {"forward_max_abs": float(np.max(np.abs(out_t.detach().numpy() - out_n))), "loss_rel": abs(loss.item() - loss_n) / loss_n,
            "grad_rel": max(gdiff(g_t, g_n)), "layers": sorted({s[0] for s in net.specs})}


def check_cnn():
    rng = np.random.default_rng(202)
    ae, _ = Sequential.load(ML / "A147_cnn_anomaly_detector" / "a147_ae.npz")
    x = rng.normal(size=(8, 32, 64))
    mixed = Sequential([["conv", 3, 4, 3], ["tanh"], ["pool"], ["flatten"], ["dense", 32, 12], ["tanh"], ["dense", 12, 32],
                        ["unflatten", 4, 8], ["up"], ["conv", 4, 3, 3]], seed=4)
    xm = rng.normal(size=(5, 3, 16))
    return {"a147_trained": cnn_case(ae, x, x), "a147_initial": cnn_case(Sequential(ae.specs, seed=0), x, x),
            "tanh_unflatten_up": cnn_case(mixed, xm, rng.normal(size=xm.shape))}


class Recorder:
    """Stands in for ml_nn.Adam in ml_ppo.update: keeps the gradients it is handed and changes nothing."""

    def __init__(self):
        self.grads = []

    def step(self, grads, max_norm=None):
        self.grads.append([np.array(g, dtype=float) for g in grads])


def ppo_case(anchor, n=512, n_obs=6, n_act=2, clip=0.2, ent=0.01):
    rng = np.random.default_rng(203)
    pol = GaussianPolicy(n_obs, n_act, hidden=(64, 64), log_std=-1.0, seed=1, anchor=anchor)
    for a in pol.net.W + pol.net.b:
        a += rng.normal(0.0, 0.1, a.shape)                         # away from the near-zero start: every term matters
    pol.log_std += rng.normal(0.0, 0.2, n_act)
    critic = MLP([n_obs, 64, 64, 1], seed=2)
    O = rng.normal(size=(n, n_obs))
    mu, _ = pol.forward(O)
    A = mu + np.exp(pol.log_std) * rng.normal(size=mu.shape)
    LP0 = pol.logp(A, mu) + rng.normal(0.0, 0.3, n)                # "old" log-probabilities: ratios on both sides of the clip
    ADV, RET = rng.normal(size=n), rng.normal(size=n)
    r_pi, r_v = Recorder(), Recorder()
    update(pol, critic, r_pi, r_v, (O, A, LP0, ADV, RET, O), np.random.default_rng(0), epochs=1, mb=n, clip=clip, ent=ent, kl_stop=1e9)
    # the same loss in PyTorch
    Ws, bs, ls = [t(a, True) for a in pol.net.W], [t(a, True) for a in pol.net.b], t(pol.log_std, True)
    mean = mlp_forward(Ws, bs, t(O))
    if anchor is not None:
        mean = mean - mlp_forward(Ws, bs, t(anchor(O)))
    lp = -0.5 * (((t(A) - mean) / torch.exp(ls)) ** 2).sum(dim=1) - ls.sum() - 0.5 * n_act * math.log(2 * math.pi)
    adv = t((ADV - ADV.mean()) / (ADV.std() + 1e-8))
    rho = torch.exp(lp - t(LP0))
    clipped = torch.clamp(rho, 1 - clip, 1 + clip) * adv
    loss = -torch.minimum(rho * adv, clipped).mean() - ent * ls.sum()
    loss.backward()
    cW, cb = [t(a, True) for a in critic.W], [t(a, True) for a in critic.b]
    ((mlp_forward(cW, cb, t(O))[:, 0] - t(RET)) ** 2).mean().backward()
    return {"actor_grad_rel": max(gdiff([p.grad.numpy() for p in Ws + bs + [ls]], r_pi.grads[0])),
            "critic_grad_rel": max(gdiff([p.grad.numpy() for p in cW + cb], r_v.grads[0])),
            "share_clipped": float((rho * adv > clipped).double().mean()), "calls": [len(r_pi.grads), len(r_v.grads)]}


def check_ppo():
    mask = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    return {"plain": ppo_case(None), "anchored": ppo_case(lambda O: O * mask)}


def check_pg(batch=16, gamma=0.98, ent=0.01):
    """ml_rl.train for one iteration at lr 1 on fixed synthetic episodes: W changes by gradient / batch."""
    rng = np.random.default_rng(204)
    W0 = rng.normal(0.0, 1.0, (3, 5))
    eps = []
    for _ in range(batch):
        n = int(rng.integers(3, 13))
        eps.append(([rng.normal(size=5) for _ in range(n)], [int(a) for a in rng.integers(0, 3, n)], [float(r) for r in rng.normal(size=n)]))
    it = iter(eps)

    class FixedPolicy(RL.Policy):
        def __init__(self, n_obs=5, n_act=3, seed=0):
            self.W = W0.copy()

    def fixed_rollout(env, dist, chooser):
        obs, acts, rews = next(it)
        return float(sum(rews)), acts, obs, rews, None

    saved = RL.Policy, RL.rollout, RL.sample_dist
    RL.Policy, RL.rollout, RL.sample_dist = FixedPolicy, fixed_rollout, lambda rng: None
    try:
        pol, _ = RL.train(None, iters=1, batch=batch, lr=1.0, gamma=gamma, ent=ent, seed=0)
    finally:
        RL.Policy, RL.rollout, RL.sample_dist = saved
    hand = (pol.W - W0) * batch
    # the objective train()'s docstring states, with the advantages as constants
    T = max(len(e[2]) for e in eps)
    G, mask = np.zeros((batch, T)), np.zeros((batch, T))
    for b, (_, _, rews) in enumerate(eps):
        g = 0.0
        for k in range(len(rews) - 1, -1, -1):
            g = rews[k] + gamma * g
            G[b, k], mask[b, k] = g, 1.0
    adv = (G - (G * mask).sum(axis=0) / np.maximum(mask.sum(axis=0), 1)) * mask
    adv = adv / (adv[mask > 0].std() + 1e-8)
    W = t(W0, True)
    obj = 0.0
    for b, (obs, acts, _) in enumerate(eps):
        logp = torch.log_softmax(t(np.array(obs)) @ W.T, dim=1)
        obj = obj + (t(adv[b, :len(acts)]) * logp[torch.arange(len(acts)), torch.tensor(acts)]).sum() - ent * (torch.exp(logp) * logp).sum()
    obj.backward()
    return {"grad_rel": float(np.max(np.abs(W.grad.numpy() - hand)) / np.max(np.abs(hand))), "steps": int(mask.sum())}


def nlml_t(th, x, y):
    """ml_gp.GP._nlml in PyTorch (no fixed length scales)."""
    s, n, l = torch.exp(th[0]), torch.exp(th[1]), torch.exp(th[2:])
    d = (x[:, None, :] - x[None, :, :]) / l
    K = s * s * torch.exp(-0.5 * (d * d).sum(dim=2)) + (n * n + 1e-10) * torch.eye(len(x))
    L = torch.linalg.cholesky(K)
    a = torch.cholesky_solve(y[:, None], L)[:, 0]
    return 0.5 * y @ a + torch.log(torch.diagonal(L)).sum() + 0.5 * len(x) * math.log(2 * math.pi)


def check_gp():
    import a150_bo as B150                                         # A150's points, noise floors, length bounds and grid
    st = json.loads((ML / "A150_gpbo_vo_priced_package" / "a150_bo.json").read_text())
    rng = np.random.default_rng(205)
    out = {}
    for c in B150.NMIN:
        x, yr = B150.xy(st["points"], c)
        g = GP(noise_min=B150.NMIN[c], l_bounds=B150.L_BOUNDS).fit(x, yr, restarts=8, seed=0)
        y, dim = g.y, x.shape[1]
        sy = max(float(np.std(y)), 1e-6)
        n_lo = max(1e-3 * sy, g.noise_min)
        bounds = [(np.log(1e-3 * sy), np.log(1e2 * sy)), (np.log(n_lo), np.log(max(10 * sy, 2 * n_lo)))] + [g.l_log] * dim
        xt, yt = t(x), t(y)

        def fun(th):
            v = t(th, True)
            f = nlml_t(v, xt, yt)
            f.backward()
            return f.item(), v.grad.numpy()

        val, fd = [], []
        for th in [g.theta] + [np.array([rng.uniform(lo, hi) for lo, hi in bounds]) for _ in range(3)]:
            f, gr = fun(th)
            val.append(abs(f - g._nlml(th, x, y)) / abs(g._nlml(th, x, y)))
            if th is not g.theta:
                num = np.array([(g._nlml(th + h, x, y) - g._nlml(th - h, x, y)) / 2e-5 for h in 1e-5 * np.eye(len(th))])
                fd.append(float(np.max(np.abs(gr - num)) / np.max(np.abs(num))))
        # had the finite-difference fit converged? the exact gradient from its optimum, and from ml_gp's eight starts
        best = minimize(fun, g.theta, jac=True, method="L-BFGS-B", bounds=bounds)
        srng = np.random.default_rng(0)
        for _ in range(8):
            th0 = np.concatenate([[np.log(sy), np.log(max(0.3 * sy, 1.01 * n_lo))], np.clip(srng.normal(0.0, 0.5, dim), *g.l_log)])
            r = minimize(fun, th0, jac=True, method="L-BFGS-B", bounds=bounds)
            if r.fun < best.fun:
                best = r
        m0, s0 = g.predict(B150.GRID, noise=False)
        g2 = GP(noise_min=B150.NMIN[c], l_bounds=B150.L_BOUNDS)
        g2.fit(x, yr, restarts=1, seed=0)
        g2.theta = best.x
        g2.s, g2.n, g2.l = g2._unpack(best.x, dim)
        K = g2._kernel(x, x, g2.s, g2.l) + (g2.n ** 2 + 1e-10) * np.eye(len(x))
        g2.c = cho_factor(K, lower=True)
        g2.alpha = cho_solve(g2.c, g2.y)
        m1, _ = g2.predict(B150.GRID, noise=False)
        fm = st.get("final_models", {}).get(c, {})
        ctrl = None
        if fm.get("kind") == "none":
            ctrl = float(max(abs(g.s - fm["s"]) / fm["s"], abs(g.n - fm["n"]) / fm["n"], np.max(np.abs(g.l - np.array(fm["l"])) / np.array(fm["l"]))))
        out[c] = {"points": len(x), "value_rel": max(val), "fd_rel": max(fd), "nlml_fit": g.nlml, "nlml_exact": float(best.fun),
                  "nlml_drop": float(g.nlml - best.fun), "pred_shift_sd": float(np.max(np.abs(m1 - m0) / s0)),
                  "theta_fit": g.theta.tolist(), "theta_exact": best.x.tolist(), "control_rel": ctrl}
    return out


def main():
    if "--smoke" in sys.argv:                                      # runs every section, prints no result
        import time
        for nm, fn in (("mlp", check_mlp), ("fit", check_fit), ("cnn", check_cnn), ("ppo", check_ppo), ("pg", check_pg), ("gp", check_gp)):
            t0 = time.time()
            try:
                fn()
                print(f"smoke {nm}: ran in {time.time() - t0:.1f} s")
            except ValueError as e:
                print(f"smoke {nm}: {e}")
        return
    out = {"torch": torch.__version__, "numpy": np.__version__, "mlp": check_mlp(), "fit": check_fit(), "cnn": check_cnn(),
           "ppo": check_ppo(), "pg": check_pg(), "gp": check_gp()}
    m, c, p, g = out["mlp"], out["cnn"], out["ppo"], out["gp"]
    EX = 1e-9
    crit = {"c1_mlp": max(v["grad_rel"] for k, v in m.items() if k != "sizes") <= EX,
            "c2_fit": out["fit"]["param_max_abs"] <= EX,
            "c3_cnn": max(max(v["grad_rel"], v["forward_max_abs"]) for v in c.values()) <= EX,
            "c4_ppo": max(max(v["actor_grad_rel"], v["critic_grad_rel"]) for v in p.values()) <= EX and min(min(v["share_clipped"], 1 - v["share_clipped"]) for v in p.values()) >= 0.10,
            "c5_pg": out["pg"]["grad_rel"] <= EX,
            "c6_gp_value_gradient": max(v["value_rel"] for v in g.values()) <= EX and max(v["fd_rel"] for v in g.values()) <= 1e-5,
            "c7_gp_converged": max(v["nlml_drop"] for v in g.values()) <= 1e-4 and max(v["pred_shift_sd"] for v in g.values()) <= 0.01
                               and all(v["control_rel"] is None or v["control_rel"] <= 1e-6 for v in g.values())}
    out["criteria"], out["passed"], out["of"] = crit, sum(crit.values()), len(crit)
    (HERE / "a200_audit.json").write_text(json.dumps(out, indent=1) + "\n")
    ok = lambda k: "PASS" if crit[k] else "FAIL"
    print(f"A200: {out['passed']} of {out['of']} criteria pass (torch {out['torch']}, numpy {out['numpy']})")
    print(f"C1 {ok('c1_mlp')} MLP gradients: A120 trained {m['a120_trained']['grad_rel']:.1e}, initial {m['a120_initial']['grad_rel']:.1e}, sigmoid {m['sigmoid']['grad_rel']:.1e}")
    print(f"C2 {ok('c2_fit')} MLP.fit, {out['fit']['steps']} Adam steps with L2: param max |diff| {out['fit']['param_max_abs']:.1e}")
    print(f"C3 {ok('c3_cnn')} CNN layers: " + "; ".join(f"{k} forward {v['forward_max_abs']:.1e} grad {v['grad_rel']:.1e}" for k, v in c.items()))
    print(f"C4 {ok('c4_ppo')} PPO: " + "; ".join(f"{k} actor {v['actor_grad_rel']:.1e} critic {v['critic_grad_rel']:.1e} clipped {v['share_clipped']:.2f}" for k, v in p.items()))
    print(f"C5 {ok('c5_pg')} REINFORCE: {out['pg']['grad_rel']:.1e} over {out['pg']['steps']} steps")
    print(f"C6 {ok('c6_gp_value_gradient')} GP likelihood: value {max(v['value_rel'] for v in g.values()):.1e}, autograd vs differences {max(v['fd_rel'] for v in g.values()):.1e}")
    for k, v in g.items():
        print(f"  {k}: {v['points']} points, NLML {v['nlml_fit']:.6f} -> exact refit {v['nlml_exact']:.6f} (drop {v['nlml_drop']:.1e}), "
              f"grid mean shift {v['pred_shift_sd']:.1e} sd, control {v['control_rel'] if v['control_rel'] is None else format(v['control_rel'], '.1e')}")
    print(f"C7 {ok('c7_gp_converged')} GP fits converged")


if __name__ == "__main__":
    main()
