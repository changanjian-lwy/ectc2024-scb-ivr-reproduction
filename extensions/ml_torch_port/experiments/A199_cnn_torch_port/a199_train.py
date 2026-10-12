"""A199 training run (C4 / C5): A146's network trained from scratch in PyTorch on A146's dataset with A146's settings
(<= 150 epochs, batch 64, lr 1e-3, patience 15, clip 5), then A146's test numbers: split-conformal widths on the
calibration set, median and 90th-percentile errors and 90 % cover on the test set. Writes runs/<tag>.json and
tmp/a199/<tag>.pt; prints <= 15 lines.

    PYTHONPATH=src <python with torch> .../a199_train.py --seed 0 [--dtype float32] [--device mps] [--threads 2] [--smoke]

--smoke: 600 training traces, 3 epochs, timing only (nothing written to runs/)."""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import torch
from a199_common import HERE, TMP, Scaler, conformal_q, dataset, metrics, net_specs, provenance
from torch_cnn import build_model, fit, predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dtype", choices=("float64", "float32"), default="float64")
    ap.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.device == "mps" and a.dtype == "float64":
        ap.error("the mps backend has no float64")
    torch.set_num_threads(a.threads)
    tag = f"s{a.seed}_{'f64' if a.dtype == 'float64' else 'f32'}_{a.device}"
    d = dataset(a.smoke)
    sc = Scaler.fit(d["ytr"])
    ten = torch.from_numpy                                         # numpy array -> tensor sharing its memory
    model = build_model(net_specs(d["xtr"].shape[2]), seed=a.seed, dtype=getattr(torch, a.dtype))
    t0 = time.time()
    hist = fit(model, ten(d["xtr"]), ten(sc.fwd(d["ytr"])), ten(d["xva"]), ten(sc.fwd(d["yva"])),
               epochs=3 if a.smoke else 150, batch=64, lr=1e-3, patience=15, seed=a.seed, device=a.device,
               log=None if a.smoke else lambda s: print(s, flush=True))
    train_s = time.time() - t0
    pr = lambda x: sc.inv(predict(model, ten(x), device=a.device).double().numpy())
    if a.smoke:
        print(f"smoke ok {tag}: {len(d['xtr'])} examples, {train_s / len(hist):.2f} s per epoch -> "
              f"{train_s / len(hist) * 32000 / len(d['xtr']):.1f} s per epoch at 32000")
        return
    q = conformal_q(pr(d["xca"]), d["yca"])
    pte = pr(d["xte"])
    tm = time.time(); pr(d["xte"][:1000]); ms_per = (time.time() - tm) / 1000 * 1e3
    TMP.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), TMP / f"{tag}.pt")              # the parameters only, not the code
    again = build_model(net_specs(d["xtr"].shape[2]), seed=99, dtype=getattr(torch, a.dtype))
    again.load_state_dict(torch.load(TMP / f"{tag}.pt", weights_only=True))
    again.to(a.device)
    reload_diff = float(np.max(np.abs(sc.inv(predict(again, ten(d["xte"]), device=a.device).double().numpy()) - pte)))
    best = min(hist, key=lambda h: h[2])
    out = {"tag": tag, "seed": a.seed, "dtype": a.dtype, "device": a.device, "threads": a.threads, "torch": torch.__version__,
           "provenance": provenance(), "n": {"train": len(d["xtr"]), "val": len(d["xva"]), "cal": len(d["xca"]), "test": len(d["xte"])},
           "epochs": len(hist), "best_epoch": best[0], "best_val": best[2], "hist": hist[-5:], "train_s": train_s,
           "s_per_epoch": train_s / len(hist), "ms_per_waveform": ms_per, "q90": q.tolist(), "reload_max_abs": reload_diff,
           **metrics(pte, d["yte"], q)}
    (HERE / "runs").mkdir(exist_ok=True)
    (HERE / "runs" / f"{tag}.json").write_text(json.dumps(out, indent=1) + "\n")
    f = lambda xs: " / ".join(f"{x:.4f}" for x in xs)
    print(f"{tag}: {len(hist)} epochs (best {best[0]}, val {best[2]:.5f}), {train_s:.0f} s, {out['s_per_epoch']:.1f} s per epoch, "
          f"{ms_per:.3f} ms per waveform, commit {out['provenance']['commit']}")
    print(f"median |err| L / Q / didt / k: {f(out['median_err'])}")
    print(f"90 % cover: {f(out['cover90'])}; reload max |diff| {reload_diff:.1e}")


if __name__ == "__main__":
    main()
