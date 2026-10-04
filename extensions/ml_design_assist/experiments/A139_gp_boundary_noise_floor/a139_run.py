"""A139 (extension ml_design_assist): A138's 200 A line-step map repeated with its two failure causes removed.
- Noise floor measured, not fitted: four points near the boundary (two per direction) are each run with the step
  moved through one switching period (six positions, 85 ns apart); the pooled sd per direction is the GP's lower
  bound on its noise (ml_gp.GP noise_min).
- The active-learning budget is split per direction: each batch takes 6 rising and 4 falling points, each by the
  straddle 1.96 sd - |mean - 200| within its own direction (kriging believer).
- Training data: every A138 point (406) + these runs; a fresh held-out test set of 20 uniform points per direction.
Ends as A138 (spec table, 20 verification cells at their table slews) and runs up to 10 cells the table leaves without
a safe slew at 20 us. Design, inputs, prior grid and response are A138's (a138_run).

    PYTHONPATH=src python3 a139_run.py      # resumes from a139_state.json and cosim/run_*.json
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.ml_gp import GP  # noqa: E402

spec = importlib.util.spec_from_file_location("a138_run", HERE.parent / "A138_gp_boundary_map" / "a138_run.py")
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
COS = A.COS = HERE / "cosim"
A138_STATE = HERE.parent / "A138_gp_boundary_map" / "a138_state.json"
STATE_PATH = HERE / "a139_state.json"
NOISE_PTS = {"r": [(1.0, 1.0, 8.0, 3.0), (0.7, 0.7, 6.4, 1.0)], "f": [(1.0, 1.0, -8.0, 6.7), (1.3, 1.0, -6.4, 8.8)]}
SHIFTS_US = [k * 0.085 for k in range(6)]
N_TEST, SPLIT, N_VERIFY, N_UNSAFE, MAX_RUNS = 20, {"r": 6, "f": 4}, 20, 10, 260
STATE = {"points": {}, "log": [], "noise": {}}


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True); STATE["log"].append(line)


def save():
    STATE_PATH.write_text(json.dumps(STATE, indent=1, default=float) + "\n")


def add(name, sign, kind, x, grid=None, t_step=A.T_STEP_US):
    if name not in STATE["points"]:
        m, c, dv, slew = x
        A.cfg(name, x)
        if t_step != A.T_STEP_US:
            p = COS / f"cfg_{name}.json"; t = json.loads(p.read_text())
            t["line_step"]["t_us"] = t_step
            t["note"] += f" Step moved to {t_step:.3f} us (step-position scatter)."
            p.write_text(json.dumps(t, indent=1) + "\n")
        STATE["points"][name] = {"sign": sign, "kind": kind, "x": list(x), "z": [float(v) for v in A.scaled(m, c, abs(dv), slew)],
                                 "grid": grid, "t_step_us": t_step, "prior": A.prior(x)}
    return name


def run(names):
    jobs = 6 if Path.home().joinpath(".lima", "openroad-rosetta", "ha.pid").exists() else 10
    todo = [n for n in names if not (COS / f"run_{n}.json").exists()]
    if todo:
        t0 = time.time()
        r = subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run"] + [str(COS / f"cfg_{n}.json") for n in todo]
                           + ["--jobs", str(jobs)], cwd=PROJECT, env={**os.environ, "PYTHONPATH": "src"},
                           capture_output=True, text=True)
        log(f"  cosim {len(todo)} runs, {jobs} jobs, {time.time() - t0:.0f} s, exit {r.returncode}")
    for n in names:
        p = COS / f"run_{n}.json"
        if p.exists():
            y, f = A.response(p, STATE["points"][n]["t_step_us"])
            STATE["points"][n].update(y=y, flags=f)
        else:
            STATE["points"][n].update(y=None, flags={"valid": False, "missing": True})
    save()


def data(sign, kinds=("noise", "al")):
    """Every valid A138 point and this experiment's points of the given kinds."""
    old = json.loads(A138_STATE.read_text())["points"].values()
    new = [p for p in STATE["points"].values() if p["kind"] in kinds]
    pts = [p for p in list(old) + new if p["sign"] == sign and p.get("y") is not None and p["flags"].get("valid")]
    return np.array([p["z"] for p in pts]), np.array([p["y"] - p["prior"] for p in pts])


