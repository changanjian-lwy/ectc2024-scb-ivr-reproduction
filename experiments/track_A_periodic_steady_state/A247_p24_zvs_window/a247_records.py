"""A247 data: every learned (predictive, how 0) turn-on of phases 2-4 in the plant-V7 records (A229-A246, every module;
a run whose turn-on list equals one already read is skipped), paired with that phase's last low-side turn-off before
its actual turn-on (within MAX_GAP_NS): i_off (A), delay = t_act - t_lo (ns), the command's t_s - t_lo, the phase's and
the next phase's rail at t_lo (sections, linear), the recorded V_DS at the actual turn-on and at the command, the report
(early, err), lo_pos where recorded, the board (L, gate temperature), time after mode P's entry.
  python3 a247_records.py [--jobs 10] -> tmp/a247_records.npz"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
EXPS = tuple(f"A{n}" for n in range(229, 247))
MAX_GAP_NS = 60.0
COLS = ("exp", "run", "module", "phase", "t_us", "t_p_us", "i_off_a", "delay_ns", "cmd_delay_ns", "rail_v",
        "rail_next_v", "vds_act_v", "vds_cmd_v", "early", "err_ns", "lo_pos", "lf_nh", "temp_c")


def runs():
    out = []
    for e in EXPS:
        d = next(TA.glob(f"{e}_*"), None)
        if d is not None:
            out += [(e, f) for f in sorted((d / "cosim").glob("run_*.json"))]
    return out


def rails_at(sec, t):
    ts = np.array([s["t_s"] for s in sec])
    v = np.array([[s["vin_v"]] + list(s["vcs_v"]) + [0.0] for s in sec])
    r = v[:, :-1] - v[:, 1:]
    return [float(np.interp(t, ts, r[:, q])) for q in range(r.shape[1])]


def one(args):
    e, f = args
    d = json.loads(Path(f).read_text())
    if d.get("status") != "COMPLETED" or d["provenance"].get("cosim_sources_modified"):
        return None
    key = hashlib.sha1(json.dumps([[x["t_s"], x["phase"]] for x in d["turnons_last"]]).encode()).hexdigest()
    c = d["cfg"]
    lf, temp = c["circuit"]["L"] * 1e9, c.get("gate", {}).get("temp", 25.0)
    rows = []
    for m, md in enumerate([d] + d.get("modules_rest", [])):
        sec, tp = md["sections"], md.get("t_mode_p_s") or d["t_mode_p_s"]
        lo = {ph: sorted((x["t_s"], x["i_a"]) for x in md["lowoffs_last"] if x["phase"] == ph) for ph in (2, 3, 4)}
        for x in md["turnons_last"]:
            if x["phase"] not in (2, 3, 4) or x["how"] != 0 or "t_act_s" not in x:
                continue
            L = lo[x["phase"]]
            j = bisect.bisect_left(L, (x["t_act_s"], -1e9)) - 1
            if j < 0 or (x["t_act_s"] - L[j][0]) * 1e9 > MAX_GAP_NS:
                continue
            t_lo, i_off = L[j]
            r = rails_at(sec, t_lo)
            k = x["phase"] - 1
            rows.append((EXPS.index(e), 0, m, x["phase"], x["t_act_s"] * 1e6, (x["t_act_s"] - tp) * 1e6, i_off,
                         (x["t_act_s"] - t_lo) * 1e9, (x["t_s"] - t_lo) * 1e9, r[k], r[k + 1] if k + 1 < len(r) else 0.0,
                         x["vds_act_v"], x["vds_v"], float(bool(x.get("early"))),
                         np.nan if x.get("err_s") is None else x["err_s"] * 1e9,
                         -1.0 if "lo_pos" not in x else float(bool(x["lo_pos"])), lf, temp))
    return key, str(Path(f).relative_to(TA)), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    from multiprocessing import Pool
    with Pool(a.jobs) as p:
        res = p.map(one, runs(), chunksize=2)
    seen, names, data = set(), [], []
    for r in res:
        if r is None or r[0] in seen:
            continue
        seen.add(r[0])
        for row in r[2]:
            data.append((row[0], len(names)) + row[2:])
        names.append(r[1])
    arr = np.array(data, dtype=np.float64)
    out = PROJECT / "tmp" / "a247_records.npz"
    np.savez_compressed(out, data=arr, cols=np.array(COLS), runs=np.array(names), exps=np.array(EXPS))
    print(f"{len(names)} distinct runs of {sum(1 for r in res if r)}, {len(arr)} turn-ons -> {out.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
