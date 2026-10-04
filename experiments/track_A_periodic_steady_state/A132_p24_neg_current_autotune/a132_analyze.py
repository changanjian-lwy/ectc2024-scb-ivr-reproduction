"""A132 analysis against BOUNDARY Section 2: identity, the loop's convergence and valley (n0), the standard matrix and
step rows (on, three corners), inertness at nominal (on vs A129's g125), efficiency (n0, D62 middle with Coss x k_C,
copper at the nominal L as predicted). Also, not criteria: off vs on per step row at the corners, turn-ons at
V_DS <= 0 (the valley gone) after the step. Writes a132_summary.json."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import scb_ivr.p24_loss_budget as LB  # noqa: E402
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a132_predict", HERE / "a132_predict.py")
PR = importlib.util.module_from_spec(spec); spec.loader.exec_module(PR)
spec = importlib.util.spec_from_file_location("a132_cfgs", HERE / "make_cfgs.py")
MC = importlib.util.module_from_spec(spec); spec.loader.exec_module(MC)
A129 = MC.A129
COS = HERE / "cosim"
D_PRED = {"nom": 0.0, "c13l07": 22.7, "c07l13": -16.6}
STEP_ROWS = [r for r in MC.STEP_ROWS if r != "n0"]


def load(p):
    return json.loads(Path(p).read_text())


def t_step(corner):
    return (800.0 + MC.LATE_US.get(corner, 0.0)) * 1e-6


def same(a, b):
    a, b = load(a), load(b)
    keys = ("sections", "turnons_last", "lowoffs_last", "highoffs_last")
    return {k: a[k] == b[k] for k in keys}


def tail(d, span=200e-6):
    t1 = d["t_end_s"]
    on = [x for x in d["turnons_last"] if x["t_s"] >= t1 - span]
    von = [float(np.mean([x["vds_v"] for x in on if x["phase"] == k])) for k in (1, 2, 3, 4)]
    out = {"von_v": von}
    if "dep_log" in d:
        log, t0 = d["dep_log"], t1 - span
        edges = [(max(t, t0), v) for t, v in log if t < t1]
        acc = 0.0
        for j, (t, v) in enumerate(edges):
            tn = edges[j + 1][0] if j + 1 < len(edges) else t1
            acc += v * max(0.0, tn - max(t, t0))
        out["dep_mean"] = acc / span
        tp = d["t_mode_p_s"] or 0.0
        out["dep_absmax_mode_p"] = max(abs(v) for t, v in log if t >= tp) if any(t >= tp for t, _ in log) else abs(log[-1][1])
        out["dep_final"] = log[-1][1]
    return out


def efficiency(d, k_c):
    m = LB.measure(d)
    sc, f, coss = PR.P.D62.SCENARIOS["middle"], 1.0 / m["period_s"], PR.ScaledCoss(k_c)
    b = LB.budget(m["phases"], m["ton_s"], m["period_s"], PR.L0, sc, m["rails_v"], m["dv_next_v"], p_rev=m["p_rev_w"], p_out=m["p_out_w"])
    n = len(m["phases"])
    b["hard_turn_on"] = sum(LB.hard_on_energy(p["vds_on"], m["rails_v"][k], m["dv_next_v"][k], n_next=2 if k < n - 1 else 0, coss=coss)
                            for k, p in enumerate(m["phases"])) * f
    b["turn_off_overlap"] = sum(LB.turn_off_overlap(p["peak"], sc["t_f"], c_node=13.5e-9 * k_c) for p in m["phases"]) * f
    b["total"] = sum(v for k, v in b.items() if k not in ("total", "efficiency"))
    b["efficiency"] = m["p_out_w"] / (m["p_out_w"] + b["total"])
    return {"eff_pct": b["efficiency"] * 100, "hard_w": b["hard_turn_on"], "valleys_a": [p["valley"] for p in m["phases"]],
            "peaks_a": [p["peak"] for p in m["phases"]], "period_ns": m["period_s"] * 1e9}


def run_row(d, corner, row):
    ts = t_step(corner)
    x = {"ipk_a": float(d["ipk_a"]), "overlaps": d["overlaps"], "late": sum(d["late_fires"]), "status": d["status"]}
    if row in ("n0",) or row[0] in "mj":
        w = window_stats(d)
        x.update(window=w, hs_on_v=[p["hs_on_vds_v"] for p in w["phases"]])
    else:
        x["peak_after_a"] = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= ts)
        x["step"] = step_stats(d, t_step=ts)
        x["v0_after"] = [sum(1 for q in d["turnons_last"] if q["phase"] == k and q["t_s"] >= ts and q["vds_v"] <= 0.0) for k in (1, 2, 3, 4)]
        x["hs_on_v"] = [p["hs_on_vds_v"] for p in window_stats(d)["phases"]]
    x["runaway"] = x.get("peak_after_a", x["ipk_a"]) > 400 or x["late"] > 100
    return x


def main():
    out, crit = {"identity": {}, "runs": {}}, {}
    for row in ("l_p48_1us", "n0"):
        a, b = PROJECT / "tmp" / "identity_a132" / f"run_g125_{row}.json", A129 / f"run_g125_{row}.json"
        out["identity"][row] = same(a, b) if a.exists() else None
    crit["1_identity"] = all(v and all(v.values()) for v in out["identity"].values())

    for corner, (k_c, _) in MC.CORNERS.items():
        for arm in ("f", "t"):
            for row in MC.STEP_ROWS + MC.MATRIX_ROWS:
                f = COS / f"run_{arm}{corner}_{row}.json"
                if f.exists():
                    d = load(f)
                    x = run_row(d, corner, row)
                    if row == "n0":
                        x.update(tail=tail(d), eff=efficiency(d, k_c))
                    elif "dep_log" in d:
                        x["tail"] = {k: v for k, v in tail(d).items() if k.startswith("dep")}
                    out["runs"][f"{arm}{corner}_{row}"] = x
    R = out["runs"]
    for row in MC.STEP_ROWS + MC.MATRIX_ROWS:                                           # nominal off = A129's g125
        f = A129 / f"run_g125_{row}.json"
        if f.exists():
            R[f"fnom_{row}"] = run_row(load(f), "nom", row)
            if row == "n0":
                R["fnom_n0"].update(tail=tail(load(f)), eff=efficiency(load(f), 1.0))

    c2, c3, c4, c5, c6, c7 = [], [], [], [], [], []
    for corner in MC.CORNERS:
        n0 = R.get(f"t{corner}_n0")
        if n0:
            c2.append(abs(n0["tail"]["dep_mean"] - D_PRED[corner]) <= 2.0 and abs(n0["tail"]["von_v"][0] - 3.9) <= 0.3)
            c3.append(min(n0["tail"]["von_v"]) >= 0.5)
        for row in MC.MATRIX_ROWS:
            x = R.get(f"t{corner}_{row}")
            if not x or not n0:
                continue
            ok = x["overlaps"] == 0 and not x["runaway"] and x["ipk_a"] <= 200.0 and x.get("peak_after_a", 0.0) <= 200.0
            if row[0] in "mj":
                ok &= all(abs(a - b) <= 0.5 for a, b in zip(x["hs_on_v"], n0["hs_on_v"]))
            if row[0] == "m":
                ok &= all(p["ls_on_vds_max_v"] <= 0.0 for p in x["window"]["phases"])
            if row == "j30":
                ok &= all(p["i_off_sd_a"] <= 0.5 for p in x["window"]["phases"])
            if row.startswith("s_"):
                ok &= math.isfinite(x["step"]["back_within_1pct_us"]) and x["step"]["back_within_1pct_us"] <= 60.0
            x["c4"] = bool(ok); c4.append(ok)
        for row in STEP_ROWS:
            x = R.get(f"t{corner}_{row}")
            if x:
                x["c5"] = bool(x["overlaps"] == 0 and not x["runaway"] and x["peak_after_a"] <= 200.0); c5.append(x["c5"])
        f0, t0 = R.get(f"f{corner}_n0"), R.get(f"t{corner}_n0")
        if corner != "nom" and f0 and t0:
            de = t0["eff"]["eff_pct"] - f0["eff"]["eff_pct"]
            c7.append(de >= -0.05 and (corner != "c13l07" or de >= 0.2))
    for row in MC.STEP_ROWS + MC.MATRIX_ROWS:
        t, f = R.get(f"tnom_{row}"), R.get(f"fnom_{row}")
        if not t or not f:
            continue
        ok = abs(t.get("peak_after_a", t["ipk_a"]) - f.get("peak_after_a", f["ipk_a"])) <= 3.0
        ok &= all(abs(a - b) <= 0.2 for a, b in zip(t["hs_on_v"], f["hs_on_v"]))
        if row.startswith("s_"):
            ok &= abs(t["step"]["extreme_mv"] - f["step"]["extreme_mv"]) <= 3.0
        ok &= t.get("tail", {}).get("dep_absmax_mode_p", 0) <= 2
        t["c6"] = bool(ok); c6.append(ok)
    for k, v in (("2_convergence", c2), ("3_valley_kept", c3), ("4_matrix_on", c4), ("5_step_rows_on", c5),
                 ("6_inert_nominal", c6), ("7_efficiency", c7)):
        crit[k] = {"pass": bool(v) and all(v), "n": len(v), "misses": len(v) - sum(v)}
    out["criteria"] = crit
    (HERE / "a132_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")

    print("criteria:", {k: (v if isinstance(v, bool) else f"{v['n'] - v['misses']}/{v['n']}") for k, v in crit.items()})
    for corner in MC.CORNERS:
        for arm in ("f", "t"):
            x = R.get(f"{arm}{corner}_n0")
            if x:
                tl, e = x["tail"], x["eff"]
                print(f"{arm}{corner:6s} n0: V_on {'/'.join(f'{v:.2f}' for v in tl['von_v'])} V, valley {'/'.join(f'{v:.1f}' for v in e['valleys_a'])} A, "
                      f"eff {e['eff_pct']:.2f}% hard {e['hard_w']:.2f} W" + (f", dep {tl['dep_mean']:+.1f}" if "dep_mean" in tl else ""))
    for corner in MC.CORNERS:
        pk = {arm: [R[f'{arm}{corner}_{r}']['peak_after_a'] for r in STEP_ROWS if f'{arm}{corner}_{r}' in R] for arm in "ft"}
        v0 = {arm: [sum(R[f'{arm}{corner}_{r}']['v0_after']) for r in STEP_ROWS if f'{arm}{corner}_{r}' in R] for arm in "ft"}
        print(f"{corner:6s} step rows peak off {'/'.join(f'{v:.0f}' for v in pk['f'])} | on {'/'.join(f'{v:.0f}' for v in pk['t'])}; "
              f"V_DS<=0 turn-ons off {sum(v0['f'])} on {sum(v0['t'])}")


if __name__ == "__main__":
    main()
