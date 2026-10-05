"""A142 analysis against BOUNDARY Section 2 -> a142_summary.json (per run: inputs, oracle hits by kind and class, peak,
end state; criteria 1-5). `--files GLOB...` runs the oracles on other records instead (prints the class counts)."""
from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import a142_oracles as O  # noqa: E402

COS = HERE / "cosim"
REF_I0 = PROJECT / "experiments/track_A_periodic_steady_state/A141_p24_floor_late_report/cosim/run_F_s100_l_p48_1us.json"


def counts(r):
    return dict(Counter(f"{e['kind']}:{e['cls']}" for e in r["events"]))


def identity():
    a, b = (json.loads(p.read_text()) for p in (COS / "run_I0.json", REF_I0))
    same = all(a[k] == b[k] for k in ("turnons_last", "highoffs_last", "ipk_a"))
    return {"identical": same, "ipk": [a["ipk_a"], b["ipk_a"]]}


def validate(patterns):
    files = sorted(f for p in patterns for f in glob.glob(p))
    with Pool(10) as p:
        res = p.map(O.check, files, chunksize=4)
    c = Counter()
    for r in res:
        c.update(counts(r))
    new = sorted({r["file"] for r in res for e in r["events"] if e["cls"] in ("NEW", "FF")})
    bad = [r["file"] for r in res if abs(r["vo_end"] - 1) > 0.01 or r["ladder_dev_end"] > 0.03]
    print(len(res), "records", dict(c))
    print("NEW/FF files", len(new), new[:8], "| settle fails", len(bad), bad[:4])


def main():
    inp = json.loads((HERE / "a142_inputs.json").read_text())["runs"]
    files = [COS / f"run_{n}.json" for n in inp]
    with Pool(10) as p:
        res = p.map(O.check, files, chunksize=2)
    runs = {}
    for n, r in zip(inp, res):
        runs[n] = {**inp[n], "hits": counts(r), **{k: r[k] for k in ("status", "src_modified", "overlaps", "late",
                   "peak_post", "vo_end", "ladder_dev_end", "t_lo_timed_us", "n_on")},
                   "events": [e for e in r["events"] if e["cls"] not in ("K1",)][:30]}
    tot = Counter()
    for v in runs.values():
        tot.update(v["hits"])

    def nruns(pred):
        return sorted(n for n, v in runs.items() if pred(v))
    ff = nruns(lambda v: any(k.endswith(":FF") for k in v["hits"]))
    alt = nruns(lambda v: v["overlaps"] or any(k.startswith("alt:") for k in v["hits"]))
    new = nruns(lambda v: any(k.endswith(":NEW") for k in v["hits"]))
    settle = nruns(lambda v: v["status"] != "COMPLETED" or v["src_modified"] or abs(v["vo_end"] - 1) > 0.01
                   or v["ladder_dev_end"] > 0.03)
    idt = identity()
    crit = {"1_floor_first_0": (not ff, ff), "2_overlap_alt_0": (not alt, alt), "3_new_0": (not new, new),
            "4_settle": (not settle, settle), "5_I0_identical": (idt["identical"], idt["ipk"])}
    lbd = [v for v in runs.values() if v["stratum"] in "LBD"]
    pk200 = sum(v["peak_post"] <= 200 for v in lbd) / len(lbd)
    out = {"criteria": {k: {"pass": bool(a), "detail": b} for k, a, b in ((k, *v) for k, v in crit.items())},
           "totals": dict(tot), "classes_by_run": {c: nruns(lambda v, c=c: any(k.endswith(":" + c) for k in v["hits"]))
                                                   for c in ("K1", "K2", "K3", "K4", "FF", "NEW")},
           "peak_le_200_LBD": pk200, "peak_max": max((v["peak_post"], n) for n, v in runs.items()), "runs": runs}
    (HERE / "a142_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in out["criteria"].items():
        print(f"{k:18s} {'PASS' if v['pass'] else 'FAIL'} {str(v['detail'])[:90]}")
    print("totals", dict(tot))
    for c, ns in out["classes_by_run"].items():
        print(f"{c}: {len(ns)} runs {ns[:10]}")
    print(f"LBD peak <= 200 A: {pk200:.2f}; max {out['peak_max'][0]:.1f} A ({out['peak_max'][1]})")


def episode(path):
    """Post hoc (RESULTS 3): oracle classes plus the large-signal episode after the disturbance - Vo excursion, time
    outside 2 %, rail 1 max, late fires, phase-1 period and valley currents (positive low-offs)."""
    r = O.check(path)
    d = json.loads(Path(path).read_text())
    ts = r["t_dist_us"] * 1e-6
    post = [q for q in d["sections"] if q["t_s"] >= ts]
    dt = (post[-1]["t_s"] - post[0]["t_s"]) / (len(post) - 1)
    t1 = sorted(x["t_s"] for x in d["turnons_last"] if x["phase"] == 1 and ts <= x["t_s"] < ts + 60e-6)
    lo = [x["i_a"] for x in d["lowoffs_last"] if ts <= x["t_s"] < ts + 60e-6]
    c = d["cfg"]
    return {"line_step": c["line_step"], "L_nH": c["circuit"]["L"] * 1e9, "cs_uF": c["circuit"]["cs"] * 1e6,
            "driver": c["driver"], "vff": "vff" in c, "peak": r["peak_post"], "hits": counts(r),
            "dvo_max_pct": max(abs(q["vo"] - 1) for q in post) * 100,
            "t_out2pct_us": sum(abs(q["vo"] - 1) > 0.02 for q in post) * dt * 1e6,
            "rail1_max_v": max(q["vin_v"] - q["vcs_v"][0] for q in post), "late": r["late"],
            "t_lo_timed_us": r["t_lo_timed_us"], "period1_max_ns": max(b - a for a, b in zip(t1, t1[1:])) * 1e9,
            "lo_min_a": min(lo), "lo_max_a": max(lo), "lo_pos_60us": sum(v > 0 for v in lo)}


def posthoc():
    files = [COS / "run_z104.json"] + sorted(COS.glob("run_[PQR]*.json"))
    with Pool(10) as p:
        res = p.map(episode, files)
    out = {f.name[4:-5]: r for f, r in zip(files, res)}
    (HERE / "a142_posthoc.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for n, r in out.items():
        ls = r["line_step"]
        print(f"{n:18s} {ls['t_us']:6.0f} us {ls['dv']:+.2f} V / {ls['slew_us']:5.2f} us  pk {r['peak']:4.0f}  dVo "
              f"{r['dvo_max_pct']:4.1f} %  out2% {r['t_out2pct_us']:4.1f} us  T1 {r['period1_max_ns']:4.0f} ns  lo+ {r['lo_pos_60us']}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--files":
        validate(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "--posthoc":
        posthoc()
    else:
        main()
