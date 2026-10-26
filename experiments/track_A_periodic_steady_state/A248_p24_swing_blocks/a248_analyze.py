"""A248 analysis (BOUNDARY Section 2): the harness (a248_swing.py, tmp/a248_swing.npz) against A247's records and
D57's table (tmp/a247_records.npz, tmp/a247_window.npz), and D57 with two blocks.
- h1: the full harness's V_DS at each record's (board, phase group, rail, i_off, actual delay), trilinear on the
  harness grid, against the recorded V_DS; per board and overall.
- h2: every variant fitted to D57 on the harness grid as V_variant(t) = V_D57(t - shift) + offset (delays 0-T_FIT ns);
  bare must sit near D57, full near A247's correction; each dropped block's share of full's shift and offset.
- h3: D57 plus the plant's r_core across the inductor, its swing held at x = 0 until the middle of the low side's
  current fall (the harness's t_fall / t_stop), against the full harness (delays 0-T_FIT ns).
- Post hoc (after h1's miss; RESULTS): each record's rail taken from its own V_DS at the turn-on command (the full
  harness inverted over rail at the command's delay) instead of the sections; then h1 again; the harness's soft
  windows, one delay per board / phase group / rail, and that delay against the learner on the same rows.
  python3 a248_analyze.py [--jobs 10] -> a248_summary.json"""
from __future__ import annotations

import argparse
import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
_s = importlib.util.spec_from_file_location("a247_analyze", TA / "A247_p24_zvs_window" / "a247_analyze.py")
A47 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A47)
_s = importlib.util.spec_from_file_location("a248_swing", HERE / "a248_swing.py")
SW = importlib.util.module_from_spec(_s)
_s.loader.exec_module(SW)
BOARD_OF = {(2.933, 25.0): "N0", (2.2, 25.0): "N75", (2.2, 125.0): "S75h", (2.933, 125.0): "N0h", (3.813, 25.0): "N13"}
T_FIT = 25.0
H1_RMSE, H1_MED, H1_AGREE, H2_SHIFT, H2_OFF, H3_RMSE = 0.35, 0.30, 0.95, 0.30, 0.20, 0.30


def harness():
    z = np.load(PROJECT / "tmp" / "a248_swing.npz")
    return {k: z[k] for k in z.files}


def trilinear(H, b, var, last, rail, i, t):
    tr = H["traces"][b, var, last]                                   # rail, i, t
    out, ok = 0.0, np.ones(len(rail), bool)
    ix = []
    for grid, x in ((H["rails"], rail), (H["currents"], i), (H["t_ns"], t)):
        f = (np.asarray(x, float) - grid[0]) / (grid[1] - grid[0])
        i0 = np.clip(np.floor(np.nan_to_num(f)).astype(int), 0, len(grid) - 2)
        ok &= (f >= 0) & (f <= len(grid) - 1)
        ix.append((i0, np.clip(f - i0, 0.0, 1.0)))
    (r0, fr), (c0, fc), (t0, ft) = ix
    for dr, wr in ((0, 1 - fr), (1, fr)):
        for dc, wc in ((0, 1 - fc), (1, fc)):
            for dt, wt in ((0, 1 - ft), (1, ft)):
                out = out + wr * wc * wt * tr[r0 + dr, c0 + dc, t0 + dt]
    return np.where(ok, out, np.nan)


def h1(H):
    R, _ = A47.load_records()
    tab = A47.Table(PROJECT / "tmp" / "a247_window.npz")
    sf = json.loads((TA / "A247_p24_zvs_window" / "a247_summary.json").read_text())["post_hoc"]["shift_fit"]
    boards = list(H["boards"])
    full = list(H["variants"]).index("full")
    key = [BOARD_OF.get((round(float(l), 3), float(t))) for l, t in zip(R["lf_nh"], R["temp_c"])]
    bi = np.array([boards.index(k) if k in boards else -1 for k in key])
    last = (R["phase"] == 4).astype(int)
    vh = np.full(len(bi), np.nan)
    for b in range(len(boards)):
        for g in (0, 1):
            m = (bi == b) & (last == g)
            vh[m] = trilinear(H, b, full, g, R["rail_v"][m], R["i_off_a"][m], R["delay_ns"][m])
    sel = np.isfinite(vh)
    vd = tab.v(R["lf_nh"], last, R["rail_v"], R["i_off_a"], R["delay_ns"])
    vc = tab.v(R["lf_nh"], last, R["rail_v"], R["i_off_a"], R["delay_ns"] - sf["shift_ns"]) + sf["offset_v"]
    y = R["vds_act_v"]
    rm = lambda v, m: float(np.sqrt(np.nanmean((v[m] - y[m]) ** 2)))
    out = {"n": int(sel.sum()), "rmse_harness_v": rm(vh, sel), "rmse_d57_v": rm(vd, sel), "rmse_d57_a247_v": rm(vc, sel),
           "boards": {}}
    ok = out["rmse_harness_v"] <= H1_RMSE
    for b, name in enumerate(boards):
        m = sel & (bi == b)
        if m.sum() < 100:
            continue
        e = vh[m] - y[m]
        x = {"n": int(m.sum()), "median_abs_v": float(np.median(np.abs(e))), "mean_v": float(np.mean(e)),
             "agree": float(np.mean((vh[m] <= A47.V_SOFT) == (y[m] <= A47.V_SOFT))), "rmse_v": rm(vh, m)}
        x["pass"] = bool(x["median_abs_v"] <= H1_MED and x["agree"] >= H1_AGREE)
        ok &= x["pass"]
        out["boards"][name] = x
    out["pass"] = bool(ok)
    return out


