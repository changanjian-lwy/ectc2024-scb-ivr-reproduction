"""A147 run: a 1D convolutional autoencoder of 64-period windows of the per-period features (a147_features.py), trained
on clean records only, against two non-learned / linear detectors and the A142 oracles. Writes a147_summary.json and
a147_ae.npz; prints <= 15 lines.

    PYTHONPATH=src python3 .../a147_run.py [--smoke]

Clean record: no NEW / FF oracle event, late <= 5, peak <= 200 A. Test experiments (held out whole): A139, A142,
A143, A145; the other clean records train (90 %) and validate (10 %, by record, seed 147). Channels are normalised
with the training periods' median and standard deviation (floor 1e-3 max(1, |median|), so a value never seen in clean
runs - a second turn-on in a period, a non-predictive turn-on - saturates the clip from the data, not from a hand rule;
the MAD would scale by the steady state alone and turn every legitimate step response into a 100-sigma event), clipped
to +-50.
Scores per window (stride 16), all the max |residual| over channels and periods (a sparse anomaly - one duplicate in
2048 values - vanishes in a mean): AE = |reconstruction - input|; zmax = |z| (the "model" is the median); PCA = 128
components (the AE's bottleneck size); the AE's mean square is kept as a secondary score (ae_ms). Threshold per method: the 99th percentile
of the validation windows. Window labels: defect = a NEW / FF oracle event inside the window; known = only K-class
events; none (registered: events in [first period, period after the window); --guard g widens that by g periods, a
post-hoc correction: an "order" event is stamped at the later turn-on, which starts the next period). Run labels: storm (late > 100), runaway (peak > 400 A), regulation (|Vo_end - 1| > 1 % or ladder
deviation > 0.03), defect (NEW / FF events), stress (peak > 200 A, none of these), clean."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from a147_features import CH, OUT  # noqa: E402

from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402

W, STRIDE, TEST_EXPS = 64, 16, ("A139", "A142", "A143", "A145")
SPECS = [["conv", 32, 32, 5], ["relu"], ["pool"], ["conv", 32, 16, 5], ["relu"], ["pool"], ["conv", 16, 8, 3], ["relu"],
         ["up"], ["conv", 8, 16, 5], ["relu"], ["up"], ["conv", 16, 32, 5]]


def is_clean(r):
    return r["n_new"] == 0 and r["late"] <= 5 and r["ipk"] <= 200 and r["status"] == "COMPLETED" and r["overlaps"] == 0


def run_label(r):
    if r["late"] > 100:
        return "storm"
    if r["ipk"] > 400:
        return "runaway"
    if abs(r["vo_end"] - 1) > 0.01 or r["ladder_dev_end"] > 0.03:
        return "regulation"
    if r["n_new"] > 0:
        return "defect"
    return "stress" if r["ipk"] > 200 else "clean"


def load(rid):
    z = np.load(OUT / "feat" / f"{rid}.npz")
    return z["x"].astype(np.float64), z["t"], z["ev_t"], z["ev_cls"], z["ev_kind"]


def windows(x, stride):
    if len(x) < W:
        return np.zeros((0, x.shape[1], W)), np.zeros(0, int)
    st = np.arange(0, len(x) - W + 1, stride)
    return np.stack([x[s:s + W].T for s in st]), st


def auroc(pos, neg):
    """Mann-Whitney: P(score of a positive > score of a negative), ties half."""
    s = np.concatenate([pos, neg])
    _, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    csum = np.cumsum(cnt); avg = csum - (cnt - 1) / 2.0
    r = avg[inv]
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guard", type=int, default=0, help="post hoc: widen each window's label span by this many periods")
    a = ap.parse_args()
    ix = json.loads((OUT / "index.json").read_text())["records"]
    rng = np.random.default_rng(147)
    tr_pool = [r for r in ix if is_clean(r) and r["exp"][:4] not in TEST_EXPS and r["n"] >= W]
    perm = rng.permutation(len(tr_pool))
    n_va = len(tr_pool) // 10
    va_rec, tr_rec = [tr_pool[i] for i in perm[:n_va]], [tr_pool[i] for i in perm[n_va:]]
    if a.smoke:
        tr_rec, va_rec = tr_rec[:20], va_rec[:5]
    # normalisation from the training periods
    xs = np.concatenate([load(r["id"])[0] for r in tr_rec])
    med = np.median(xs, axis=0)
    floor = 1e-3 * np.maximum(1.0, np.abs(med))       # data only: a value never seen in clean runs saturates the clip
    sd = np.maximum(xs.std(axis=0), floor)            # the sd, not the MAD: the MAD sees only the steady state
    norm = lambda x: np.clip((x - med) / sd, -50, 50)
    del xs
    # training / validation windows
    def wins(recs, stride, cap):
        out = [windows(norm(load(r["id"])[0]), stride)[0] for r in recs]
        w = np.concatenate([o for o in out if len(o)])
        return w[rng.permutation(len(w))[:cap]] if cap else w
    wtr, wva = wins(tr_rec, 8, 2000 if a.smoke else 60000), wins(va_rec, STRIDE, 500 if a.smoke else 0)
    t0 = time.time()
    ae = Sequential(SPECS, seed=0)
    hist = ae.fit(wtr.astype(np.float32), wtr, wva.astype(np.float32), wva, epochs=2 if a.smoke else 60, batch=128, lr=1e-3,
                  patience=8, log=(lambda s: print(s, flush=True)))
    t_train = time.time() - t0
    # PCA on the same training windows (flattened), 128 components
    flat = wtr.reshape(len(wtr), -1)
    mu = flat.mean(axis=0)
    _, _, vt = np.linalg.svd(flat[:20000] - mu, full_matrices=False)
    P = vt[:128]
    def scores(w):
        if not len(w):
            return {k: np.zeros(0) for k in ("ae", "zmax", "pca", "ae_ms")}
        rec = np.concatenate([ae.forward(w[k:k + 512].astype(np.float32)) for k in range(0, len(w), 512)])
        f = w.reshape(len(w), -1) - mu
        return {"ae": np.max(np.abs(rec - w), axis=(1, 2)), "zmax": np.max(np.abs(w), axis=(1, 2)),
                "pca": np.max(np.abs(f - (f @ P.T) @ P), axis=1), "ae_ms": np.mean((rec - w) ** 2, axis=(1, 2))}
    sva = scores(wva)
    thr = {k: float(np.percentile(v, 99)) for k, v in sva.items()}
    # score every window of every record; labels
    allw = []
    recs = ix if not a.smoke else ix[::25]
    tr_ids, va_ids = {r["id"] for r in tr_rec}, {r["id"] for r in va_rec}
    for r in recs:
        split = ("train" if r["id"] in tr_ids else "val" if r["id"] in va_ids else
                 "test" if r["exp"][:4] in TEST_EXPS else "other")
        x, t, ev_t, ev_c, ev_k = load(r["id"])
        w, st = windows(norm(x), STRIDE)
        if not len(w):
            continue
        sc = scores(w)
        t_lo, t_hi = t[np.maximum(st - a.guard, 0)], t[np.minimum(st + W + a.guard, len(t) - 1)]
        for m in range(len(st)):
            inside = (ev_t >= t_lo[m]) & (ev_t < t_hi[m])
            defect = bool(np.any(inside & (ev_c <= 1)))
            kinds = sorted(set(ev_k[inside & (ev_c <= 1)].tolist()))
            allw.append({"id": r["id"], "exp": r["exp"][:4], "t_us": float(t[st[m]] * 1e6), "run": run_label(r),
                         "clean_rec": is_clean(r), "split": split, "defect": defect, "kinds": kinds,
                         "known": bool(np.any(inside & (ev_c > 1))), **{k: float(v[m]) for k, v in sc.items()}})
    meth = ("ae", "zmax", "pca", "ae_ms")
    ct = [w for w in allw if w["clean_rec"] and w["split"] == "test"]
    dw = [w for w in allw if w["defect"]]
    res = {"thr": thr, "n_windows": len(allw), "n_clean_test": len(ct), "n_defect": len(dw), "train_s": t_train,
           "epochs": len(hist), "hist": hist[-3:]}
    for k in meth:
        neg = np.array([w[k] for w in ct]); pos = np.array([w[k] for w in dw])
        kinds = sorted({q for w in dw for q in w["kinds"]})
        runs = {}
        for lab in ("storm", "runaway", "regulation", "defect", "stress", "clean"):
            ids = {w["id"] for w in allw if w["run"] == lab}
            hit = {w["id"] for w in allw if w["run"] == lab and w[k] > thr[k]}
            runs[lab] = [len(hit), len(ids)]
        res[k] = {"far_clean_test": float(np.mean(neg > thr[k])) if len(neg) else None,
                  "far_by_exp": {e: float(np.mean([w[k] > thr[k] for w in ct if w["exp"] == e])) for e in TEST_EXPS
                                 if any(w["exp"] == e for w in ct)},
                  "auroc_defect": auroc(pos, neg) if len(pos) and len(neg) else None,
                  "recall_defect": float(np.mean(pos > thr[k])) if len(pos) else None,
                  "recall_by_kind": {q: float(np.mean([w[k] > thr[k] for w in dw if q in w["kinds"]])) for q in kinds},
                  "runs_flagged": runs}
    # unexplained flags: AE above threshold, no oracle event in the window, run not storm / runaway / regulation
    un = [w for w in allw if w["ae"] > thr["ae"] and not w["defect"] and not w["known"]
          and w["run"] in ("clean", "stress", "defect")]
    un.sort(key=lambda w: -w["ae"])
    seen, top = set(), []
    for w in un:                                   # one per record, the 20 highest
        if w["id"] not in seen:
            seen.add(w["id"]); top.append(w)
        if len(top) == 20:
            break
    res["unexplained"] = {"n_windows": len(un), "n_records": len({w["id"] for w in un}), "top20": top,
                          "by_run": {lab: sum(w["run"] == lab for w in un) for lab in ("clean", "stress", "defect")}}
    name = "a147_smoke.json" if a.smoke else ("a147_summary.json" if not a.guard else f"a147_summary_guard{a.guard}.json")
    (HERE / name).write_text(json.dumps(res, indent=1) + "\n")
    if not a.smoke and not a.guard:
        ae.save(HERE / "a147_ae.npz", med=med, sd=sd, thr=np.array([thr[k] for k in meth]), pca_mu=mu, pca_p=P)
    print(f"{len(tr_rec)} train / {len(va_rec)} val records, {len(wtr)} windows, {len(hist)} epochs, {t_train:.0f} s; "
          f"{len(allw)} windows scored, {len(ct)} clean test, {len(dw)} defect")
    for k in meth:
        q = res[k]
        print(f"{k:4s}: FAR clean test {q['far_clean_test']:.3f} {q['far_by_exp']}; AUROC {q['auroc_defect']:.3f}; "
              f"recall {q['recall_defect']:.3f}")
        print(f"      kinds {{{', '.join(f'{a_}: {b:.2f}' for a_, b in q['recall_by_kind'].items())}}}; runs {q['runs_flagged']}")
    print(f"unexplained AE flags: {res['unexplained']['n_windows']} windows in {res['unexplained']['n_records']} records "
          f"{res['unexplained']['by_run']}")


if __name__ == "__main__":
    main()
