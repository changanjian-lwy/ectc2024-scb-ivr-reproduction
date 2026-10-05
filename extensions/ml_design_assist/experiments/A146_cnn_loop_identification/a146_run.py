"""A146 run: build the measured dataset from tmp/a146/traces.npz, train the CNN, register split-conformal intervals on
the calibration set, test, and compare with the sine fit, the simulator fit (centre start and CNN start) and the
Cramer-Rao bound. Writes a146_summary.json and a146_cnn.npz; prints <= 15 lines.

    PYTHONPATH=src python3 .../a146_run.py [--smoke] [--jobs 10]

Split (by trace index, fixed): train 0-15999 (two measurements of each), val 16000-17999, cal 18000-19999,
test 20000-23999. Measurement draws per example: probe fc U[0.7, 2] GHz, noise sd U[0.05, 0.4] V, trigger jitter
U[-50, 50] ps, I0 sensed with a U[-2, +2] % error; none of them is given to any estimator (the fits assume 1 GHz).
Input channels: (V_DS - 12 V) / 20 V and I0_sensed / 143 A. Targets: log L, log Q_act, log didt, k (standardised)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from a146_baselines import crb, measure, q_act, sim_fit, sine_fit, theta_of  # noqa: E402
from a146_data import OUT  # noqa: E402

from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402
from scb_ivr.extensions.ml_nn import Scaler  # noqa: E402

NAMES = ("log_l", "log_q", "log_didt", "k")
ALPHA = 0.10
N_FIT = 40


def draws(n, rng):
    return dict(fc=rng.uniform(0.7e9, 2e9, n), sigma=rng.uniform(0.05, 0.4, n), jit=rng.uniform(-50e-12, 50e-12, n),
                ierr=rng.uniform(-0.02, 0.02, n))


def build(v, i0, idx, rng, fixed=None):
    """Measured inputs (n, 2, T) for traces idx; fixed overrides draws (robustness rows)."""
    d = draws(len(idx), rng)
    if fixed:
        d.update({k: np.full(len(idx), x) for k, x in fixed.items()})
    ys = [measure(v[j], rng, d["fc"][m], d["sigma"][m], d["jit"][m]) for m, j in enumerate(idx)]
    y = np.stack(ys)
    ism = i0[idx] * (1 + d["ierr"])
    x = np.stack([(y - 12.0) / 20.0, np.repeat((ism / 143.0)[:, None], y.shape[1], axis=1)], axis=1).astype(np.float32)
    return x, y, ism


def targets(z, idx):
    return np.stack([np.log(z["l_ph"][idx]), np.log(q_act(z["q"][idx], z["k"][idx])), np.log(z["didt"][idx]), z["k"][idx]], axis=1)


def net_specs(t):
    m = t // 16
    return [["conv", 2, 16, 9], ["relu"], ["pool"], ["conv", 16, 32, 7], ["relu"], ["pool"], ["conv", 32, 32, 5], ["relu"],
            ["pool"], ["conv", 32, 32, 5], ["relu"], ["pool"], ["flatten"], ["dense", 32 * m, 64], ["relu"], ["dense", 64, 4]]


def errors(pred, true):
    """Per parameter: relative error for L, Q, didt (exp of the log difference - 1), absolute for k."""
    e = np.empty_like(pred)
    e[:, :3] = np.exp(pred[:, :3] - true[:, :3]) - 1.0
    e[:, 3] = pred[:, 3] - true[:, 3]
    return e


def _fits(args):
    y, i0, th_cnn = args
    a = sim_fit(y, i0)
    b = sim_fit(y, i0, th0=th_cnn)
    return a, b, sine_fit(y, i0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    z = dict(np.load(OUT / "traces.npz"))
    v = z["v"].astype(np.float64)
    rng = np.random.default_rng(1460)
    tr, va, ca, te = np.arange(16000), np.arange(16000, 18000), np.arange(18000, 20000), np.arange(20000, 24000)
    if a.smoke:
        tr, va, ca, te = tr[:600], va[:200], ca[:200], te[:200]
    t0 = time.time()
    x1, _, _ = build(v, z["i0"], tr, rng); x2, _, _ = build(v, z["i0"], tr, rng)
    xtr, ytr = np.concatenate([x1, x2]), np.concatenate([targets(z, tr)] * 2)
    xva, _, _ = build(v, z["i0"], va, rng); xca, _, _ = build(v, z["i0"], ca, rng)
    xte, yte_meas, ite = build(v, z["i0"], te, rng)
    sc = Scaler.fit(ytr)
    net = Sequential(net_specs(xtr.shape[2]), seed=0)
    hist = net.fit(xtr, sc.fwd(ytr), xva, sc.fwd(targets(z, va)), epochs=3 if a.smoke else 150, batch=64, lr=1e-3,
                   patience=15, log=lambda s: print(s, flush=True) if a.smoke else None)
    t_train = time.time() - t0
    pr = lambda x: sc.inv(net.predict(x))
    # split conformal: |residual| quantile per parameter on the calibration set (finite-sample rank)
    rc = np.abs(pr(xca) - targets(z, ca))
    q = np.sort(rc, axis=0)[int(np.ceil((len(ca) + 1) * (1 - ALPHA))) - 1]
    pte, yte = pr(xte), targets(z, te)
    tm = time.time(); pr(xte[:1000]); ms_per = (time.time() - tm) / 1000 * 1e3
    cover = (np.abs(pte - yte) <= q).mean(axis=0)
    e_cnn = errors(pte, yte)
    # baselines on all test traces (sine fit) and N_FIT (simulator fits, CRB)
    nf = 4 if a.smoke else min(N_FIT, len(te))
    with Pool(a.jobs) as pool:
        fits = pool.map(_fits, [(yte_meas[m], ite[m], pte[m]) for m in range(nf)])
        sines = pool.starmap(sine_fit, [(yte_meas[m], ite[m]) for m in range(nf, len(te))])
        crbs = pool.starmap(crb, [(yte[m], z["i0"][te[m]]) for m in range(min(10, nf))])
    sines = [f[2] for f in fits] + sines
    med3 = lambda e: [float(np.nanmedian(np.abs(e[:, j]))) for j in range(3)]
    p_sine = np.array([[np.log(s["l_ph"]), np.log(s["q_act"]), np.log(s["didt"]), np.nan] for s in sines])
    e_sine = errors(p_sine, yte)
    p_fa = np.array([[np.log(f[0]["l_ph"]), np.log(f[0]["q_act"]), np.log(f[0]["didt"]), f[0]["k"]] for f in fits])
    p_fb = np.array([[np.log(f[1]["l_ph"]), np.log(f[1]["q_act"]), np.log(f[1]["didt"]), f[1]["k"]] for f in fits])
    e_fa, e_fb = errors(p_fa, yte[:nf]), errors(p_fb, yte[:nf])
    agree = (np.abs(p_fb - pte[:nf]) <= q).mean(axis=0)
    med = lambda e: [float(np.nanmedian(np.abs(e[:, j]))) for j in range(4)]
    # robustness rows: the same test traces, one measurement condition fixed outside / at the edge of the draws
    rob = {}
    for nm, fx in {"noise_0p8": {"sigma": 0.8}, "probe_0p5ghz": {"fc": 0.5e9}, "jitter_150ps": {"jit": 150e-12},
                   "ierr_5pct": {"ierr": 0.05}}.items():
        xr, _, _ = build(v, z["i0"], te[:1000], np.random.default_rng(7), fx)
        pr_r = pr(xr)
        rob[nm] = {"median_err": med(errors(pr_r, yte[:1000])), "cover90": (np.abs(pr_r - yte[:1000]) <= q).mean(axis=0).tolist()}
    tf = z["i0"][te] / z["didt"][te]                                    # ns at the true current
    split = {nm: float(np.median(np.abs(e_cnn[m, 2]))) for nm, m in (("tf_lt_0p5ns", tf < 0.5), ("tf_ge_0p5ns", tf >= 0.5))}
    out = {"n": {"train": len(xtr), "val": len(va), "cal": len(ca), "test": len(te), "fits": nf}, "train_s": t_train,
           "epochs": len(hist), "hist": hist[-5:], "ms_per_waveform": ms_per, "q90": q.tolist(), "names": NAMES,
           "cnn": {"median_err": med(e_cnn), "p90_err": [float(np.nanpercentile(np.abs(e_cnn[:, j]), 90)) for j in range(4)],
                   "cover90": cover.tolist(), "didt_by_tf": split},
           "sine": {"median_err": med3(e_sine), "fail": int(np.isnan(p_sine[:, 0]).sum())},
           "fit_centre": {"median_err": med(e_fa), "nfev_mean": float(np.mean([f[0]["nfev"] for f in fits])),
                          "cost_med": float(np.median([f[0]["cost"] for f in fits]))},
           "fit_cnn_start": {"median_err": med(e_fb), "nfev_mean": float(np.mean([f[1]["nfev"] for f in fits])),
                             "cost_med": float(np.median([f[1]["cost"] for f in fits])), "within_cnn_interval": agree.tolist()},
           "crb_sd": [[float(x) for x in c[0]] for c in crbs], "robust": rob}
    (HERE / ("a146_smoke.json" if a.smoke else "a146_summary.json")).write_text(json.dumps(out, indent=1) + "\n")
    if not a.smoke:
        net.save(HERE / "a146_cnn.npz", mean=sc.mean, sd=sc.sd, q90=q)
    f = lambda xs: " / ".join(f"{x:.3f}" for x in xs)
    print(f"train {len(xtr)} ex, {len(hist)} epochs, {t_train:.0f} s; CNN {ms_per:.2f} ms per waveform")
    print(f"median |err| L / Q / didt / k:  CNN {f(out['cnn']['median_err'])}")
    print(f"  sine fit {f(out['sine']['median_err'][:3])} (fails {out['sine']['fail']})")
    print(f"  sim fit centre {f(out['fit_centre']['median_err'])} ({out['fit_centre']['nfev_mean']:.0f} evals)")
    print(f"  sim fit CNN start {f(out['fit_cnn_start']['median_err'])} ({out['fit_cnn_start']['nfev_mean']:.0f} evals)")
    print(f"CNN 90% cover {f(out['cnn']['cover90'])}; sim fit within CNN interval {f(agree)}")
    print(f"CNN didt median |err| t_f < 0.5 ns {split['tf_lt_0p5ns']:.3f}, >= 0.5 ns {split['tf_ge_0p5ns']:.3f}")
    print(f"CRB sd (median of {len(crbs)}) {f(np.median(np.array(out['crb_sd']), axis=0))}")
    for nm, r in rob.items():
        print(f"robust {nm}: err {f(r['median_err'])} cover {f(r['cover90'])}")


if __name__ == "__main__":
    main()
