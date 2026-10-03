"""A124 registered predictions (before any run): at 2.5 MHz (Eq. (4) 2.933 nH) - the orbit, D57's turn-on and D62's
efficiency at 10 / 12.5 / 15% (a115_predict.row); D59's loop at 100 kHz designed at 12.5%; D57's threshold; D63 (its
thresholds at 2.933 nH computed here) for the step rows with the floor and the no-floor control.
Writes a124_predictions.json."""
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.p24_aux_commutation import EdgeCircuit  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import node_model, required_i_neg  # noqa: E402
from scb_ivr.p24_valley_map import Design, metrics, simulate, thresholds  # noqa: E402

spec = importlib.util.spec_from_file_location("a115_predict", HERE.parent / "A115_p24_one_mhz_design_point" / "a115_predict.py")
P = importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
L = 7.3333333e-9 / 2.5


def main():
    res = {"i_th_a": required_i_neg(replace(EdgeCircuit(), lf=L)), "rows": {}}
    for pct in (10.0, 12.5, 15.0):
        r = P.row(L, pct)
        res["rows"][f"p{pct:g}".replace(".", "")] = r
        print(f"{pct:4.1f}%: HS {r['hs_on_vds_v_phase1']:+.2f} / ph4 {r['hs_on_vds_v_phase4']:+.2f} V, Ton {r['ton_ns']:.2f} ns, T {r['period_ns']:.1f} ns, "
              f"ripple {r['ripple_pp_a']:.1f} A, efficiency middle {r['efficiency_pct']['middle']:.2f}% ideal {r['efficiency_pct']['middle_ideal_inductor']:.2f}%")
    r = res["rows"]["p125"]
    P.FC = 100e3
    res["loop"] = P.loop(L, r["ton_ns"] * 1e-9, r["period_ns"] * 1e-9, r["i_neg_a"])
    print(f"I_th {res['i_th_a']:.1f} A; loop kp {res['loop']['kp_ns_per_v']:.2f}, ki {res['loop']['ki_ns_per_v']:.3f} (register {res['loop']['ki_register']}), PM {res['loop']['pm_deg']:.0f}")
    e = EdgeCircuit()
    t1 = node_model(replace(e, lf=L)).valley_free(15.625, t_max=200e-9)[0]
    t4 = node_model(replace(e, lf=L, v_rail=12.0, dv_cs=0.0, n_next=0)).valley_free(15.625, t_max=200e-9)[0]
    d = Design(lf=L, cs=6e-6, i_tgt=-15.625, mode="floor", floor_a=2.0, kp_ns=res["loop"]["kp_ns_per_v"], ki_ns=res["loop"]["ki_ns_per_v"],
               ton_cfg_ns=35.5, smax=64, rs_low_ns=800.0, t_tr=(t1, t1, t1, t4), ith=thresholds(L))
    res["d63"] = {}
    for name, dd, kw in (("p125_s_m62", d, {"i_step": -62.5}), ("t125_s_m62", replace(d, mode="timed"), {"i_step": -62.5}),
                         ("p125_s_p62", d, {"i_step": 62.5}), ("p125_l_p48_1us", d, {"dvin": 4.8, "t_slew": 1e-6}),
                         ("p125_l_m48_1us", d, {"dvin": -4.8, "t_slew": 1e-6}), ("p125_l_p48_5us", d, {"dvin": 4.8, "t_slew": 5e-6}),
                         ("p125_l_m48_5us", d, {"dvin": -4.8, "t_slew": 5e-6}), ("p125_l_m80_10us", d, {"dvin": -8.0, "t_slew": 10e-6})):
        recs = simulate(dd, 300e-6, 50e-6, **kw)
        m = metrics(recs, 50e-6)
        a = [x for x in recs if x["t"] >= 50e-6]
        m["ph1_depth_a"] = max(x["depth"][0] for x in a); m["ph1_periods"] = sum(1 for x in a if x["depth"][0] > 0)
        res["d63"][name] = m
        print(f"D63 {name:16s}: peak {m['peak_max_a']:5.0f} A, Vo {m['extreme_mv']:+7.1f} mV, back {m['back_us']:6.1f} us, phase 1 crossing {m['ph1_depth_a']:.1f} A x {m['ph1_periods']}")
    (HERE / "a124_predictions.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
