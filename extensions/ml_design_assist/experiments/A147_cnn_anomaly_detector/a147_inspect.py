"""A147 inspection (criterion 4): for each of the 20 highest unexplained AE flags (a147_summary.json) and for the
storm / runaway runs without a flag: the record's stimulus, the three scores against their thresholds, and the three
channels with the largest AE residual (input and reconstruction in physical units, period of the maximum).
Writes a147_inspect.json; prints one line per flag."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from a147_features import CH, OUT  # noqa: E402
from a147_run import STRIDE, W, load, run_label, windows  # noqa: E402

from scb_ivr.extensions.ml_cnn import Sequential  # noqa: E402


def main(name="a147_summary.json"):
    s = json.loads((HERE / name).read_text())
    ix = {r["id"]: r for r in json.loads((OUT / "index.json").read_text())["records"]}
    ae, z = Sequential.load(HERE / "a147_ae.npz")
    med, sd, thr = z["med"], z["sd"], dict(zip(("ae", "zmax", "pca", "ae_ms"), z["thr"]))
    norm = lambda x: np.clip((x - med) / sd, -50, 50)
    out = []
    for w in s["unexplained"]["top20"]:
        r = ix[w["id"]]
        x, t, ev_t, ev_c, ev_k = load(w["id"])
        k = int(np.argmin(np.abs(t - w["t_us"] * 1e-6)))
        win = norm(x[k:k + W]).T[None]
        rec = ae.forward(win.astype(np.float32))[0]
        res = np.abs(rec - win[0])                                         # (32, 64)
        top = np.argsort(res.max(axis=1))[::-1][:3]
        chans = []
        for c in top:
            j = int(np.argmax(res[c]))
            chans.append({"ch": CH[c], "period": j, "t_us": float(t[k + j] * 1e6), "value": float(x[k + j, c]),
                          "recon": float(rec[c, j] * sd[c] + med[c]), "res_sd": float(res[c, j])})
        near = [(round(float(a) * 1e6, 2), str(b)) for a, b, c_ in zip(ev_t, ev_k, ev_c) if abs(a - w["t_us"] * 1e-6) < 200e-6][:4]
        out.append({"id": w["id"], "run": w["run"], "t_us": w["t_us"], "stim": r["stim"], "L": r["L"], "loop": r["loop"],
                    "scores": {m: [round(w[m], 2), round(float(thr[m]), 2)] for m in ("ae", "zmax", "pca")},
                    "top": chans, "events_within_200us": near, "late": r["late"], "ipk": r["ipk"]})
    missed = []
    for lab in ("storm", "runaway"):
        for rid, r in ix.items():
            if run_label(r) == lab:
                x = load(rid)[0]
                n_w = len(windows(x, STRIDE)[1])
                missed.append({"id": rid, "label": lab, "periods": int(len(x)), "windows": n_w, "late": r["late"], "ipk": r["ipk"]})
    (HERE / name.replace("summary", "inspect")).write_text(json.dumps({"top20": out, "storm_runaway": missed}, indent=1) + "\n")
    for o in out:
        st = o["stim"]; ls, ld = st.get("line"), st.get("load")
        stim = (f"line {ls['dv']:+.1f} V/{ls.get('slew_us', 0)} us @ {ls['t_us']:.0f}" if ls else "") + \
               (f" load {ld['i_a']:+.0f} A @ {ld['t_us']:.0f}" if ld else "")
        c = o["top"][0]
        print(f"{o['id'][:34]:34s} {o['run']:6s} t {o['t_us']:7.1f} | {stim:28s} | ae {o['scores']['ae'][0]:5.1f} z {o['scores']['zmax'][0]:5.1f}"
              f" | {c['ch']} {c['value']:.2f} vs {c['recon']:.2f} @ {c['t_us']:.1f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