def d57_grid(H, lf_of):
    """D57's V_DS on the harness grid (A247's table, interpolated)."""
    tab = A47.Table(PROJECT / "tmp" / "a247_window.npz")
    t = H["t_ns"]
    out = np.zeros(H["traces"].shape[:1] + H["traces"].shape[2:], np.float32)
    for b, name in enumerate(H["boards"]):
        for g in (0, 1):
            for r, rail in enumerate(H["rails"]):
                for c, i in enumerate(H["currents"]):
                    n = t.size
                    out[b, g, r, c] = tab.v(np.full(n, lf_of[name]), np.full(n, g), np.full(n, rail), np.full(n, i), t)
    return out


def fit(V, D, t):
    """shift, offset, rmse of V(t) = D(t - shift) + offset over delays 0-T_FIT ns (V, D: [..., t])."""
    m = t <= T_FIT
    best = None
    for sh in np.arange(-1.0, 3.01, 0.05):
        Ds = np.array([np.interp(t - sh, t, d, left=d[0]) for d in D.reshape(-1, t.size)]).reshape(D.shape)
        r = (V - Ds)[..., m]
        off = float(np.median(r))
        rm = float(np.sqrt(np.mean((r - off) ** 2)))
        if best is None or rm < best[2]:
            best = (float(sh), off, rm)
    return {"shift_ns": round(best[0], 3), "offset_v": best[1], "rmse_v": best[2]}


def h2(H, D):
    t = H["t_ns"]
    res = {v: fit(H["traces"][:, k], D, t) for k, v in enumerate(H["variants"])}
    full = res["full"]
    for v in SW.DROP:
        res[v]["share_shift"] = (full["shift_ns"] - res[v]["shift_ns"]) / full["shift_ns"] if full["shift_ns"] else None
        res[v]["share_offset"] = (full["offset_v"] - res[v]["offset_v"]) / full["offset_v"] if full["offset_v"] else None
    ok = abs(res["bare"]["shift_ns"]) <= H2_SHIFT and abs(res["bare"]["offset_v"]) <= H2_OFF
    return {"variants": res, "pass": bool(ok)}


def d57_plus(args):
    """D57's free node with r_core across the inductor, held at x = 0 until t_start (ns)."""
    from scipy.integrate import solve_ivp
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import node_model
    lf, last, rail, i_off, r_core, t_start = args
    e = EdgeCircuit()
    k = e.dv_cs / e.v_rail
    m = node_model(replace(e, lf=lf, v_rail=float(rail), dv_cs=0.0 if last else float(rail) * k,
                           n_next=0 if last else e.n_next))
    c = m.ckt
    i0 = i_off + (-c.vo - c.rl * i_off) / c.lf * t_start * 1e-9           # the inductor at x = 0 until t_start

    def f(t, z):
        x, i_f, i_r = z
        return [(i_r - i_f + m.idev(x) - (x - c.vo) / r_core) / m.cnode(x), (x - c.vo - c.rl * i_f) / c.lf, 0.0]
    T = SW.T_NS
    s = solve_ivp(f, (0.0, (T[-1] - t_start) * 1e-9), [0.0, i0, 0.0], max_step=2e-12, rtol=1e-9, atol=1e-7,
                  dense_output=True)
    x = np.where(T < t_start, 0.0, s.sol(np.clip(T - t_start, 0.0, None) * 1e-9)[0])
    return (rail - x).astype(np.float32)


