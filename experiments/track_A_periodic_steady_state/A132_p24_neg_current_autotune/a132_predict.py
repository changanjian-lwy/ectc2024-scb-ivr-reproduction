"""A132 step 1 (paper level, before any RTL or cosim): component spread L x C_node +-30% on the 2.5 MHz design (A124,
2 high + 3 low, L 2.933 nH, i_tgt 15.625 A). D57's node model scales with s = sqrt(k_C / k_L): I_th = s I_th0,
V_on(i) = V_on0(i / s), valley time x sqrt(k_C k_L) (checked on four corners below), so the steady state uses nominal
tables. Coss spread = the EPC2067 curve times k_C (Costinett 2015: the threshold sees the energy-equivalent C).
Each corner is priced with A115's orbit and D62's budget in A131's form (hard turn-on and turn-off overlap with
C x k_C; inductor copper at the nominal L). Targets: the fixed 15.625 A, the per-corner best, and a constant V_on set
point (depth s i0(V_set), what a V_DS-comparator loop converges to). `d63` runs the A124 rows on 9 corners.
Writes a132_predictions.json (steady) and a132_d63.json (`d63`)."""
from __future__ import annotations

import importlib.util
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
import scb_ivr.p24_loss_budget as LB  # noqa: E402
from scb_ivr.cosim.circuit import EPC2067Coss  # noqa: E402
from scb_ivr.extensions import ml_rl_ff as FF  # noqa: E402
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import node_model  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


TA = HERE.parent
P = load("a115_predict", TA / "A115_p24_one_mhz_design_point" / "a115_predict.py")
D63S = load("d63", PROJECT / "scripts" / "p24_valley_map.py")
A118 = load("a118_predict", TA / "A118_p24_floor_turn_off" / "a118_predict.py")
DESIGN = PROJECT / "extensions/ml_design_assist/experiments/A126_ppo_line_feedforward/a126_design.json"
L0, I_TGT = 7.3333333e-9 / 2.5, 15.625
KS = (0.7, 0.85, 1.0, 1.15, 1.3)
IG = np.arange(4.0, 30.01, 0.125)
V_SETS = (2.0, 3.0, None, 5.0)          # None: the nominal V_on at 15.625 A (the current design at k = 1)
MARGIN_MIN = 2.5                       # T12: valley margin <= 2.5 A fails transients


class ScaledCoss:
    def __init__(self, k):
        self.base, self.k = EPC2067Coss(), k

    def c(self, v):
        return self.k * self.base.c(v)

    def q(self, v):
        return self.k * self.base.q(v)


def nodes(k=1.0, m=1.0):
    base = replace(EdgeCircuit(), lf=L0 * m)
    m1, m4 = node_model(base), node_model(replace(base, v_rail=P.V_RAIL, dv_cs=0.0, n_next=0))
    m1.coss = m4.coss = ScaledCoss(k)
    return m1, m4


def ith(model):
    return brentq(lambda i: model.valley_free(i, t_max=200e-9)[1], 0.1, 200.0, xtol=0.01)


def tables():
    m1, m4 = nodes()
    v1, t1, v4 = [], [], []
    for i in IG:
        t, v = m1.valley_free(i, t_max=200e-9)
        v1.append(v); t1.append(t); v4.append(m4.valley_free(i, t_max=200e-9)[1])
    return {"ith1": ith(m1), "ith4": ith(m4), "v1": np.array(v1), "t1": np.array(t1), "v4": np.array(v4)}


def scaling_check(tb):
    out = []
    for k, m in ((0.7, 1.3), (1.3, 0.7), (0.7, 0.7), (1.3, 1.3)):
        s = np.sqrt(k / m)
        m1, _ = nodes(k, m)
        t, v = m1.valley_free(I_TGT, t_max=200e-9)
        out.append({"k_c": k, "k_l": m, "ith_err_a": ith(m1) - s * tb["ith1"],
                    "von_err_v": v - np.interp(I_TGT / s, IG, tb["v1"]),
                    "t_err_ns": (t - np.sqrt(k * m) * np.interp(I_TGT / s, IG, tb["t1"])) * 1e9})
    return out


