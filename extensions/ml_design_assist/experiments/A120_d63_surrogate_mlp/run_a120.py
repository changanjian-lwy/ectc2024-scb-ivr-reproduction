"""A120: the D63 dataset, the MLP surrogate, and its checks against BOUNDARY Section 2.

    python3 extensions/ml_design_assist/experiments/A120_d63_surrogate_mlp/run_a120.py

Writes a120_dataset.npz (cached; delete to regenerate), a120_mlp.npz (the trained network and its scalers) and
a120_summary.json.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats  # noqa: E402
from scb_ivr.extensions import ml_d63_data as DD  # noqa: E402
from scb_ivr.extensions.ml_nn import MLP, Scaler  # noqa: E402

TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
COSIM = {   # run file: outcome label from its RESULTS (runaways are excluded from the error statistics)
    TA / "A115_p24_one_mhz_design_point" / "cosim": ["n5_s_p62", "n5_s_m62", "n10_s_p62", "n10_s_m62"],
    TA / "A116_p24_one_mhz_transients" / "cosim": ["t30_s_m62", "c60_s_m62", "c30_s_m62", "t30_s_p62", "c60_s_p62", "c30_s_p62",
                                                   "t60_l_p48_1us", "t30_l_p48_1us", "c60_l_p48_1us", "c30_l_p48_1us",
                                                   "t60_l_m48_1us", "t30_l_m48_1us", "c60_l_m48_1us", "c30_l_m48_1us"],
    TA / "A117_p24_one_mhz_line_slew_cs" / "cosim": ["c3_cmp_l_p48_5us", "c3_cmp_l_m48_1us", "c15_tim_l_m48_20us",
                                                     "c3_tim_l_m48_10us", "c15_tim_l_m48_50us", "c15_cmp_l_p48_20us",
                                                     "c15_cmp_l_p48_50us", "c15_cmp_l_m48_5us", "c15_tim_l_p48_10us",
                                                     "c3_tim_l_p48_1us", "c3_cmp_l_p48_20us", "c3_cmp_s_m62"],
}
STANDARD = [("load", -62.5, 0.0, 1.0), ("load", 62.5, 0.0, 1.0)] + [("line", 0.0, dv, s) for s in (1.0, 5.0, 20.0) for dv in (4.8, -4.8)]


def r2(y, p):
    return float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


def dataset(n=8000, seed=1):
    path = HERE / "a120_dataset.npz"
    if path.exists():
        z = np.load(path, allow_pickle=False)
        return z["x"], z["y"], z["div"], json.loads(str(z["ttr"]))
    ss, res, ttr = DD.generate(n, seed)
    x, div = DD.features(ss), np.array([r["diverged"] for r in res])
    y = np.full((n, len(DD.TARGETS)), np.nan)
    ok = ~div
    y[ok] = DD.targets([r for r, d in zip(res, div) if not d])
    np.savez(path, x=x, y=y, div=div, ttr=json.dumps(ttr))
    return x, y, div, ttr


def cosim_cases():
    """(sample dict, cosim peak after the step A, cosim extreme mV, runaway?) for each 1 MHz co-simulated transient."""
    out = []
    for folder, names in COSIM.items():
        for name in names:
            d = json.loads((folder / f"run_{name}.json").read_text())
            c = d["cfg"]
            pct = -c["i_target"] / 1.25
            cs = (c.get("circuit") or {}).get("cs", 15e-6) * 1e6
            fc = 60.0 * c["kp_ns_per_v"] / DD.KP60
            rule = "timed" if c.get("lo_pred", 0) else "cmp"
            if c.get("load_step"):
                s = dict(kind="load", di_a=float(c["load_step"]["i_a"]), dv_v=0.0, slew_us=1.0)
                t_step = c["load_step"]["t_us"] * 1e-6
            else:
                ls = c["line_step"]
                s = dict(kind="line", di_a=0.0, dv_v=float(ls["dv"]), slew_us=float(ls.get("slew_us", 1.0)))
                t_step = ls["t_us"] * 1e-6
            s.update(pct=pct, cs_uf=cs, fc_khz=fc, rule=rule, floor_a=0.0)
            pk = max(x["i_a"] for x in d["highoffs_last"] if x["t_s"] >= t_step)
            st = step_stats(d, t_step=t_step)
            run_away = pk > 400.0 or not math.isfinite(st["back_within_1pct_us"]) and pk > 300.0
            out.append((name, s, pk, st["extreme_mv"], run_away))
    return out


def main():
    t0 = time.time()
    x, y, div, ttr = dataset()
    print(f"dataset: {len(x)} samples, {int(div.sum())} diverged ({time.time() - t0:.0f} s)")
    ok = ~div
    xs, ys = x[ok], y[ok]
    n = len(xs)
    i_tr, i_va, i_te = np.arange(0, int(0.8 * n)), np.arange(int(0.8 * n), int(0.9 * n)), np.arange(int(0.9 * n), n)
    sx, sy = Scaler.fit(xs[i_tr]), Scaler.fit(ys[i_tr])
    net = MLP([x.shape[1], 64, 64, y.shape[1]], seed=0)
    hist = net.fit(sx.fwd(xs[i_tr]), sy.fwd(ys[i_tr]), sx.fwd(xs[i_va]), sy.fwd(ys[i_va]), epochs=600, batch=128, lr=2e-3,
                   l2=1e-5, patience=40, log=print)
    pred = sy.inv(net.predict(sx.fwd(xs[i_te])))
    yt = ys[i_te]
    res = {"n": int(len(x)), "diverged": int(div.sum()), "epochs": len(hist), "test": {}}
    for k, name in enumerate(DD.TARGETS):
        res["test"][name] = {"mae": float(np.mean(np.abs(pred[:, k] - yt[:, k]))), "r2": r2(yt[:, k], pred[:, k])}
        print(f"test {name:18s}: MAE {res['test'][name]['mae']:.3f}, R2 {res['test'][name]['r2']:.4f}")
    net.save(HERE / "a120_mlp.npz", x_mean=sx.mean, x_sd=sx.sd, y_mean=sy.mean, y_sd=sy.sd)

    # speed: D63 per transient (measured on 40 test samples) against the batched MLP
    ith = tuple(tuple(v) for v in json.loads(DD.D63_DIAG.read_text())["thresholds"][str(DD.L1)])
    smp = DD.sample(40, 99)
    t1 = time.time(); [DD.evaluate((s, ith, ttr)) for s in smp]; t_d63 = (time.time() - t1) / 40
    big = sx.fwd(np.repeat(xs[i_te], 50, axis=0))
    t1 = time.time(); sy.inv(net.predict(big)); t_mlp = (time.time() - t1) / len(big)
    res["speed"] = {"d63_s": t_d63, "mlp_s": t_mlp, "ratio": t_d63 / t_mlp}
    print(f"speed: D63 {t_d63 * 1e3:.1f} ms, MLP {t_mlp * 1e6:.2f} us per transient, x{t_d63 / t_mlp:.0f}")

    # against the co-simulation
    cases = cosim_cases()
    rows = []
    for name, s, pk, mv, run_away in cases:
        d63 = DD.evaluate((s, ith, ttr))
        p = sy.inv(net.predict(sx.fwd(DD.features([s]))))[0]
        rows.append({"case": name, "cosim_peak_a": pk, "cosim_extreme_mv": mv, "runaway": run_away, "d63_peak_a": d63["peak_a"],
                     "d63_diverged": d63["diverged"], "mlp_peak_a": float(p[0]), "d63_extreme_mv": d63["extreme_mv"],
                     "mlp_extreme_mv": float(p[1])})
    use = [r for r in rows if not r["runaway"] and not r["d63_diverged"]]
    e_d63 = float(np.mean([abs(r["d63_peak_a"] - r["cosim_peak_a"]) for r in use]))
    e_mlp = float(np.mean([abs(r["mlp_peak_a"] - r["cosim_peak_a"]) for r in use]))
    res["cosim"] = {"rows": rows, "n_used": len(use), "d63_peak_mae": e_d63, "mlp_peak_mae": e_mlp,
                    "mlp_vs_d63_peak_mae": float(np.mean([abs(r["mlp_peak_a"] - r["d63_peak_a"]) for r in use]))}
    print(f"co-simulation ({len(use)} transients): peak MAE D63 {e_d63:.1f} A, MLP {e_mlp:.1f} A")
    for r in rows:
        print(f"   {r['case']:20s} cosim {r['cosim_peak_a']:5.0f} A{' (runaway)' if r['runaway'] else ''}, D63 {r['d63_peak_a']:5.0f}"
              f"{' (diverged)' if r['d63_diverged'] else ''}, MLP {r['mlp_peak_a']:5.0f}")

    # the design check on 200 random designs
    rng = np.random.default_rng(7)
    agree, edge, tot, rows_d = 0, 0, 0, []
    for _ in range(200):
        base = DD.sample(1, int(rng.integers(1e9)))[0]
        ss = [dict(base, kind=k, di_a=di, dv_v=dv, slew_us=sl) for k, di, dv, sl in STANDARD]
        d63 = [DD.evaluate((s, ith, ttr)) for s in ss]
        f_d63 = all((not r["diverged"]) and r["peak_a"] <= 200 and not (r["ph1_depth_a"] > 12 and r["ph1_periods"] >= 25) for r in d63)
        p = sy.inv(net.predict(sx.fwd(DD.features(ss))))
        f_mlp = all(q[0] <= 200 and not (q[2] > 12 and math.expm1(q[3]) >= 25) for q in p)
        near = any(abs(r["peak_a"] - 200) < 10 for r in d63 if not r["diverged"])
        agree += f_d63 == f_mlp; tot += 1; edge += near and f_d63 != f_mlp
        rows_d.append({"design": {k: base[k] for k in ("pct", "cs_uf", "fc_khz", "rule", "floor_a")}, "d63": f_d63, "mlp": f_mlp, "near_edge": near})
    res["design_check"] = {"agree": agree / tot, "disagree_near_200a_edge": edge, "feasible_d63": sum(r["d63"] for r in rows_d),
                           "rows": rows_d}
    print(f"design check: agreement {agree / tot:.1%}, D63-feasible {res['design_check']['feasible_d63']} of {tot}; "
          f"disagreements within 10 A of 200 A: {edge} of {tot - agree}")
    t = res["test"]
    res["criteria"] = {"peak_mae_5A": t["peak_a"]["mae"] <= 5.0, "peak_r2_0p97": t["peak_a"]["r2"] >= 0.97,
                       "extreme_r2_0p90": t["extreme_mv"]["r2"] >= 0.90, "depth_mae_2A": t["ph1_depth_a"]["mae"] <= 2.0,
                       "back_r2_0p80": t["log1p_back_us"]["r2"] >= 0.80, "speed_1000x": res["speed"]["ratio"] >= 1000,
                       "cosim_within_d63_plus_5A": e_mlp <= e_d63 + 5.0, "design_agree_90pct": agree / tot >= 0.90}
    print("criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in res["criteria"].items()))
    (HERE / "a120_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
