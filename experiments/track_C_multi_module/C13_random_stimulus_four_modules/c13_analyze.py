"""C13 analysis against BOUNDARY Section 2 -> c13_summary.json: A142's oracles on every module (a142_oracles.check),
floor-first duplicates, overlaps, settling, I0 identity vs A143's run, handover rail gate (C10.rails limits, cut at the first
step when that is before 242 us). Peak-after-step and late fires are reported, not gated."""
from __future__ import annotations

import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parents[1] / "track_A_periodic_steady_state"
sys.path.insert(0, str(TA / "A142_p24_random_stimulus"))
import a142_oracles as O  # noqa: E402

COS = HERE / "cosim"
REF_I0 = TA / "A143_p24_short_comparator_phase/cosim/run_g5_l_p48_1us_k4.json"
RAIL_MAX, RAIL_HI, RAIL_HI_US, T_HAND = 13.5, 13.3, 5.0, 242e-6


def rails(d, cut):
    out = []
    for r in [d] + d["modules_rest"]:
        s = [q for q in r["sections"] if q["t_s"] <= cut and q["mode_p"]]
        v = [q["vin_v"] - q["vcs_v"][0] for q in s]
        hi = sum(b["t_s"] - a["t_s"] for a, b, x in zip(s, s[1:], v) if x > RAIL_HI)
        out.append({"max_v": max(v), "hi_us": hi * 1e6})
    return out


def one(path):
    r = O.check(path)
    d = json.loads(Path(path).read_text())
    c = d["cfg"]
    ts = [s["t_us"] * 1e-6 for s in (c.get("line_step"), c.get("load_step")) if s]
    rl = rails(d, min([T_HAND] + ts))
    r["rail_ok"] = all(x["max_v"] <= RAIL_MAX and x["hi_us"] <= RAIL_HI_US for x in rl)
    r["rail_max_v"] = max(x["max_v"] for x in rl)
    return r


def main():
    inp = json.loads((HERE / "c13_inputs.json").read_text())["runs"]
    names = ["I0"] + list(inp)
    with Pool(10) as p:
        res = p.map(one, [COS / f"run_{n}.json" for n in names], chunksize=1)
    runs, tot = {}, Counter()
    for n, r in zip(names, res):
        h = dict(Counter(f"{e['kind']}:{e['cls']}" for e in r["events"]))
        tot.update(h)
        runs[n] = {**inp.get(n, {}), "hits": h, **{k: r[k] for k in ("status", "src_modified", "overlaps", "late",
                   "peak_post", "vo_end", "ladder_dev_end", "t_lo_timed_us", "rail_ok", "rail_max_v")},
                   "events": [e for e in r["events"] if e["cls"] != "K1"][:30]}
    run = {n: v for n, v in runs.items() if n != "I0"}

    def sel(f):
        return sorted(n for n, v in run.items() if f(v))
    ff = sel(lambda v: any(k.endswith(":FF") for k in v["hits"]))
    alt = sel(lambda v: v["overlaps"] or any(k.startswith("alt:") for k in v["hits"]))
    new = sel(lambda v: any(k.endswith(":NEW") for k in v["hits"]))
    settle = sel(lambda v: v["status"] != "COMPLETED" or v["src_modified"] or abs(v["vo_end"] - 1) > 0.01
                 or v["ladder_dev_end"] > 0.03)
    rail = sel(lambda v: not v["rail_ok"])
    a, b = (json.loads(p.read_text()) for p in (COS / "run_I0.json", REF_I0))

    def mods(d):
        return [d] + d["modules_rest"]
    idt = all(x[k] == y[k] for x, y in zip(mods(a), mods(b)) for k in ("turnons_last", "highoffs_last", "ipk_a"))
    crit = {"1_floor_first_0": (not ff, ff), "2_overlap_alt_0": (not alt, alt), "3_new_0": (not new, new),
            "4_settle": (not settle, settle), "5_I0_identical": (idt, None), "6_rails": (not rail, rail)}
    lbd = [v for v in run.values() if v["stratum"] in "LBD"]
    out = {"criteria": {k: {"pass": bool(x), "detail": y} for k, (x, y) in crit.items()}, "totals": dict(tot),
           "peak_le_200_LBD": sum(v["peak_post"] <= 200 for v in lbd) / len(lbd),
           "peak_max": max((v["peak_post"], n) for n, v in run.items() if v["peak_post"]), "runs": runs}
    (HERE / "c13_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in out["criteria"].items():
        print(f"{k:16s} {'PASS' if v['pass'] else 'FAIL'} {str(v['detail'])[:90]}")
    print("totals", dict(tot))
    print(f"LBD peak <= 200 A: {out['peak_le_200_LBD']:.2f}; max {out['peak_max']}")


if __name__ == "__main__":
    main()
