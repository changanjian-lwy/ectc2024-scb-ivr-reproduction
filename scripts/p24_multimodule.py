"""D61: what a P24 module must offer for multi-module operation (averaged; no co-simulation).

    python3 scripts/p24_multimodule.py

1. Static: currents and periods of a module whose inductors differ by eps (equal Ton); the negative current that
   equalises its current; the largest eps that keeps i_neg >= 2.5 A (2%, A82's soft edge).
2. Interleaving: time for free-running modules to slip by one slot (T/16) for a Ton difference (LSB) or a transition-
   time difference (ns).
3. Dynamics on four modules sharing Vo (Co and load x4): independent PIs with ADC offsets; one shared PI with
   inductor tolerances; per-module droop.
Writes symbolic_derivations/03_P24_native/diagnostics/D61_multimodule.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

from scb_ivr.p24_multimodule import drift_time_us, i_neg_for_equal_current, module_current, period, simulate  # noqa: E402
from scb_ivr.p24_startup_averaged import Module  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"


def main():
    m = Module()
    out = {}
    i0 = module_current(m, 568.0, 1.0)
    print(f"1. static, Ton 568 LSB: nominal module {i0:.1f} A, period {period(m, 568.0, 1.0) * 1e9:.1f} ns (independent of L and i_neg)")
    rows = []
    for eps in (-0.10, -0.05, 0.05, 0.10):
        i = module_current(m, 568.0, 1.0, eps=eps)
        rows.append({"eps": eps, "current_a": i, "share_error": i / i0 - 1, "i_neg_for_equal_current_a": i_neg_for_equal_current(m, eps)})
        print(f"   L {eps:+.0%}: {i:6.1f} A ({i / i0 - 1:+.1%}); equal current needs i_neg {rows[-1]['i_neg_for_equal_current_a']:5.2f} A")
    eps_max = brentq(lambda e: i_neg_for_equal_current(m, e) - 2.5, 0.0, 0.2)
    print(f"   i_neg stays >= 2.5 A (2%) for L up to {eps_max:+.1%} above nominal")
    out["static"] = {"nominal_current_a": i0, "rows": rows, "eps_max_for_ineg_2p5": eps_max}

    print("\n2. interleaving drift between free-running modules (time to slip T/16)")
    dr = {"ton_lsb": {str(d): drift_time_us(m, d) for d in (1, 2, 5, 28)}}
    t0 = period(m, 568.0, 1.0)
    dr["t_x_ns"] = {str(x): float(t0 / 16 / (x * 1e-9) * t0 * 1e6) for x in (0.05, 0.2, 1.0)}
    print("   Ton difference " + ", ".join(f"{k} LSB: {v:.1f} us" for k, v in dr["ton_lsb"].items()))
    print("   transition-time difference " + ", ".join(f"{k} ns: {v:.1f} us" for k, v in dr["t_x_ns"].items()))
    out["drift_us"] = dr

    print("\n3. four modules on one output (Co and load x4), 300 us")
    off = (0.5e-3, 0.0, 0.0, -0.5e-3); eps = (0.05, 0.0, 0.0, -0.05)
    cases = {"independent_pi_adc_pm0p5mV": dict(strategy="independent", adc_offset_v=off),
             "shared_pi_L_pm5pct": dict(strategy="shared", eps=eps),
             "droop_0p08mOhm_adc_pm0p5mV": dict(strategy="droop", adc_offset_v=off, r_droop=0.08e-3),
             "droop_0p08mOhm_adc_and_L": dict(strategy="droop", adc_offset_v=off, eps=eps, r_droop=0.08e-3)}
    dyn = {}
    for name, kw in cases.items():
        t, vo, I, N = simulate(t_end=300e-6, **kw)
        rec = {}
        for tt in (50e-6, 150e-6, 299e-6):
            i = int(np.argmin(np.abs(t - tt)))
            rec[f"{tt * 1e6:.0f}us"] = {"vo_v": float(vo[i]), "currents_a": [float(x) for x in I[i]], "ton_lsb": [int(x) for x in N[i]]}
        last = rec["299us"]
        rec["spread_a"] = max(last["currents_a"]) - min(last["currents_a"]); rec["ton_spread_lsb"] = max(last["ton_lsb"]) - min(last["ton_lsb"])
        rec["growing"] = (max(rec["150us"]["currents_a"]) - min(rec["150us"]["currents_a"])) < rec["spread_a"] - 1.0
        dyn[name] = rec
        print(f"   {name:28s}: at 299 us Vo {last['vo_v']:.4f} V, currents " + "/".join(f"{x:.1f}" for x in last["currents_a"])
              + f" (spread {rec['spread_a']:.1f} A{', still growing' if rec['growing'] else ''}), Ton spread {rec['ton_spread_lsb']} LSB"
              + f" -> slips a slot in {drift_time_us(m, rec['ton_spread_lsb']) if rec['ton_spread_lsb'] else float('inf'):.2f} us")
    out["dynamics"] = dyn
    (DIAG / "D61_multimodule.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote {(DIAG / 'D61_multimodule.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
