"""A138 (extension ml_design_assist): Gaussian-process level-set active learning of the adopted single-module design's
200 A boundary for bus line steps under L / Cs tolerance.

Design: A129's g125 + vff {rel_q8 320, rel_lp 1, seed 2} (C10's single-module cfg), every run one line step at 1000 us,
end 1200 us. Inputs per step direction (rising / falling, one GP each): L x m in [0.7, 1.3], Cs x c in [0.7, 1.3],
|dv| in [4.8, 8.0] V, log10 slew in [0, log10 20] us, scaled to [0, 1]. Response y: the post-step peak (max high-side
turn-off current at t >= 1000 us), clipped at 260 A. Prior: D63 with the RTL-exact relative cap on Ton's low-pass
(A136's VffLP) and Cs x c; the GP models the residual y - prior. Acquisition: straddle 1.96 sd - |mean - 200|, ten
points a batch chosen greedily over both directions with the kriging believer. Data: per direction 20 Latin-hypercube
points, plus A137's six rising runs (seed 1 = seed 2 bit for bit, C10); 15 uniform random test points per direction
are held out. Ends with a spec table (smallest grid slew whose 95 % one-sided bound is <= 200 A from there up) and
20 verification runs at those slews.

    PYTHONPATH=src python3 a138_run.py --prior     # D63 prior on the candidate grid (registered predictions)
    PYTHONPATH=src python3 a138_run.py [--dry]     # the campaign (resumes from cosim/run_*.json); --dry: fake cosim
Progress goes to stdout (redirect to a log); state to a138_state.json; the end summary to a138_summary.json.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import subprocess
import sys
import time
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.ml_gp import GP  # noqa: E402

TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
TEMPLATE = PROJECT / "experiments" / "track_C_multi_module" / "C10_seed_before_entry" / "cosim" / "cfg_s100_l_p48_1us.json"
A137 = TA / "A137_p24_vff_restart_at_handover" / "cosim"
COS = HERE / "cosim"
LIMIT, CLIP, Z95, Z90 = 200.0, 260.0, 1.645, 1.645
T_STEP_US, T_END_US = 1000.0, 1200.0
LO = np.array([0.7, 0.7, 4.8, 0.0])
HI = np.array([1.3, 1.3, 8.0, math.log10(20.0)])
SIGNS = {"r": 1.0, "f": -1.0}
N_INIT, N_TEST, BATCH, N_VERIFY, MAX_RUNS = 20, 15, 10, 20, 400
GRID = (np.linspace(0.7, 1.3, 13), np.linspace(0.7, 1.3, 13), np.linspace(4.8, 8.0, 9), np.linspace(0.0, math.log10(20.0), 12))
TABLE_MC, TABLE_A = (0.7, 1.0, 1.3), (4.8, 6.4, 8.0)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


Q = _load("a136_predict", TA / "A136_p24_relative_cap_lowpass" / "a136_predict.py")
P = Q.P                 # a135_predict (VffRTL, ValleyMap, steady_ton)
PP = P.P                # a134_predict (A132.d63_design, T_STEP, N_RUN)


def prior(x):
    """D63 post-step peak for (m, c, dv, slew_us), clipped at CLIP."""
    m, c, dv, slew = x
    d = PP.A132.d63_design(1.0, m, 15.625)
    d = replace(d, cs=d.cs * c)
    law = Q.VffLP()
    mw = P.ValleyMap(replace(d, mode="cmp"))
    s = mw.init_state(P.steady_ton(d))
    ton = s["acc"]
    for _ in range(600):
        sc, cap = law(d.vin, ton); ton = mw.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    vm = P.ValleyMap(d)
    for _ in range(200):
        sc, cap = law(d.vin, ton); ton = vm.period(s, d.vin, 0.0, ton_scale=sc, ton_cap=cap)["ton"]
    s["t"], peak = 0.0, 0.0
    for _ in range(PP.N_RUN):
        t = s["t"]
        vin = d.vin + dv * min(max((t - PP.T_STEP) / (slew * 1e-6), 0.0), 1.0)
        sc, cap = law(vin, ton)
        r = vm.period(s, vin, 0.0, ton_scale=sc, ton_cap=cap)
        ton = r["ton"]
        if not all(math.isfinite(v) and abs(v) < P.DIVERGED_A for v in r["valley"] + r["peak"]):
            return CLIP
        if r["t"] >= PP.T_STEP:
            peak = max(peak, max(r["peak"]))
    return min(float(peak), CLIP)


def phys(z, sign):
    """[0, 1]^4 -> (m, c, dv, slew_us)."""
    v = LO + np.asarray(z) * (HI - LO)
    return float(v[0]), float(v[1]), SIGNS[sign] * float(v[2]), float(10 ** v[3])


def scaled(m, c, a, slew):
    return (np.array([m, c, a, math.log10(slew)]) - LO) / (HI - LO)


def grid_points():
    g = np.array(np.meshgrid(*GRID, indexing="ij")).reshape(4, -1).T
    return (g - LO) / (HI - LO)


def prior_grid(jobs=10):
    zs = grid_points()
    out = {}
    with Pool(jobs) as pool:
        for sign in SIGNS:
            out[sign] = np.array(pool.map(prior, [phys(z, sign) for z in zs], chunksize=64))
    np.savez(HERE / "a138_prior_grid.npz", z=zs, **out)
    return zs, out


def lhs(n, rng):
    cut = (np.arange(n)[:, None] + rng.random((n, 4))) / n
    for j in range(4):
        cut[:, j] = cut[rng.permutation(n), j]
    return cut


def cfg(name, x):
    m, c, dv, slew = x
    t = json.loads(TEMPLATE.read_text())
    t["circuit"] = dict(t["circuit"], L=t["circuit"]["L"] * m, cs=t["circuit"]["cs"] * c)
    t["line_step"] = {"t_us": T_STEP_US, "dv": round(dv, 4), "slew_us": round(slew, 4)}
    t["t_end_us"] = T_END_US
    t["note"] = (f"A138 {name}: adopted single-module design (g125 + vff rel_q8 320, rel_lp 1, seed 2), L x {m:.4f}, "
                 f"Cs x {c:.4f}, line step {dv:+.4f} V over {slew:.4f} us at {T_STEP_US:.0f} us.")
    t["out"] = f"run_{name}.json"
    (COS / f"cfg_{name}.json").write_text(json.dumps(t, indent=1) + "\n")


def response(path, t_step_us=T_STEP_US):
    """Post-step peak and validity flags of one record."""
    d = json.loads(Path(path).read_text())
    ts = t_step_us * 1e-6
    hi = d["highoffs_last"]
    post = max(q["i_a"] for q in hi if q["t_s"] >= ts)
    pre = max((q["i_a"] for q in hi if q["t_s"] < ts), default=float("nan"))
    tail = d["sections"][-100:]
    vo_end = float(np.mean([q["vo"] for q in tail]))
    dev = max(max(abs(v / q["vin_v"] - (3 - j) / 4) for j, v in enumerate(q["vcs_v"])) for q in tail)
    timed = d.get("t_lo_timed_s")
    flags = {"timed_before_step": bool(timed is not None and timed < ts), "overlaps": int(d["overlaps"]),
             "status": d["status"], "pre_peak_a": float(pre), "late": int(sum(d["late_fires"])),
             "vo_end": vo_end, "ladder_dev_end": float(dev), "src_modified": d["provenance"].get("cosim_sources_modified")}
    flags["valid"] = flags["timed_before_step"] and flags["status"] == "COMPLETED" and not flags["src_modified"]
    y = CLIP if flags["overlaps"] else min(float(post), CLIP)
    return y, flags


def run_batch(names, dry, log):
    if dry:
        for n in names:
            x = STATE["points"][n]["x"]
            y = prior(x) + 4.0 + 3.0 * np.random.default_rng(sum(map(ord, n))).normal()
            STATE["points"][n].update(y=float(min(y, CLIP)), flags={"valid": True, "dry": True})
        return
    jobs = 6 if Path.home().joinpath(".lima", "openroad-rosetta", "ha.pid").exists() else 10
    todo = [n for n in names if not (COS / f"run_{n}.json").exists()]
    if todo:
        t0 = time.time()
        r = subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run"] + [str(COS / f"cfg_{n}.json") for n in todo]
                           + ["--jobs", str(jobs)], cwd=PROJECT, env={**__import__("os").environ, "PYTHONPATH": "src"},
                           capture_output=True, text=True)
        log(f"  cosim {len(todo)} runs, {jobs} jobs, {time.time() - t0:.0f} s, exit {r.returncode}")
    for n in names:
        p = COS / f"run_{n}.json"
        if p.exists():
            y, f = response(p)
            STATE["points"][n].update(y=y, flags=f)
        else:
            STATE["points"][n].update(y=None, flags={"valid": False, "missing": True})


class Posterior:
    """GP posterior with fixed hyperparameters on (training + pseudo) data, for the kriging believer."""

    def __init__(self, gp, z, r):
        self.gp, self.z, self.r = gp, np.asarray(z), np.asarray(r)
        K = gp._kernel(self.z, self.z, gp.s, gp.l) + (gp.n ** 2 + 1e-10) * np.eye(len(self.z))
        self.L = np.linalg.cholesky(K)
        self.alpha = np.linalg.solve(self.L.T, np.linalg.solve(self.L, self.r - gp.mu))

    def predict(self, zs, noise=False):
        ks = self.gp._kernel(np.asarray(zs), self.z, self.gp.s, self.gp.l)
        mean = ks @ self.alpha + self.gp.mu
        v = np.linalg.solve(self.L, ks.T)
        var = self.gp.s ** 2 - np.sum(v * v, axis=0) + (self.gp.n ** 2 if noise else 0.0)
        return mean, np.sqrt(np.maximum(var, 1e-12))


def train(sign, kinds=("init", "al", "a137")):
    pts = [p for p in STATE["points"].values() if p["sign"] == sign and p["kind"] in kinds
           and p.get("y") is not None and p["flags"].get("valid")]
    z = np.array([p["z"] for p in pts]); r = np.array([p["y"] - p["prior"] for p in pts])
    return GP().fit(z, r, restarts=6, seed=len(pts)), z, r


def choose(n, zs, pri):
    """n candidates (sign, grid index) by straddle with the kriging believer."""
    post, used = {}, {s: set() for s in SIGNS}
    for s in SIGNS:
        gp, z, r = train(s)
        post[s] = [gp, list(z), list(r)]
        for p in STATE["points"].values():
            if p["sign"] == s and p.get("grid") is not None:
                used[s].add(p["grid"])
    picks = []
    for _ in range(n):
        best = None
        for s in SIGNS:
            gp, z, r = post[s]
            mean, sd = Posterior(gp, z, r).predict(zs)
            mu = pri[s] + mean
            a = 1.96 * sd - np.abs(mu - LIMIT)
            a[list(used[s])] = -np.inf
            i = int(np.argmax(a))
            if best is None or a[i] > best[0]:
                best = (float(a[i]), s, i, float(mean[i]))
        _, s, i, m = best
        used[s].add(i)
        post[s][1].append(zs[i]); post[s][2].append(m)              # kriging believer: the mean as an observation
        picks.append((s, i))
    return picks


def ambiguous(zs, pri):
    out = {}
    for s in SIGNS:
        gp, z, r = train(s)
        mean, sd = gp.predict(zs, noise=False)
        out[s] = float(np.mean(np.abs(pri[s] + mean - LIMIT) < 1.96 * sd))
    return out


def evaluate(kinds):
    """Test-set coverage of the 90 % predictive interval and boundary classification, GP vs the D63 prior."""
    res = {}
    for s in SIGNS:
        gp, _, _ = train(s, kinds)
        test = [p for p in STATE["points"].values() if p["sign"] == s and p["kind"] == "test" and p.get("y") is not None
                and p["flags"].get("valid")]
        if not test:
            continue
        z = np.array([p["z"] for p in test]); y = np.array([p["y"] for p in test]); pr = np.array([p["prior"] for p in test])
        mean, sd = gp.predict(z, noise=True)
        mu = pr + mean
        res[s] = {"n": len(test), "cover90": float(np.mean(np.abs(y - mu) <= Z90 * sd)),
                  "acc_gp": float(np.mean((mu <= LIMIT) == (y <= LIMIT))), "acc_prior": float(np.mean((pr <= LIMIT) == (y <= LIMIT))),
                  "mae_gp": float(np.mean(np.abs(y - mu))), "mae_prior": float(np.mean(np.abs(y - pr))),
                  "length_scales": [float(v) for v in gp.l], "noise_a": float(gp.n)}
    return res


def spec_table():
    """Per (sign, m, c, a): the smallest grid slew from which every larger grid slew has mean + 1.645 sd <= 200 A."""
    slews = 10 ** GRID[3]
    table = {}
    for s in SIGNS:
        gp, _, _ = train(s)
        for m in TABLE_MC:
            for c in TABLE_MC:
                for a in TABLE_A:
                    zs = np.array([scaled(m, c, a, t) for t in slews])
                    pri = np.array([prior((m, c, SIGNS[s] * a, t)) for t in slews])
                    mean, sd = gp.predict(zs, noise=True)
                    ub = pri + mean + Z95 * sd
                    ok = ub <= LIMIT
                    k = next((i for i in range(len(slews)) if ok[i:].all()), None)
                    table[f"{s}_{m:.1f}_{c:.1f}_{a:.1f}"] = {"slew_min_us": None if k is None else float(slews[k]),
                                                             "ub_a": [float(v) for v in ub], "prior_a": [float(v) for v in pri]}
    return table


STATE = {"points": {}, "log": []}
STATE_PATH = HERE / "a138_state.json"


def save():
    STATE_PATH.write_text(json.dumps(STATE, indent=1, default=float) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prior", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    COS.mkdir(exist_ok=True)
    if a.prior:
        t0 = time.time(); zs, pri = prior_grid()
        print(f"prior grid {len(zs)} points per direction, {time.time() - t0:.0f} s")
        return
    g = np.load(HERE / "a138_prior_grid.npz")
    zs, pri = g["z"], {s: g[s] for s in SIGNS}
    global STATE, STATE_PATH
    if a.dry:
        STATE_PATH = HERE.parents[3] / "tmp" / "a138" / "a138_state_dry.json"
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    elif STATE_PATH.exists():
        STATE = json.loads(STATE_PATH.read_text())

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True); STATE["log"].append(line)

    def add(name, sign, kind, z, grid=None):
        if name not in STATE["points"]:
            x = phys(z, sign)
            STATE["points"][name] = {"sign": sign, "kind": kind, "z": [float(v) for v in z], "x": list(x), "grid": grid,
                                     "prior": prior(x)}
            if not a.dry:
                cfg(name, x)
        return name

    rng = np.random.default_rng(138)
    names = []
    for s in SIGNS:
        names += [add(f"i{s}{k:02d}", s, "init", z) for k, z in enumerate(lhs(N_INIT, rng))]
    for s in SIGNS:
        names += [add(f"t{s}{k:02d}", s, "test", z) for k, z in enumerate(rng.random((N_TEST, 4)))]
    for f in sorted(A137.glob("run_s*_l_p48_*us.json")):                  # A137's rising rows: same design, step at 1000 us
        m, slew = int(f.stem.split("_")[1][1:]) / 100, float(f.stem.split("_")[-1][:-2])
        n = f"x{f.stem[4:]}"
        if n not in STATE["points"]:
            x = (m, 1.0, 4.8, slew)
            y, fl = response(f)
            STATE["points"][n] = {"sign": "r", "kind": "a137", "z": [float(v) for v in scaled(m, 1.0, 4.8, slew)], "x": list(x),
                                  "grid": None, "prior": prior(x), "y": y, "flags": fl}
    save()
    batch = [n for n in names if STATE["points"][n].get("y") is None]
    if batch:                                                              # one submission: the runner keeps 10 jobs busy
        log(f"init/test: {len(batch)} runs")
        run_batch(batch, a.dry, log); save()
    n_al = sum(p["kind"] == "al" for p in STATE["points"].values())
    calm = 0
    runs = lambda: sum(p["kind"] != "a137" for p in STATE["points"].values())
    while runs() + BATCH + N_VERIFY <= MAX_RUNS:
        amb = ambiguous(zs, pri)
        log(f"AL {n_al // BATCH}: ambiguous fraction r {amb['r']:.3f} f {amb['f']:.3f}")
        calm = calm + 1 if max(amb.values()) < 0.01 else 0
        if calm >= 2:                                                      # the boundary is settled on the grid
            break
        picks = choose(BATCH, zs, pri)
        batch = [add(f"a{s}{n_al + j:03d}", s, "al", zs[i], grid=i) for j, (s, i) in enumerate(picks)]
        n_al += len(batch)
        run_batch(batch, a.dry, log); save()
        ys = [STATE["points"][n].get("y") for n in batch]
        log(f"  batch peaks {[None if y is None else round(y, 1) for y in ys]}")
    STATE["eval_init_only"] = evaluate(("init", "a137"))
    STATE["eval_final"] = evaluate(("init", "al", "a137"))
    table = spec_table()
    STATE["table"] = table
    cells = sorted(k for k, v in table.items() if v["slew_min_us"] is not None)
    pick = np.random.default_rng(1380).choice(len(cells), size=min(N_VERIFY, len(cells)), replace=False)
    ver = []
    for j, i in enumerate(sorted(pick)):
        s, m, c, amp = cells[i].split("_")
        z = scaled(float(m), float(c), float(amp), table[cells[i]]["slew_min_us"])
        ver.append(add(f"v{s}{j:02d}", s, "verify", z))
        STATE["points"][ver[-1]]["cell"] = cells[i]
    save()
    log(f"verify: {len(ver)} runs")
    run_batch(ver, a.dry, log); save()
    vy = [STATE["points"][n].get("y") for n in ver]
    pts = STATE["points"].values()
    summary = {"runs": sum(p["kind"] != "a137" for p in pts), "invalid": [n for n, p in STATE["points"].items() if not p.get("flags", {}).get("valid")],
               "eval_init_only": STATE["eval_init_only"], "eval_final": STATE["eval_final"],
               "verify": {n: {"cell": STATE["points"][n]["cell"], "y": STATE["points"][n].get("y")} for n in ver},
               "table": {k: v["slew_min_us"] for k, v in table.items()}}
    c = {"1_valid": not summary["invalid"],
         "2_cover80": all(v["cover90"] >= 0.8 for v in summary["eval_final"].values()),
         "2_acc90": all(v["acc_gp"] >= 0.9 for v in summary["eval_final"].values()),
         "2_acc_ge_prior": all(v["acc_gp"] >= v["acc_prior"] for v in summary["eval_final"].values()),
         "3_verify": sum(y is not None and y <= LIMIT for y in vy) >= len(vy) - 2 and all(y is not None and y <= 205.0 for y in vy)}
    summary["criteria"] = c
    (HERE / ("a138_summary_dry.json" if a.dry else "a138_summary.json")).write_text(json.dumps(summary, indent=1, default=float) + "\n")
    log("criteria " + " ".join(f"{k}={'P' if v else 'F'}" for k, v in c.items()))
    for s, v in summary["eval_final"].items():
        log(f"{s}: test n {v['n']} cover90 {v['cover90']:.2f} acc gp {v['acc_gp']:.2f} prior {v['acc_prior']:.2f} "
            f"mae gp {v['mae_gp']:.1f} prior {v['mae_prior']:.1f} A")
    log(f"verify peaks {[None if y is None else round(y, 1) for y in vy]}")
    save()


if __name__ == "__main__":
    main()