def h3(H, lf_of, rcore_of, jobs):
    from multiprocessing import Pool
    full = list(H["variants"]).index("full")
    tm = 0.5 * (H["t_fall"][:, full] + H["t_stop"][:, full])          # board, phase group, rail, current
    tasks = [(lf_of[name] * 1e-9, bool(g), float(r), float(i), rcore_of[name], float(tm[b, g, ri, ci]))
             for b, name in enumerate(H["boards"]) for g in (0, 1) for ri, r in enumerate(H["rails"])
             for ci, i in enumerate(H["currents"])]
    with Pool(jobs) as p:
        V = np.array(p.map(d57_plus, tasks, chunksize=4)).reshape(H["traces"][:, full].shape)
    m = H["t_ns"] <= T_FIT
    err = (V - H["traces"][:, full])[..., m]
    by = {str(name): float(np.sqrt(np.mean(err[b] ** 2))) for b, name in enumerate(H["boards"])}
    rm = float(np.sqrt(np.mean(err ** 2)))
    return {"rmse_v": rm, "by_board_rmse_v": by, "t_start_ns_p10_p50_p90": [float(x) for x in np.quantile(tm, [.1, .5, .9])],
            "pass": bool(rm <= H3_RMSE)}, V


def own_rail(H, R, n=40000, seed=11, dr=np.arange(-0.3, 1.21, 0.02)):
    """Rows (indices) whose rail is found from their own command V_DS, that rail, and the full harness at the actual
    delay with it; rows sampled at random."""
    key = np.array([BOARD_OF.get((round(float(l), 3), float(t)), "") for l, t in zip(R["lf_nh"], R["temp_c"])])
    m = (key != "") & (R["i_off_a"] >= -60) & (R["i_off_a"] <= -10) & (R["rail_v"] >= 10.3) & (R["rail_v"] <= 13.7) \
        & (R["cmd_delay_ns"] > 0.0)
    idx = np.random.default_rng(seed).choice(np.flatnonzero(m), min(n, int(m.sum())), replace=False)
    bl = list(H["boards"])
    rows, rails, va = [], [], []
    for j in idx:
        b, g = bl.index(key[j]), int(R["phase"][j] == 4)
        rr = R["rail_v"][j] + dr
        vc = trilinear(H, b, 0, g, rr, np.full(dr.size, R["i_off_a"][j]), np.full(dr.size, R["cmd_delay_ns"][j]))
        if np.isnan(vc).all():
            continue
        k = int(np.nanargmin(np.abs(vc - R["vds_cmd_v"][j])))
        if abs(vc[k] - R["vds_cmd_v"][j]) > 0.1 or k in (0, dr.size - 1):
            continue
        rows.append(j); rails.append(rr[k])
        va.append(trilinear(H, b, 0, g, rr[k:k + 1], R["i_off_a"][j:j + 1], R["delay_ns"][j:j + 1])[0])
    return np.array(rows), np.array(rails), np.array(va), key


def windows_fixed(H, v_soft=2.0, margin=0.5):
    """The full harness's soft windows on the grid; per board / phase group / rail, among the delays keeping the most
    grid currents with a window <= v_soft over +-margin, the one with the least mean V_DS over every grid current
    (the valley turn-ons included); nesting and coverage."""
    t = H["t_ns"]
    w = int(round(margin / (t[1] - t[0])))
    out, fixed = {}, np.zeros(H["traces"].shape[:1] + H["traces"].shape[2:4])
    nest_ok, cov_n, cov_d = 0, 0, 0
    for b, name in enumerate(H["boards"]):
        for g in (0, 1):
            for r, rail in enumerate(H["rails"]):
                tr = H["traces"][b, 0, g, r]                                  # current, t
                worst = np.max(np.stack([np.roll(tr, s, axis=-1) for s in range(-w, w + 1)]), axis=0)
                worst[:, :w], worst[:, -w:] = np.inf, np.inf
                has = tr.min(axis=1) <= v_soft
                good = (worst <= v_soft) & has[:, None]
                sc = good.sum(axis=0)
                cand = np.flatnonzero(sc == sc.max())
                d = float(t[cand[np.argmin(tr[:, cand].mean(axis=0))]])
                fixed[b, g, r] = d
                k = int(np.argmin(np.abs(t - d)))
                cov_n += int(good[:, k].sum()); cov_d += int(has.sum())
                spans = [(t[np.flatnonzero(x <= v_soft)[0]], t[np.flatnonzero(x <= v_soft)[-1]]) for x in tr[has]]
                nest_ok += int(all(a2 <= a1 + 0.05 and b2 >= b1 - 0.05 for (a1, b1), (a2, b2) in zip(spans[::-1], spans[-2::-1])))
                if rail == 12.0:
                    out[f"{name}, {'phase 4' if g else 'phases 2-3'}"] = {
                        "fixed_ns": d, "windows_ns": {f"{H['currents'][c]:.0f} A": [float(a), float(z)] for c, (a, z) in
                                                      zip(np.flatnonzero(has), spans)}}
    n_cells = H["traces"].shape[0] * 2 * len(H["rails"])
    return {"at_12v": out, "nested_cells": f"{nest_ok} / {n_cells}", "grid_coverage": cov_n / max(cov_d, 1)}, fixed


