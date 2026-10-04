"""A131 paper-level check (before any cosim): node devices per phase 2 high + 3 low (P24 Table 3, the main line) against
1 high + 2 low (P24 Sec. IV and P25), at 2.5 MHz (Eq. (4) 2.933 nH). D57 threshold and high-side turn-on, A115's orbit
with R scaled by the duty-weighted on-resistance, D62 loss budget with the device counts as arguments.
Writes a131_predictions.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import node_model, required_i_neg  # noqa: E402
import scb_ivr.p24_loss_budget as LB  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_predict", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
L = 7.3333333e-9 / 2.5
D = 1 / 12
CONFIGS = {"2h3l": (2, 3), "1h2l": (1, 2)}


def r_eff(nh, nl):
    """Duty-weighted on-resistance; the main line's 0.54 mOhm is (2, 3)."""
    f = lambda a, b: D / a + (1 - D) / b
    return 0.54e-3 * f(nh, nl) / f(2, 3)


def budget(phases, ton, period, lf, sc, nh, nl, rails):
    n, f = len(phases), 1.0 / period
    out = dict.fromkeys(("switch_conduction", "inductor_copper", "series_caps", "hard_turn_on", "turn_off_overlap", "gate_drive"), 0.0)
    on_ms = []
    for k, p in enumerate(phases):
        hs, ls, on = LB.phase_ms(p["valley"], p["peak"], ton, period)
        on_ms.append(on)
        out["switch_conduction"] += hs * sc["ron"] / nh + ls * sc["ron"] / nl
        out["inductor_copper"] += (hs + ls) * lf * LB.L_TECH[sc["l_tech"]]
        out["hard_turn_on"] += LB.hard_on_energy(p["vds_on"], P.V_RAIL, P.V_RAIL, n_h=nh, n_l=nl, n_next=nh if k < n - 1 else 0) * f
        out["turn_off_overlap"] += LB.turn_off_overlap(p["peak"], sc["t_f"]) * f
    for k in range(n - 1):
        out["series_caps"] += ton / period * (on_ms[k] + on_ms[k + 1]) * sc["esr_cs"]
    out["gate_drive"] = n * (nh + nl) * sc["q_gate"] * LB.VGS * f
    tot = sum(out.values())
    out["total"], out["efficiency"] = tot, 250.0 / (250.0 + tot)
    return out


def row(nh, nl, pct, sc="middle"):
    P.R = r_eff(nh, nl)
    base = replace(EdgeCircuit(), lf=L, n_h=nh, n_l=nl, n_next=nh)
    i = pct / 100 * P.PEAK
    m1 = node_model(base)
    m4 = node_model(replace(base, v_rail=P.V_RAIL, dv_cs=0.0, n_next=0))
    (t1, v1), (t4, v4) = m1.valley_free(i, t_max=200e-9), m4.valley_free(i, t_max=200e-9)
    pk, ton, period = P.orbit(L, i, t1)
    ph = [{"valley": -i, "peak": pk, "vds_on": max(v1, 0.0)}] * 3 + [{"valley": -i, "peak": pk, "vds_on": max(v4, 0.0)}]
    b = budget(ph, ton, period, L, P.D62.SCENARIOS[sc], nh, nl, None)
    return {"hs_on_v_ph1": v1, "hs_on_v_ph4": v4, "peak_a": pk, "ton_ns": ton * 1e9, "period_ns": period * 1e9,
            "r_mohm": P.R * 1e3, "efficiency_pct": b["efficiency"] * 100, "loss_w": {k: v for k, v in b.items() if k != "efficiency"}}


def main():
    res = {}
    for name, (nh, nl) in CONFIGS.items():
        ith = required_i_neg(replace(EdgeCircuit(), lf=L, n_h=nh, n_l=nl, n_next=nh))
        res[name] = {"i_th_a": ith, "i_th_pct": ith / 1.25, "rows": {}}
        print(f"{name}: I_th {ith:.1f} A = {ith / 1.25:.1f}%  R {r_eff(nh, nl) * 1e3:.3f} mOhm")
        for pct in (5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0):
            r = row(nh, nl, pct)
            res[name]["rows"][f"p{pct:g}"] = r
            w = r["loss_w"]
            print(f"  {pct:5.1f}%: HS {r['hs_on_v_ph1']:+5.2f}/{r['hs_on_v_ph4']:+5.2f} V  peak {r['peak_a']:.1f} A  T {r['period_ns']:.0f} ns  "
                  f"eff {r['efficiency_pct']:.2f}%  cond {w['switch_conduction']:.1f} hard {w['hard_turn_on']:.1f} gate {w['gate_drive']:.1f} W")
    (HERE / "a131_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