def fit(sign, kinds=("noise", "al")):
    z, r = data(sign, kinds)
    return GP(noise_min=STATE["noise"][sign]).fit(z, r, restarts=6, seed=len(z)), z, r


def choose(zs, pri):
    picks = []
    used = {s: {p["grid"] for p in STATE["points"].values() if p["sign"] == s and p.get("grid") is not None} for s in A.SIGNS}
    for s in A.SIGNS:
        gp, z, r = fit(s)
        z, r = list(z), list(r)
        for _ in range(SPLIT[s]):
            mean, sd = A.Posterior(gp, z, r).predict(zs)
            a = 1.96 * sd - np.abs(pri[s] + mean - A.LIMIT)
            a[list(used[s])] = -np.inf
            i = int(np.argmax(a))
            used[s].add(i); z.append(zs[i]); r.append(float(mean[i]))
            picks.append((s, i))
    return picks


def evaluate(kinds):
    res = {}
    for s in A.SIGNS:
        gp, _, _ = fit(s, kinds)
        test = [p for p in STATE["points"].values() if p["sign"] == s and p["kind"] == "test" and p.get("y") is not None
                and p["flags"].get("valid")]
        z = np.array([p["z"] for p in test]); y = np.array([p["y"] for p in test]); pr = np.array([p["prior"] for p in test])
        mean, sd = gp.predict(z, noise=True)
        mu = pr + mean
        res[s] = {"n": len(test), "cover90": float(np.mean(np.abs(y - mu) <= A.Z90 * sd)),
                  "acc_gp": float(np.mean((mu <= A.LIMIT) == (y <= A.LIMIT))), "acc_prior": float(np.mean((pr <= A.LIMIT) == (y <= A.LIMIT))),
                  "mae_gp": float(np.mean(np.abs(y - mu))), "mae_prior": float(np.mean(np.abs(y - pr))),
                  "length_scales": [float(v) for v in gp.l], "noise_a": float(gp.n)}
    return res


def spec_table():
    slews = 10 ** A.GRID[3]
    table = {}
    for s in A.SIGNS:
        gp, _, _ = fit(s)
        for m in A.TABLE_MC:
            for c in A.TABLE_MC:
                for a in A.TABLE_A:
                    zs = np.array([A.scaled(m, c, a, t) for t in slews])
                    pri = np.array([A.prior((m, c, A.SIGNS[s] * a, t)) for t in slews])
                    mean, sd = gp.predict(zs, noise=True)
                    ub, mu = pri + mean + A.Z95 * sd, pri + mean
                    k = next((i for i in range(len(slews)) if (ub[i:] <= A.LIMIT).all()), None)
                    table[f"{s}_{m:.1f}_{c:.1f}_{a:.1f}"] = {"slew_min_us": None if k is None else float(slews[k]),
                                                             "mean_a": [float(v) for v in mu], "ub_a": [float(v) for v in ub]}
    return table


