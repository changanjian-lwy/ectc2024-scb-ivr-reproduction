"""D66: the loss and temperature cost of passive current sharing between P24 modules (common Ton, D61 scheme A), and the
valley margin an i_neg sharing trim (D61 scheme B) would leave, for the four-module final design (C12).

    PYTHONPATH=src python3 scripts/p24_sharing_loss.py

Method (math, no new co-simulation):
- every module runs the common Ton and period; a module with L0 (1 + e) has its per-phase swing (peak - valley) scaled
  by 1 / (1 + e); the shared voltage loop scales Ton by x so that the four modules carry the same total current;
- valley against e: (a) fixed at the nominal module's (D61's averaged law), (b) the slave law measured on C12 ls_p5 /
  ls_p10 (linear in e); the two bound the case;
- high-side turn-on V_DS: the nominal module's measured value plus the edge model's change (p24_aux_commutation.Model,
  datasheet Coss(V), L and valley of the case);
- loss: D62's middle scenario (p24_loss_budget.budget) on the constructed phases; output power scales with the
  module's current.
Calibration: the same construction against the measured modules of C12 ls_p5, ls_p10 and C07 all_n0.
Writes symbolic_derivations/03_P24_native/diagnostics/D66_sharing_loss.json.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit, Model  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import required_i_neg  # noqa: E402
from scb_ivr.p24_loss_budget import QG_TYP, RON_MAX, budget, measure  # noqa: E402

C = ROOT / "experiments" / "track_C_multi_module"
DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
L0 = 2.93333332e-9
MIDDLE = dict(ron=RON_MAX, l_tech="mpc_hbs1_500nH", esr_cs=1.0e-3, q_gate=QG_TYP, t_f=0.75e-9)
TOL = (0.05, 0.10, 0.20)
RTH = (0.5, 1.0, 2.0)               # K/W per module, assumed (P24 gives no thermal path)
MARGIN_RULE = 2.5                   # A, scorecard T12: every design with a valley margin <= 2.5 A failed a transient
PEAK_TRANSIENT = 189.0 - 144.0      # A above the steady peak on the worst registered four-module row (C10 / C12)


def modules(path):
    d = json.load(open(path))
    return [(m["cfg"]["circuit"]["L"], measure(m)) for m in [d] + d["modules_rest"]]


def current(phases):
    return sum((p["valley"] + p["peak"]) / 2.0 for p in phases)


class Edge:
    """High-side turn-on V_DS of phase k at inductance lf and valley current, from the edge model (cached)."""

    def __init__(self, rails, dv_next):
        self.rails, self.dv, self.cache = rails, dv_next, {}

    def von(self, k, lf, valley):
        key = (k, round(lf * 1e13), round(valley, 3))
        if key not in self.cache:
            e = replace(EdgeCircuit(), lf=lf, v_rail=self.rails[k], dv_cs=self.dv[k], n_next=2 if k < 3 else 0)
            self.cache[key] = float(Model(e).valley_free(-valley, t_max=200e-9)[1])
        return self.cache[key]

    def ith(self, k, lf, rail_scale=1.0):
        key = ("ith", k, round(lf * 1e13), rail_scale)
        if key in self.cache:
            return self.cache[key]
        e = replace(EdgeCircuit(), lf=lf, v_rail=self.rails[k] * rail_scale, dv_cs=self.dv[k] * rail_scale,
                    n_next=2 if k < 3 else 0)
        self.cache[key] = required_i_neg(e)
        return self.cache[key]


def build(nom, edge, e, x, valley_shift):
    """Phases of a module at L0 (1 + e), Ton scale x, valleys moved by valley_shift (A, per phase)."""
    out = []
    for k, p in enumerate(nom["phases"]):
        swing = (p["peak"] - p["valley"]) * x / (1.0 + e)
        v = p["valley"] + valley_shift[k]
        dv = edge.von(k, L0 * (1 + e), v) - edge.von(k, L0, p["valley"])
        out.append({"valley": v, "peak": v + swing, "vds_on": max(p["vds_on"] + dv, 0.0)})
    return out


def loss(nom, phases, x, i_nom):
    i = current(phases)
    b = budget(phases, nom["ton_s"] * x, nom["period_s"] * x, L0, MIDDLE, nom["rails_v"], nom["dv_next_v"],
               p_out=250.0 * i / i_nom)
    return {"current_a": i, "loss_w": b["total"], "terms": {k: round(v, 3) for k, v in b.items()},
            "peak_a": max(p["peak"] for p in phases), "von_v": [round(p["vds_on"], 2) for p in phases]}


def solve(nom, edge, eps, shifts):
    """Ton scale x giving the four modules the nominal total current, and each module's phases."""
    i_nom = current(nom["phases"])
    lo, hi = 0.8, 1.3
    for _ in range(60):
        x = 0.5 * (lo + hi)
        tot = sum(current(build(nom, edge, e, x, s)) for e, s in zip(eps, shifts))
        lo, hi = (x, hi) if tot < 4 * i_nom else (lo, x)
    return x, [build(nom, edge, e, x, s) for e, s in zip(eps, shifts)]


