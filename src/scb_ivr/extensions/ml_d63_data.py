"""Datasets from D63, the valley map (extension ml_design_assist): random 1 MHz designs and disturbances, each run
through scb_ivr.p24_valley_map, as features and targets for the surrogate (A120) and the residual model (A121).

Design (1 MHz, Eq. (4)'s 7.333 nH): the negative-current target pct (5-15% of 125 A), Cs (3-20 uF, log-uniform),
the loop's crossover fc (20-80 kHz; D59's gains scale kp ~ fc, ki ~ fc^2 from A115's 60 kHz design), phase 1's
turn-off rule (comparator, timed, floor with floor_a 1-5 A).
Disturbance at 50 us: a load step di (-62.5..+62.5 A) or an input step dv (-4.8..+4.8 V) over a slew of 1-50 us
(log-uniform).
Targets (after the step): the peak (A), Vo's extreme (mV), phase 1's crossing depth (A) and its periods, the time
back within 1% (us, capped at 400), and whether the map diverged.
The valley times t_tr come from D57 on a pct grid (interpolated), the thresholds from D63's diagnostics file.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.p24_valley_map import Design, metrics, simulate

PROJECT = Path(__file__).resolve().parents[3]
D63_DIAG = PROJECT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D63_valley_map.json"
L1, T_STEP, BACK_CAP = 7.3333333e-9, 50e-6, 400.0
KP60, KI60 = 574.46, 47.9264
RULES = ("cmp", "timed", "floor")
FEATURES = ("pct", "log_cs_uf", "fc_khz", "rule_cmp", "rule_timed", "rule_floor", "floor_a", "is_load", "di_a", "dv_v",
            "log_slew_us")
TARGETS = ("peak_a", "extreme_mv", "ph1_depth_a", "log1p_ph1_periods", "log1p_back_us")


def ttr_grid(pcts=np.arange(4.0, 16.01, 1.0)):
    """D57's valley time (s) of phase 1's and phase 4's nodes on a pct grid."""
    from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit
    from scb_ivr.extensions.p24_aux_scenarios import node_model
    e = EdgeCircuit()
    n1, n4 = node_model(replace(e, lf=L1)), node_model(replace(e, lf=L1, v_rail=12.0, dv_cs=0.0, n_next=0))
    return {"pct": [float(p) for p in pcts], "t1": [n1.valley_free(p * 1.25, t_max=200e-9)[0] for p in pcts],
            "t4": [n4.valley_free(p * 1.25, t_max=200e-9)[0] for p in pcts]}


def sample(n, seed):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        rule = RULES[rng.integers(3)]
        s = {"pct": float(rng.uniform(5, 15)), "cs_uf": float(np.exp(rng.uniform(np.log(3), np.log(20)))),
             "fc_khz": float(rng.uniform(20, 80)), "rule": rule, "floor_a": float(rng.uniform(1, 5)) if rule == "floor" else 0.0}
        if rng.random() < 0.4:
            s.update(kind="load", di_a=float(rng.uniform(-62.5, 62.5)), dv_v=0.0, slew_us=1.0)
        else:
            s.update(kind="line", di_a=0.0, dv_v=float(rng.uniform(-4.8, 4.8)), slew_us=float(np.exp(rng.uniform(0, np.log(50)))))
        out.append(s)
    return out


def design(s, ith, ttr):
    t1 = float(np.interp(s["pct"], ttr["pct"], ttr["t1"]))
    t4 = float(np.interp(s["pct"], ttr["pct"], ttr["t4"]))
    k = s["fc_khz"] / 60.0
    return Design(lf=L1, cs=s["cs_uf"] * 1e-6, i_tgt=-s["pct"] * 1.25, mode=s["rule"], floor_a=s["floor_a"] or 2.0,
                  kp_ns=KP60 * k, ki_ns=KI60 * k * k, t_tr=(t1, t1, t1, t4), ith=ith)


def evaluate(args):
    s, ith, ttr = args
    d = design(s, ith, ttr)
    if s["kind"] == "load":
        recs = simulate(d, T_STEP + 350e-6, T_STEP, i_step=s["di_a"])
    else:
        recs = simulate(d, T_STEP + s["slew_us"] * 1e-6 + 350e-6, T_STEP, dvin=s["dv_v"], t_slew=s["slew_us"] * 1e-6)
    m = metrics(recs, T_STEP)
    after = [r for r in recs if r["t"] >= T_STEP]
    depth = [r["depth"][0] for r in after]
    return {"diverged": m["diverged_us"] is not None, "peak_a": m["peak_max_a"], "extreme_mv": m["extreme_mv"],
            "ph1_depth_a": max(depth), "ph1_periods": sum(1 for v in depth if v > 0),
            "back_us": min(m["back_us"], BACK_CAP) if math.isfinite(m["back_us"]) else BACK_CAP}


def features(samples):
    rows = []
    for s in samples:
        rows.append([s["pct"], math.log(s["cs_uf"]), s["fc_khz"], float(s["rule"] == "cmp"), float(s["rule"] == "timed"),
                     float(s["rule"] == "floor"), s["floor_a"], float(s["kind"] == "load"), s["di_a"], s["dv_v"],
                     math.log(s["slew_us"])])
    return np.array(rows)


def targets(results):
    return np.array([[r["peak_a"], r["extreme_mv"], r["ph1_depth_a"], math.log1p(r["ph1_periods"]), math.log1p(r["back_us"])]
                     for r in results])


def generate(n, seed, workers=None, ttr=None):
    ith = tuple(tuple(x) for x in json.loads(D63_DIAG.read_text())["thresholds"][str(L1)])
    ttr = ttr or ttr_grid()
    ss = sample(n, seed)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(evaluate, [(s, ith, ttr) for s in ss], chunksize=8))
    return ss, res, ttr
