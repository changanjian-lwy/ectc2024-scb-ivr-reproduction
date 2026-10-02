"""D56: an auxiliary commutation branch for the P24 high side's zero-voltage turn-on (A101).

    python3 scripts/p24_aux_commutation.py

1. Validation: the single-phase edge model against the full model's valley table (D47's 5% state).
2. Requirement at the edge: the auxiliary current needed at the low-side turn-off for the node to reach the rail,
   for a branch to the output (Nan and Ayyanar's ZVT) and to a capacitor at Vm (ARCP-type), against Lr.
3. Cycle with a bidirectional switch to a self-balanced Cm: Vm from Cm's charge balance, the high side turning off at
   the baseline's peak current, the low side turning on at the fixed dead time or at the baseline's turn-on voltage.
4. Loss bookkeeping per cycle against the baseline (the same model without the branch), the die area alpha chosen
   per Lr; powers for four phases at the orbit's period.
5. Timing: the BDS turn-on offset from the low-side turn-off, and the high side's turn-on window.
Writes symbolic_derivations/03_P24_native/diagnostics/D56_aux_commutation_5p0pct.json.
"""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

from scb_ivr.p24_aux_commutation import AuxBranch, Model, losses, phase_circuits, validation  # noqa: E402
from scripts.p24_orbits import DIAG  # noqa: E402

I_NEG = 6.25
N_PH = 4
LRS_NH = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
ALPHAS = (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0)
R_LR = 0.2e-3


def fmt(e):
    return round(e * 1e9, 1)