def main():
    nom = modules(C / "C12_floor_late_four_modules" / "cosim" / "run_n0.json")[0][1]
    i_nom = current(nom["phases"])
    edge = Edge(nom["rails_v"], nom["dv_next_v"])
    p_nom = loss(nom, nom["phases"], 1.0, i_nom)

    # slave valley law, C12 ls_p5 / ls_p10: valley shift per phase = slope_k x e
    meas = {n: modules(C / "C12_floor_late_four_modules" / "cosim" / f"run_{n}.json") for n in ("ls_p5", "ls_p10")}
    pts = [(m[1][0] / L0 - 1, [p["valley"] - q["valley"] for p, q in zip(m[1][1]["phases"], nom["phases"])])
           for m in meas.values()]
    slope = [float(np.polyfit([0.0] + [e for e, _ in pts], [0.0] + [s[k] for _, s in pts], 1)[0]) for k in range(4)]
    laws = {"fixed_valley": lambda e: [0.0] * 4, "slave_law": lambda e: [sl * e for sl in slope]}

    # calibration against measured modules
    calib = []
    for name, path in (("C12 ls_p5", "C12_floor_late_four_modules/cosim/run_ls_p5.json"),
                       ("C12 ls_p10", "C12_floor_late_four_modules/cosim/run_ls_p10.json"),
                       ("C07 all_n0 (also Cs / R spread)", "C07_module_spread_final/cosim/run_all_n0.json")):
        ms_ = modules(C / path)
        eps = [lf / L0 - 1 for lf, _ in ms_]
        tot = sum(current(r["phases"]) for _, r in ms_)
        x_meas = ms_[0][1]["ton_s"] / nom["ton_s"]
        for law, f in laws.items():
            x, built = solve(nom, edge, eps, [f(e) for e in eps])
            for j, ((lf, r), b) in enumerate(zip(ms_, built)):
                if abs(eps[j]) < 1e-6 and j != 3:
                    continue
                lm, lp = loss(r, r["phases"], 1.0, i_nom), loss(nom, b, x, i_nom)
                calib.append({"run": name, "module": j, "e": round(eps[j], 3), "law": law,
                              "share_meas_pct": round(100 * (4 * current(r["phases"]) / tot - 1), 2),
                              "share_pred_pct": round(100 * (current(b) / i_nom - 1), 2),
                              "loss_meas_w": round(lm["loss_w"], 2), "loss_pred_w": round(lp["loss_w"], 2),
                              "von_meas": [round(p["vds_on"], 2) for p in r["phases"]], "von_pred": lp["von_v"]})

    # passive sharing (scheme A): heaviest module at -t; others nominal (one off) or +t (worst spread)
    cases = []
    for t in TOL:
        for spread, eps in (("one_low", [-t, 0, 0, 0]), ("one_low_three_high", [-t, t, t, t])):
            for law, f in laws.items():
                x, built = solve(nom, edge, eps, [f(e) for e in eps])
                h = loss(nom, built[0], x, i_nom)
                dp = h["loss_w"] - p_nom["loss_w"]
                cases.append({"tol": t, "spread": spread, "law": law, "ton_scale": round(x, 4),
                              "heavy_share_pct": round(100 * (h["current_a"] / i_nom - 1), 2),
                              "heavy_loss_w": round(h["loss_w"], 2), "extra_loss_w": round(dp, 2),
                              "extra_loss_pct": round(100 * dp / p_nom["loss_w"], 1),
                              "heavy_peak_a": round(h["peak_a"], 1),
                              "heavy_peak_plus_transient_a": round(h["peak_a"] + PEAK_TRANSIENT, 1),
                              "heavy_von_v": h["von_v"], "dT_K": {str(r): round(dp * r, 1) for r in RTH}})

    # active sharing by i_neg (scheme B): equal currents, common Ton, mean valley kept; margin = I_th(L, rail) - i_neg
    trim = []
    ith_nom = [edge.ith(k, L0) for k in range(4)]
    for t in TOL:
        for spread, eps in (("one_low", [-t, 0, 0, 0]), ("one_low_three_high", [-t, t, t, t])):
            sw = [[(p["peak"] - p["valley"]) / (1 + e) for p in nom["phases"]] for e in eps]
            mean_v = float(np.mean([p["valley"] for p in nom["phases"]]))
            # per-phase mean current a_k = valley + x swing / 2 equal to nominal: valley_mk = a_k - x sw_mk / 2;
            # x from the mean valley over the modules kept at the nominal mean
            a = [(p["peak"] + p["valley"]) / 2 for p in nom["phases"]]
            x = (float(np.mean(a)) - mean_v) / float(np.mean([np.mean(s) for s in sw]) / 2)
            rows = []
            for m, e in enumerate(eps):
                valleys = [a[k] - x * sw[m][k] / 2 for k in range(4)]
                ph = [{"valley": v, "peak": v + x * sw[m][k],
                       "vds_on": max(nom["phases"][k]["vds_on"] + edge.von(k, L0 * (1 + e), v)
                                     - edge.von(k, L0, nom["phases"][k]["valley"]), 0.0)}
                      for k, v in enumerate(valleys)]
                ith = [edge.ith(k, L0 * (1 + e)) for k in range(4)]
                ith_lo = [edge.ith(k, L0 * (1 + e), 0.9) for k in range(4)]
                rows.append({"e": e, "valleys_a": [round(v, 2) for v in valleys],
                             "margin_a": [round(i + v, 2) for i, v in zip(ith, valleys)],
                             "margin_43v2_a": [round(i + v, 2) for i, v in zip(ith_lo, valleys)],
                             "loss_w": round(loss(nom, ph, x, i_nom)["loss_w"], 2),
                             "von_v": [round(p["vds_on"], 2) for p in ph]})
            trim.append({"tol": t, "spread": spread, "ton_scale": round(x, 4), "modules": rows})

    out = {"nominal": {"current_a": round(i_nom, 1), "loss_w": round(p_nom["loss_w"], 2), "terms": p_nom["terms"],
                       "von_v": p_nom["von_v"], "ith_a": [round(i, 2) for i in ith_nom],
                       "margin_a": [round(i + p["valley"], 2) for i, p in zip(ith_nom, nom["phases"])]},
           "valley_slope_a_per_unit_e": [round(s, 2) for s in slope], "calibration": calib,
           "passive": cases, "trim": trim,
           "assumptions": {"loss": "D62 middle", "rth_k_per_w": RTH, "margin_rule_a": MARGIN_RULE,
                           "peak_transient_a": PEAK_TRANSIENT}}
    DIAG.mkdir(parents=True, exist_ok=True)
    (DIAG / "D66_sharing_loss.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["nominal"]), "\nslope", out["valley_slope_a_per_unit_e"])
    for c in calib:
        print("CAL", c)
    for c in cases:
        print("A", c)
    for c in trim:
        print("B", c["tol"], c["spread"], c["ton_scale"])
        for r in c["modules"]:
            print("   ", r)


if __name__ == "__main__":
    main()
