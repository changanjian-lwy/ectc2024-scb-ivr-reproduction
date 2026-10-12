"""A199 shared pieces: paths, A146's measured dataset rebuilt exactly as a146_run.main draws it (cached in
tmp/a199), A146's stored network and numbers, and the test metrics in a146_run's definitions."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
A146 = PROJECT / "extensions" / "ml_design_assist" / "experiments" / "A146_cnn_loop_identification"
TMP = PROJECT / "tmp" / "a199"
sys.path.insert(0, str(A146))
sys.path.insert(0, str(HERE.parents[1]))                           # torch_cnn.py

from a146_data import OUT  # noqa: E402
from a146_run import ALPHA, build, errors, net_specs, targets  # noqa: E402, F401

from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402
from scb_ivr.extensions.ml_nn import Scaler  # noqa: E402

NAMES = ("log_l", "log_q", "log_didt", "k")


def dataset(smoke=False):
    """xtr (two measurements of each training trace), xva, xca, xte and their targets. The generator (1460), the
    splits and the order of the build calls are a146_run.main's, so the arrays are the ones A146 trained on."""
    f = TMP / ("data_smoke.npz" if smoke else "data.npz")
    if f.exists():
        return dict(np.load(f))
    z = dict(np.load(OUT / "traces.npz"))
    v = z["v"].astype(np.float64)
    rng = np.random.default_rng(1460)
    tr, va, ca, te = np.arange(16000), np.arange(16000, 18000), np.arange(18000, 20000), np.arange(20000, 24000)
    if smoke:
        tr, va, ca, te = tr[:600], va[:200], ca[:200], te[:200]
    x1, _, _ = build(v, z["i0"], tr, rng)
    x2, _, _ = build(v, z["i0"], tr, rng)
    xva, _, _ = build(v, z["i0"], va, rng)
    xca, _, _ = build(v, z["i0"], ca, rng)
    xte, _, _ = build(v, z["i0"], te, rng)
    d = {"xtr": np.concatenate([x1, x2]), "ytr": np.concatenate([targets(z, tr)] * 2), "xva": xva, "yva": targets(z, va),
         "xca": xca, "yca": targets(z, ca), "xte": xte, "yte": targets(z, te)}
    TMP.mkdir(parents=True, exist_ok=True)
    np.savez(f, **d)
    return d


def reference():
    """A146's trained numpy network, its scaler, its conformal widths and its stored summary."""
    net, z = Sequential.load(A146 / "a146_cnn.npz")
    return net, Scaler(z["mean"], z["sd"]), z["q90"], json.loads((A146 / "a146_summary.json").read_text())


def conformal_q(pred, y):
    """Split conformal: the finite-sample (1 - ALPHA) rank of |residual| per parameter on the calibration set."""
    return np.sort(np.abs(pred - y), axis=0)[int(np.ceil((len(y) + 1) * (1 - ALPHA))) - 1]


def metrics(pred, y, q):
    e = np.abs(errors(pred, y))
    return {"median_err": np.median(e, axis=0).tolist(), "p90_err": np.percentile(e, 90, axis=0).tolist(),
            "cover90": (np.abs(pred - y) <= q).mean(axis=0).tolist()}


def provenance():
    """HEAD and whether this extension's tracked files differ from it."""
    git = lambda *a: subprocess.run(["git", "-C", str(PROJECT), *a], capture_output=True, text=True).stdout.strip()
    return {"commit": git("rev-parse", "--short", "HEAD"),
            "extension_modified": bool(git("status", "--porcelain", "--", "extensions/ml_torch_port/*.py",
                                           "extensions/ml_torch_port/experiments/A199_cnn_torch_port/*.py"))}
