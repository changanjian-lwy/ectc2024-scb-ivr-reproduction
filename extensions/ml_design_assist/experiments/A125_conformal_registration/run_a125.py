"""A125: conformal intervals around D63's registered predictions, tested in the order the experiments were run.

    python3 .../run_a125.py            # the sequential test and the calibration file -> a125_summary.json, a125_calibration.json

Data: every step row of A117, A118, A119, A123 and A124 with a D63 prediction registered before the run
(*_predictions.json) and a co-simulation record (cosim/run_*.json). Measured as the main line does: the peak after the
step from the high-side turn-off records, step_stats' Vo extreme and recovery within 1%; a runaway is a peak > 400 A,
> 100 late fires, or no recovery with a peak > 300 A (A121's rule). D63's outcome is a118_predict's rule; rows it
calls runaway or slow carry no point prediction and stay out of the intervals (their outcomes are tabulated).

Sequential test: for each experiment from A118 on, calibrate on the bounded rows of all earlier experiments and band
its rows; a row is covered when the co-simulation lies in the band. Quantities and scores (ml_conformal): the peak
"rel", the Vo extreme "abs" (mV), the recovery "log" (times floored at 1 us). Methods: S symmetric (the primary), G
signed, M Mondrian on {rising line step, other}, ACI on S (gamma 0.05 per row, carried across experiments); and for
the peak the hand band +-10% the boundaries used.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402
from scb_ivr.extensions.ml_conformal import ACI, band, mondrian_band  # noqa: E402

TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
EXPS = ("A117", "A118", "A119", "A123", "A124")          # the order the predictions were registered and run
QUANT = {"peak": "rel", "mv": "abs", "back": "log"}
ALPHAS = (0.2, 0.1)
GAMMA = 0.05
CAL = HERE / "a125_calibration.json"


def registered(e, p):
    if e in ("A117", "A118"):
        return {k: v["model"] for k, v in p.items() if isinstance(v, dict) and "model" in v}
    if e == "A119":
        return p
    if e == "A123":                                       # f6 repeats A118 / A119 rows; it has no runs of its own
        return {f"{v}_{r}": m for v, rr in p.items() if v != "f6" for r, m in rr.items()}
    return p["d63"]


def d63_outcome(m):
    crossing = m.get("ph1_crossing_periods", m.get("ph1_periods", 0))
    if m["diverged_us"] is not None:
        return "runaway"
    if m["ph1_depth_a"] > 12.0 and crossing >= 25:
        return "slow_or_runaway"
    return "peak" if m["peak_max_a"] > 200.0 else "ok"


def rows():
    out = []
    for e in EXPS:
        folder = next(TA.glob(f"{e}_*"))
        pred = json.loads(next(folder.glob("*_predictions.json")).read_text())
        for name, m in sorted(registered(e, pred).items()):
            run = folder / "cosim" / f"run_{name}.json"
            if not run.exists():
                continue
            d = json.loads(run.read_text())
            c = d["cfg"]
            step = c.get("load_step") or c.get("line_step")
            t_step = step["t_us"] * 1e-6
            pk = max(x["i_a"] for x in d["highoffs_last"] if x["t_s"] >= t_step)
            st = step_stats(d, t_step=t_step)
            back = st["back_within_1pct_us"]
            runaway = pk > 400.0 or sum(d["late_fires"]) > 100 or (not math.isfinite(back) and pk > 300.0)
            rising = bool(c.get("line_step")) and step["dv"] > 0
            o = d63_outcome(m)
            out.append({"exp": e, "name": name, "group": "rising" if rising else "other", "d63_outcome": o,
                        "bounded": o in ("ok", "peak"), "runaway": runaway,
                        "pred": {"peak": m["peak_max_a"], "mv": m["extreme_mv"], "back": max(m["back_us"], 1.0)},
                        "y": {"peak": pk, "mv": st["extreme_mv"], "back": max(back, 1.0)}})
    return out


def arrays(rr, q):
    return (np.array([r["pred"][q] for r in rr]), np.array([r["y"][q] for r in rr]), np.array([r["group"] for r in rr]))


def methods(cal, test, q, alpha, aci):
    kind = QUANT[q]
    cp, cy, cg = arrays(cal, q)
    tp, _, tg = arrays(test, q)
    out = {"S": band(cp, cy, tp, alpha, kind), "G": band(cp, cy, tp, alpha, kind, signed=True),
           "M": mondrian_band(cp, cy, cg, tp, tg, alpha, kind), "ACI": aci.band(cp, cy, tp, kind)}
    if q == "peak":
        out["hand"] = (0.9 * tp, 1.1 * tp)
    return out


def width(lo, hi, p, kind):
    """Band width relative to the prediction (rel, log) or in the quantity's unit (abs); inf when unbounded."""
    w = hi - lo
    return w if kind == "abs" else w / p


