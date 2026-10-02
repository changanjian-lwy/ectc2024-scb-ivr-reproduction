"""D57: scenarios for the auxiliary commutation branch (D56, A101) over the values its verdict rests on (A102).

    python3 extensions/aux_commutation_branch/scripts/p24_aux_scenarios.py

1. P24's 1-2% claim: the negative current a phase needs, without a branch, for the high side to reach zero voltage,
   over P24's own inductor values (Table I) and three node compositions; the capacitance 2% would allow.
2. Loss scenarios per design (phase 1 of the 5% orbit, retuned dead time, x 4 phases): the hard turn-on model x Lr's
   technology (its R) x the BDS gate supply's efficiency x the residual current at the opening. One at a time from
   the central case, both corners, and the full grid in the JSON.
3. Area against the main stage of the same technology.
4. Enable: D56's cycle with Cm at the balance, at 5 V (a gate-drive rail) and at 0 V.
5. Load: the balance at the load stepped by -62.5 / +62.5 A (the high-side turn-off current scaled with the
   average phase current; the low side turning on at the 5% baseline's voltage, as the controller's low-side
   corrector keeps it).
6. Per-phase predictions for A102's co-simulation: the designs at 5% (as D56) with Lr's R of P24 Table 2's substrate
   air core (p125); the 2% target (D51's 2% orbit).
Writes extensions/aux_commutation_branch/derivations/diagnostics/D57_aux_scenarios.json and A102's d57_predictions.json.
"""
from __future__ import annotations

import itertools
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # the project
EXT = Path(__file__).resolve().parents[1]           # this extension
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402

from scb_ivr.extensions.p24_aux_commutation import QG, VGATE, AuxBranch, EdgeCircuit, Model, losses, phase_circuits  # noqa: E402
from scb_ivr.extensions.p24_aux_scenarios import (LR_TECH, NODES, P24_LF_NH, P24_PEAK_A, area, first_cycle, hard_on,  # noqa: E402
                                       linear_floor, node_model, r_lr, required_i_neg, zcs_residual)
from scripts.p24_orbits import DIAG  # noqa: E402

A102 = EXT / "experiments" / "A102_aux_branch_scenarios"
OUT = EXT / "derivations" / "diagnostics"
N_PH = 4
I_NEG = 6.25
DESIGNS = {"z075": (0.75e-9, 0.3), "lr100": (1.0e-9, 0.25), "p125": (1.25e-9, 0.25)}
HARD_ON = ("a91_lower", "d56_central", "a91_upper")
ETAS = (1.0, 0.7, 0.5)
I_RES = (0.0, 2.0, 5.0)
CENTRAL = {"hard_on": "d56_central", "tech": "as_main_inductor", "eta": 1.0, "i_res": 0.0}
T_F = (0.5e-9, 1.0e-9)


def balanced(m, i_neg, lr, alpha, rr, i_pk=None, x_low=None):
    """D56's balanced cycle (Vm from Cm's charge balance) and its baseline; i_pk / x_low default to the baseline's."""
    base = m.cycle(i_neg) if i_pk is None else m.cycle(i_neg, i_pk=i_pk)
    kw = {"i_pk": base["i_hs_off"], "x_low": base["low_on_vds"] if x_low is None else x_low}
    a = AuxBranch(lr, "cm", alpha=alpha, r_lr=rr)
    vm = m.balance_vm(i_neg, a, **kw)
    a = replace(a, vm=vm)
    return base, m.cycle(i_neg, a, **kw), a, kw


def scenario_energy(m, base, r, a, e, c_eff, hard_model, eta, i_res):
    """Per-cycle net energy (J, positive = more loss) as (t_f 0.5 ns, t_f 1 ns)."""
    other = e["net_without_overlap"] - e["hard_on_saved"] - e["bds_gate"]
    saved = hard_on(m, r["vds_on"], hard_model) - hard_on(m, base["vds_on"], hard_model)
    core = other + saved + e["bds_gate"] / eta + zcs_residual(m, a.lr, a.alpha, a.vm, i_res)["energy_j"]
    return [core + x for x in e["turn_off_overlap_range"]], saved


