"""A201 shared pieces: A199's dataset plus what A146's criteria 4 and 5 need (the first N_FIT measured test captures
with their sensed currents, and the four robustness rows), and A146's five criteria as one function."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A199_cnn_torch_port"))

from a199_common import A146, OUT, PROJECT, build, conformal_q, dataset, errors, metrics, reference  # noqa: E402, F401

TMP = PROJECT / "tmp" / "a201"
N_FIT = 40
ROB = {"noise_0p8": {"sigma": 0.8}, "probe_0p5ghz": {"fc": 0.5e9}, "jitter_150ps": {"jit": 150e-12}, "ierr_5pct": {"ierr": 0.05}}
LIMITS = (0.05, 0.10, 0.15, 0.03)                                  # A146 criterion 1: medians of L, Q_act, di/dt, k
COVER = (0.87, 0.93)                                               # A146 criterion 2
ROB_COVER, WITHIN = 0.75, 0.85                                     # A146 criteria 5 and 4


def extra():
    """y_meas, i_sensed: the first N_FIT test captures as measured (V) and their sensed I0; rob_<row>: the inputs of
    A146's robustness rows. Drawn as a146_run.main draws them (same generator, same order of calls)."""
    f = TMP / "extra.npz"
    if f.exists():
        return dict(np.load(f))
    z = dict(np.load(OUT / "traces.npz"))
    v = z["v"].astype(np.float64)
    rng = np.random.default_rng(1460)
    tr, va, ca, te = np.arange(16000), np.arange(16000, 18000), np.arange(18000, 20000), np.arange(20000, 24000)
    for idx in (tr, tr, va, ca):                                   # a146_run.main's first four draws advance the generator
        build(v, z["i0"], idx, rng)
    xte, y_meas, i_sensed = build(v, z["i0"], te, rng)
    if not np.array_equal(xte, dataset()["xte"]):
        raise RuntimeError("extra: the replayed test inputs differ from A199's dataset")
    d = {"y_meas": y_meas[:N_FIT], "i_sensed": i_sensed[:N_FIT]}
    for nm, fx in ROB.items():
        d[f"rob_{nm}"] = build(v, z["i0"], te[:1000], np.random.default_rng(7), fx)[0]
    TMP.mkdir(parents=True, exist_ok=True)
    np.savez(f, **d)
    return d


def a146_criteria(p_ca, p_te, p_rob, d, sine_med, fit=None):
    """A146's criteria for one estimator. p_ca, p_te: its predictions (log L, log Q_act, log di/dt, k) on the
    calibration and test sets; p_rob: {row: predictions on the row}; fit: {"within", "nfev", "nfev_centre", "cost",
    "cost_centre"} from the simulator fits started at this estimator (criterion 4), or None."""
    q = conformal_q(p_ca, d["yca"])
    m = metrics(p_te, d["yte"], q)
    y_rob = d["yte"][:1000]
    rob = {nm: {"median_err": np.median(np.abs(errors(p, y_rob)), axis=0).tolist(),
                "cover90": (np.abs(p - y_rob) <= q).mean(axis=0).tolist()} for nm, p in p_rob.items()}
    out = {**m, "q90": q.tolist(), "robust": rob,
           "c1": bool(np.all(np.array(m["median_err"]) <= LIMITS)),
           "c2": bool(np.all((np.array(m["cover90"]) >= COVER[0]) & (np.array(m["cover90"]) <= COVER[1]))),
           "c3": bool(np.all(np.array(m["median_err"][:3]) <= 0.5 * np.array(sine_med))),
           "c5_rows": {nm: bool(min(r["cover90"]) >= ROB_COVER) for nm, r in rob.items()}}
    out["c5"] = all(out["c5_rows"].values())
    if fit is not None:
        out["fit"] = fit
        out["c4"] = bool(min(fit["within"]) >= WITHIN and fit["nfev"] < fit["nfev_centre"] and fit["cost"] <= 1.001 * fit["cost_centre"])
    return out


def provenance():
    git = lambda *a: subprocess.run(["git", "-C", str(PROJECT), *a], capture_output=True, text=True).stdout.strip()
    return {"commit": git("rev-parse", "--short", "HEAD"),
            "extension_modified": bool(git("status", "--porcelain", "--", "extensions/ml_torch_port/torch_cnn.py",
                                           "extensions/ml_torch_port/experiments/A199_cnn_torch_port/a199_common.py",
                                           "extensions/ml_torch_port/experiments/A201_cnn_seed_ensemble/*.py"))}


def load_json(path):
    return json.loads(Path(path).read_text())