def budget(phases, ton, period, k, sc):
    n, f, coss = len(phases), 1.0 / period, ScaledCoss(k)
    out = dict.fromkeys(("switch_conduction", "inductor_copper", "series_caps", "hard_turn_on", "turn_off_overlap", "gate_drive"), 0.0)
    on_ms = []
    for j, p in enumerate(phases):
        hs, ls, on = LB.phase_ms(p["valley"], p["peak"], ton, period)
        on_ms.append(on)
        out["switch_conduction"] += hs * sc["ron"] / 2 + ls * sc["ron"] / 3
        out["inductor_copper"] += (hs + ls) * L0 * LB.L_TECH[sc["l_tech"]]
        out["hard_turn_on"] += LB.hard_on_energy(p["vds_on"], P.V_RAIL, P.V_RAIL, n_h=2, n_l=3, n_next=2 if j < n - 1 else 0, coss=coss) * f
        out["turn_off_overlap"] += LB.turn_off_overlap(p["peak"], sc["t_f"], c_node=13.5e-9 * k) * f
    for j in range(n - 1):
        out["series_caps"] += ton / period * (on_ms[j] + on_ms[j + 1]) * sc["esr_cs"]
    out["gate_drive"] = n * 5 * sc["q_gate"] * LB.VGS * f
    tot = sum(out.values())
    out["total"], out["efficiency"] = tot, 250.0 / (250.0 + tot)
    return out


def corner(tb, k, m, i):
    s = np.sqrt(k / m)
    v1, v4 = np.interp(i / s, IG, tb["v1"]), np.interp(i / s, IG, tb["v4"])
    pk, ton, period = P.orbit(L0 * m, i, np.sqrt(k * m) * np.interp(i / s, IG, tb["t1"]))
    ph = [{"valley": -i, "peak": pk, "vds_on": max(v1, 0.0)}] * 3 + [{"valley": -i, "peak": pk, "vds_on": max(v4, 0.0)}]
    b = budget(ph, ton, period, k, P.D62.SCENARIOS["middle"])
    return {"i_a": i, "von1_v": v1, "von4_v": v4, "margin1_a": s * tb["ith1"] - i, "margin4_a": s * tb["ith4"] - i,
            "peak_a": pk, "period_ns": period * 1e9, "hard_w": b["hard_turn_on"], "eff_pct": b["efficiency"] * 100}


def i_for_von(tb, v_set):
    """Nominal depth giving V_on1 = v_set (V_on0 falls with i)."""
    return float(np.interp(v_set, tb["v1"][::-1], IG[::-1]))


def lowline_ith(vin):
    """I_th phases 1-3 at the rail Vin / 4 from A124's cached D57 grid (nominal L, C)."""
    rails, t13, _ = json.loads(DESIGN.read_text())["ith"]
    return float(np.interp(vin / 4.0, rails, t13))