def main():
    m0 = Model()
    k0 = m0.ckt
    f0 = 1.0 / (k0.period_ns * 1e-9)
    w = lambda e: e * f0 * N_PH
    c_eff = float(m0.cnode(np.linspace(0, k0.v_rail, 200)).mean())
    out = {"conditions": {"orbit": "D51_orbit_5p0pct_m0p0.json, phase 1 (Sections 2-5), all phases (Section 6)",
                          "i_neg_a": I_NEG, "v_rail_v": k0.v_rail, "lf_nh": k0.lf * 1e9, "period_ns": k0.period_ns,
                          "phases": N_PH, "c_eff_nf": c_eff * 1e9, "p24_peak_a": P24_PEAK_A,
                          "lr_tech_ohm_per_h": LR_TECH, "turn_off_fall_s": T_F}}

    print("1. P24's 1-2%: negative current for zero voltage without a branch (% of the 125 A peak)")
    claim = []
    for lname, lf in P24_LF_NH.items():
        for nname, (nh, nl, nn) in NODES.items():
            ckt = replace(k0, lf=lf * 1e-9, n_h=nh, n_l=nl, n_next=nn)
            i = required_i_neg(ckt)
            mm = node_model(ckt)
            xs = np.linspace(0, ckt.v_rail, 400)
            ceq = float(np.trapezoid(mm.cnode(xs), xs)) / ckt.v_rail
            c2 = lf * 1e-9 * (0.02 * P24_PEAK_A) ** 2 / (ckt.v_rail ** 2 - 2 * ckt.v_rail * ckt.vo)
            row = {"lf": lname, "lf_nh": lf, "node": nname, "i_req_a": i, "pct_of_peak": 100 * i / P24_PEAK_A,
                   "c_eq_nf": ceq * 1e9, "i_req_linear_a": linear_floor(lf * 1e-9, ceq, ckt.v_rail, ckt.vo),
                   "c_allowed_by_2pct_pf": c2 * 1e12, "c_ratio_needed": ceq / c2,
                   "vds_at_2pct_v": mm.valley_free(0.02 * P24_PEAK_A, t_max=200e-9)[1],
                   "vds_at_5pct_v": mm.valley_free(0.05 * P24_PEAK_A, t_max=200e-9)[1]}
            claim.append(row)
            print(f"   {lname:15s} ({lf:6.3f} nH) {nname:22s}: {i:6.2f} A = {row['pct_of_peak']:5.1f}%; C_eq {ceq * 1e9:5.2f} nF, "
                  f"2% allows {c2 * 1e12:5.0f} pF (x{row['c_ratio_needed']:4.0f}); valley at 2% {row['vds_at_2pct_v']:5.2f} V, 5% {row['vds_at_5pct_v']:5.2f} V")
    out["p24_claim"] = claim

    print("\n2. loss scenarios (phase 1 x 4 phases, W; negative = saving)")
    loss = {}
    cyc = {}
    for dn, (lr, al) in DESIGNS.items():
        loss[dn] = {"grid": [], "tech": {}}
        for tech in LR_TECH:
            rr = r_lr(tech, lr)
            base, r, a, kw = balanced(m0, I_NEG, lr, al, rr)
            e = losses(m0, base, r, a, c_eff, T_F)
            cyc[(dn, tech)] = (base, r, a, e)
            loss[dn]["tech"][tech] = {"r_lr_mohm": rr * 1e3, "vm_v": a.vm, "vds_on_v": r["vds_on"], "ir_max_a": r["ir_max"],
                                      "ir_min_a": r["ir_min"], "aux_conduction_w": w(e["aux_conduction"]),
                                      "int_ir2_a2s": r["int_ir2"]}
        for hm, tech, eta, ires in itertools.product(HARD_ON, LR_TECH, ETAS, I_RES):
            base, r, a, e = cyc[(dn, tech)]
            net, saved = scenario_energy(m0, base, r, a, e, c_eff, hm, eta, ires)
            loss[dn]["grid"].append({"hard_on": hm, "tech": tech, "eta": eta, "i_res": ires,
                                     "net_w": [w(x) for x in net], "hard_on_saved_w": w(saved)})
        g = loss[dn]["grid"]
        pick = lambda **c: next(x for x in g if all(x[kk] == v for kk, v in c.items()))
        cen = pick(**CENTRAL)
        print(f"   {dn} (Lr {lr * 1e9:.2f} nH, alpha {al}): central {cen['net_w'][0]:+.2f}..{cen['net_w'][1]:+.2f} W "
              f"(hard turn-on saved {cen['hard_on_saved_w']:+.2f} W)")
        oat = {}
        for key, vals in (("hard_on", HARD_ON), ("tech", tuple(LR_TECH)), ("eta", ETAS), ("i_res", I_RES)):
            for v in vals:
                c = dict(CENTRAL, **{key: v})
                x = pick(**c)
                oat[f"{key}={v}"] = x["net_w"]
            print("      " + key + ": " + ", ".join(f"{v}: {pick(**dict(CENTRAL, **{key: v}))['net_w'][1]:+.2f}" for v in vals))
        best = pick(hard_on="a91_upper", tech="a101_fixed_0p2mohm", eta=1.0, i_res=0.0)
        worst = pick(hard_on="a91_lower", tech="p24_t2_substrate_air", eta=0.5, i_res=5.0)
        loss[dn].update(central=cen, one_at_a_time=oat, optimistic=best, pessimistic=worst,
                        n_saving=sum(1 for x in g if x["net_w"][1] < 0), n_grid=len(g))
        print(f"      corners: optimistic {best['net_w'][0]:+.2f} W, pessimistic {worst['net_w'][1]:+.2f} W; "
              f"saving in {loss[dn]['n_saving']} of {len(g)} grid cases (t_f 1 ns)")
        for tech, t in loss[dn]["tech"].items():
            print(f"      Lr {tech:22s}: R {t['r_lr_mohm']:5.2f} mOhm, Vm {t['vm_v']:5.2f} V, V_DS {t['vds_on_v']:+5.2f} V, "
                  f"i_r {t['ir_max_a']:+5.1f}/{t['ir_min_a']:+5.1f} A, branch conduction {t['aux_conduction_w']:.2f} W")
        z = {i: zcs_residual(m0, lr, al, loss[dn]['tech']['as_main_inductor']['vm_v'], i) for i in I_RES}
        loss[dn]["zcs"] = {str(i): {"energy_nj": v["energy_j"] * 1e9, "overshoot_v": v["overshoot_v"]} for i, v in z.items()}
        print("      residual current at the opening: " + ", ".join(
            f"{i:.0f} A -> {v['energy_j'] * 1e9:.1f} nJ, ring {v['overshoot_v']:.1f} V" for i, v in z.items()))
    out["loss"] = loss

    print("\n3. area (per phase; the main stage of the same technology)")
    vcs = [35.792569779918395, 23.88268463001492, 11.963681917756546]
    ar = {}
    for dn, (lr, al) in DESIGNS.items():
        base, r, a, e = cyc[(dn, "as_main_inductor")]
        ipk, ineg = base["i_hs_off"], I_NEG
        if_rms = float(np.sqrt((ipk ** 2 - ipk * ineg + ineg ** 2) / 3.0))      # triangle from -i_neg to i_pk and back
        ir_rms = float(np.sqrt(r["int_ir2"] / (k0.period_ns * 1e-9)))
        ir_pk = max(abs(r["ir_max"]), abs(r["ir_min"]))
        x = area(lr, ir_pk, ir_rms, k0.lf, ipk, if_rms, al, 1e-6, [a.vm] * N_PH, 3e-6, vcs)
        x.update(ir_peak_a=ir_pk, ir_rms_a=ir_rms, if_peak_a=ipk, if_rms_a=if_rms,
                 cm_0p22uF_vs_series_caps=x["cm_vs_series_caps"] * 0.22)
        ar[dn] = x
        print(f"   {dn}: BDS dies {x['bds_dies_mm2']:.1f} mm^2 = {100 * x['bds_vs_main_dies']:.0f}% of the main dies (46.3 mm^2); "
              f"Lr {100 * x['lr_vs_lf_by_peak_energy']:.1f}% of Lf by peak energy ({ir_pk:.0f} vs {ipk:.0f} A), "
              f"{100 * x['lr_vs_lf_by_rms']:.1f}% by L I_rms^2 ({ir_rms:.1f} vs {if_rms:.1f} A); "
              f"Cm (1 uF) {100 * x['cm_vs_series_caps']:.1f}% of the series capacitors' C V^2 (0.22 uF: {100 * x['cm_0p22uF_vs_series_caps']:.1f}%)")
    out["area"] = ar

    print("\n4. enable: the first cycle with Cm at the balance, 5 V, 0 V (Cm 1 uF)")
    en = {}
    for dn, (lr, al) in DESIGNS.items():
        base, r, a, e = cyc[(dn, "a101_fixed_0p2mohm")]
        en[dn] = {}
        for lab, vm0 in (("balance", a.vm), ("5V", 5.0), ("0V", 0.0)):
            c = first_cycle(m0, I_NEG, a, vm0, base["i_hs_off"], base["low_on_vds"])
            row = {"vm0_v": vm0, "vds_on_v": c["vds_on"], "ir_max_a": c["ir_max"], "ir_min_a": c["ir_min"],
                   "tail_ok": c["tail_ok"], "t_tail_ns": c["t_tail_ns"], "dvm_per_cycle_v": -c["q_aux"] / 1e-6,
                   "cycles_to_balance": (a.vm - vm0) / (-c["q_aux"] / 1e-6) if c["q_aux"] < 0 else None}
            en[dn][lab] = row
            print(f"   {dn} Cm {vm0:5.2f} V: V_DS {c['vds_on']:+5.2f} V, i_r {c['ir_max']:+6.1f}/{c['ir_min']:+6.1f} A, tail "
                  f"{'ok' if c['tail_ok'] else 'NOT back to zero'} ({c['t_tail_ns']:.0f} ns), dVm {row['dvm_per_cycle_v']:+.3f} V/cycle"
                  + (f", ~{row['cycles_to_balance']:.0f} cycles to the balance" if row["cycles_to_balance"] else ""))
    out["enable"] = en

    print("\n5. load stepped by -62.5 / +62.5 A (phase 1, the turn-off current scaled with the phase's average)")
    ld = {}
    base0 = m0.cycle(I_NEG)
    i_avg0 = 62.5
    for dn in ("z075", "p125"):
        lr, al = DESIGNS[dn]
        ld[dn] = {}
        for di in (-62.5, 0.0, 62.5):
            i_avg = i_avg0 + di / N_PH
            i_pk = (base0["i_hs_off"] + I_NEG) * i_avg / i_avg0 - I_NEG       # triangle: average ~ (i_pk - i_neg) / 2
            base, r, a, kw = balanced(m0, I_NEG, lr, al, 0.2e-3, i_pk=i_pk, x_low=base0["low_on_vds"])
            ld[dn][str(di)] = {"i_pk_a": i_pk, "vm_v": a.vm, "vds_on_v": r["vds_on"], "ir_max_a": r["ir_max"],
                               "ir_min_a": r["ir_min"], "low_on_vds_v": r["low_on_vds"], "i_hs_off_a": r["i_hs_off"]}
            print(f"   {dn} step {di:+6.1f} A: HS off {i_pk:5.1f} A -> Vm {a.vm:5.2f} V, V_DS {r['vds_on']:+5.2f} V, "
                  f"i_r {r['ir_max']:+5.1f}/{r['ir_min']:+5.1f} A, LS on {r['low_on_vds']:+5.2f} V")
    out["load"] = ld

    print("\n6. per-phase predictions for A102")
    pred = {"conditions": {"retuned dead time": True, "cm_uf": 1.0}}

    def per_phase(orbit, lr, al, rr):
        rows = []
        for ph, ckt in enumerate(phase_circuits(orbit), 1):
            mp = Model(ckt)
            i_neg = -orbit["lowoff_i"][ph - 1]
            ce = float(mp.cnode(np.linspace(0, ckt.v_rail, 200)).mean())
            base, r, a, kw = balanced(mp, i_neg, lr, al, rr)
            e = losses(mp, base, r, a, ce, T_F)
            fp = 1.0 / (ckt.period_ns * 1e-9)
            rows.append({"phase": ph, "i_neg_a": i_neg, "vm_v": a.vm, "vds_on_v": r["vds_on"], "baseline_vds_on_v": base["vds_on"],
                         "ir_max_a": r["ir_max"], "ir_min_a": r["ir_min"], "i_hs_off_a": r["i_hs_off"],
                         "low_on_vds_v": r["low_on_vds"], "q_excursion_nc": r["q_excursion"] * 1e9,
                         "net_w_per_phase": [x * fp for x in e["net_range"]]})
        return rows

    o5 = json.loads((DIAG / "D51_orbit_5p0pct_m0p0.json").read_text())
    rr_air = r_lr("p24_t2_substrate_air", DESIGNS["p125"][0])
    pred["p125_lr_air"] = {"lr_nh": 1.25, "alpha": 0.25, "r_lr_ohm": rr_air,
                           "phases": per_phase(o5, DESIGNS["p125"][0], 0.25, rr_air)}
    o2p = DIAG / "D51_orbit_2p0pct_m0p0.json"
    if o2p.exists():
        o2 = json.loads(o2p.read_text())
        pred["orbit_2pct"] = {k: o2[k] for k in ("status", "ton_ns", "period_ns", "lowoff_i", "turnon_vds", "low_on_vds")}
        for dn in ("z075", "p125"):
            lr, al = DESIGNS[dn]
            pred[f"{dn}_2pct"] = {"lr_nh": lr * 1e9, "alpha": al, "r_lr_ohm": 0.2e-3, "phases": per_phase(o2, lr, al, 0.2e-3)}
    pred["enable"] = en
    pred["load"] = ld
    pred["cm_0p22uF_vm_excursion_v"] = [rw["q_excursion_nc"] * 1e-9 / 0.22e-6 for rw in per_phase(o5, 1.25e-9, 0.25, 0.2e-3)]
    for key, p in pred.items():
        if isinstance(p, dict) and "phases" in p:
            tot = [sum(rw["net_w_per_phase"][j] for rw in p["phases"]) for j in (0, 1)]
            p["net_w_four_phases"] = tot
            print(f"   {key}: " + "; ".join(f"ph{rw['phase']} Vm {rw['vm_v']:.2f} V, V_DS {rw['vds_on_v']:+.2f} V (no branch {rw['baseline_vds_on_v']:.2f}), "
                                          f"i_r {rw['ir_max_a']:+.1f}/{rw['ir_min_a']:+.1f} A" for rw in p["phases"])
                  + f" | net {tot[0]:+.2f}..{tot[1]:+.2f} W")
    print(f"   Cm 0.22 uF: Vm excursion within a cycle {', '.join(f'{v:.2f}' for v in pred['cm_0p22uF_vm_excursion_v'])} V")
    out["predictions"] = pred
    (OUT / "D57_aux_scenarios.json").write_text(json.dumps(out, indent=1, default=float))
    A102.mkdir(parents=True, exist_ok=True)
    (A102 / "d57_predictions.json").write_text(json.dumps(pred, indent=1, default=float))
    print(f"\nwrote {(OUT / 'D57_aux_scenarios.json').relative_to(ROOT)} and {(A102 / 'd57_predictions.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
