"""A101 analysis: the auxiliary commutation branch in the Verilog co-simulation against the reference run (no branch)
and against D56's registered predictions (d56_predictions.json, BOUNDARY Section 7).

Per phase, over the last 200 phase-1 periods: Cm's voltage, the high side's turn-on V_DS, the branch current extremes,
the phase and branch currents at the high-side turn-off, the low side's turn-on V_DS, the ripple (peak at the
high-side turn-off minus the valley at the low-side turn-off) and the mean of peak and valley, Vo; Cm's settling
from 0 V. Loss bookkeeping per cycle and phase, with D56's formulas on measured quantities: the hard turn-on from
each turn-on's V_DS (p24_aux_commutation.Model.hard_on_energy of that phase), branch conduction from the recorded
int i^2 dt, reverse conduction from the recorded energies, BDS gate and Coss at the measured Vm, the turn-off overlap
range at the measured currents; the main switches' extra conduction is D56's (not measured). Writes a101_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.extensions.p24_aux_commutation import QG, VGATE, Model, phase_circuits, turn_off_overlap  # noqa: E402

N, LAST = 4, 200
ORBIT = PROJECT / "symbolic_derivations" / "03_P24_native" / "diagnostics" / "D51_orbit_5p0pct_m0p0.json"


def load(name):
    p = HERE / "cosim" / f"run_{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def per_phase(recs, key, k, n=LAST):
    v = [r[key] for r in recs if r["phase"] == k + 1]
    return np.array(v[-n:]) if v else np.array([np.nan])


def stats(d, models):
    sec = d["sections"][-LAST:]
    t = np.array([s["t_s"] for s in sec])
    period = float(np.mean(np.diff(t)))
    out = {"status": d["status"], "t_end_us": d["t_end_s"] * 1e6, "overlaps": d["overlaps"], "ipk_a": d["ipk_a"],
           "period_ns": period * 1e9, "vo_mean_v": float(np.mean([s["vo"] for s in sec])), "phases": []}
    hoffs = d.get("highoffs_last", [])
    rev = np.array([s["rev_energy_j"] for s in sec]).mean(axis=0)          # per cycle, per switch
    for k in range(N):
        von = per_phase(d["turnons_last"], "vds_v", k)
        lon = per_phase(d["lowons_last"], "vds_v", k)
        valley = per_phase(d["lowoffs_last"], "i_a", k)
        ph = {"hs_on_vds_mean_v": float(von.mean()), "hs_on_vds_max_v": float(von.max()),
              "ls_on_vds_max_v": float(lon.max()), "ls_on_vds_mean_v": float(lon.mean()),
              "i_lowoff_mean_a": float(valley.mean()),
              "e_hard_on_nj": float(np.mean([models[k].hard_on_energy(models[k].ckt.v_rail - v) for v in von])) * 1e9,
              "rev_e_hs_nj": float(rev[k]) * 1e9, "rev_e_ls_nj": float(rev[N + k]) * 1e9}
        if hoffs:
            ia = per_phase(hoffs, "i_a", k); ib = per_phase(hoffs, "i_aux_a", k)
            ph.update(i_peak_mean_a=float(ia.mean()), i_aux_hs_off_mean_a=float(ib.mean()),
                      i_hs_off_mean_a=float((ia - ib).mean()), ripple_pp_a=float(ia.mean() - valley.mean()),
                      i_mid_a=float(0.5 * (ia.mean() + valley.mean())))
        if "aux_params" in d and k + 1 in d["aux_params"]["phases"]:
            a = d["aux_params"]["phases"].index(k + 1)
            vm = np.array([s["vm_v"][a] for s in sec])
            ph.update(vm_mean_v=float(vm.mean()), vm_pp_v=float(vm.max() - vm.min()),
                      ir_max_a=float(np.mean([s["aux_imax_a"][a] for s in sec])),
                      ir_min_a=float(np.mean([s["aux_imin_a"][a] for s in sec])),
                      int_ir2_per_cycle=float(np.mean([s["aux_i2s"][a] for s in sec])))
            allv = np.array([s["vm_v"][a] for s in d["sections"]]); allt = np.array([s["t_s"] for s in d["sections"]])
            fin = vm.mean()
            outside = np.nonzero(np.abs(allv - fin) > 0.02 * fin)[0]
            ph["vm_settle_us"] = float(allt[outside[-1] + 1] * 1e6) if len(outside) and outside[-1] + 1 < len(allt) else None
        out["phases"].append(ph)
    return out


def bookkeeping(ref, run, cfg, models, d56):
    """Per cycle and phase (nJ), run against ref; positive = more loss."""
    aux = cfg["aux"]
    r_aux = 2 * aux["rds_on_mohm"] * 1e-3 / aux["alpha"] + aux["r_lr_mohm"] * 1e-3
    c_eff = 13.5e-9
    rows = []
    for k in range(N):
        a, b, m = run["phases"][k], ref["phases"][k], models[k]
        e = {"hard_on": a["e_hard_on_nj"] - b["e_hard_on_nj"],
             "aux_conduction": a["int_ir2_per_cycle"] * r_aux * 1e9,
             "reverse_conduction": (a["rev_e_hs_nj"] + a["rev_e_ls_nj"]) - (b["rev_e_hs_nj"] + b["rev_e_ls_nj"]),
             "bds_gate": 2 * aux["alpha"] * QG * VGATE * 1e9,
             "bds_coss": aux["alpha"] * 2 * m.eoss(a["vm_mean_v"]) * 1e9,
             "main_conduction_d56": d56[k]["main_conduction_nj"]}
        lo = (turn_off_overlap(a["i_hs_off_mean_a"], c_eff, 0.5e-9) - turn_off_overlap(b["i_peak_mean_a"], c_eff, 0.5e-9)) * 1e9
        hi = (turn_off_overlap(a["i_hs_off_mean_a"], c_eff, 1.0e-9) - turn_off_overlap(b["i_peak_mean_a"], c_eff, 1.0e-9)) * 1e9
        core = sum(e.values())
        e.update(turn_off_overlap_range=[lo, hi], net_range=[core + lo, core + hi])
        rows.append(e)
    f = 1.0 / (run["period_ns"] * 1e-9)
    tot = [sum(r["net_range"][j] for r in rows) * 1e-9 * f for j in (0, 1)]
    return {"per_phase_nj": rows, "net_w_four_phases": tot, "frequency_mhz": f * 1e-6}


def main():
    orbit = json.loads(ORBIT.read_text())
    models = [Model(c) for c in phase_circuits(orbit)]
    pred = json.loads((HERE / "d56_predictions.json").read_text())
    d56 = json.loads((HERE.parents[1] / "derivations" / "diagnostics" / "D56_aux_commutation_5p0pct.json").read_text())
    main_cond = {}                                               # D56 phase-1 main-switch extra conduction, per design
    for row in d56["cycle"]:
        if row["dead_time"] == "retuned":
            e = row["energy_nj"]
            main_cond[row["lr_nh"]] = e["hs_conduction"] + e["ls_tail_conduction"]
    out = {"runs": {}, "against_d56": {}}
    ref_d = load("ref")
    if ref_d is None:
        print("no reference run yet"); return
    ref = stats(ref_d, models)
    out["runs"]["ref"] = ref
    print(f"ref: {ref['status']} to {ref['t_end_us']:.0f} us, overlaps {ref['overlaps']}, period {ref['period_ns']:.1f} ns, Vo {ref['vo_mean_v']:.4f} V")
    for k, ph in enumerate(ref["phases"]):
        print(f"   phase {k + 1}: HS on {ph['hs_on_vds_mean_v']:.2f} V (hard {ph['e_hard_on_nj']:.0f} nJ), LS on {ph['ls_on_vds_mean_v']:+.2f} V, "
              f"valley {ph['i_lowoff_mean_a']:+.2f} A" + (f", peak {ph['i_peak_mean_a']:.1f} A, ripple {ph['ripple_pp_a']:.1f} A" if "i_peak_mean_a" in ph else ""))
    runs = (("z075", "zvs_0p75nH"), ("p125", "partial_1p25nH"), ("z075_j30", "zvs_0p75nH"),     # registered
            ("dz_vz0", "zvs_0p75nH"), ("dz_lr100", None), ("dz_cm10", "zvs_0p75nH"), ("dz_ph1", None))  # diagnostics
    for name, design in runs:
        d = load(name)
        if d is None:
            continue
        cfg = json.loads((HERE / "cosim" / f"cfg_{name}.json").read_text())
        r = stats(d, models)
        out["runs"][name] = r
        print(f"\n{name}{' (diagnostic)' if name.startswith('dz_') else ''}: {r['status']} to {r['t_end_us']:.0f} us, "
              f"overlaps {r['overlaps']}, ipk {r['ipk_a']:.0f} A, period {r['period_ns']:.1f} ns, Vo {r['vo_mean_v']:.4f} V")
        if len(cfg["aux"].get("phases", [1, 2, 3, 4])) < N:
            print("   branch on some phases only: no bookkeeping")
            continue
        d56rows = [{"main_conduction_nj": main_cond[cfg["aux"]["lr_nh"]]} for _ in range(N)]
        bk = bookkeeping(ref, r, cfg, models, d56rows) if "i_peak_mean_a" in ref["phases"][0] else None
        r["bookkeeping"] = bk
        if design is None:
            for k, ph in enumerate(r["phases"]):
                print(f"   phase {k + 1}: Vm {ph['vm_mean_v']:.2f} V, HS on {ph['hs_on_vds_mean_v']:+.2f} V, i_r {ph['ir_max_a']:+.1f}/{ph['ir_min_a']:+.1f} A, "
                      f"HS off {ph['i_hs_off_mean_a']:.1f} A, LS on max {ph['ls_on_vds_max_v']:+.2f} V, ripple {ph['ripple_pp_a']:.1f} A, mid {ph['i_mid_a']:.1f} A")
            print(f"   net four phases {bk['net_w_four_phases'][0]:+.2f}..{bk['net_w_four_phases'][1]:+.2f} W; phase 1 (nJ): " + ", ".join(
                f"{kk} {v:+.0f}" if not isinstance(v, list) else f"{kk} {v[0]:+.0f}..{v[1]:+.0f}" for kk, v in bk["per_phase_nj"][0].items()))
            continue
        pp = pred[design]["phases"]
        checks = []
        for k, ph in enumerate(r["phases"]):
            q, b = pp[k], ref["phases"][k]
            c = {"vm": abs(ph["vm_mean_v"] - q["vm_v"]) <= 0.4,
                 "vds": (ph["hs_on_vds_mean_v"] <= 0.5) if design.startswith("zvs") else abs(ph["hs_on_vds_mean_v"] - q["vds_on_v"]) <= 0.5,
                 "ir": abs(ph["ir_max_a"] / q["ir_max_a"] - 1) <= 0.2 and abs(ph["ir_min_a"] / q["ir_min_a"] - 1) <= 0.2,
                 "i_hs_off": abs(ph["i_hs_off_mean_a"] - q["i_hs_off_a"]) <= 12,
                 "low_side": ph["ls_on_vds_max_v"] <= 0.0,
                 "ripple": ("ripple_pp_a" in b) and abs(ph["ripple_pp_a"] / b["ripple_pp_a"] - 1) <= 0.03,
                 "sharing": ("i_mid_a" in b) and abs(ph["i_mid_a"] - b["i_mid_a"]) <= 1.5,
                 "start": ph["vm_settle_us"] is not None}
            checks.append(c)
            print(f"   phase {k + 1}: Vm {ph['vm_mean_v']:.2f} V (pred {q['vm_v']:.2f}, p-p {ph['vm_pp_v']:.3f}, settled {ph['vm_settle_us']} us) | "
                  f"HS on {ph['hs_on_vds_mean_v']:+.2f} V (max {ph['hs_on_vds_max_v']:+.2f}; pred {q['vds_on_v']:+.2f}) | "
                  f"i_r {ph['ir_max_a']:+.1f}/{ph['ir_min_a']:+.1f} A (pred {q['ir_max_a']:+.1f}/{q['ir_min_a']:+.1f}) | "
                  f"HS off {ph['i_hs_off_mean_a']:.1f} A (pred {q['i_hs_off_a']:.1f}) | LS on max {ph['ls_on_vds_max_v']:+.2f} V | "
                  f"ripple {ph['ripple_pp_a']:.1f} A (ref {b.get('ripple_pp_a', float('nan')):.1f}) | mid {ph['i_mid_a']:.1f} A (ref {b.get('i_mid_a', float('nan')):.1f})")
            print("      " + ", ".join(f"{kk} {'ok' if v else 'MISS'}" for kk, v in c.items()))
        vo_ok = abs(r["vo_mean_v"] - ref["vo_mean_v"]) <= 0.005
        out["against_d56"][name] = {"per_phase": checks, "vo": vo_ok, "overlaps": r["overlaps"] == 0,
                                    "all": vo_ok and r["overlaps"] == 0 and all(all(c.values()) for c in checks)}
        print(f"   Vo {'ok' if vo_ok else 'MISS'}; overall {'MEETS' if out['against_d56'][name]['all'] else 'MISSES'} the registered criteria")
        if bk:
            print(f"   loss per cycle, phase 1 (nJ): " + ", ".join(
                f"{kk} {v:+.0f}" if not isinstance(v, list) else f"{kk} {v[0]:+.0f}..{v[1]:+.0f}" for kk, v in bk["per_phase_nj"][0].items()))
            print(f"   net four phases {bk['net_w_four_phases'][0]:+.2f}..{bk['net_w_four_phases'][1]:+.2f} W "
                  f"(D56 central {pred[design]['net_w_four_phases_central'][0]:+.2f}..{pred[design]['net_w_four_phases_central'][1]:+.2f} W)")
    (HERE / "a101_summary.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