def sequential(rr, alpha):
    res = {q: {} for q in QUANT}
    for q in QUANT:
        aci = ACI(alpha, GAMMA)
        acc = {}
        for k, e in enumerate(EXPS[1:], 1):
            cal = [r for r in rr if r["exp"] in EXPS[:k] and r["bounded"]]
            test = [r for r in rr if r["exp"] == e and r["bounded"]]
            if not test:
                continue
            bands = methods(cal, test, q, alpha, aci)
            tp, ty, _ = arrays(test, q)
            for meth, (lo, hi) in bands.items():
                a = acc.setdefault(meth, {"covered": [], "width": [], "rows": []})
                cov = (lo <= ty) & (ty <= hi)
                a["covered"] += cov.tolist(); a["width"] += width(lo, hi, tp, QUANT[q]).tolist()
                a["rows"] += [{"exp": e, "name": r["name"], "group": r["group"], "pred": float(p), "y": float(y), "lo": float(l), "hi": float(h),
                               "covered": bool(c)} for r, p, y, l, h, c in zip(test, tp, ty, lo, hi, cov)]
            aci.update((bands["ACI"][0] <= ty) & (ty <= bands["ACI"][1]))
        for meth, a in acc.items():
            w = np.array(a["width"])
            res[q][meth] = {"n": len(a["covered"]), "coverage": float(np.mean(a["covered"])),
                            "coverage_rising": float(np.mean([c for c, r in zip(a["covered"], a["rows"]) if r["group"] == "rising"] or [np.nan])),
                            "coverage_other": float(np.mean([c for c, r in zip(a["covered"], a["rows"]) if r["group"] == "other"] or [np.nan])),
                            "finite": int(np.isfinite(w).sum()), "median_width": float(np.median(w)),
                            "per_exp": {e: float(np.mean([c for c, r in zip(a["covered"], a["rows"]) if r["exp"] == e])) for e in EXPS[1:]
                                        if any(r["exp"] == e for r in a["rows"])},
                            "rows": a["rows"]}
    return res


def final_bands(rr):
    """Calibrated on every bounded row: the half-widths a new registration would use (relative for peak and
    recovery, mV for the Vo extreme), per method and group."""
    cal = [r for r in rr if r["bounded"]]
    out = {}
    for q, kind in QUANT.items():
        cp, cy, cg = arrays(cal, q)
        ref = 100.0 if kind == "abs" else 1.0
        for alpha in ALPHAS:
            for meth in ("S", "G", "M"):
                for g in ("rising", "other"):
                    if meth == "M":
                        lo, hi = mondrian_band(cp, cy, cg, [ref], [g], alpha, kind)
                    else:
                        lo, hi = band(cp, cy, [ref], alpha, kind, signed=meth == "G")
                    out[f"{q}/{1 - alpha:.0%}/{meth}/{g}"] = {"lo": float(lo[0] - ref) if kind == "abs" else float(lo[0]),
                                                             "hi": float(hi[0] - ref) if kind == "abs" else float(hi[0])}
    return out


def register_band(pred, q, group, alpha=0.2, method="M"):
    """(lo, hi) for a new registration, calibrated on every bounded row in a125_calibration.json."""
    cal = json.loads(CAL.read_text())["rows"]
    cp = np.array([r["pred"][q] for r in cal]); cy = np.array([r["y"][q] for r in cal]); cg = np.array([r["group"] for r in cal])
    if method == "M":
        lo, hi = mondrian_band(cp, cy, cg, [pred], [group], alpha, QUANT[q])
    else:
        lo, hi = band(cp, cy, [pred], alpha, QUANT[q], signed=method == "G")
    return float(lo[0]), float(hi[0])


def main():
    rr = rows()
    print(f"{len(rr)} registered step rows with a co-simulation; bounded by D63: {sum(r['bounded'] for r in rr)}")
    table = {}
    for r in rr:
        key = f"{r['d63_outcome']} -> {'runaway' if r['runaway'] else 'bounded'}"
        table[key] = table.get(key, 0) + 1
    print("D63 outcome -> co-simulation: " + ", ".join(f"{k} {v}" for k, v in sorted(table.items())))
    res = {"n_rows": len(rr), "outcome_table": table, "sequential": {}}
    for alpha in ALPHAS:
        s = sequential(rr, alpha)
        res["sequential"][f"{1 - alpha:.0%}"] = s
        print(f"\nnominal {1 - alpha:.0%}: prospective coverage (A118-A124), [rising / other], median width")
        for q, mm in s.items():
            for meth, v in mm.items():
                print(f"  {q:5s} {meth:4s}: {v['coverage']:5.0%} of {v['n']:2d} [{v['coverage_rising']:4.0%} / {v['coverage_other']:4.0%}], "
                      f"width {v['median_width']:.3g}" + ("" if QUANT[q] == "abs" else " (x pred)") + f", finite {v['finite']}; per exp "
                      + " ".join(f"{e} {c:.0%}" for e, c in v["per_exp"].items()))
    fb = final_bands(rr)
    res["final_bands"] = fb
    print("\nbands for the next registration (every bounded row; peak and recovery x prediction, Vo extreme mV):")
    for k, v in fb.items():
        print(f"  {k:24s} {v['lo']:+.3f} .. {v['hi']:+.3f}")
    CAL.write_text(json.dumps({"rows": [r for r in rr if r["bounded"]], "quantities": QUANT}, indent=1, default=float) + "\n")
    (HERE / "a125_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print("wrote a125_summary.json, a125_calibration.json")


if __name__ == "__main__":
    main()
