"""D62: the P24 module's loss budget and efficiency for the recommended design (A105's I2, n0 row), per module.

    python3 scripts/p24_loss_budget.py

Measured from the co-simulation (last 200 periods): each phase's valley (low-side turn-off current) and peak (high-side
turn-off current), its high-side turn-on V_DS, Ton, the period, the series-capacitor voltages, the reverse-conduction
energy. Device data: EPC2067 datasheet (public). Scenarios for every value not known: on-resistance (typ / max, and
A90's 125 C factor), inductor technology (P24 Table 2), series-capacitor ESR, gate charge (zero-voltage QG - QGD / typ /
max), turn-off fall time.
Writes symbolic_derivations/03_P24_native/diagnostics/D62_loss_budget.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402

from scb_ivr.p24_loss_budget import L_TECH, QG_MAX, QG_TYP, QGD, RON_MAX, RON_TYP, budget  # noqa: E402

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
RUN = ROOT / "experiments" / "track_A_periodic_steady_state" / "A105_p24_integrated_standard_matrix" / "cosim" / "run_i2_n0.json"
LSB = 4e-9 / 128
LF = 1.4666667e-9
HOT = 0.8563 / 0.54                    # A90: RDS(on) at 125 C against 25 C (datasheet Fig. 5)

SCENARIOS = {
    "best": dict(ron=RON_TYP, l_tech="mpc_hbs1_500nH", esr_cs=0.5e-3, q_gate=QG_TYP - QGD, t_f=0.5e-9),
    "middle": dict(ron=RON_MAX, l_tech="mpc_hbs1_500nH", esr_cs=1.0e-3, q_gate=QG_TYP, t_f=0.75e-9),
    "worst_magnetic": dict(ron=RON_MAX, l_tech="mpc_hbs1_20nH", esr_cs=2.0e-3, q_gate=QG_MAX, t_f=1.0e-9),
    "middle_125C": dict(ron=RON_MAX * HOT, l_tech="mpc_hbs1_500nH", esr_cs=1.0e-3, q_gate=QG_TYP, t_f=0.75e-9),
    "middle_ideal_inductor": dict(ron=RON_MAX, l_tech="ideal", esr_cs=1.0e-3, q_gate=QG_TYP, t_f=0.75e-9),
    "middle_air_core_inductor": dict(ron=RON_MAX, l_tech="substrate_air", esr_cs=1.0e-3, q_gate=QG_TYP, t_f=0.75e-9),
}


def measured():
    d = json.loads(RUN.read_text())
    secs = d["sections"][-200:]
    t0, t1 = secs[0]["t_s"], secs[-1]["t_s"]
    period = float(np.mean(np.diff([s["t_s"] for s in secs])))
    ton = float(np.mean([s["ton_lsb"] for s in secs])) * LSB
    vcs = np.mean([s["vcs_v"] for s in secs], axis=0)
    chain = [48.0] + list(vcs) + [0.0]
    rails = [chain[k] - chain[k + 1] for k in range(4)]
    dv_next = [chain[k + 1] - chain[k + 2] for k in range(3)] + [0.0]
    phases = []
    for k in range(4):
        win = lambda recs: [r for r in recs if r["phase"] == k + 1 and t0 <= r["t_s"] <= t1]
        phases.append({"valley": float(np.mean([r["i_a"] for r in win(d["lowoffs_last"])])),
                       "peak": float(np.mean([r["i_a"] for r in win(d["highoffs_last"])])),
                       "vds_on": float(np.mean([r["vds_v"] for r in win(d["turnons_last"])]))})
    p_rev = float(np.mean([sum(s["rev_energy_j"]) for s in secs[1:]]) / period)
    p_out = float(np.mean([s["vo"] for s in secs])) ** 2 / 4e-3
    return {"phases": phases, "ton_s": ton, "period_s": period, "rails_v": rails, "dv_next_v": dv_next, "p_rev_w": p_rev, "p_out_w": p_out}


def main():
    m = measured()
    print(f"measured (A105 i2_n0, last 200 periods): Ton {m['ton_s'] * 1e9:.2f} ns, period {m['period_s'] * 1e9:.1f} ns, P_out {m['p_out_w']:.1f} W, "
          f"rails " + "/".join(f"{v:.2f}" for v in m["rails_v"]) + " V")
    for k, p in enumerate(m["phases"]):
        print(f"   phase {k + 1}: valley {p['valley']:+.2f} A, peak {p['peak']:.1f} A, high-side turn-on {p['vds_on']:.2f} V")
    out = {"measured": m, "scenarios": {}}
    keys = ("switch_conduction", "inductor_copper", "series_caps", "hard_turn_on", "turn_off_overlap", "gate_drive", "reverse_conduction")
    print("\n" + f"{'scenario':26s}" + "".join(f"{k[:14]:>15s}" for k in keys) + f"{'total':>9s}{'eff':>8s}")
    for name, sc in SCENARIOS.items():
        b = budget(m["phases"], m["ton_s"], m["period_s"], LF, sc, m["rails_v"], m["dv_next_v"], p_rev=m["p_rev_w"], p_out=m["p_out_w"])
        out["scenarios"][name] = {"assumptions": sc, "w": b}
        print(f"{name:26s}" + "".join(f"{b[k]:15.2f}" for k in keys) + f"{b['total']:9.1f}{100 * b['efficiency']:7.1f}%")
    (DIAG / "D62_loss_budget.json").write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote {(DIAG / 'D62_loss_budget.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