def main():
    global STATE
    COS.mkdir(exist_ok=True)
    if STATE_PATH.exists():
        STATE = json.loads(STATE_PATH.read_text())
    g = np.load(HERE.parent / "A138_gp_boundary_map" / "a138_prior_grid.npz")
    zs, pri = g["z"], {s: g[s] for s in A.SIGNS}
    runs = lambda: len(STATE["points"])
    # 1. step-position scatter and the fresh test set, one submission
    names = []
    for s, pts in NOISE_PTS.items():
        for j, x in enumerate(pts):
            names += [add(f"n{s}{j}{k}", s, "noise", x, t_step=A.T_STEP_US + d) for k, d in enumerate(SHIFTS_US)]
    rng = np.random.default_rng(139)
    for s in A.SIGNS:
        names += [add(f"t{s}{k:02d}", s, "test", A.phys(z, s)) for k, z in enumerate(rng.random((N_TEST, 4)))]
    save()
    if any(STATE["points"][n].get("y") is None for n in names):
        log(f"noise + test: {len(names)} runs")
        run(names)
    for s, pts in NOISE_PTS.items():
        var = []
        for j in range(len(pts)):
            ys = [STATE["points"][f"n{s}{j}{k}"]["y"] for k in range(len(SHIFTS_US))]
            var.append(np.var(ys, ddof=1))
            log(f"noise {s}{j}: {[round(v, 1) for v in ys]} sd {np.sqrt(var[-1]):.2f} A")
        STATE["noise"][s] = float(np.sqrt(np.mean(var)))
    log(f"noise floor r {STATE['noise']['r']:.2f} A, f {STATE['noise']['f']:.2f} A")
    save()
    # 2. active learning, per-direction split
    n_al = sum(p["kind"] == "al" for p in STATE["points"].values())
    while runs() + sum(SPLIT.values()) + N_VERIFY + N_UNSAFE <= MAX_RUNS:
        picks = choose(zs, pri)
        batch = [add(f"a{s}{n_al + j:03d}", s, "al", A.phys(zs[i], s), grid=i) for j, (s, i) in enumerate(picks)]
        n_al += len(batch)
        log(f"AL batch {n_al // 10}: {len(batch)} runs")
        run(batch)
        log(f"  peaks {[round(STATE['points'][n]['y'], 1) if STATE['points'][n].get('y') else None for n in batch]}")
    # 3. evaluation, table, verification, unsafe cells
    STATE["eval_noise_only"] = evaluate(("noise",))
    STATE["eval_final"] = evaluate(("noise", "al"))
    table = STATE["table"] = spec_table()
    safe = sorted(k for k, v in table.items() if v["slew_min_us"] is not None)
    unsafe = sorted(k for k, v in table.items() if v["slew_min_us"] is None)
    r2 = np.random.default_rng(1390)
    ver = []
    for j, i in enumerate(sorted(r2.choice(len(safe), size=min(N_VERIFY, len(safe)), replace=False))):
        s, m, c, a = safe[i].split("_")
        ver.append(add(f"v{s}{j:02d}", s, "verify", (float(m), float(c), A.SIGNS[s] * float(a), table[safe[i]]["slew_min_us"])))
        STATE["points"][ver[-1]]["cell"] = safe[i]
    uns = []
    for j, i in enumerate(sorted(r2.choice(len(unsafe), size=min(N_UNSAFE, len(unsafe)), replace=False)) if unsafe else []):
        s, m, c, a = unsafe[i].split("_")
        uns.append(add(f"u{s}{j:02d}", s, "unsafe", (float(m), float(c), A.SIGNS[s] * float(a), 20.0)))
        STATE["points"][uns[-1]]["cell"] = unsafe[i]
    save()
    log(f"verify {len(ver)} + unsafe {len(uns)} runs")
    run(ver + uns)
    vy = [STATE["points"][n].get("y") for n in ver]
    uy = [STATE["points"][n].get("y") for n in uns]
    pts = STATE["points"]
    summary = {"runs": len(pts), "noise_floor_a": STATE["noise"], "invalid": [n for n, p in pts.items() if not p.get("flags", {}).get("valid")],
               "eval_noise_only": STATE["eval_noise_only"], "eval_final": STATE["eval_final"],
               "verify": {n: {"cell": pts[n]["cell"], "y": pts[n].get("y")} for n in ver},
               "unsafe_at_20us": {n: {"cell": pts[n]["cell"], "y": pts[n].get("y")} for n in uns},
               "table": {k: v["slew_min_us"] for k, v in table.items()}}
    ef = summary["eval_final"]
    summary["criteria"] = {"1_valid": not summary["invalid"],
                           "2_cover80": all(v["cover90"] >= 0.8 for v in ef.values()),
                           "2_acc90": all(v["acc_gp"] >= 0.9 for v in ef.values()),
                           "2_acc_ge_prior": all(v["acc_gp"] >= v["acc_prior"] for v in ef.values()),
                           "3_verify": sum(y is not None and y <= A.LIMIT for y in vy) >= len(vy) - 2
                           and all(y is not None and y <= 205.0 for y in vy)}
    (HERE / "a139_summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n")
    log("criteria " + " ".join(f"{k}={'P' if v else 'F'}" for k, v in summary["criteria"].items()))
    for s, v in ef.items():
        log(f"{s}: test n {v['n']} cover90 {v['cover90']:.2f} acc gp {v['acc_gp']:.2f} prior {v['acc_prior']:.2f} "
            f"mae gp {v['mae_gp']:.1f} prior {v['mae_prior']:.1f} A noise {v['noise_a']:.2f}")
    log(f"verify {[None if y is None else round(y, 1) for y in vy]}")
    log(f"unsafe cells at 20 us {[None if y is None else round(y, 1) for y in uy]}")
    save()


if __name__ == "__main__":
    main()
