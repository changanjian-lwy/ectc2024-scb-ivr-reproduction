"""A150 - constrained GP Bayesian optimisation of A148's phase-1 edge law (rail gain gr, Ton gain gt) in RTL cosim:
can control hold the 50 pH / 72 A/ns package switch <= 40 V on +4.8 V / 1 us, and what does it cost in Vo?

One evaluation = five cosim runs at x = (gr, gt) (vs_kr / vs_kt = round(g x 1310.72), Q24 on scb_vff, no RTL change):
  e50  A145 e72_l50_l_p48_1us (loop 50 pH Q 7 + 72 A/ns edges)  -> V50 = whole-run max switch V_DS
  l0 / l07 / l13  A143 g4 l_p48_1us at L x 1 / 0.7 / 1.3       -> PK1 = max post-step peak; OBJ = log max Vo IAE
  l5   A143 g4 l_p48_5us                                        -> PK5 = post-step peak (A149's oscillation row)
Constraints V50 <= 40 V, PK1 <= 200 A, PK5 <= 200 A (+ no NEW oracle event on any run, checked, not modelled);
objective OBJ = log of the worst-L Vo error area (mV us, 100 us after the step, about the pre-step mean): the price.
Model: one GP per output (ml_gp, length scales 0.2-3 gain units: D63 slice varies on 0.2-0.7); V50 / PK1 use D63's A149 grid (rel_k 0, kv 0)
as the prior mean when that lowers the leave-one-out RMSE; PK5 / OBJ have none (D63 is blind to the 5 us mechanism
and 2-3x off in Vo). Acquisition on a 0.025 grid over [0, 1.25]^2: EI(OBJ) x P(feasible) (Gardner et al. 2014;
Eriksson & Poloczek 2021), P(feasible) alone until a feasible point is seen; batches of 4 by kriging believer with
0.075 exclusion. Stop: P(feasible) < 0.02 everywhere or max cEI < 0.02 after >= 2 new batches; at most 4 batches.

python3 a150_bo.py [--dry]  BO loop (resumes from a150_bo.json; --dry proposes one batch, writes no cfg, runs nothing)
python3 a150_bo.py --confirm  confirmation rows for the chosen candidate (and the frozen design's slew rows)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE.parent / "A148_rl_zvs_line_step"))
sys.path.insert(0, str(HERE.parent / "A149_bo_rising_step_overshoot"))
import a148_analyze as A  # noqa: E402
import a149_analyze as B  # noqa: E402
from scb_ivr.extensions.ml_gp import GP  # noqa: E402

COS = HERE / "cosim"
STATE = HERE / "a150_bo.json"
A148C = HERE.parent / "A148_rl_zvs_line_step" / "cosim"
A149C = HERE.parent / "A149_bo_rising_step_overshoot" / "cosim"
KVS = 2 ** 24 * 0.02 / 256
BASE = {"e50": B.A145C / "cfg_e72_l50_l_p48_1us.json", "l0": B.A143C / "cfg_g4_s100_l_p48_1us_k4.json",
        "l07": B.A143C / "cfg_g4_s070_l_p48_1us_k4.json", "l13": B.A143C / "cfg_g4_s130_l_p48_1us_k4.json",
        "l5": B.A143C / "cfg_g4_s100_l_p48_5us_k4.json"}
ROWS = tuple(BASE)                                           # e50 first: the long run starts first
LIM = {"V50": 40.0, "PK1": 200.0, "PK5": 200.0}
L_BOUNDS = (0.2, 3.0)                                       # D63 slice: its own length scales are 0.2-0.7
NMIN = {"V50": 0.1, "PK1": 1.0, "PK5": 1.0, "OBJ": 0.05}     # noise floors (A139: repeats within 0.2-1.1 A)
PK_CAP, IAE_WIN = 260.0, 100e-6
LO, HI, STEP, EXCL, Q, MAX_BATCH = 0.0, 1.25, 0.025, 0.075, 4, 4
GRID = np.array([(a, b) for a in np.arange(LO, HI + 1e-9, STEP) for b in np.arange(LO, HI + 1e-9, STEP)])


def prior_points():
    """The five (gr, gt) points already run: frozen (A143 / A145), A148 v075 / v100 (kr = kt), A149 r075 / r100."""
    def srcs(d, pre):
        return {"e50": d / f"run_{pre}_e72_l50_l_p48_1us.json", "l0": d / f"run_{pre}_l_p48_1us.json",
                "l07": d / f"run_{pre}_s070_l_p48_1us.json", "l13": d / f"run_{pre}_s130_l_p48_1us.json",
                "l5": d / f"run_{pre}_l_p48_5us.json"}
    frozen = {"e50": B.A145C / "run_e72_l50_l_p48_1us.json", **{k: Path(str(BASE[k]).replace("cfg_", "run_"))
                                                               for k in ("l0", "l07", "l13", "l5")}}
    pts = [(0, 0, frozen), (983, 983, srcs(A148C, "v075")), (1311, 1311, srcs(A148C, "v100")),
           (983, 0, srcs(A149C, "r075")), (1311, 0, srcs(A149C, "r100"))]
    out = []
    for i, (kr, kt, s) in enumerate(pts):
        src = {k: str(p.relative_to(ROOT)) if p.exists() else None for k, p in s.items()}
        out.append({"idx": i, "kr": kr, "kt": kt, "src": src, "batch": 0})
    return out


def iae(r, t0):
    secs = r["sections"]
    t = np.array([s["t_s"] for s in secs])
    vo = np.array([s["vo"] for s in secs]) * 1e3
    pre = vo[(t >= 600e-6) & (t < t0)].mean()
    m = (t >= t0) & (t < t0 + IAE_WIN)
    e, tu = np.abs(vo[m] - pre), t[m] * 1e6
    return float(np.sum(0.5 * (e[1:] + e[:-1]) * np.diff(tu)))


def metrics(p, tab):
    """Outputs of one point from its records (None where a row is missing)."""
    st, ok = {}, True
    for row, rel in p["src"].items():
        if rel is None or not (ROOT / rel).exists():
            st[row] = None
            continue
        r = A.load(ROOT / rel)
        s = A.stats(r, row)
        s["iae"] = iae(r, A.t_step(r))
        if row == "l0":
            s["sh50_block"] = B.block_pred(r, tab, A.t_step(r))
        st[row] = s
        ok &= s["status"] == "COMPLETED" and s["src_modified"] is False
    m = {"ok": ok, "rows": {k: (None if v is None else {q: v.get(q) for q in (
        "peak_post", "back_within_1pct_us", "extreme_mv", "oracle_new", "late", "iae", "status", "sh50_block",
        "von_max", "vds")}) for k, v in st.items()}}
    good = lambda k: st.get(k) is not None and st[k]["status"] == "COMPLETED"
    if st.get("e50") is not None:
        m["V50"] = st["e50"]["vds"]["whole"] if good("e50") else 45.0
    if all(st.get(k) is not None for k in ("l0", "l07", "l13")):
        m["PK1"] = min(max(st[k]["peak_post"] if good(k) else PK_CAP for k in ("l0", "l07", "l13")), PK_CAP)
        m["OBJ"] = float(np.log(max(st[k]["iae"] for k in ("l0", "l07", "l13"))))
    if st.get("l5") is not None:
        m["PK5"] = min(st["l5"]["peak_post"] if good("l5") else PK_CAP, PK_CAP)
    if all(v is not None for v in st.values()):
        m["new"] = int(sum(v["oracle_new"] for v in st.values()))
        m["feasible"] = bool(ok and m["new"] == 0 and all(m[c] <= LIM[c] for c in LIM))
    return m


def d63_prior():
    """Bilinear D63 (A149 grid, rel_k 0, kv 0) for V50 (sh50 on l_p48_1us) and PK1 (max peak over the three L)."""
    g = json.loads((HERE.parent / "A149_bo_rising_step_overshoot" / "a149_grid.json").read_text())
    gr, gt = np.array(g["grid"]["gr"]), np.array(g["grid"]["gt"])
    P = {tuple(p["th"][:2]): p["rows"] for p in g["points"] if p["th"][2] == 0 and p["th"][3] == 0}
    tabs = {"V50": np.array([[P[(a, b)]["l_p48_1us@1.0"]["sh50"] for b in gt] for a in gr]),
            "PK1": np.array([[max(P[(a, b)][f"l_p48_1us@{m}"]["peak"] for m in (1.0, 0.7, 1.3)) for b in gt] for a in gr])}

    def f(c, x):
        x = np.atleast_2d(x)
        i = np.clip(np.searchsorted(gr, x[:, 0], side="right") - 1, 0, len(gr) - 2)
        j = np.clip(np.searchsorted(gt, x[:, 1], side="right") - 1, 0, len(gt) - 2)
        u = (x[:, 0] - gr[i]) / (gr[i + 1] - gr[i])
        v = (x[:, 1] - gt[j]) / (gt[j + 1] - gt[j])
        T = tabs[c]
        return (1 - u) * (1 - v) * T[i, j] + u * (1 - v) * T[i + 1, j] + (1 - u) * v * T[i, j + 1] + u * v * T[i + 1, j + 1]
    return f


def xy(points, c):
    x = [(p["kr"] / KVS, p["kt"] / KVS) for p in points if c in p.get("m", {})]
    y = [p["m"][c] for p in points if c in p.get("m", {})]
    return np.array(x), np.array(y)


class Model:
    """GP on y (or on y - D63(x) when that wins leave-one-out)."""

    def __init__(self, c, x, y, d63):
        self.c, self.d63 = c, None
        fits = {"none": GP(noise_min=NMIN[c], l_bounds=L_BOUNDS).fit(x, y, restarts=8, seed=0)}
        if d63 is not None and c in ("V50", "PK1"):
            fits["d63"] = GP(noise_min=NMIN[c], l_bounds=L_BOUNDS).fit(x, y - d63(c, x), restarts=8, seed=0)
        self.loo = {}
        for k, g in fits.items():
            mu, _ = g.loo()
            self.loo[k] = float(np.sqrt(np.mean((mu - (y if k == "none" else y - d63(c, x))) ** 2)))
        self.kind = min(self.loo, key=self.loo.get)
        self.g = fits[self.kind]
        if self.kind == "d63":
            self.d63 = lambda q: d63(c, q)

    def predict(self, q, noise=False):
        mu, sd = self.g.predict(np.atleast_2d(q), noise=noise)
        return (mu + self.d63(q) if self.d63 else mu), sd

    def believe(self, q):
        """Kriging believer: condition on the posterior mean at q, hyperparameters fixed."""
        g = self.g
        mu, _ = g.predict(np.atleast_2d(q), noise=False)
        h = GP(noise_min=g.noise_min)
        h.s, h.n, h.l, h.mu = g.s, g.n, g.l, g.mu
        h.x = np.vstack([g.x, q])
        h.y = np.concatenate([g.y, mu - g.mu])
        K = h._kernel(h.x, h.x, h.s, h.l) + (h.n ** 2 + 1e-10) * np.eye(len(h.x))
        from scipy.linalg import cho_factor, cho_solve
        h.c = cho_factor(K, lower=True)
        h.alpha = cho_solve(h.c, h.y)
        self.g = h

    def info(self):
        return {"kind": self.kind, "loo_rmse": self.loo, "s": float(self.g.s), "n": float(self.g.n),
                "l": [float(v) for v in self.g.l]}


def fit_models(points, d63):
    return {c: Model(c, *xy(points, c), d63) for c in ("V50", "PK1", "PK5", "OBJ")}


def acquisition(models, best):
    pof = np.ones(len(GRID))
    for c, lim in LIM.items():
        mu, sd = models[c].predict(GRID)
        pof *= norm.cdf((lim - mu) / sd)
    if best is None:
        return pof, pof
    mu, sd = models["OBJ"].predict(GRID)
    z = (best - mu) / sd
    return (best - mu) * norm.cdf(z) + sd * norm.pdf(z), pof


def propose(points, models, q=Q):
    feas = [p["m"]["OBJ"] for p in points if p.get("m", {}).get("feasible")]
    best = min(feas) if feas else None
    taken = [np.array([p["kr"] / KVS, p["kt"] / KVS]) for p in points]
    picks = []
    ei0, pof0 = acquisition(models, best)
    for _ in range(q):
        ei, pof = acquisition(models, best)
        acq = ei * pof if best is not None else pof
        for t in taken:
            acq[np.max(np.abs(GRID - t), axis=1) < EXCL] = -1.0
        k = int(np.argmax(acq))
        x = GRID[k]
        pred = {c: [float(v[0]) for v in models[c].predict(x, noise=True)] for c in models}
        picks.append({"gr": float(x[0]), "gt": float(x[1]), "acq": float(acq[k]), "pof": float(pof[k]), "pred": pred})
        for m in models.values():
            m.believe(x)
        taken.append(x)
    return picks, {"best_obj": best, "max_pof": float(pof0.max()), "argmax_pof": GRID[int(np.argmax(pof0))].tolist(),
                   "max_cei": float((ei0 * pof0).max()) if best is not None else None}


def write_cfg(name, base, kr, kt, note, **over):
    c = json.loads(Path(base).read_text())
    c = dict(c, vff=dict(c["vff"], vs_kr=int(kr), vs_kt=int(kt)), out=f"run_{name}.json", note=f"A150 {name}: {note}")
    for k, v in over.items():
        c[k] = v
    COS.mkdir(exist_ok=True)
    p = COS / f"cfg_{name}.json"
    p.write_text(json.dumps(c, indent=1) + "\n")
    return p


def run_cosim(cfgs):
    todo = [c for c in cfgs if not (c.parent / json.loads(c.read_text())["out"]).exists()]
    if not todo:
        return 0
    jobs = 6 if Path.home().joinpath(".lima/openroad-rosetta/ha.pid").exists() else 10
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run", *map(str, todo), "--jobs", str(jobs)],
                          cwd=ROOT, env=env, stdout=subprocess.DEVNULL).returncode


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"points": prior_points(), "batches": [], "stop": None}


def save(st):
    STATE.write_text(json.dumps(st, indent=1) + "\n")


def refresh(st, tab):
    for p in st["points"]:
        p["m"] = metrics(p, tab)


def bo(dry=False):
    tab = json.loads((HERE.parent / "A149_bo_rising_step_overshoot" / "a149_sh_table.json").read_text())["L50_e72"]
    d63 = d63_prior()
    st = load_state()
    # the frozen-gain prior point (1, 1) has no L corners in A148: run them before the first proposal
    fill = [(p, r) for p in st["points"] if p["batch"] == 0 for r in ROWS if p["src"][r] is None]
    if fill and not dry:
        cfgs = []
        for p, r in fill:
            name = f"p{p['idx']:02d}_{r}"
            cfgs.append(write_cfg(name, BASE[r], p["kr"], p["kt"], f"prior point fill, kr {p['kr']} kt {p['kt']}"))
            p["src"][r] = str((COS / f"run_{name}.json").relative_to(ROOT))
        run_cosim(cfgs)
    refresh(st, tab)
    save(st)
    while st["stop"] is None:
        nb = len(st["batches"])
        models = fit_models(st["points"], d63)
        picks, glob = propose(st["points"], models)
        if nb >= 2:
            if glob["best_obj"] is None and glob["max_pof"] < 0.02:
                st["stop"] = "infeasible"
            elif glob["max_cei"] is not None and glob["max_cei"] < 0.02:
                st["stop"] = "converged"
        if nb >= MAX_BATCH:
            st["stop"] = st["stop"] or "budget"
        if st["stop"]:
            st["final_models"] = {c: m.info() for c, m in fit_models(st["points"], d63).items()}
            st["final_global"] = glob
            break
        batch = {"n": nb + 1, "models": {c: m.info() for c, m in fit_models(st["points"], d63).items()},
                 "global": glob, "picks": picks}
        if dry:
            print(json.dumps({"global": glob, "picks": [(p["gr"], p["gt"], round(p["acq"], 4)) for p in picks],
                              "models": {c: (v["kind"], {k: round(x, 3) for k, x in v["loo_rmse"].items()},
                                             [round(x, 2) for x in v["l"]]) for c, v in batch["models"].items()}}, indent=0))
            return
        cfgs = []
        for pk in picks:
            kr, kt = round(pk["gr"] * KVS), round(pk["gt"] * KVS)
            idx = len(st["points"])
            src = {}
            for r in ROWS:
                name = f"p{idx:02d}_{r}"
                cfgs.append(write_cfg(name, BASE[r], kr, kt, f"batch {nb + 1}, gr {pk['gr']:.3f} gt {pk['gt']:.3f}"))
                src[r] = str((COS / f"run_{name}.json").relative_to(ROOT))
            st["points"].append({"idx": idx, "kr": kr, "kt": kt, "src": src, "batch": nb + 1, "pred": pk["pred"]})
        st["batches"].append(batch)
        save(st)
        cfgs.sort(key=lambda c: ROWS.index(c.stem.split("_", 2)[2]))
        run_cosim(cfgs)
        refresh(st, tab)
        save(st)
        new = [p for p in st["points"] if p["batch"] == nb + 1]
        print(f"batch {nb + 1}: " + "; ".join(f"({p['kr'] / KVS:.3f},{p['kt'] / KVS:.3f}) V {p['m'].get('V50', 0):.1f} "
                                             f"PK1 {p['m'].get('PK1', 0):.0f} PK5 {p['m'].get('PK5', 0):.0f} "
                                             f"{'F' if p['m'].get('feasible') else '-'}" for p in new), flush=True)
    save(st)
    print("stop:", st["stop"])


CONF_SLEWS = (2.0, 3.0, 4.0, 7.0, 10.0)
CONF_DT = (0.17, 0.34)


def candidate(st):
    feas = [p for p in st["points"] if p.get("m", {}).get("feasible")]
    return min(feas, key=lambda p: p["m"]["OBJ"]) if feas else None


def confirm():
    st = load_state()
    p = candidate(st)
    if p is None:
        print("no feasible point: nothing to confirm")
        return
    kr, kt, i = p["kr"], p["kt"], p["idx"]
    cfgs, conf = [], {"idx": i, "kr": kr, "kt": kt, "rows": {}}

    def put(name, base, k_r, k_t, note, **over):
        cfgs.append(write_cfg(name, base, k_r, k_t, note, **over))
        conf["rows"][name] = str((COS / f"run_{name}.json").relative_to(ROOT))
    for j, dt in enumerate(CONF_DT, 1):
        for r in ROWS:
            ls = dict(json.loads(BASE[r].read_text())["line_step"])
            ls["t_us"] = round(ls["t_us"] + dt, 3)
            put(f"c{i:02d}_ph{j}_{r}", BASE[r], kr, kt, f"confirm point {i}, step +{dt} us", line_step=ls)
    for s in CONF_SLEWS:
        ls = dict(json.loads(BASE["l0"].read_text())["line_step"], slew_us=s)
        put(f"c{i:02d}_slew{s:g}", BASE["l0"], kr, kt, f"confirm point {i}, +4.8 V / {s:g} us", line_step=ls)
        put(f"c00_slew{s:g}", BASE["l0"], 0, 0, f"frozen design reference, +4.8 V / {s:g} us", line_step=ls)
    for name, f in (("l5_s070", "cfg_g4_s070_l_p48_5us_k4.json"), ("l5_s130", "cfg_g4_s130_l_p48_5us_k4.json"),
                    ("s_p62", "cfg_g4_s100_s_p62_k4.json"), ("l_m48_1us", "cfg_g4_s100_l_m48_1us_k4.json")):
        put(f"c{i:02d}_{name}", B.A143C / f, kr, kt, f"confirm point {i}, {name}")
    st["confirm"] = conf
    save(st)
    cfgs.sort(key=lambda c: 0 if c.stem.endswith("_e50") else 1)
    rc = run_cosim(cfgs)
    print(f"confirm point {i} ({kr / KVS:.3f}, {kt / KVS:.3f}): {len(cfgs)} runs, rc {rc}")


if __name__ == "__main__":
    if "--confirm" in sys.argv:
        confirm()
    else:
        bo(dry="--dry" in sys.argv)
