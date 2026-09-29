"""A67 - how much negative current does series-capacitor-buck ZVS need?

A single-node, lossless, linear-capacitance resonant criterion. It is checked
against Track A's full-network bisections (A53/A54), then evaluated at P25's
built point, at P24's 48 V point, and for the main-line synthetic fixture.

Rising (high-side ZVS) edge of phase k. The low side turns off with the
inductor current at -I_n. The node x_k starts at 0 V; the output (Vo) is
stiff; the flying capacitor is stiff, so a_k moves with x_k. Then

    v(t) = Vo (1 - cos wt) + Z0 I_n sin wt,   w = 1/sqrt(L C),  Z0 = sqrt(L/C)

The high side turns on at zero voltage if v reaches Vh (the phase high
level, Vin/nP) within the dead time. With no dead-time limit, this needs

    I_n >= sqrt(Vh (Vh - 2 Vo)) / Z0.

Relative to the ripple dI = (Vh - Vo) Ton / L, that is

    I_n / dI = [sqrt(Vh (Vh - 2 Vo)) / (Vh - Vo)] * sqrt(L C) / Ton,

i.e. about the node's flip time sqrt(LC) over the on-time.

C is the charge-equivalent capacitance the node moves. In the SCB, the rise
of x_k charges:
- low side k (0 -> Vh);
- high side k (Vh -> 0);
- high side k+1 (Vh -> 2 Vh; its drain a_k rises while its source is held
  by the next flying capacitor).
The last phase has no k+1.

Usage: python3 zvs_criterion.py   (writes results.json)
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
T_GRID = 4001


def node_peak(L, C, i_n, vo, t_max):
    """max over 0 <= t <= t_max of the node voltage (resonant rise from 0 V)."""
    w, z0 = 1 / np.sqrt(L * C), np.sqrt(L / C)
    t = np.linspace(0.0, t_max, T_GRID)
    return float(np.max(vo * (1 - np.cos(w * t)) + z0 * i_n * np.sin(w * t)))


def i_n_min(vh, vo, L, C):
    """Negative current needed with no dead-time limit."""
    return float(np.sqrt(vh * (vh - 2 * vo)) / np.sqrt(L / C))


def summary(vh, vo, L, C, ton, i_peak):
    need = i_n_min(vh, vo, L, C)
    tau = float(np.sqrt(L * C))
    return {"L_h": L, "C_node_f": C, "sqrt_LC_s": tau, "quarter_period_s": np.pi / 2 * tau,
            "on_time_s": ton, "sqrt_LC_over_on_time": tau / ton,
            "I_neg_min_a": need, "I_neg_min_over_peak": need / i_peak, "peak_a": i_peak}


# ---- 1. Validation against Track A's bisected critical L (A53, A54) ----------
# P24 point (P24_EXPLICIT): 48 V -> 1 V, nP = 4, 5 MHz, 250 W per module
P24 = {"vin": 48.0, "vo": 1.0, "np": 4, "f": 5e6, "p_module": 250.0}
VH24 = P24["vin"] / P24["np"]
TON24 = P24["np"] * P24["vo"] / (P24["f"] * P24["vin"])      # P24 Eq. 3: 16.67 ns
IDC24 = P24["p_module"] / P24["vo"] / P24["np"]               # 62.5 A per phase
DEAD_A53_A54 = 2.15e-9                                        # A53/A54 BOUNDARY dead time

VALIDATION = {   # device, per-switch linear C used by A53/A54 (CH_TOTAL, CL_TOTAL), bisected L_crit
    "A53 GS61008T": (385e-12, 770e-12, 1.19625e-9),
    "A54 EPC2067": (3720e-12, 5580e-12, 0.62741e-9),
}


def critical_l(C, t_max):
    def margin(L):
        i_n = (VH24 - P24["vo"]) * TON24 / L / 2 - IDC24          # valley current magnitude at 250 W
        return node_peak(L, C, i_n, P24["vo"], t_max) - VH24
    return brentq(margin, 0.2e-9, 1.45e-9)


# ---- 2. P25's built point (P25_SUPPLEMENT; order of magnitude only) ---------
# 12 V -> 1 V, nP = 3 (Vh = 4 V), 0.5 MHz, D = 0.25 (Ton = 500 ns), peak 50 A;
# 1 high / 2 low GS61008T; Coilcraft 22 nH (the reported 50 A peak implies
# ~30 nH effective, so both are shown).
def q_gs61008t(v):
    """Per-device Qoss(V), project model (A47 fit of the GS61008T datasheet Fig. 7)."""
    cf, a, vk = 203.754e-12, 498.502e-12, 13.1432
    return cf * v + a * vk * np.arctan(v / vk)


# ---- 3. Main-line synthetic fixture (SYNTHETIC; read 2026-09-29 from the
# working tree, other session, uncommitted, may change): scripts/
# audit_p25_synthetic_seeds.py make_synthetic_context, "D12 synthetic F/H/s".
FIXTURE = {"coss_f_each": 1.0, "inductance_h": (2.0, 3.0, 4.0), "on_time_s": 0.02,
           "vin": 12.0, "np": 3, "vo": 1.0, "peak_reference_a": 20.0, "alpha": 0.05}


def main():
    out = {"experiment": "A67", "classification": "SENSITIVITY_ONLY (analytical criterion + cross-checks)"}

    val = {}
    for name, (ch, cl, sim) in VALIDATION.items():
        rows = {}
        for label, C in (("own high + low only", ch + cl), ("+ next phase's high side (phases 1-3)", 2 * ch + cl)):
            lc = critical_l(C, DEAD_A53_A54)
            rows[label] = {"C_node_f": C, "predicted_L_crit_h": lc, "bisected_L_crit_h": sim,
                           "relative_error": lc / sim - 1}
        val[name] = rows
    out["validation_vs_A53_A54"] = val

    p25 = {}
    vh, vo = 4.0, 1.0
    c12 = (2 * q_gs61008t(vh) + q_gs61008t(vh) + (q_gs61008t(2 * vh) - q_gs61008t(vh))) / vh
    c3 = 3 * q_gs61008t(vh) / vh
    for label, C in (("phases 1-2", c12), ("phase 3", c3)):
        for L in (22e-9, 30e-9):
            p25[f"{label}, L = {L * 1e9:.0f} nH"] = summary(vh, vo, L, C, 0.25 / 0.5e6, 50.0)
    out["P25_built_point"] = p25

    p24 = {}
    for label, C in (("phases 1-3", 7 * 1860e-12), ("phase 4", 5 * 1860e-12)):
        p24[label] = summary(VH24, P24["vo"], 1.4667e-9, C, TON24, 125.0)
    reach = {}
    for frac in (0.01, 0.02):
        i_n, C, L = frac * 125.0, 7 * 1860e-12, 1.4667e-9
        reach[f"{frac:.0%}"] = {"I_neg_a": i_n,
                                "node_max_any_dead_time_v": P24["vo"] + float(np.sqrt(P24["vo"] ** 2 + (np.sqrt(L / C) * i_n) ** 2)),
                                "node_within_2p15ns_v": node_peak(L, C, i_n, P24["vo"], DEAD_A53_A54)}
    out["P24_48V_point"] = {"EPC2067_Co_tr_f": 1860e-12, "phases": p24, "with_1_2_percent": reach}

    fx = {}
    vh = FIXTURE["vin"] / FIXTURE["np"]
    for k, L in enumerate(FIXTURE["inductance_h"], start=1):
        C = FIXTURE["coss_f_each"] * (3 if k < FIXTURE["np"] else 2)
        s = summary(vh, FIXTURE["vo"], L, C, FIXTURE["on_time_s"], FIXTURE["peak_reference_a"])
        s["negative_target_a"] = FIXTURE["alpha"] * FIXTURE["peak_reference_a"]
        s["target_over_needed"] = s["negative_target_a"] / s["I_neg_min_a"]
        s["ripple_per_on_time_a"] = (vh - FIXTURE["vo"]) * FIXTURE["on_time_s"] / L
        fx[f"phase {k}"] = s
    out["main_line_fixture"] = {"values": FIXTURE, "phases": fx}
    (HERE / "results.json").write_text(json.dumps(out, indent=1))

    for name, rows in val.items():
        for label, r in rows.items():
            print(f"{name:13s} {label:38s} C {r['C_node_f'] * 1e12:6.0f} pF  L_crit {r['predicted_L_crit_h'] * 1e9:.4f} "
                  f"vs {r['bisected_L_crit_h'] * 1e9:.4f} nH ({r['relative_error']:+.1%})")
    for group, rows in (("P25", p25), ("P24", p24), ("fixture", fx)):
        for label, s in rows.items():
            print(f"{group:7s} {label:24s} sqrt(LC)/Ton {s['sqrt_LC_over_on_time']:.3g}  I_neg,min {s['I_neg_min_a']:.3g} A "
                  f"= {s['I_neg_min_over_peak']:.1%} of peak"
                  + (f"; target {s['negative_target_a']:.2f} A = {s['target_over_needed']:.0%} of needed; "
                     f"ripple per on-time {s['ripple_per_on_time_a']:.3f} A" if group == "fixture" else ""))
    for frac, r in reach.items():
        print(f"P24 with {frac}: node reaches {r['node_max_any_dead_time_v']:.2f} V (any dead time), "
              f"{r['node_within_2p15ns_v']:.2f} V within 2.15 ns, of 12 V")


if __name__ == "__main__":
    main()