def steady():
    tb = tables()
    v_nom = float(np.interp(I_TGT, IG, tb["v1"]))
    res = {"ith1_a": tb["ith1"], "ith4_a": tb["ith4"], "von_nominal_v": v_nom, "scaling_check": scaling_check(tb),
           "method_check_eff_pct": corner(tb, 1.0, 1.0, I_TGT)["eff_pct"], "corners": {}}
    ith_low = {v: lowline_ith(v) for v in (40.0, 43.2)}
    for k in KS:
        for m in KS:
            s = np.sqrt(k / m)
            grid = [corner(tb, k, m, i) for i in np.arange(6.0, s * tb["ith1"] - MARGIN_MIN + 1e-9, 0.25)]
            best = max(grid, key=lambda r: r["eff_pct"])
            fixed = corner(tb, k, m, I_TGT)
            row = {"s": s, "best": best, "fixed": dict(fixed, regret_pt=best["eff_pct"] - fixed["eff_pct"]), "tuned": {}}
            for name, i in (("fixed", I_TGT),):
                row[name].update({f"margin1_vin{v:g}_a": s * ith_low[v] - i for v in ith_low})
            for vs in V_SETS:
                vs = v_nom if vs is None else vs
                i = s * i_for_von(tb, vs)
                r = corner(tb, k, m, i)
                r.update({"regret_pt": best["eff_pct"] - r["eff_pct"], **{f"margin1_vin{v:g}_a": s * ith_low[v] - i for v in ith_low}})
                row["tuned"][f"v{vs:.2f}"] = r
            res["corners"][f"c{k:g}_l{m:g}"] = row
    (HERE / "a132_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    summarise(res)


def summarise(res):
    c = res["corners"]
    err = max(max(abs(x["ith_err_a"]), abs(x["von_err_v"]) / 10) for x in res["scaling_check"])
    print(f"I_th0 {res['ith1_a']:.2f} / {res['ith4_a']:.2f} A (ph1-3 / ph4), V_on0 {res['von_nominal_v']:.2f} V; "
          f"method check {res['method_check_eff_pct']:.2f}% (A131 90.43); scaling error <= {err:.3f} A")
    worst = lambda key, f: min(c.items(), key=lambda kv: f(kv[1]))
    for label, get in (("fixed 15.625 A", lambda r: r["fixed"]),
                       *[(f"V_set {t[1:]} V", (lambda t: lambda r: r["tuned"][t])(t)) for t in next(iter(c.values()))["tuned"]]):
        rows = [get(r) for r in c.values()]
        m1 = min(rows, key=lambda r: r["margin1_a"]); m4 = min(r["margin4_a"] for r in rows)
        print(f"{label:15s}: i {min(r['i_a'] for r in rows):5.1f}-{max(r['i_a'] for r in rows):5.1f} A  margin1 >= {m1['margin1_a']:5.2f} "
              f"(43.2 V {min(r['margin1_vin43.2_a'] for r in rows):5.2f}, 40 V {min(r['margin1_vin40_a'] for r in rows):5.2f})  "
              f"margin4 >= {m4:5.2f}  V_on1 <= {max(r['von1_v'] for r in rows):4.2f}  hard <= {max(r['hard_w'] for r in rows):4.2f} W  "
              f"regret <= {max(r['regret_pt'] for r in rows):4.2f} pt  peak {min(r['peak_a'] for r in rows):.0f}-{max(r['peak_a'] for r in rows):.0f} A")
    k, r = worst("regret", lambda r: -r["fixed"]["regret_pt"])
    print(f"fixed worst regret at {k}: {r['fixed']['eff_pct']:.2f}% vs best {r['best']['eff_pct']:.2f}% at {r['best']['i_a']:.1f} A")


# ---- D63 transients on 9 corners ----
def d63_design(k, m, i):
    d = FF.design(DESIGN)
    s, rails_t13_t4 = np.sqrt(k / m), d.ith
    return replace(d, lf=d.lf * m, i_tgt=-i, t_dn=d.t_dn * k, t_tr=tuple(t * np.sqrt(k * m) for t in d.t_tr),
                   ith=(rails_t13_t4[0], tuple(np.array(rails_t13_t4[1]) * s), tuple(np.array(rails_t13_t4[2]) * s)))


def d63_case(args):
    k, m, target, i, row = args
    st = FF.A124_ROWS[row]
    kw = {"i_step": st[1]} if st[0] == "load" else {"dvin": st[1], "t_slew": st[2] * 1e-6}
    mt = D63S.run_case(d63_design(k, m, i), kw, t_end=600e-6)
    return {"k_c": k, "k_l": m, "target": target, "i_a": i, "row": row, "outcome": A118.outcome(mt),
            "peak_a": mt["peak_max_a"], "ph1_depth_a": mt["ph1_depth_a"], "ph1_crossing": mt["ph1_crossing_periods"],
            "slot_depth_a": max(mt["depth_max_a"][1:]), "valley_min_a": mt["valley_min_a"], "extreme_mv": mt["extreme_mv"],
            "back_us": mt["back_us"]}


def d63(jobs=6, smoke=False):
    v_nom = json.loads((HERE / "a132_predictions.json").read_text())["von_nominal_v"]
    cases = []
    for k in (0.7, 1.0, 1.3):
        for m in (0.7, 1.0, 1.3):
            s = np.sqrt(k / m)
            for target, i in (("fixed", I_TGT), ("tuned", s * I_TGT)):
                if target == "tuned" and abs(s - 1) < 1e-9:
                    continue
                cases += [(k, m, target, i, row) for row in FF.A124_ROWS]
    if smoke:
        cases = cases[:2]
    with ProcessPoolExecutor(jobs) as ex:
        out = list(ex.map(d63_case, cases))
    if smoke:
        print(out[0]["outcome"], out[0]["peak_a"]); return
    (HERE / "a132_d63.json").write_text(json.dumps({"v_set_v": v_nom, "runs": out}, indent=1, default=float) + "\n")
    for target in ("fixed", "tuned"):
        rs = [r for r in out if r["target"] == target]
        bad = [r for r in rs if r["outcome"] != "ok"]
        pk = max(rs, key=lambda r: r["peak_a"])
        print(f"{target}: {len(rs)} runs, not ok {len(bad)} {sorted({(r['k_c'], r['k_l'], r['row'], r['outcome']) for r in bad})[:6]}; "
              f"peak max {pk['peak_a']:.0f} A ({pk['k_c']}, {pk['k_l']}, {pk['row']}); runs with ph1 crossing "
              f"{sum(1 for r in rs if r['ph1_crossing'] > 0)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "d63":
        d63(smoke="smoke" in sys.argv)
    else:
        steady()
