"""A199 checks C0-C3: the PyTorch network against the numpy network, in float64 on the CPU. Writes a199_checks.json;
prints <= 15 lines.

    PYTHONPATH=src <python with torch> .../a199_checks.py [--smoke]

C0  the rebuilt dataset with A146's stored weights reproduces A146's stored numbers (so the data are A146's)
C1  forward: the stored weights copied into the PyTorch model give the numpy outputs on the test set
C2  gradients: autograd against ml_cnn's hand-written backward, at the trained and at the initial weights
C3  optimiser: 20 Adam steps from the same initial weights on the same batches, at max_norm 5 (A146's) and 0.1
--smoke runs on the 600-trace smoke dataset and prints timings only."""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import torch
from a199_common import HERE, NAMES, Scaler, Sequential, conformal_q, dataset, metrics, net_specs, provenance, reference
from torch import nn
from torch_cnn import build_model, load_numpy, predict, sse

from scb_ivr.extensions.ml_nn import Adam

STEPS, BATCH = 20, 64


def rel(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b) / np.abs(b)))


def np_params(model):
    """The model's parameters in ml_cnn's order and shapes (dense weights transposed back)."""
    return [p.detach().numpy().T if p.ndim == 2 else p.detach().numpy() for p in model.parameters()]


def np_grads(model):
    return [p.grad.numpy().T if p.ndim == 2 else p.grad.numpy() for p in model.parameters()]


def c0(d, net, sc, q90, ref):
    pr = lambda x: sc.inv(net.predict(x))
    q = conformal_q(pr(d["xca"]), d["yca"])
    m = metrics(pr(d["xte"]), d["yte"], q)
    sc2 = Scaler.fit(d["ytr"])
    return {"q90": rel(q, q90), "q90_summary": rel(q, ref["q90"]), "scaler": max(rel(sc2.mean, sc.mean), rel(sc2.sd, sc.sd)),
            **{k: rel(m[k], ref["cnn"][k]) for k in ("median_err", "p90_err", "cover90")}}


def c1(d, net, specs):
    model = load_numpy(build_model(specs), net)
    out_t = predict(model, torch.from_numpy(d["xte"])).numpy()
    return {"max_abs": float(np.max(np.abs(out_t - net.predict(d["xte"])))), "n": len(d["xte"])}


def c2(d, net, sc, specs):
    """Per parameter tensor: max |autograd - backward| / max |backward|, on the first 64 training examples."""
    xb, yb = d["xtr"][:BATCH], sc.fwd(d["ytr"][:BATCH])
    out = {}
    for nm, n in (("trained", net), ("initial", Sequential(specs, seed=0))):
        loss_n, g_n = n.loss_grads(xb, yb)
        model = load_numpy(build_model(specs), n)
        loss_t = sse(model(torch.from_numpy(xb).double()), torch.from_numpy(yb))
        loss_t.backward()
        out[nm] = {"loss_rel": abs(loss_t.item() - loss_n) / loss_n,
                   "grad_rel": [float(np.max(np.abs(a - b)) / np.max(np.abs(b))) for a, b in zip(np_grads(model), g_n)]}
    return out


def c3(d, sc, specs, max_norm):
    """The numpy loop is ml_cnn.Sequential.fit's inner loop; the PyTorch loop is torch_cnn.fit's with the same batches."""
    x, y = d["xtr"], sc.fwd(d["ytr"])
    idx = np.random.default_rng(0).permutation(len(x))
    net = Sequential(specs, seed=0)
    model = load_numpy(build_model(specs), net)
    opt_n, opt_t = Adam(net.params(), lr=1e-3), torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_n, loss_t, clipped, t_n, t_t = [], [], 0, 0.0, 0.0
    steps = min(STEPS, len(x) // BATCH)                             # the smoke dataset is shorter than 20 batches
    for k in range(steps):
        j = idx[k * BATCH:(k + 1) * BATCH]
        t0 = time.perf_counter()
        loss, g = net.loss_grads(x[j], y[j])
        opt_n.step(g, max_norm)
        t1 = time.perf_counter()
        opt_t.zero_grad()
        lt = sse(model(torch.from_numpy(x[j]).double()), torch.from_numpy(y[j]))
        lt.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm)
        opt_t.step()
        t2 = time.perf_counter()
        clipped += float(np.sqrt(sum(np.sum(gi * gi) for gi in g))) > max_norm
        loss_n.append(loss)
        loss_t.append(lt.item())
        t_n, t_t = t_n + t1 - t0, t_t + t2 - t1
    return {"max_norm": max_norm, "steps": steps, "clipped_steps": int(clipped), "loss_rel": rel(loss_t, loss_n),
            "param_max_abs": max(float(np.max(np.abs(a - b))) for a, b in zip(np_params(model), net.params())),
            "ms_per_step_numpy": 1e3 * t_n / steps, "ms_per_step_torch": 1e3 * t_t / steps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    t0 = time.time()
    d = dataset(a.smoke)
    t_data = time.time() - t0
    net, sc, q90, ref = reference()
    specs = net_specs(d["xtr"].shape[2])
    out = {"torch": torch.__version__, "numpy": np.__version__, "threads": a.threads, "provenance": provenance(),
           "c0": c0(d, net, sc, q90, ref), "c1": c1(d, net, specs), "c2": c2(d, net, sc, specs),
           "c3": [c3(d, sc, specs, 5.0), c3(d, sc, specs, 0.1)]}
    if a.smoke:
        s = out["c3"][0]
        print(f"smoke ok: data {t_data:.1f} s ({len(d['xtr'])} + {len(d['xte'])} examples), all checks {time.time() - t0 - t_data:.1f} s, "
              f"step numpy {s['ms_per_step_numpy']:.0f} ms / torch {s['ms_per_step_torch']:.0f} ms")
        return
    (HERE / "a199_checks.json").write_text(json.dumps(out, indent=1) + "\n")
    f = lambda xs: " / ".join(f"{x:.1e}" for x in xs)
    c = out["c0"]
    print(f"torch {out['torch']}, numpy {out['numpy']}, commit {out['provenance']['commit']}"
          f"{' (modified)' if out['provenance']['extension_modified'] else ''}; data {t_data:.0f} s")
    print(f"C0 stored numbers, max rel diff: q90 {c['q90']:.1e}, median {c['median_err']:.1e}, p90 {c['p90_err']:.1e}, "
          f"cover {c['cover90']:.1e}, scaler {c['scaler']:.1e}")
    print(f"C1 forward, max |diff| over {out['c1']['n']} test waveforms: {out['c1']['max_abs']:.1e}")
    for nm, r in out["c2"].items():
        print(f"C2 gradients ({nm} weights): loss rel {r['loss_rel']:.1e}; worst tensor {max(r['grad_rel']):.1e} "
              f"(per tensor {f(r['grad_rel'])})")
    for s in out["c3"]:
        print(f"C3 {s['steps']} Adam steps, max_norm {s['max_norm']}: clipped on {s['clipped_steps']}, loss rel {s['loss_rel']:.1e}, "
              f"param max |diff| {s['param_max_abs']:.1e}; step numpy {s['ms_per_step_numpy']:.0f} ms / torch {s['ms_per_step_torch']:.0f} ms")
    print("names:", ", ".join(NAMES))


if __name__ == "__main__":
    main()
