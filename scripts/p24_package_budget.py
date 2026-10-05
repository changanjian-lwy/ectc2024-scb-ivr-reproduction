"""D65: the package parasitic budget of P24's Fig. 5 layout at the adopted 2.5 MHz design (scb_ivr.p24_package_parasitics).

    python3 scripts/p24_package_budget.py

Currents: A143's four-module steady record (run_g5_n0_k4, master, last 50 us): period, Ton, peak, valley, turn-on current
per phase -> piecewise-linear SCB waveforms. Scenarios (P24 prints none of these): lateral copper per layer stack
35-400 um; switch-node via field 0.5-5 mm^2 over glass 0.3 / 0.5 mm; central strip vias; Cs ESR 0.2-2 mOhm; commutation
loop 25-500 pH. Loss is per 250 W module against the measured 25.9 W (90.61 %); the loop bound is checked against the
EPC2067's 40 V rating at the steady peak, the 200 A spec limit and C13's 260 A falling-ramp peak, plus the low-side
turn-off at C13's +173 A positive valley.
Writes symbolic_derivations/03_P24_native/diagnostics/D65_package_budget.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from scb_ivr import p24_package_parasitics as P  # noqa: E402
from scb_ivr.cosim.circuit import EPC2067Coss  # noqa: E402

REC = ROOT / "experiments/track_A_periodic_steady_state/A143_p24_short_comparator_phase/cosim/run_g5_n0_k4.json"
OUT = ROOT / "symbolic_derivations/03_P24_native/diagnostics/D65_package_budget.json"
P_OUT, P_LOSS = 250.0, 250.0 * (1 / 0.9061 - 1)
V_MAX = 40.0


def steady(path=REC, window=50e-6):
    d = json.loads(path.read_text())
    te = d["highoffs_last"][-1]["t_s"]
    t0 = te - window
    on = [x for x in d["turnons_last"] if x["t_s"] > t0]
    hi = [x for x in d["highoffs_last"] if x["t_s"] > t0]
    lo = [x for x in d["lowoffs_last"] if x["t_s"] > t0]
    T = float(np.mean(np.diff(sorted(x["t_s"] for x in on if x["phase"] == 1))))
    ton = float(np.mean([min(h["t_s"] for h in hi if h["phase"] == x["phase"] and h["t_s"] > x["t_s"]) - x["t_s"]
                         for x in on if x["t_s"] < te - T]))
    t_res = float(np.mean([min(x["t_s"] for x in on if x["phase"] == l["phase"] and x["t_s"] > l["t_s"]) - l["t_s"]
                           for l in lo if l["t_s"] < te - T]))
    s = d["sections"][-1]
    rails = [s["vin_v"] - s["vcs_v"][0]] + [a - b for a, b in zip(s["vcs_v"], s["vcs_v"][1:])] + [s["vcs_v"][-1]]
    return {"T": T, "ton": ton, "t_res": t_res, "ipk": float(np.mean([h["i_a"] for h in hi])),
            "ilo": float(np.mean([l["i_a"] for l in lo])), "i_on": float(np.mean([x["i_a"] for x in on])),
            "rails_v": rails, "vo": s["vo"]}


def main():
    st = steady()
    t, i, hs, lo = P.phase_waveforms(st["T"], st["ton"], st["ipk"], st["ilo"], st["i_on"], st["t_res"])
    br = P.branch_currents(i, hs, lo)
    cur = {"phase_dc": float(i.mean()), "phase_rms": float(P.rms(i).mean()), "hs_rms": float(P.rms(br["hs"]).mean()),
           "ls_rms": [float(x) for x in P.rms(br["ls"])], "cs_rms": [float(x) for x in P.rms(br["cs"])],
           "in_rms": float(P.rms(br["in"])), "out_dc": float(i.sum(axis=0).mean())}
    gnd = br["ls"].copy(); gnd[0] += br["in"]                     # Cin's return enters at the strip, next to phase 1
    lat = {}
    for t_cu in (35e-6, 105e-6, 210e-6, 400e-6):
        lv, seg = P.lateral_loss(i, t_cu)
        lg, _ = P.lateral_loss(gnd, t_cu)
        lat[f"{t_cu * 1e6:.0f}um"] = {"vo_w": lv, "gnd_w": lg, "pct_of_pout": 100 * (lv + lg) / P_OUT,
                                       "pct_of_loss": 100 * (lv + lg) / P_LOSS}
    k = (P.lateral_loss(i, 1.0)[0] + P.lateral_loss(gnd, 1.0)[0])   # W x m: loss = k / t_cu
    t_for = {f"{p}pct": k / (p / 100 * P_OUT) * 1e6 for p in (1, 2, 5)}   # um of copper for that loss
    vias = {}
    for h in (0.3e-3, 0.5e-3):
        for a in (0.5e-6, 2e-6, 5e-6):
            r = P.via_field_r(h, a)
            vias[f"h{h * 1e3:.1f}mm_A{a * 1e6:.1f}mm2"] = {"r_uohm": r * 1e6, "w_4_phases": float(np.sum(P.rms(i) ** 2) * r)}
    strip_area = 1.2e-3 * 10e-3                                      # Fig. 5b: ~1.2 mm bus x 10 mm module
    strip = {f"h{h * 1e3:.1f}mm": 2 * cur["out_dc"] ** 2 * P.via_field_r(h, strip_area) for h in (0.5e-3, 1.0e-3)}
    esr = {f"{e * 1e3:.1f}mohm": float(np.sum(P.rms(br["cs"]) ** 2) * e) for e in (0.2e-3, 0.5e-3, 1e-3, 2e-3)}
    coss = EPC2067Coss()
    rail = max(st["rails_v"])
    cases = {"hs_steady": (st["ipk"], rail, 2), "hs_200A": (200.0, rail, 2), "hs_c13_260A_16.4V": (260.0, 16.4, 2),
             "ls_c13_pos_valley_173A": (173.0, 16.4, 3)}
    loops = (25e-12, 50e-12, 100e-12, 150e-12, 300e-12, 500e-12)
    ovs = {c: {f"{l * 1e12:.0f}pH": P.overshoot(l, a, v, coss, n) for l in loops} for c, (a, v, n) in cases.items()}
    allow = {}
    for c, (a, v, n) in cases.items():
        for lim in (V_MAX, 0.8 * V_MAX):
            ls = np.arange(1e-12, 1000e-12, 1e-12)
            ok = [l for l in ls if P.overshoot(l, a, v, coss, n) <= lim]
            allow[f"{c}_le_{lim:.0f}V_pH"] = round(ok[-1] * 1e12) if ok else 0
    out = {"steady": st, "currents_a": cur, "lateral": lat, "lateral_cu_um_for": t_for, "switch_node_vias": vias,
           "strip_vias_w": strip, "cs_esr_w": esr, "loop_overshoot_vds_v": ovs, "loop_allowed_pH": allow,
           "ref": {"p_out_w": P_OUT, "p_loss_w": P_LOSS, "v_rating": V_MAX}}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"T {st['T'] * 1e9:.1f} ns Ton {st['ton'] * 1e9:.1f} ns t_res {st['t_res'] * 1e9:.1f} ns rails {[round(v, 2) for v in st['rails_v']]}")
    print(f"phase dc {cur['phase_dc']:.1f} rms {cur['phase_rms']:.1f} | hs {cur['hs_rms']:.1f} ls {[round(x, 1) for x in cur['ls_rms']]} cs {[round(x, 1) for x in cur['cs_rms']]} A")
    for kk, v in lat.items():
        print(f"lateral {kk}: Vo {v['vo_w']:.1f} + GND {v['gnd_w']:.1f} W = {v['pct_of_pout']:.1f} % of Pout, {v['pct_of_loss']:.0f} % of the loss")
    print("Cu for 1/2/5 %:", {k2: round(v) for k2, v in t_for.items()}, "um")
    print("switch-node vias W:", {k2: round(v['w_4_phases'], 2) for k2, v in vias.items()})
    print("strip vias W:", {k2: round(v, 2) for k2, v in strip.items()}, "| Cs ESR W:", {k2: round(v, 2) for k2, v in esr.items()})
    for c, v in ovs.items():
        print(f"{c}: Vds", {k2: round(x, 1) for k2, x in v.items()})
    print("allowed loop pH:", allow)


if __name__ == "__main__":
    main()
