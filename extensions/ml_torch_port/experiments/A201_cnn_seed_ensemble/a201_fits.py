"""A201 simulator fits for A146's criterion 4: a146_baselines.sim_fit on the first N_FIT measured test captures,
started from the ranges' centre (once) and from each estimator's prediction. Estimators: "numpy" (A146's stored
network, the control), "s<seed>" (every runs/pred_s<seed>.npz) and "ens" (the mean of all seeds present).
Writes a201_fits.json, resumable: an estimator already in the file is skipped. Prints <= 15 lines.

    PYTHONPATH=src python3 .../a201_fits.py [--jobs 8] [--only numpy centre]"""
from __future__ import annotations

import argparse
import json
import time
from multiprocessing import Pool

import numpy as np
from a201_common import HERE, N_FIT, dataset, extra, reference

from a146_baselines import sim_fit

OUT = HERE / "a201_fits.json"


def _fit(args):
    y, i0, th0 = args
    return sim_fit(y, i0, th0=th0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    d, ex = dataset(), extra()
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    starts = {"centre": [None] * N_FIT}
    net, sc, _, _ = reference()
    starts["numpy"] = list(sc.inv(net.predict(d["xte"]))[:N_FIT])                # the whole test set, as a146_run predicts it
    preds = {p.stem[5:]: np.load(p)["te"].astype(np.float64) for p in sorted((HERE / "runs").glob("pred_s*.npz"))}
    starts.update({k: list(p[:N_FIT]) for k, p in preds.items()})
    if preds:
        starts["ens"] = list(np.mean([p[:N_FIT] for p in preds.values()], axis=0))
    with Pool(a.jobs) as pool:
        for name, th in starts.items():
            if (a.only and name not in a.only) or (name in done and name != "ens") or (name == "ens" and done.get("ens_members") == sorted(preds)):
                continue
            t0 = time.time()
            done[name] = pool.map(_fit, [(ex["y_meas"][m], float(ex["i_sensed"][m]), th[m]) for m in range(N_FIT)])
            if name == "ens":
                done["ens_members"] = sorted(preds)
            OUT.write_text(json.dumps(done, indent=1) + "\n")
            print(f"{name}: {N_FIT} fits, mean evals {np.mean([f['nfev'] for f in done[name]]):.1f}, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
