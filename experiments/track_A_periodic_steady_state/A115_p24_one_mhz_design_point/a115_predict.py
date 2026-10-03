"""A115 registered predictions (before any run): P24's 1 MHz design point (Table I, 4 phases x 4 modules) with Eq. (4)'s
filter inductance, 7.333 nH, against the 5 MHz point (1.4667 nH) of A110.

Per negative-current target (5, 7.5, 10, 12.5% of the 125 A peak):
- D57's free valley: the high side's V_DS at its turn-on and the time to the valley, phase 1's node (2 high-side, 3
  low-side EPC2067 and the next phase's 2 high-side) and phase 4's (no next phase), and the target for zero voltage;
- the boundary-mode orbit by charge balance (average 62.5 A per phase, R 0.54 mOhm in both slopes, the current from
  -i_neg to 0 over the valley time, the high side on at the valley at ~0 A): peak, Ton, period, ripple peak - valley;
  checked first on A110's measured 5 MHz rows;
- D62's middle-case efficiency on these waveforms (and the ideal-inductor and best cases);
- D59's PI on Ton at the 1 MHz point (fc 60 kHz, zero at fc / 5) and its +-62.5 A load steps.
Writes a115_predictions.json (make_cfgs.py reads the gains from it).
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scipy.optimize import brentq  # noqa: E402

import scb_ivr.p24_voltage_loop as VL  # noqa: E402
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import node_model, required_i_neg  # noqa: E402
from scb_ivr.p24_loss_budget import budget  # noqa: E402
from scb_ivr.p24_startup_averaged import LSB, Module  # noqa: E402

spec = importlib.util.spec_from_file_location("d62_script", PROJECT / "scripts" / "p24_loss_budget.py")
D62 = importlib.util.module_from_spec(spec); spec.loader.exec_module(D62)
A110 = PROJECT / "experiments" / "track_A_periodic_steady_state" / "A110_p24_high_side_zvs" / "a110_summary.json"

PEAK, I_PH, R, VO, V_RAIL = 125.0, 62.5, 0.54e-3, 1.0, 12.0
L5, L1 = 1.4666667e-9, 7.3333333e-9          # Eq. (4) at 5 and 1 MHz (P24 Table I prints 2.68 and 13.44 nH)
T_DN = 1.26e-9                              # the high-to-low node transition (D51 orbit, d_low_ns)
PCTS = (5.0, 7.5, 10.0, 12.5)
FC = 60e3


def seg(v, r, lf, i0, i1):
    """A linear-R segment di/dt = (v - r i) / lf from i0 to i1: (duration, charge)."""
    t = (lf / r) * math.log((v - r * i0) / (v - r * i1))
    return t, (v * t - lf * (i1 - i0)) / r


def orbit(lf, i_neg, t_valley):
    """(peak A, Ton s, period s) with the cycle-average current I_PH."""
    def f(pk):
        ton, q_on = seg(V_RAIL - VO, R, lf, 0.0, pk)
        t_ls, q_ls = seg(-VO, R, lf, pk, -i_neg)
        q = q_on + q_ls + pk * T_DN - (2 / math.pi) * i_neg * t_valley
        period = ton + t_ls + T_DN + t_valley
        return q / period - I_PH, ton, period
    pk = brentq(lambda p: f(p)[0], 50.0, 400.0)
    return pk, f(pk)[1], f(pk)[2]


def d57(lf, i_neg):
    """Free valley (V_DS, time) of phase 1's and phase 4's node."""
    p1 = node_model(replace(EdgeCircuit(), lf=lf))
    p4 = node_model(replace(EdgeCircuit(), lf=lf, v_rail=V_RAIL, dv_cs=0.0, n_next=0))
    (t1, v1), (t4, v4) = p1.valley_free(i_neg, t_max=200e-9), p4.valley_free(i_neg, t_max=200e-9)
    return v1, t1, v4, t4


def row(lf, pct):
    i_neg = pct / 100 * PEAK
    v1, t1, v4, t4 = d57(lf, i_neg)
    pk, ton, period = orbit(lf, i_neg, t1)
    ph = [{"valley": -i_neg, "peak": pk, "vds_on": max(v1, 0.0)}] * 3 + [{"valley": -i_neg, "peak": pk, "vds_on": max(v4, 0.0)}]
    eff = {sc: budget(ph, ton, period, lf, D62.SCENARIOS[sc], [V_RAIL] * 4, [V_RAIL] * 4)
           for sc in ("middle", "middle_ideal_inductor", "best")}
    return {"i_neg_a": i_neg, "hs_on_vds_v_phase1": v1, "t_valley_ns_phase1": t1 * 1e9, "hs_on_vds_v_phase4": v4,
            "t_valley_ns_phase4": t4 * 1e9, "peak_a": pk, "ton_ns": ton * 1e9, "period_ns": period * 1e9,
            "f_mhz": 1e-6 / period, "ripple_pp_a": pk + i_neg,
            "budget_middle_w": {k: v for k, v in eff["middle"].items() if k != "efficiency"},
            "efficiency_pct": {k: v["efficiency"] * 100 for k, v in eff.items()}}


def loop(lf, ton, period, i_neg):
    """D59 at this point: kp, ki for FC, margins, and the +-62.5 A steps (TS = the period)."""
    m = Module(lf=lf, i_neg=i_neg, ton_full=ton / LSB, period_full=period)
    VL.TS = period
    kp, ki = VL.design_pi(FC, m)
    fc, pm = VL.margins(kp, ki, m, td=0.75 * period)
    out = {"fc_target_hz": FC, "kp_ns_per_v": kp * LSB * 1e9, "ki_ns_per_v": ki * LSB * 1e9, "fc_hz": fc, "pm_deg": pm,
           "ki_register": int(round(ki * 0.5e-3 * 65536)), "ladder_hz_cs15uF":
           VL.ladder_f(15e-6, m, d=ton / period)}
    kp100, ki100 = VL.design_pi(100e3, m)
    out["fc100"] = {"pm_deg": VL.margins(kp100, ki100, m, td=0.75 * period)[1],
                    "ki_register": int(round(ki100 * 0.5e-3 * 65536))}
    for name, di in (("s_p62", 62.5), ("s_m62", -62.5)):
        t, vo, tn = VL.step(di, kp, ki, m, t_end=400e-6, t_step=50e-6, dt=5e-9, ton0=ton / LSB)
        out[name] = VL.step_metrics(t, vo, tn, t_step=50e-6)
    VL.TS = 232.2e-9
    return out


def main():
    res = {"conditions": {"l_1mhz_h": L1, "l_5mhz_h": L5, "r_ohm": R, "v_rail_v": V_RAIL, "t_dn_s": T_DN,
                          "required_pct_phase1": {"1MHz": required_i_neg(replace(EdgeCircuit(), lf=L1)) / PEAK * 100,
                                                  "5MHz": required_i_neg(replace(EdgeCircuit(), lf=L5)) / PEAK * 100}}}
    print("required negative current for zero voltage (phase 1): 1 MHz {1MHz:.1f}%, 5 MHz {5MHz:.1f}%".format(
        **res["conditions"]["required_pct_phase1"]))
    a110 = json.loads(A110.read_text())
    chk = {}
    for name, pct in (("n5", 5.0), ("n10", 10.0), ("n15", 15.0), ("n20", 20.0), ("n25", 25.0)):
        p, mrow = row(L5, pct), a110[name]
        pk_m = sum(mrow["peaks_a"]) / 4
        chk[name] = {"ton_ratio": mrow["ton_ns"] / p["ton_ns"], "period_ratio": mrow["period_ns"] / p["period_ns"],
                     "peak_offset_a": pk_m - p["peak_a"], "efficiency_offset_pts": mrow["efficiency_pct"] - p["efficiency_pct"]["middle"]}
        print(f"5 MHz {pct:4.1f}% against A110: Ton x{chk[name]['ton_ratio']:.3f}, period x{chk[name]['period_ratio']:.4f}, "
              f"peak {chk[name]['peak_offset_a']:+.1f} A, efficiency {chk[name]['efficiency_offset_pts']:+.2f} points")
    res["check_5mhz_a110"] = chk
    for lf, tag in ((L5, "5MHz"), (L1, "1MHz")):
        for pct in PCTS:
            r = row(lf, pct)
            res[f"{tag}_n{pct:g}".replace(".", "p")] = r
            e = r["efficiency_pct"]
            print(f"{tag} {pct:4.1f}%: HS on {r['hs_on_vds_v_phase1']:+.2f} V (phase 4 {r['hs_on_vds_v_phase4']:+.2f}) at "
                  f"{r['t_valley_ns_phase1']:.1f} ns; peak {r['peak_a']:.1f} A, Ton {r['ton_ns']:.2f} ns, T {r['period_ns']:.1f} ns "
                  f"({r['f_mhz']:.3f} MHz), ripple {r['ripple_pp_a']:.1f} A pp; efficiency middle {e['middle']:.2f}%, "
                  f"ideal inductor {e['middle_ideal_inductor']:.2f}%, best {e['best']:.2f}%")
    for pct in (5.0, 10.0):
        r = res[f"1MHz_n{pct:g}"]
        lp = loop(L1, r["ton_ns"] * 1e-9, r["period_ns"] * 1e-9, r["i_neg_a"])
        res[f"loop_1MHz_n{pct:g}"] = lp
        print(f"loop at 1 MHz {pct:g}%: kp {lp['kp_ns_per_v']:.2f} ns/V, ki {lp['ki_ns_per_v']:.3f} ns/V per sample "
              f"(register {lp['ki_register']}), fc {lp['fc_hz'] / 1e3:.1f} kHz, PM {lp['pm_deg']:.0f} deg "
              f"(at 100 kHz: PM {lp['fc100']['pm_deg']:.0f} deg, ki register {lp['fc100']['ki_register']} > 65535); "
              f"steps +62.5 A {lp['s_p62']['extreme_mv']:+.1f} mV back {lp['s_p62']['back_within_1pct_us']:.1f} us, "
              f"-62.5 A {lp['s_m62']['extreme_mv']:+.1f} mV back {lp['s_m62']['back_within_1pct_us']:.1f} us")
    (HERE / "a115_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print("wrote a115_predictions.json")


if __name__ == "__main__":
    main()
