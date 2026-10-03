"""A121: a Gaussian process on the residual co-simulation - D63 (peak current after a step), its leave-one-out check,
its prospective predictions of A118's rows (registered before A118's results are read), and the next co-simulation
runs it would choose (largest predictive sd in the region of interest).

    python3 .../run_a121.py register     # fit on A115-A117, predict A118's step rows -> a121_predictions_a118.json
    python3 .../run_a121.py evaluate     # after A118: score the registered predictions, refit on all, propose runs

Inputs (10): pct, ln Cs, fc (standardised); comparator, timed edge (timed or floor), floor (binary; the floor's length
scale fixed at 1, a registered prior: a floor row is a timed row with added uncertainty); load; di / 62.5; dv / 4.8;
ln slew (standardised). The baseline is D63 (ml_d63_data.evaluate); runaways and D63-diverged rows are left out.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402
from scb_ivr.extensions import ml_d63_data as DD  # noqa: E402
from scb_ivr.extensions.ml_gp import GP  # noqa: E402

spec = importlib.util.spec_from_file_location("run_a120", HERE.parent / "A120_d63_surrogate_mlp" / "run_a120.py")
A120 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A120)
A118 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A118_p24_floor_turn_off" / "cosim"
FLOOR_COL = 5


def sample_from_cfg(c):
    pct = -c["i_target"] / 1.25
    cs = (c.get("circuit") or {}).get("cs", 15e-6) * 1e6
    fc = 60.0 * c["kp_ns_per_v"] / DD.KP60
    rule = ("floor" if c.get("lo_floor", 0) else "timed") if c.get("lo_pred", 0) else "cmp"
    s = dict(pct=pct, cs_uf=cs, fc_khz=fc, rule=rule, floor_a=float(c.get("lo_floor_a", 2.0)) if rule == "floor" else 0.0)
    if c.get("load_step"):
        s.update(kind="load", di_a=float(c["load_step"]["i_a"]), dv_v=0.0, slew_us=1.0)
        t_step = c["load_step"]["t_us"] * 1e-6
    elif c.get("line_step"):
        ls = c["line_step"]
        s.update(kind="line", di_a=0.0, dv_v=float(ls["dv"]), slew_us=float(ls.get("slew_us", 1.0)))
        t_step = ls["t_us"] * 1e-6
    else:
        return None, None
    return s, t_step


def raw_features(s):
    return [s["pct"], math.log(s["cs_uf"]), s["fc_khz"], float(s["rule"] == "cmp"), float(s["rule"] in ("timed", "floor")),
            float(s["rule"] == "floor"), float(s["kind"] == "load"), s["di_a"] / 62.5, s["dv_v"] / 4.8, math.log(s["slew_us"])]


class Features:
    CONT = (0, 1, 2, 9)

    def fit(self, rows):
        a = np.array(rows)
        self.m = a[:, self.CONT].mean(axis=0)
        self.sd = np.where(a[:, self.CONT].std(axis=0) > 0, a[:, self.CONT].std(axis=0), 1.0)
        return self

    def __call__(self, rows):
        a = np.array(rows, float)
        a[:, self.CONT] = (a[:, self.CONT] - self.m) / self.sd
        return a


def training():
    ith = tuple(tuple(v) for v in json.loads(DD.D63_DIAG.read_text())["thresholds"][str(DD.L1)])
    ttr = json.loads(str(np.load(HERE.parent / "A120_d63_surrogate_mlp" / "a120_dataset.npz")["ttr"]))
    rows = []
    for name, s, pk, mv, run_away in A120.cosim_cases():
        d = DD.evaluate((s, ith, ttr))
        if run_away or d["diverged"]:
            continue
        rows.append({"case": name, "sample": s, "cosim_peak_a": pk, "d63_peak_a": d["peak_a"]})
    return rows, ith, ttr


def fit(rows):
    f = Features().fit([raw_features(r["sample"]) for r in rows])
    x = f([raw_features(r["sample"]) for r in rows])
    y = np.array([r["cosim_peak_a"] - r["d63_peak_a"] for r in rows])
    return f, GP(fixed_l={FLOOR_COL: 1.0}).fit(x, y, restarts=12), y


def register():
    rows, ith, ttr = training()
    f, g, y = fit(rows)
    mu, sd = g.loo()
    d63_mae = float(np.mean(np.abs(y)))
    gp_mae = float(np.mean(np.abs(y - mu)))
    cover = float(np.mean(np.abs(y - mu) <= 1.645 * sd))
    print(f"training: {len(rows)} transients; residual co-simulation - D63: mean {y.mean():+.1f} A, MAE {d63_mae:.1f} A")
    print(f"leave-one-out: D63 + GP MAE {gp_mae:.1f} A ({gp_mae / d63_mae:.2f} of D63's), coverage at +-1.645 sd {cover:.0%}; "
          f"GP s {g.s:.1f} A, noise {g.n:.1f} A, length scales " + ", ".join(f"{v:.2f}" for v in g.l))
    preds = {}
    for p in sorted(A118.glob("cfg_*.json")):
        c = json.loads(p.read_text())
        s, _ = sample_from_cfg(c)
        if s is None:
            continue
        d = DD.evaluate((s, ith, ttr))
        m, sdv = g.predict(f([raw_features(s)]))
        preds[p.stem[4:]] = {"sample": s, "d63_peak_a": d["peak_a"], "d63_diverged": d["diverged"],
                             "gp_peak_a": d["peak_a"] + float(m[0]), "gp_sd_a": float(sdv[0])}
        print(f"   A118 {p.stem[4:]:16s}: D63 {d['peak_a']:6.1f} A -> D63 + GP {d['peak_a'] + m[0]:6.1f} +- {sdv[0]:4.1f} A")
    out = {"training": {"n": len(rows), "cases": [r["case"] for r in rows], "d63_mae_a": d63_mae, "loo_gp_mae_a": gp_mae,
                        "loo_coverage_1p645": cover, "hyper": {"s": g.s, "noise": g.n, "l": list(g.l)},
                        "loo_sd_median_a": float(np.median(sd))},
           "a118": preds}
    (HERE / "a121_predictions_a118.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote a121_predictions_a118.json")


def evaluate():
    reg = json.loads((HERE / "a121_predictions_a118.json").read_text())
    tr = reg["training"]
    res = {"loo": tr, "a118": {}}
    errs_d63, errs_gp, cov, sds = [], [], [], []
    new_rows = []
    for name, p in reg["a118"].items():
        run = A118 / f"run_{name}.json"
        if not run.exists():
            continue
        d = json.loads(run.read_text())
        s, t_step = sample_from_cfg(d["cfg"])
        pk = max(x["i_a"] for x in d["highoffs_last"] if x["t_s"] >= t_step)
        st = step_stats(d, t_step=t_step)
        run_away = pk > 400.0 or (not math.isfinite(st["back_within_1pct_us"]) and pk > 300.0) or sum(d["late_fires"]) > 100
        row = {"cosim_peak_a": pk, "runaway": run_away, **p}
        res["a118"][name] = row
        if run_away or p["d63_diverged"]:
            continue
        errs_d63.append(abs(pk - p["d63_peak_a"])); errs_gp.append(abs(pk - p["gp_peak_a"]))
        cov.append(abs(pk - p["gp_peak_a"]) <= 1.645 * p["gp_sd_a"]); sds.append(p["gp_sd_a"])
        new_rows.append({"case": f"A118_{name}", "sample": s, "cosim_peak_a": pk, "d63_peak_a": p["d63_peak_a"]})
        print(f"A118 {name:16s}: co-simulation {pk:6.1f} A | D63 {p['d63_peak_a']:6.1f} | D63 + GP {p['gp_peak_a']:6.1f} +- {p['gp_sd_a']:4.1f}")
    pro = {"n": len(errs_gp), "d63_mae_a": float(np.mean(errs_d63)), "gp_mae_a": float(np.mean(errs_gp)), "coverage_1p645": float(np.mean(cov)),
           "sd_median_a": float(np.median(sds)), "loo_sd_median_a": tr["loo_sd_median_a"]}
    res["prospective"] = pro
    print(f"prospective on A118 ({pro['n']}): MAE D63 {pro['d63_mae_a']:.1f} A, D63 + GP {pro['gp_mae_a']:.1f} A; coverage {pro['coverage_1p645']:.0%}; "
          f"median sd {pro['sd_median_a']:.1f} A against {pro['loo_sd_median_a']:.1f} A in training")
    res["criteria"] = {"loo_gp_0p8_of_d63": tr["loo_gp_mae_a"] <= 0.8 * tr["d63_mae_a"], "loo_coverage_75pct": tr["loo_coverage_1p645"] >= 0.75,
                       "prospective_not_worse": pro["gp_mae_a"] <= pro["d63_mae_a"], "prospective_coverage_75pct": pro["coverage_1p645"] >= 0.75,
                       "floor_rows_less_certain": pro["sd_median_a"] > pro["loo_sd_median_a"]}
    print("criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in res["criteria"].items()))
    # refit on everything and propose the next co-simulation runs (largest predictive sd in the region of interest)
    rows, ith, ttr = training()
    rows += new_rows
    f, g, y = fit(rows)
    rng = np.random.default_rng(11)
    cands = []
    for _ in range(4000):
        s = dict(pct=float(rng.uniform(8, 12)), cs_uf=float(np.exp(rng.uniform(np.log(4), np.log(10)))), fc_khz=60.0, rule="floor",
                 floor_a=float(rng.uniform(1, 4)))
        if rng.random() < 0.3:
            s.update(kind="load", di_a=float(rng.choice([-62.5, 62.5])), dv_v=0.0, slew_us=1.0)
        else:
            s.update(kind="line", di_a=0.0, dv_v=float(rng.choice([-4.8, 4.8])), slew_us=float(np.exp(rng.uniform(0, np.log(20)))))
        cands.append(s)
    m, sdv = g.predict(f([raw_features(s) for s in cands]))
    order = np.argsort(-sdv)
    chosen = []
    for i in order:                                           # greedy, with a minimum spacing in feature space
        xi = f([raw_features(cands[i])])[0]
        if all(np.linalg.norm(xi - f([raw_features(c["sample"])])[0]) > 0.8 for c in chosen):
            chosen.append({"sample": cands[i], "gp_residual_a": float(m[i]), "gp_sd_a": float(sdv[i])})
        if len(chosen) == 8:
            break
    res["refit"] = {"n": len(rows), "hyper": {"s": g.s, "noise": g.n, "l": list(g.l)}}
    res["proposal"] = chosen
    print(f"refit on {len(rows)}; next co-simulation runs (largest sd, floor rule region):")
    for c in chosen:
        s = c["sample"]
        print(f"   pct {s['pct']:4.1f}, Cs {s['cs_uf']:4.1f} uF, floor {s['floor_a']:.1f} A, {s['kind']} "
              + (f"{s['di_a']:+.1f} A" if s["kind"] == "load" else f"{s['dv_v']:+.1f} V over {s['slew_us']:.1f} us")
              + f": residual {c['gp_residual_a']:+.1f} +- {c['gp_sd_a']:.1f} A")
    (HERE / "a121_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    register() if sys.argv[1:] == ["register"] else evaluate()
