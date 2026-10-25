"""A247 analysis (BOUNDARY Section 2): D57's free-node traces (a247_window.py) against the recorded turn-ons of phases
2-4 (a247_records.py).
- c1: V_DS at the actual delay, D57 against the record, per board (L, gate temperature), rows with i_off <= I_NEG.
- c2: a delay set from the low-side turn-off current known to K bins (uniform over [I_LO, I_NEG]) and the rail known to
  the grid (or not known), chosen on D57's grid alone (the most grid currents of the bin kept <= V_SOFT over +-MARGIN),
  then scored on the records whose own window is not empty.
- c3 (reported): the learner's own outcome on those records (V_DS at the actual turn-on > V_SOFT = hard).
- m1: a GP (ml_gp) on the residual record - D57 against (i_off, rail, delay, dv_err, L, temperature, last); test RMSE
  against D57 alone and the ARD length scales (feature sd / length scale: large = the residual depends on it).
- m2: an MLP classifier (ml_nn) of soft turn-ons from the records alone; its window edges against D57's.
  python3 a247_analyze.py -> a247_summary.json"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scb_ivr.extensions.ml_gp import GP
from scb_ivr.extensions.ml_nn import MLP, Scaler
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
V_SOFT, I_NEG, MARGIN, KS = 2.0, -5.0, 0.5, (1, 2, 4, 8, 16)
C1_MED, C1_AGREE, C2_COVER, C2_KMAX, M1_GAIN, N_BOARD = 1.0, 0.90, 0.95, 8, 0.20, 1000
K_DV = EdgeCircuit().dv_cs / EdgeCircuit().v_rail


class Table:
    def __init__(self, path):
        z = np.load(path)
        self.tr, self.lf, self.rails, self.cur, self.t = z["traces"], z["lf"], z["rails"], z["currents"], z["t_ns"]
        self.vmin = self.tr.min(axis=-1)

    @staticmethod
    def _ix(grid, x):
        f = (np.asarray(x, float) - grid[0]) / (grid[1] - grid[0])
        i0 = np.clip(np.floor(f).astype(int), 0, len(grid) - 2)
        return i0, np.clip(f - i0, 0.0, 1.0), (f >= 0) & (f <= len(grid) - 1)

    def lfi(self, lf_nh):
        return np.argmin(np.abs(self.lf[None, :] * 1e9 - np.asarray(lf_nh)[:, None]), axis=1)

    def v(self, lf_nh, last, rail, i, t):
        """D57's V_DS, trilinear in (rail, i_off, t); nan outside the grid."""
        a, b = self.lfi(lf_nh), np.asarray(last, int)
        (r0, fr, okr), (i0, fi, oki), (t0, ft, okt) = self._ix(self.rails, rail), self._ix(self.cur, i), self._ix(self.t, t)
        out = 0.0
        for dr, wr in ((0, 1 - fr), (1, fr)):
            for di, wi in ((0, 1 - fi), (1, fi)):
                for dt, wt in ((0, 1 - ft), (1, ft)):
                    out = out + wr * wi * wt * self.tr[a, b, r0 + dr, i0 + di, t0 + dt]
        return np.where(okr & oki & okt, out, np.nan)

    def v_min(self, lf_nh, last, rail, i):
        a, b = self.lfi(lf_nh), np.asarray(last, int)
        (r0, fr, okr), (i0, fi, oki) = self._ix(self.rails, rail), self._ix(self.cur, i)
        out = sum(wr * wi * self.vmin[a, b, r0 + dr, i0 + di]
                  for dr, wr in ((0, 1 - fr), (1, fr)) for di, wi in ((0, 1 - fi), (1, fi)))
        return np.where(okr & oki, out, np.nan)


def load_records():
    z = np.load(PROJECT / "tmp" / "a247_records.npz")
    cols = list(z["cols"])
    return {c: z["data"][:, k] for k, c in enumerate(cols)}, list(z["runs"])


def boards(R):
    key = np.round(R["lf_nh"], 3) * 1000 + R["temp_c"]
    return key, {float(k): f"L {k // 1000:.3f} nH, {k % 1000:.0f} C" for k in np.unique(key)}


def c1(tab, R, sel, bkey, bname):
    out, ok = {}, True
    vm = tab.v(R["lf_nh"], R["phase"] == 4, R["rail_v"], R["i_off_a"], R["delay_ns"])
    for k, name in bname.items():
        m = sel & (bkey == k) & np.isfinite(vm)
        if m.sum() < 10:
            continue
        e = vm[m] - R["vds_act_v"][m]
        agree = float(np.mean((vm[m] <= V_SOFT) == (R["vds_act_v"][m] <= V_SOFT)))
        res = {"n": int(m.sum()), "median_abs_v": float(np.median(np.abs(e))), "mean_v": float(np.mean(e)),
               "p90_abs_v": float(np.quantile(np.abs(e), 0.9)), "agree": agree}
        if m.sum() >= N_BOARD:
            res["pass"] = bool(res["median_abs_v"] <= C1_MED and agree >= C1_AGREE)
            ok &= res["pass"]
        out[name] = res
    return out, ok, vm


