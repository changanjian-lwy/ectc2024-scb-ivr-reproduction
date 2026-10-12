"""A201 training: A146's network in PyTorch (float32, MPS) at A146's settings, one run per seed. Per seed it writes
runs/s<seed>.json (epochs, losses, time, provenance) and runs/pred_s<seed>.npz (predictions on the calibration set,
the test set and the four robustness rows, in the targets' units); prints one line per seed.

    PYTHONPATH=src <python with torch> .../a201_train.py --seeds 0 1 2 3 [--device mps] [--smoke]"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import torch
from a201_common import HERE, ROB, dataset, extra, provenance
from a199_common import Scaler, net_specs
from torch_cnn import build_model, fit, predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", required=True)
    ap.add_argument("--device", choices=("cpu", "mps"), default="mps")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    d, ex = dataset(), extra()
    sc = Scaler.fit(d["ytr"])
    ten = torch.from_numpy
    n = 1200 if a.smoke else len(d["xtr"])
    for seed in a.seeds:
        model = build_model(net_specs(d["xtr"].shape[2]), seed=seed, dtype=torch.float32)
        t0 = time.time()
        hist = fit(model, ten(d["xtr"][:n]), ten(sc.fwd(d["ytr"][:n])), ten(d["xva"]), ten(sc.fwd(d["yva"])),
                   epochs=2 if a.smoke else 150, batch=64, lr=1e-3, patience=15, seed=seed, device=a.device)
        train_s = time.time() - t0
        pr = lambda x: sc.inv(predict(model, ten(x), device=a.device).double().numpy())
        if a.smoke:
            print(f"smoke ok seed {seed}: {train_s / len(hist):.2f} s per epoch at {n} examples, rows {[pr(ex[f'rob_{nm}']).shape for nm in ROB][:1]}")
            continue
        best = min(hist, key=lambda h: h[2])
        (HERE / "runs").mkdir(exist_ok=True)
        np.savez_compressed(HERE / "runs" / f"pred_s{seed}.npz", ca=pr(d["xca"]).astype(np.float32), te=pr(d["xte"]).astype(np.float32),
                            **{nm: pr(ex[f"rob_{nm}"]).astype(np.float32) for nm in ROB})
        out = {"seed": seed, "dtype": "float32", "device": a.device, "torch": torch.__version__, "provenance": provenance(),
               "epochs": len(hist), "best_epoch": best[0], "best_val": best[2], "train_s": train_s}
        (HERE / "runs" / f"s{seed}.json").write_text(json.dumps(out, indent=1) + "\n")
        print(f"seed {seed}: {len(hist)} epochs (best {best[0]}, val {best[2]:.5f}), {train_s:.0f} s, commit {out['provenance']['commit']}", flush=True)


if __name__ == "__main__":
    main()
