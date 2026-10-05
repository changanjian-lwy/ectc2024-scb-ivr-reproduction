"""A146 post hoc (decision rule for criterion 4): rebuild a146_run's test captures (same random sequence), the saved
CNN's predictions and the centre-start simulator fits on the first 40; for every capture whose fit lies outside the
CNN's 90 % interval, which of the two is closer to the truth; the captures where the fit is worse are
fitted again from the CNN's estimate. Writes a146_posthoc.json; prints <= 15 lines."""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from a146_baselines import sim_fit  # noqa: E402
from a146_data import OUT  # noqa: E402
from a146_run import N_FIT, NAMES, build, targets  # noqa: E402

from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402


def _fit(args):
    return sim_fit(*args)


def main():
    z = dict(np.load(OUT / "traces.npz"))
    v = z["v"].astype(np.float64)
    rng = np.random.default_rng(1460)
    tr, va, ca, te = np.arange(16000), np.arange(16000, 18000), np.arange(18000, 20000), np.arange(20000, 24000)
    for idx in (tr, tr, va, ca):                                   # advance the generator as a146_run does
        build(v, z["i0"], idx, rng)
    xte, yte_meas, ite = build(v, z["i0"], te, rng)
    net, s = Sequential.load(HERE / "a146_cnn.npz")
    pte = net.predict(xte[:N_FIT]) * s["sd"] + s["mean"]
    q, yte = s["q90"], targets(z, te[:N_FIT])
    with Pool(10) as pool:
        fits = pool.map(_fit, [(yte_meas[m], ite[m]) for m in range(N_FIT)])
    pf = np.array([[np.log(f["l_ph"]), np.log(f["q_act"]), np.log(f["didt"]), f["k"]] for f in fits])
    rows = []
    for m in range(N_FIT):
        for j, nm in enumerate(NAMES):
            if abs(pf[m, j] - pte[m, j]) > q[j]:
                rows.append({"capture": m, "param": nm, "fit_err": float(pf[m, j] - yte[m, j]), "cnn_err": float(pte[m, j] - yte[m, j]),
                             "cnn_covers_truth": bool(abs(pte[m, j] - yte[m, j]) <= q[j]), "tf_ns": float(z["i0"][te[m]] / z["didt"][te[m]]),
                             "fc_ghz": fits[m]["fc_ghz"], "shift_ps": fits[m]["shift_ps"]})
    worse = sorted({r["capture"] for r in rows if abs(r["fit_err"]) > abs(r["cnn_err"])})
    with Pool(10) as pool:                                          # the same captures fitted from the CNN's estimate
        refits = pool.map(_fit, [(yte_meas[m], ite[m], 150, pte[m]) for m in worse])
    rescue = []
    for m, f in zip(worse, refits):
        e = np.array([np.log(f["l_ph"]), np.log(f["q_act"]), np.log(f["didt"]), f["k"]]) - yte[m]
        rescue.append({"capture": m, "centre_err": (pf[m] - yte[m]).tolist(), "cnn_start_err": e.tolist(),
                       "cnn_err": (pte[m] - yte[m]).tolist(), "fc_ghz": f["fc_ghz"], "shift_ps": f["shift_ps"]})
    out = {"disagreements": rows, "fit_closer": sum(abs(r["fit_err"]) < abs(r["cnn_err"]) for r in rows), "n": len(rows),
           "fit_worse_captures": worse, "cnn_start_refits": rescue}
    (HERE / "a146_posthoc.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(rows)} disagreements; the fit is closer to the truth in {out['fit_closer']}")
    for r in rescue:
        print(f"capture {r['capture']:2d} |err| L/Q/didt/k centre {np.round(np.abs(r['centre_err']), 3).tolist()} "
              f"CNN start {np.round(np.abs(r['cnn_start_err']), 3).tolist()} CNN {np.round(np.abs(r['cnn_err']), 3).tolist()}")


if __name__ == "__main__":
    main()