def bin_delays(tab, a, b, edges, rails_idx):
    """For each bin, the delay on T keeping the most grid currents of the bin <= V_SOFT over +-MARGIN (summed over the
    given rail indices); None where no grid current of the bin has a window."""
    w = int(round(MARGIN / (tab.t[1] - tab.t[0])))
    tr = tab.tr[a, b]                                             # rail, i, t
    worst = np.max(np.stack([np.roll(tr, s, axis=-1) for s in range(-w, w + 1)]), axis=0)
    worst[..., :w], worst[..., -w:] = np.inf, np.inf
    good = worst <= V_SOFT
    has = tab.vmin[a, b] <= V_SOFT
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        ci = np.flatnonzero((tab.cur >= lo) & (tab.cur < hi))
        sc = sum(good[r][ci][has[r][ci]].sum(axis=0) for r in rails_idx)
        if np.isscalar(sc) or sc.max() == 0:
            out.append(None); continue
        best = np.flatnonzero(sc == sc.max())
        out.append(float(tab.t[best[len(best) // 2]]))
    return out


def c2(tab, R, sel):
    has = sel & (tab.v_min(R["lf_nh"], R["phase"] == 4, R["rail_v"], R["i_off_a"]) <= V_SOFT)
    i_lo = float(np.quantile(R["i_off_a"][has], 0.01))
    res = {"i_lo_a": i_lo, "n_with_window": int(has.sum()), "rail_known": {}, "rail_unknown": {}}
    a_all, b_all = tab.lfi(R["lf_nh"]), (R["phase"] == 4).astype(int)
    ri = np.clip(np.round((R["rail_v"] - tab.rails[0]) / (tab.rails[1] - tab.rails[0])).astype(int), 0, len(tab.rails) - 1)
    typical = [j for j, r in enumerate(tab.rails) if 8.0 <= r <= 16.0]
    for K in KS:
        edges = np.linspace(i_lo, I_NEG, K + 1)
        bi = np.clip(np.searchsorted(edges, R["i_off_a"], side="right") - 1, 0, K - 1)
        for mode in ("rail_known", "rail_unknown"):
            d = np.full(len(R["i_off_a"]), np.nan)
            for a in range(len(tab.lf)):
                for b in (0, 1):
                    if mode == "rail_known":
                        for j in range(len(tab.rails)):
                            ds = bin_delays(tab, a, b, edges, [j])
                            m = has & (a_all == a) & (b_all == b) & (ri == j)
                            d[m] = [np.nan if ds[q] is None else ds[q] for q in bi[m]]
                    else:
                        ds = bin_delays(tab, a, b, edges, typical)
                        m = has & (a_all == a) & (b_all == b)
                        d[m] = [np.nan if ds[q] is None else ds[q] for q in bi[m]]
            cov = np.ones(len(d), bool)
            for s in (-MARGIN, 0.0, MARGIN):
                vv = tab.v(R["lf_nh"], R["phase"] == 4, R["rail_v"], R["i_off_a"], d + s)
                cov &= np.nan_to_num(vv, nan=99.0) <= V_SOFT
            res[mode][str(K)] = float(cov[has].mean())
    ks = [K for K in KS if res["rail_known"][str(K)] >= C2_COVER]
    res["k_min_rail_known"] = ks[0] if ks else None
    return res, has


def c3(R, has):
    hard = R["vds_act_v"] > V_SOFT
    edges = [-100.0, -60.0, -40.0, -30.0, -20.0, -5.0]
    by = {f"{lo:.0f}..{hi:.0f} A": {"n": int(m.sum()), "hard": float(hard[m].mean())}
          for lo, hi in zip(edges[:-1], edges[1:]) for m in [has & (R["i_off_a"] >= lo) & (R["i_off_a"] < hi)] if m.sum()}
    late = has & (R["t_p_us"] >= 20.0)
    return {"hard_with_window": float(hard[has].mean()), "hard_with_window_after_20us": float(hard[late].mean()),
            "by_i_off": by}


def features(R):
    dv = np.where(R["phase"] == 4, 0.0, R["rail_next_v"] - K_DV * R["rail_v"])
    return np.column_stack([R["i_off_a"], R["rail_v"], R["delay_ns"], dv, R["lf_nh"], R["temp_c"], R["phase"] == 4])


FEAT = ("i_off_a", "rail_v", "delay_ns", "dv_err_v", "lf_nh", "temp_c", "last")


def m1(R, vm, sel, n=800, seed=0):
    ok = np.flatnonzero(sel & np.isfinite(vm))
    rng = np.random.default_rng(seed)
    idx = rng.choice(ok, 2 * n, replace=False)
    tr, te = idx[:n], idx[n:]
    X, y = features(R), R["vds_act_v"] - vm
    sc = Scaler.fit(X[tr])
    keep = [j for j in range(X.shape[1]) if np.std(X[tr, j]) > 0]
    gp = GP()
    gp.fit(sc.fwd(X[tr])[:, keep], y[tr], restarts=3, seed=seed)
    mu = gp.predict(sc.fwd(X[te])[:, keep], noise=False)[0]
    rm0, rm1 = float(np.sqrt(np.mean(y[te] ** 2))), float(np.sqrt(np.mean((y[te] - mu) ** 2)))
    l = gp.l if hasattr(gp, "l") else None
    rel = {FEAT[j]: (None if l is None else float(1.0 / l[q])) for q, j in enumerate(keep)}
    return {"n_train": n, "n_test": n, "rmse_d57_v": rm0, "rmse_d57_gp_v": rm1, "gain": 1.0 - rm1 / rm0,
            "relevance_1_over_l": rel, "missing_block": bool(1.0 - rm1 / rm0 >= M1_GAIN)}


def m2(tab, R, sel, seed=0):
    ok = np.flatnonzero(sel)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(ok)[:60000]
    X = features(R)[:, [0, 1, 2, 4, 5, 6]]
    y = (R["vds_act_v"] <= V_SOFT).astype(float)[:, None]
    sc = Scaler.fit(X[idx])
    net = MLP([X.shape[1], 32, 32, 1], out="sigmoid", seed=seed)
    net.fit(sc.fwd(X[idx[:50000]]), y[idx[:50000]], sc.fwd(X[idx[50000:]]), y[idx[50000:]], epochs=200, patience=20,
            seed=seed)
    acc = float(np.mean((net.predict(sc.fwd(X[idx[50000:]]))[:, 0] > 0.5) == (y[idx[50000:], 0] > 0.5)))
    pts = []
    t = tab.t
    for lf_nh, temp in sorted({(round(a, 3), b) for a, b in zip(R["lf_nh"][ok], R["temp_c"][ok])}):
        for i in (-30.0, -40.0, -50.0, -70.0):
            near = sel & (np.abs(R["lf_nh"] - lf_nh) < 1e-3) & (R["temp_c"] == temp) & (R["phase"] < 4) & \
                (np.abs(R["i_off_a"] - i) <= 3.0) & (np.abs(R["rail_v"] - 12.0) <= 1.0)
            if near.sum() < 100:
                continue
            xg = np.column_stack([np.full_like(t, i), np.full_like(t, 12.0), t, np.full_like(t, lf_nh),
                                  np.full_like(t, temp), np.zeros_like(t)])
            p = net.predict(sc.fwd(xg))[:, 0] > 0.5
            v = tab.v(np.full_like(t, lf_nh), np.zeros_like(t), np.full_like(t, 12.0), np.full_like(t, i), t) <= V_SOFT
            span = lambda q: [float(t[q][0]), float(t[q][-1])] if q.any() else None
            pts.append({"board": f"L {lf_nh:.3f} nH, {temp:.0f} C", "i_off_a": i, "rail_v": 12.0, "n_near": int(near.sum()),
                        "delays_near_p5_p95_ns": [float(np.quantile(R["delay_ns"][near], 0.05)),
                                                  float(np.quantile(R["delay_ns"][near], 0.95))],
                        "mlp_window_ns": span(p), "d57_window_ns": span(v)})
    return {"val_accuracy": acc, "windows": pts}


def main():
    tab = Table(PROJECT / "tmp" / "a247_window.npz")
    R, runs = load_records()
    bkey, bname = boards(R)
    sel = R["i_off_a"] <= I_NEG
    res = {"n_runs": len(runs), "n_turn_ons": int(len(R["i_off_a"])), "n_neg": int(sel.sum())}
    res["c1"], ok1, vm = c1(tab, R, sel, bkey, bname)
    res["c2"], has = c2(tab, R, sel)
    res["c3"] = c3(R, has)
    res["m1"] = m1(R, vm, sel)
    res["m2"] = m2(tab, R, sel)
    k = res["c2"]["k_min_rail_known"]
    res["criteria"] = {"c1": bool(ok1), "c2": bool(k is not None and k <= C2_KMAX)}
    (HERE / "a247_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    for name, x in res["c1"].items():
        print(f"c1 {name}: n {x['n']} med|e| {x['median_abs_v']:.2f} V mean {x['mean_v']:+.2f} agree {x['agree']:.3f}")
    print("c2 rail known", res["c2"]["rail_known"], "| unknown", res["c2"]["rail_unknown"], "| K_min", k)
    print("c3", {kk: v for kk, v in res["c3"].items() if kk != "by_i_off"})
    print("m1 rmse", round(res["m1"]["rmse_d57_v"], 3), "->", round(res["m1"]["rmse_d57_gp_v"], 3), "relevance",
          {kk: round(v, 2) for kk, v in res["m1"]["relevance_1_over_l"].items() if v is not None})
    print("m2 acc", round(res["m2"]["val_accuracy"], 3), "windows", len(res["m2"]["windows"]))
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
