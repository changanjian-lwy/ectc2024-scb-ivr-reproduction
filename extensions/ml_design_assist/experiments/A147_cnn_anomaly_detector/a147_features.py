"""A147 features: every local single-module cosim record of the 2.5 MHz design family (cfg t0_ns 400, no "modules")
-> one row per phase-1 period (between consecutive sections) from the oracle window on (A142: where the event lists
overlap and >= mode P + 20 us), with the A142 oracles' events of the same record as labels.

Channels (32): per phase k = 1..4 (6 each): turn-ons in the period, peak current (max high-off i_a), valley (min
low-off i_a), V_DS at the first turn-on, Ton (first high-off - first turn-on, ns), non-predictive turn-ons (how != 0);
then Vo, Vin, the three flying-capacitor ladder deviations vcs_j / vin - (3 - j) / 4, Ton code, period (ns), mode P.
A phase without an event in a period keeps its previous value (counts stay 0).

    PYTHONPATH=src python3 .../a147_features.py [--jobs 6]   -> tmp/a147/feat/<id>.npz, tmp/a147/index.json"""
from __future__ import annotations

import argparse
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "experiments" / "track_A_periodic_steady_state" / "A142_p24_random_stimulus"))
import a142_oracles  # noqa: E402

OUT = PROJECT / "tmp" / "a147"
N = 4
CH = [f"{nm}{k}" for k in range(1, N + 1) for nm in ("n_on", "i_pk", "i_val", "v_on", "ton", "n_how")] + \
     ["vo", "vin", "lad1", "lad2", "lad3", "ton_code", "period", "mode_p"]
CLS = ("NEW", "FF", "K1", "K2", "K3", "K4", "K5")


def records():
    out = []
    for r in sorted(PROJECT.glob("**/cosim/run_*.json")):
        if "tmp" in r.relative_to(PROJECT).parts or r.stat().st_size < 1e6:
            continue
        c = r.with_name("cfg_" + r.name[4:])
        if not c.exists():
            continue
        cfg = json.loads(c.read_text())
        if cfg.get("t0_ns") == 400.0 and cfg.get("modules", 1) == 1:
            out.append(r)
    return out


def per_phase(sec_t, ev, key, how="first"):
    """(n_periods, N) array of field `key` of events ev (sorted by t) per period and phase: first / max / min."""
    n = len(sec_t) - 1
    out = np.full((n, N), np.nan)
    if not ev:
        return np.zeros((n, N)) if how == "count" else out
    t = np.array([e["t_s"] for e in ev]); ph = np.array([e["phase"] for e in ev]) - 1
    v = np.array([float(e[key]) for e in ev]) if key else np.ones(len(ev))
    p = np.searchsorted(sec_t, t, side="right") - 1
    ok = (p >= 0) & (p < n)
    p, ph, v = p[ok], ph[ok], v[ok]
    if how == "count":
        out = np.zeros((n, N)); np.add.at(out, (p, ph), v)
    elif how == "max":
        np.fmax.at(out, (p, ph), v)
    elif how == "min":
        np.fmin.at(out, (p, ph), v)
    else:                                            # first event of each (period, phase)
        idx = p * N + ph
        _, first = np.unique(idx, return_index=True)
        out[p[first], ph[first]] = v[first]
    return out


def ffill(a):
    for j in range(a.shape[1]):
        col, last = a[:, j], 0.0
        for i in range(len(col)):
            if np.isnan(col[i]):
                col[i] = last
            else:
                last = col[i]
    return a


def one(path):
    path = Path(path)
    d = json.loads(path.read_text())
    chk = a142_oracles.check_dict(d, path.name)
    secs = d["sections"]
    sec_t = np.array([s["t_s"] for s in secs])
    on = sorted(d["turnons_last"], key=lambda e: e["t_s"])
    ho = sorted(d["highoffs_last"], key=lambda e: e["t_s"])
    lo = sorted(d["lowoffs_last"], key=lambda e: e["t_s"])
    n_on = per_phase(sec_t, on, None, "count")
    n_how = per_phase(sec_t, [e for e in on if e["how"] != 0], None, "count")
    t_on1, v_on = per_phase(sec_t, on, "t_s"), per_phase(sec_t, on, "vds_v")
    t_ho1, i_pk = per_phase(sec_t, ho, "t_s"), per_phase(sec_t, ho, "i_a", "max")
    i_val = per_phase(sec_t, lo, "i_a", "min")
    ton = (t_ho1 - t_on1) * 1e9
    ton[(ton < 0) | (ton > 400)] = np.nan
    ph = np.stack([n_on, ffill(i_pk), ffill(i_val), ffill(v_on), ffill(ton), n_how], axis=2).reshape(len(sec_t) - 1, -1)
    m = np.array([[s["vo"], s["vin_v"]] + [s["vcs_v"][j] / s["vin_v"] - (3 - j) / 4 for j in range(3)]
                  + [s["ton_lsb"], 0.0, float(s["mode_p"])] for s in secs[:-1]])
    m[:, 6] = np.diff(sec_t) * 1e9
    x = np.concatenate([ph, m], axis=1).astype(np.float32)
    keep = sec_t[:-1] >= chk["t0_us"] * 1e-6
    rid = f"{path.parts[path.parts.index('cosim') - 1][:4]}_{path.stem[4:]}"
    ev = chk["events"]
    np.savez_compressed(OUT / "feat" / f"{rid}.npz", x=x[keep], t=sec_t[:-1][keep],
                        ev_t=np.array([e["t_s"] for e in ev]), ev_cls=np.array([CLS.index(e["cls"]) for e in ev], dtype=np.int8),
                        ev_kind=np.array([e["kind"] for e in ev]))
    cfg = d["cfg"]
    ls, ld = cfg.get("line_step"), cfg.get("load_step")
    return {"id": rid, "file": str(path.relative_to(PROJECT)), "exp": path.parts[path.parts.index("cosim") - 1],
            "n": int(keep.sum()), "status": d["status"], "late": chk["late"], "ipk": d["ipk_a"], "overlaps": d["overlaps"],
            "peak_post": chk["peak_post"], "ladder_dev_end": chk["ladder_dev_end"], "vo_end": chk["vo_end"],
            "n_new": sum(e["cls"] in ("NEW", "FF") for e in ev), "n_known": sum(e["cls"] not in ("NEW", "FF") for e in ev),
            "src_modified": chk["src_modified"], "t_dist_us": chk["t_dist_us"],
            "stim": {"line": ls, "load": ld}, "loop": cfg.get("loop"), "edge": cfg.get("edge"),
            "L": cfg.get("circuit", {}).get("L"), "cs": cfg.get("circuit", {}).get("cs")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    (OUT / "feat").mkdir(parents=True, exist_ok=True)
    rs = records()
    t0 = time.time()
    with Pool(a.jobs) as pool:
        idx = pool.map(one, rs, chunksize=4)
    (OUT / "index.json").write_text(json.dumps({"channels": CH, "classes": CLS, "records": idx}, indent=1) + "\n")
    n = sum(r["n"] for r in idx)
    print(f"{len(idx)} records, {n} periods in {time.time() - t0:.0f} s; with NEW/FF events {sum(r['n_new'] > 0 for r in idx)}, "
          f"late > 100 {sum(r['late'] > 100 for r in idx)}, ipk > 200 A {sum(r['ipk'] > 200 for r in idx)}")


if __name__ == "__main__":
    main()