def against_learner(H, R, rows, rails, key, fixed):
    """On the own-rail rows: the full harness's V_DS at one delay per board / phase group / rail against the record."""
    bl = list(H["boards"])
    vf, d = np.empty(len(rows)), np.empty(len(rows))
    for q, j in enumerate(rows):
        b, g = bl.index(key[j]), int(R["phase"][j] == 4)
        d[q] = float(np.interp(rails[q], H["rails"], fixed[b, g]))
        vf[q] = trilinear(H, b, 0, g, rails[q:q + 1], R["i_off_a"][j:j + 1], d[q:q + 1])[0]
    y, dl = R["vds_act_v"][rows], R["delay_ns"][rows]
    qq = lambda x: [float(v) for v in np.nanquantile(x, [0.5, 0.9, 0.99])]
    st = lambda m: {"rows": int(m.sum()), "recorded_p50_p90_p99_v": qq(y[m]), "fixed_p50_p90_p99_v": qq(vf[m]),
                    "recorded_hard": float(np.mean(y[m] > 2.0)), "fixed_hard": float(np.nanmean(vf[m] > 2.0))}
    far = np.abs(dl - d) > 2.0
    return {"all": st(np.ones(len(rows), bool)), "learner_off_by_2ns": st(far) | {"learner_shorter": float(np.mean(dl[far] < d[far]))}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=10)
    a = ap.parse_args()
    H = harness()
    cf = {b: json.loads(f.read_text())["circuit"] for b, f in SW.CFGS.items()}
    lf_of = {b: round(c["L"] * 1e9, 4) for b, c in cf.items()}
    rcore_of = {b: float(c["r_core"]) for b, c in cf.items()}
    res = {"boards": {b: {"lf_nh": lf_of[b], "r_core_ohm": rcore_of[b]} for b in cf},
           "t_fall_stop_ns_full_p50": [float(np.median(H["t_fall"][:, 0])), float(np.median(H["t_stop"][:, 0]))]}
    res["h1"] = h1(H)
    D = d57_grid(H, lf_of)
    res["h2"] = h2(H, D)
    res["h3"], _ = h3(H, lf_of, rcore_of, a.jobs)
    res["criteria"] = {k: res[k]["pass"] for k in ("h1", "h2", "h3")}
    R, _ = A47.load_records()
    rows, rails, va, key = own_rail(H, R)
    e = va - R["vds_act_v"][rows]
    sec = R["rail_v"][rows]
    ph = {"own_rail": {"rows": int(len(rows)), "rmse_v": float(np.sqrt(np.mean(e ** 2))), "boards": {}}}
    for name in H["boards"]:
        m = key[rows] == name
        if m.sum() >= 30:
            ph["own_rail"]["boards"][str(name)] = {"n": int(m.sum()), "median_abs_v": float(np.median(np.abs(e[m]))),
                                                   "mean_v": float(np.mean(e[m])),
                                                   "rail_minus_sections_p50_v": float(np.median(rails[m] - sec[m]))}
    ph["windows"], fixed = windows_fixed(H)
    ph["fixed_against_learner"] = against_learner(H, R, rows, rails, key, fixed)
    res["post_hoc"] = ph
    (HERE / "a248_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    x = res["h1"]
    print(f"h1 rmse harness {x['rmse_harness_v']:.3f} (D57 {x['rmse_d57_v']:.3f}, A247 corrected {x['rmse_d57_a247_v']:.3f}) V,"
          f" n {x['n']}")
    for b, y in x["boards"].items():
        print(f"   {b:5s} n {y['n']:7d} med|e| {y['median_abs_v']:.2f} mean {y['mean_v']:+.2f} agree {y['agree']:.3f}")
    for v, y in res["h2"]["variants"].items():
        print(f"h2 {v:7s} shift {y['shift_ns']:+.2f} ns offset {y['offset_v']:+.2f} V rmse {y['rmse_v']:.2f}"
              + (f"  share {y['share_shift']:+.2f} / {y['share_offset']:+.2f}" if "share_shift" in y else ""))
    print("h3", {k: v for k, v in res["h3"].items()})
    print("post hoc own rail:", round(ph["own_rail"]["rmse_v"], 3), {b: (round(x["median_abs_v"], 3), round(x["rail_minus_sections_p50_v"], 2))
                                                         for b, x in ph["own_rail"]["boards"].items()})
    print("post hoc windows:", ph["windows"]["nested_cells"], "nested; grid coverage", round(ph["windows"]["grid_coverage"], 3),
          {k: v["fixed_ns"] for k, v in ph["windows"]["at_12v"].items()})
    print("post hoc fixed vs learner:", ph["fixed_against_learner"])
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