def main():
    m = Model()
    k = m.ckt
    f = 1.0 / (k.period_ns * 1e-9)
    w = lambda e: e * f * N_PH
    out = {"conditions": {"orbit": "D51_orbit_5p0pct_m0p0.json, phase 1", "i_neg_a": I_NEG, "v_rail_v": k.v_rail,
                          "dv_cs_v": k.dv_cs, "vo_v": k.vo, "lf_nh": k.lf * 1e9, "rds_on_ohm": 1.3e-3,
                          "qg_c": 17.1e-9, "r_lr_ohm": R_LR, "period_ns": k.period_ns, "phases": N_PH}}

    print("1. validation (single-phase edge against the full model's valley)")
    out["validation"] = validation(m)
    for r in out["validation"]:
        print(f"   i_neg {r['i_neg_a']:6.3f} A: {r['valley_v']:+6.2f} V at {r['t_ns']:5.2f} ns, full {r['full_model_v']:+5.2f}, "
              f"diff {r['diff_v']:+.3f}")

    orbit = json.loads((DIAG / "D51_orbit_5p0pct_m0p0.json").read_text())
    ckts = phase_circuits(orbit)
    out["validation_phases"] = []
    print("1b. the four phases (series-capacitor charge of the previous phase's on-time included) against the orbit")
    for ph, ckt in enumerate(ckts, 1):
        t, v = Model(ckt).valley_free(-orbit["lowoff_i"][ph - 1])
        row = {"phase": ph, "v_rail_v": ckt.v_rail, "i_neg_a": -orbit["lowoff_i"][ph - 1], "valley_v": v, "t_ns": t * 1e9,
               "orbit_turn_on_vds_v": orbit["turnon_vds"][ph - 1], "orbit_valley_ns": orbit["valley_ns"][ph - 1]}
        out["validation_phases"].append(row)
        print(f"   phase {ph}: rail {ckt.v_rail:.3f} V, i_neg {row['i_neg_a']:.3f} A: valley {v:.3f} V at {t * 1e9:.2f} ns; "
              f"orbit turn-on V_DS {row['orbit_turn_on_vds_v']:.3f} V, valley {row['orbit_valley_ns']:.2f} ns")

    print("\n2. auxiliary current needed at the low-side turn-off for zero-voltage turn-on")
    req = {"vo": [], "cm": []}
    for lr in (0.25, 0.5, 1.0, 1.4667, 2.0, 3.0, 5.0, 10.0):
        ir = m.min_ir_for_zvs(I_NEG, AuxBranch(lr * 1e-9, "vo", alpha=1.0, r_lr=0.0))
        req["vo"].append({"lr_nh": lr, "ir_a": ir, "build_ns_at_vo": lr * ir / k.vo, "energy_nj": 0.5 * lr * ir ** 2,
                          "charge_from_vo_nc": 0.5 * ir * lr * ir / k.vo})
        print(f"   to Vo: Lr {lr:6.3f} nH -> {ir:5.1f} A, build-up {lr * ir / k.vo:5.1f} ns, Lr energy {0.5 * lr * ir ** 2:6.0f} nJ")
    for lr in (0.15, 0.25, 0.5, 1.0, 2.0):
        for vm in (5.0, 6.0, 7.0, 8.0, 9.0, 10.0):
            a = AuxBranch(lr * 1e-9, "cm", vm=vm, alpha=1.0, r_lr=0.0)
            t0, v0, _ = m.rising_edge(I_NEG, a)
            ir = m.min_ir_for_zvs(I_NEG, a)
            req["cm"].append({"lr_nh": lr, "vm_v": vm, "vds_at_ir0_zero_v": v0, "ir_a": ir})
        print(f"   to Cm: Lr {lr:4.2f} nH, Vm 5..10 V -> " + ", ".join(
            f"{r['vm_v']:.0f}: {r['ir_a']:.1f} A" for r in req["cm"] if r["lr_nh"] == lr))
    out["requirement"] = req

    print("\n3-4. cycle with a BDS to a self-balanced Cm")
    base = m.cycle(I_NEG)
    i_pk = base["i_hs_off"]
    c_eff = float(m.cnode(np.linspace(0, k.v_rail, 200)).mean())
    lo, hi = base["a91_bounds"]
    out["baseline"] = {"vds_on_v": base["vds_on"], "t_hs_on_ns": base["t_hs_on_ns"], "e_hard_on_nj": base["e_hard_on"] * 1e9,
                       "p_hard_on_w": w(base["e_hard_on"]), "a91_bounds_w": [w(lo), w(hi)], "i_hs_off_a": i_pk,
                       "low_on_vds_v": base["low_on_vds"], "c_eff_nf": c_eff * 1e9}
    print(f"   baseline: V_DS {base['vds_on']:.2f} V at {base['t_hs_on_ns']:.2f} ns; hard turn-on {fmt(base['e_hard_on'])} nJ "
          f"= {w(base['e_hard_on']):.2f} W (A91 bounds {w(lo):.2f}-{w(hi):.2f} W); HS off {i_pk:.1f} A; LS on at {base['low_on_vds']:+.2f} V")
    x_low = base["low_on_vds"]
    cyc = []
    for dead in ("fixed", "retuned"):
        for lr in LRS_NH:
            kw = {"i_pk": i_pk, "x_low": x_low if dead == "retuned" else None}
            a0 = AuxBranch(lr * 1e-9, "cm", alpha=0.3, r_lr=R_LR)
            vm = m.balance_vm(I_NEG, a0, **kw)
            if vm is None:
                print(f"   [{dead}] Lr {lr} nH: no balance"); continue
            best = None
            for al in ALPHAS:
                a = replace(a0, vm=vm, alpha=al)
                r = m.cycle(I_NEG, a, **kw)          # alpha changes R_aux, hence the trajectory slightly
                e = losses(m, base, r, a, c_eff)
                if best is None or e["net_without_overlap"] < best[1]["net_without_overlap"]:
                    best = (al, e, r)
            al, e, r = best
            b_lo, b_hi = base["a91_bounds"]; r_lo, r_hi = r["a91_bounds"]
            other = e["net_without_overlap"] - e["hard_on_saved"]
            net_a91 = [w(other + (r_lo - b_lo)), w(other + (r_hi - b_hi))]   # A91's lower / upper loss bound as the saving
            row = {"dead_time": dead, "net_w_with_a91_lower_upper_bound": net_a91, "q_excursion_nc": r["q_excursion"] * 1e9, "lr_nh": lr, "vm_v": vm, "alpha": al, "vds_on_v": r["vds_on"], "t_hs_on_ns": r["t_hs_on_ns"],
                   "ir_max_a": r["ir_max"], "ir_min_a": r["ir_min"], "ir_at_hs_off_a": r["ir_hs_off"], "i_hs_off_a": r["i_hs_off"],
                   "low_on_vds_v": r["low_on_vds"], "t_fall_ns": r["t_fall_ns"], "t_tail_ns": r["t_tail_ns"], "tail_ok": r["tail_ok"],
                   "q_aux_nc": r["q_aux"] * 1e9, "int_ir2_ua2s": r["int_ir2"] * 1e6,
                   "energy_nj": {kk: ([fmt(x) for x in v] if isinstance(v, tuple) else fmt(v)) for kk, v in e.items()},
                   "power_w": {kk: ([w(x) for x in v] if isinstance(v, tuple) else w(v)) for kk, v in e.items()}}
            cyc.append(row)
            nr = row["power_w"]["net_range"]
            print(f"   [{dead:7s}] Lr {lr:4.2f} nH: Vm* {vm:5.2f} V, alpha {al}, V_DS {r['vds_on']:+5.2f} V at {r['t_hs_on_ns']:4.2f} ns, "
                  f"i_r {r['ir_max']:+5.1f}/{r['ir_min']:+5.1f} A, HS off {r['i_hs_off']:5.1f} A, LS on {r['low_on_vds']:+5.2f} V "
                  f"(fall {r['t_fall_ns']:.2f} ns)")
            print("        " + ", ".join(f"{kk} {v:+.0f}" for kk, v in row["energy_nj"].items() if not isinstance(v, list))
                  + f" nJ | net {nr[0]:+.2f}..{nr[1]:+.2f} W (negative = saving); with A91's bounds {net_a91[0]:+.2f} / {net_a91[1]:+.2f} W;"
                  f" Cm swing {r['q_excursion'] * 1e9:.0f} nC, tail ok {r['tail_ok']} ({r['t_tail_ns']:.1f} ns)")
    out["cycle"] = cyc

    print("\n5. timing (retuned dead time, the balanced Vm of each Lr)")
    tim = []
    for row in [c for c in cyc if c["dead_time"] == "retuned"]:
        lr, vm = row["lr_nh"] * 1e-9, row["vm_v"]
        a = AuxBranch(lr, "cm", vm=vm, alpha=row["alpha"], r_lr=R_LR)
        offs = []
        for d in (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0):
            if d < 0:
                r = m.cycle(I_NEG, a, i_pk=i_pk, x_low=x_low, i_r0=vm / lr * (-d * 1e-9))
            else:
                r = m.cycle(I_NEG, a, i_pk=i_pk, x_low=x_low, t_bds=d * 1e-9)
            offs.append({"offset_ns": d, "vds_on_v": r["vds_on"], "e_hard_on_nj": r["e_hard_on"] * 1e9, "q_aux_nc": r["q_aux"] * 1e9})
        win = m.turn_on_timing(I_NEG, a)
        tim.append({"lr_nh": row["lr_nh"], "bds_offset": offs, "hs_turn_on_timing": win})
        print(f"   Lr {row['lr_nh']:4.2f} nH: V_DS at HS turn-on for BDS offset -1..+2 ns: "
              + ", ".join(f"{o['offset_ns']:+.2f}: {o['vds_on_v']:+.2f}" for o in offs)
              + (" | HS turn-on early/late by 0.25, 0.5, 1 ns: " + ", ".join(
                  f"{r['early_e_nj']:.0f}/{r['late_e_nj']:.0f}" for r in win["rows"]) + " nJ" if win else " | x does not reach the rail"))
    out["timing"] = tim

    print("\n6. per-phase predictions for the co-simulation (retuned dead time, a capacitor Cm per phase)")
    pred = {}
    for name, lr_nh, al in (("zvs_0p75nH", 0.75, 0.3), ("partial_1p25nH", 1.25, 0.25)):
        rows = []
        for ph, ckt in enumerate(ckts, 1):
            mp = Model(ckt)
            i_neg = -orbit["lowoff_i"][ph - 1]
            b = mp.cycle(i_neg)
            ceff = float(mp.cnode(np.linspace(0, ckt.v_rail, 200)).mean())
            a = AuxBranch(lr_nh * 1e-9, "cm", alpha=al, r_lr=R_LR)
            vm = mp.balance_vm(i_neg, a, i_pk=b["i_hs_off"], x_low=b["low_on_vds"])
            a = replace(a, vm=vm)
            r = mp.cycle(i_neg, a, i_pk=b["i_hs_off"], x_low=b["low_on_vds"])
            e = losses(mp, b, r, a, ceff)
            fp = 1.0 / (ckt.period_ns * 1e-9)
            rows.append({"phase": ph, "vm_v": vm, "vds_on_v": r["vds_on"], "t_hs_on_ns": r["t_hs_on_ns"],
                         "baseline_vds_on_v": b["vds_on"], "baseline_t_hs_on_ns": b["t_hs_on_ns"],
                         "ir_max_a": r["ir_max"], "ir_min_a": r["ir_min"], "i_hs_off_a": r["i_hs_off"],
                         "baseline_i_hs_off_a": b["i_hs_off"], "dead_time_low_ns": r["t_fall_ns"],
                         "baseline_dead_time_low_ns": b["t_fall_ns"], "low_on_vds_v": r["low_on_vds"],
                         "t_tail_ns": r["t_tail_ns"], "q_excursion_nc": r["q_excursion"] * 1e9,
                         "net_w_per_phase": [x * fp for x in e["net_range"]],
                         "hard_on_saved_w_per_phase": e["hard_on_saved"] * fp})
            print(f"   {name} phase {ph}: Vm* {vm:.2f} V, V_DS {r['vds_on']:+.2f} V at {r['t_hs_on_ns']:.2f} ns (baseline {b['vds_on']:.2f} V), "
                  f"i_r {r['ir_max']:+.1f}/{r['ir_min']:+.1f} A, HS off {r['i_hs_off']:.1f} A (baseline {b['i_hs_off']:.1f}), "
                  f"low dead time {r['t_fall_ns']:.2f} ns (baseline {b['t_fall_ns']:.2f}), net {rows[-1]['net_w_per_phase'][0]:+.2f}..{rows[-1]['net_w_per_phase'][1]:+.2f} W")
        tot = [sum(rr["net_w_per_phase"][j] for rr in rows) for j in (0, 1)]
        pred[name] = {"lr_nh": lr_nh, "alpha": al, "r_lr_ohm": R_LR, "phases": rows, "net_w_four_phases": tot}
        print(f"   {name}: four phases net {tot[0]:+.2f}..{tot[1]:+.2f} W")
    out["per_phase"] = pred
    path = DIAG / "D56_aux_commutation_5p0pct.json"
    path.write_text(json.dumps(out, indent=1, default=float))
    print(f"\nwrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
