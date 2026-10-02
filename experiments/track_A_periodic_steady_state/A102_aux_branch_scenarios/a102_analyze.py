"""A102 analysis: the auxiliary commutation branch over its assumed values, in the Verilog co-simulation, against the
registered criteria (BOUNDARY Section 5) and D57's predictions (d57_predictions.json).

Per-phase statistics are A101's (a101_analyze.stats, imported unchanged): over the last 200 phase-1 periods, or over a
time window (window()). Families:
- enable (e*): peak branch current after the enable, Vo range, Vm and high-side V_DS settling, the final state against
  A101's run of the same design;
- load steps (s*): Vo extreme against A100's reference for the same step, the branch current after against before,
  the state after the step against D57;
- the 2% target (ref_2pct, n*): against D51's 2% orbit and D57;
- realism (r125_lrair, c125_cm022).
Loss scenarios on measured quantities: A101's bookkeeping (a101_analyze.bookkeeping) with the hard turn-on under the
three models, a 50% gate supply and a 5 A residual; and a conduction estimate per phase (triangle from the valley to
the peak; Lf's R plus the duty-weighted switch R) for the 2%-against-5% comparison. Writes a102_summary.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src")); sys.path.insert(0, str(TA / "A101_aux_commutation_branch"))
from a101_analyze import bookkeeping, stats  # noqa: E402
from scb_ivr.p24_aux_commutation import QG, VGATE, Model, phase_circuits  # noqa: E402
from scb_ivr.p24_aux_scenarios import hard_on, zcs_residual  # noqa: E402

N, LAST = 4, 200
DIAG = PROJECT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
A101C, A100C, C = TA / "A101_aux_commutation_branch" / "cosim", TA / "A100_timed_turn_off_load_steps" / "cosim", HERE / "cosim"
FINAL = {"125": "p125", "075": "dz_vz0"}
LSB_NS = 4.0 / 128
R_L, R_HS, R_LS = 0.54e-3, 1.3e-3 / 2, 1.3e-3 / 3


def load(folder, name):
    p = folder / f"run_{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def cfg_of(folder, name):
    return json.loads((folder / f"cfg_{name}.json").read_text())


def window(d, t0, t1):
    """The run restricted to [t0, t1): sections and records."""
    dd = dict(d)
    dd["sections"] = [s for s in d["sections"] if t0 <= s["t_s"] < t1]
    for k in ("turnons_last", "lowoffs_last", "lowons_last", "highoffs_last"):
        dd[k] = [r for r in d.get(k, []) if t0 <= r["t_s"] < t1]
    return dd


def aux_peak(secs):
    if not secs or "aux_imax_a" not in secs[0]:
        return 0.0
    return float(max(max(max(s["aux_imax_a"]), -min(s["aux_imin_a"])) for s in secs))


def cond_w(ph, ton_ns, period_ns):
    """Main conduction per phase (W): triangle from the valley to the peak, Lf's R plus the duty-weighted switches."""
    a, b = ph["i_peak_mean_a"], ph["i_lowoff_mean_a"]
    rms2 = (a * a + a * b + b * b) / 3.0
    dty = ton_ns / period_ns
    return rms2 * (R_L + dty * R_HS + (1 - dty) * R_LS)


def scenarios(ref_d, run_d, ref, run, cfg, models, main_cond):
    """Net (W, four phases, t_f 1 ns) under the three hard turn-on models; with a 50% gate supply; with 5 A residual."""
    bk = bookkeeping(ref, run, cfg, models, [{"main_conduction_nj": main_cond}] * N)
    f = bk["frequency_mhz"] * 1e6
    out = {"bookkeeping_central": bk["net_w_four_phases"]}
    aux = cfg["aux"]
    for model in ("a91_lower", "d56_central", "a91_upper"):
        tot = 0.0
        for k in range(N):
            m = models[k]
            von_run = [r["vds_v"] for r in run_d["turnons_last"] if r["phase"] == k + 1][-LAST:]
            von_ref = [r["vds_v"] for r in ref_d["turnons_last"] if r["phase"] == k + 1][-LAST:]
            e_run = np.mean([hard_on(m, v, model) for v in von_run]) * 1e9
            e_ref = np.mean([hard_on(m, v, model) for v in von_ref]) * 1e9
            row = bk["per_phase_nj"][k]
            tot += (row["net_range"][1] - row["hard_on"] + (e_run - e_ref)) * 1e-9 * f
        out[model] = tot
    gate = 2 * aux["alpha"] * QG * VGATE
    out["gate_50pct"] = bk["net_w_four_phases"][1] + N * gate * f
    vm = np.mean([p["vm_mean_v"] for p in run["phases"]])
    out["residual_5a"] = bk["net_w_four_phases"][1] + N * zcs_residual(models[0], aux["lr_nh"] * 1e-9, aux["alpha"], vm, 5.0)["energy_j"] * f
    return out


def main():
    orbit5 = json.loads((DIAG / "D51_orbit_5p0pct_m0p0.json").read_text())
    orbit2 = json.loads((DIAG / "D51_orbit_2p0pct_m0p0.json").read_text())
    models5 = [Model(c) for c in phase_circuits(orbit5)]
    models2 = [Model(c) for c in phase_circuits(orbit2)]
    pred = json.loads((HERE / "d57_predictions.json").read_text())
    d56 = json.loads((DIAG / "D56_aux_commutation_5p0pct.json").read_text())
    main_cond = {r["lr_nh"]: r["energy_nj"]["hs_conduction"] + r["energy_nj"]["ls_tail_conduction"]
                 for r in d56["cycle"] if r["dead_time"] == "retuned"}
    out = {"enable": {}, "steps": {}, "two_pct": {}, "realism": {}, "loss_scenarios": {}, "conduction": {}}
    ref5_d = load(A101C, "ref"); ref5 = stats(ref5_d, models5)
    finals = {k: stats(load(A101C, v), models5) for k, v in FINAL.items()}

    print("1. enable at 200 us")
    for name in ("e125_5v", "e075_5v", "e125_pc", "e075_pc", "e125_0v", "e075_0v"):
        d = load(C, name)
        if d is None:
            continue
        dn = name[1:4]
        t_arm = d["aux_params"]["t_armed_s"]
        after = [s for s in d["sections"] if s["t_s"] >= t_arm]
        r = stats(d, models5)
        fin = finals[dn]
        pk = aux_peak(after)
        vo = [s["vo"] for s in after]
        e = {"status": r["status"], "overlaps": r["overlaps"], "t_armed_us": t_arm * 1e6, "peak_ir_a": pk,
             "vo_min_v": min(vo), "vo_max_v": max(vo)}
        # settling after the enable: Vm (sections) and the high side's V_DS (turn-on records, if they reach back)
        set_vm, set_vds = [], []
        for k in range(N):
            vmf = r["phases"][k]["vm_mean_v"]
            bad = [s["t_s"] for s in after if abs(s["vm_v"][k] - vmf) > 0.02 * vmf]
            set_vm.append(((max(bad) - t_arm) * 1e6) if bad else 0.0)
            ton = [x for x in d["turnons_last"] if x["phase"] == k + 1]
            vf = r["phases"][k]["hs_on_vds_mean_v"]
            if ton and ton[0]["t_s"] <= t_arm:
                bad = [x["t_s"] for x in ton if x["t_s"] >= t_arm and abs(x["vds_v"] - vf) > 0.3]
                set_vds.append(((max(bad) - t_arm) * 1e6) if bad else 0.0)
            else:
                set_vds.append(None)
        e.update(vm_settle_us=set_vm, vds_settle_us=set_vds)
        fs = {"vm": all(abs(r["phases"][k]["vm_mean_v"] - fin["phases"][k]["vm_mean_v"]) <= 0.1 for k in range(N)),
              "vds": all(abs(r["phases"][k]["hs_on_vds_mean_v"] - fin["phases"][k]["hs_on_vds_mean_v"]) <= 0.2 for k in range(N)),
              "ir": all(abs(r["phases"][k]["ir_max_a"] / fin["phases"][k]["ir_max_a"] - 1) <= 0.05
                        and abs(r["phases"][k]["ir_min_a"] / fin["phases"][k]["ir_min_a"] - 1) <= 0.05 for k in range(N)),
              "low_side": all(p["ls_on_vds_max_v"] <= 0 for p in r["phases"]),
              "vo": abs(r["vo_mean_v"] - fin["vo_mean_v"]) <= 1e-3}
        key = "p125" if dn == "125" else "z075"
        lab = name.split("_")[1]
        fc = pred["enable"][key]["balance" if lab == "pc" else ("5V" if lab == "5v" else "0V")]
        fc_pk = max(abs(fc["ir_max_a"]), abs(fc["ir_min_a"]))
        fin_pk = max(max(abs(p["ir_max_a"]), abs(p["ir_min_a"])) for p in fin["phases"])
        crit = {"no_overlap_vo": r["overlaps"] == 0 and 0.95 <= min(vo) and max(vo) <= 1.05,
                "peak": (pk <= 1.3 * fin_pk) if lab == "pc" else ((abs(pk / fc_pk - 1) <= 0.3) if lab == "5v" else pk >= 0.7 * fc_pk),
                "settle": (max(set_vm) <= 50 and all(v is not None and v <= 50 for v in set_vds)) if lab != "0v" else None,
                "final_state": all(fs.values())}
        e.update(final_state_checks=fs, criteria=crit, d57_first_cycle_peak_a=fc_pk, final_peak_a=fin_pk, phases=r["phases"])
        out["enable"][name] = e
        print(f"   {name}: {r['status']}, overlaps {r['overlaps']}, armed {t_arm * 1e6:.2f} us; peak |i_r| {pk:.0f} A "
              f"(D57 first cycle {fc_pk:.0f}, final {fin_pk:.0f}); Vo {min(vo):.3f}-{max(vo):.3f} V; Vm settle "
              + "/".join(f"{x:.1f}" for x in set_vm) + " us; V_DS settle " + "/".join("n/a" if x is None else f"{x:.1f}" for x in set_vds) + " us")
        print("      final state vs A101: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in fs.items())
              + " | criteria: " + ", ".join(f"{k} {'-' if v is None else ('ok' if v else 'MISS')}" for k, v in crit.items()))

    print("\n2. load steps at 400 us")
    for name in ("s125_m62", "s125_p62", "s075_m62", "s075_p62"):
        d = load(C, name)
        if d is None:
            continue
        dn, tag = name[1:4], name.split("_")[1]
        refd = load(A100C, f"ref_{tag}")
        t_s = 400e-6
        pre, post = window(d, 350e-6, t_s), d
        rp, rq = stats(pre, models5), stats(post, models5)
        aft = [s for s in d["sections"] if s["t_s"] >= t_s]
        dv = [s["vo"] - 1.0 for s in aft]
        ext = max(dv, key=abs)
        rdv = [s["vo"] - 1.0 for s in refd["sections"] if s["t_s"] >= t_s]
        rext = max(rdv, key=abs)
        pk_pre, pk_post = aux_peak(pre["sections"]), aux_peak(aft)
        key = "p125" if dn == "125" else "z075"
        lp = pred["load"][key]["-62.5" if tag == "m62" else "62.5"]
        p1 = rq["phases"][0]
        settled = abs(rq["vo_mean_v"] - 1.0) <= 5e-3
        crit = {"no_overlap": d["overlaps"] == 0,
                "vo_extreme": abs(ext / rext - 1) <= 0.15,
                "peak": pk_post <= 1.5 * pk_pre,
                "vm": abs(p1["vm_mean_v"] - lp["vm_v"]) <= 0.5,
                "vds": (abs(p1["hs_on_vds_mean_v"] - lp["vds_on_v"]) <= 0.7) if dn == "125" else p1["hs_on_vds_mean_v"] <= 1.0,
                "low_side": all(p["ls_on_vds_max_v"] <= 0 for p in rq["phases"])}
        out["steps"][name] = {"status": d["status"], "overlaps": d["overlaps"], "vo_extreme_mv": ext * 1e3,
                              "a100_ref_vo_extreme_mv": rext * 1e3, "peak_ir_before_a": pk_pre, "peak_ir_after_a": pk_post,
                              "settled": settled, "vo_mean_after_v": rq["vo_mean_v"], "pre": rp["phases"], "post": rq["phases"],
                              "d57_phase1": lp, "criteria": crit, "period_ns_pre": rp["period_ns"], "period_ns_post": rq["period_ns"]}
        print(f"   {name}: {d['status']}, overlaps {d['overlaps']}; Vo extreme {ext * 1e3:+.1f} mV (A100 ref {rext * 1e3:+.1f}); "
              f"|i_r| peak {pk_pre:.0f} -> {pk_post:.0f} A; after: Vo {rq['vo_mean_v']:.4f} V ({'settled' if settled else 'NOT settled'})")
        for k in range(N):
            a, b = rp["phases"][k], rq["phases"][k]
            print(f"      phase {k + 1}: Vm {a['vm_mean_v']:.2f} -> {b['vm_mean_v']:.2f} V, HS V_DS {a['hs_on_vds_mean_v']:+.2f} -> "
                  f"{b['hs_on_vds_mean_v']:+.2f} V, LS on max {b['ls_on_vds_max_v']:+.2f} V, HS off {a['i_hs_off_mean_a']:.0f} -> {b['i_hs_off_mean_a']:.0f} A"
                  + (f"  (D57 phase 1: Vm {lp['vm_v']:.2f}, V_DS {lp['vds_on_v']:+.2f})" if k == 0 else ""))
        print("      criteria: " + ", ".join(f"{k} {'ok' if v else 'MISS'}" for k, v in crit.items()))

    print("\n3. the 2% target")
    r2d = load(C, "ref_2pct")
    if r2d is not None:
        r2 = stats(r2d, models2)
        ok = [abs(r2["phases"][k]["hs_on_vds_mean_v"] - orbit2["turnon_vds"][k]) <= 0.3 for k in range(N)]
        out["two_pct"]["ref_2pct"] = {"stats": r2, "soft_vs_d51": ok}
        print(f"   ref_2pct: {r2['status']}, overlaps {r2['overlaps']}, period {r2['period_ns']:.1f} ns, Vo {r2['vo_mean_v']:.4f} V; HS V_DS "
              + " / ".join(f"{p['hs_on_vds_mean_v']:.2f} (D51 {v:.2f})" for p, v in zip(r2["phases"], orbit2["turnon_vds"]))
              + f" -> {'ok' if all(ok) else 'MISS'}")
        for name, key in (("n125_2pct", "p125_2pct"), ("n075_2pct", "z075_2pct")):
            d = load(C, name)
            if d is None:
                continue
            r = stats(d, models2)
            pp = pred[key]["phases"]
            checks = []
            for k in range(N):
                ph, q, b = r["phases"][k], pp[k], r2["phases"][k]
                checks.append({"vm": abs(ph["vm_mean_v"] - q["vm_v"]) <= 0.4,
                               "vds": (ph["hs_on_vds_mean_v"] <= 0.5) if key.startswith("z") else abs(ph["hs_on_vds_mean_v"] - q["vds_on_v"]) <= 0.5,
                               "ir": abs(ph["ir_max_a"] / q["ir_max_a"] - 1) <= 0.2 and abs(ph["ir_min_a"] / q["ir_min_a"] - 1) <= 0.2,
                               "low_side": ph["ls_on_vds_max_v"] <= 0.0,
                               "ripple": abs(ph["ripple_pp_a"] / b["ripple_pp_a"] - 1) <= 0.03})
                print(f"   {name} phase {k + 1}: Vm {ph['vm_mean_v']:.2f} V (pred {q['vm_v']:.2f}), HS V_DS {ph['hs_on_vds_mean_v']:+.2f} V "
                      f"(pred {q['vds_on_v']:+.2f}), i_r {ph['ir_max_a']:+.1f}/{ph['ir_min_a']:+.1f} A (pred {q['ir_max_a']:+.1f}/{q['ir_min_a']:+.1f}), "
                      f"LS on max {ph['ls_on_vds_max_v']:+.2f} V, ripple {ph['ripple_pp_a']:.1f} A (ref {b['ripple_pp_a']:.1f}) | "
                      + ", ".join(f"{kk} {'ok' if v else 'MISS'}" for kk, v in checks[-1].items()))
            cfg = cfg_of(C, name)
            sc = scenarios(r2d, d, r2, r, cfg, models2, main_cond[cfg["aux"]["lr_nh"]])
            allok = d["overlaps"] == 0 and all(all(c.values()) for c in checks)
            out["two_pct"][name] = {"stats": r, "checks": checks, "all": allok, "loss": sc}
            out["loss_scenarios"][name] = sc
            print(f"   {name}: {'MEETS' if allok else 'MISSES'} the criteria; net vs ref_2pct (W): central {sc['bookkeeping_central'][0]:+.2f}..{sc['bookkeeping_central'][1]:+.2f}")

    print("\n4. realism")
    p125 = finals["125"]
    for name in ("r125_lrair", "c125_cm022"):
        d = load(C, name)
        if d is None:
            continue
        r = stats(d, models5)
        cfg = cfg_of(C, name)
        if name == "r125_lrair":
            pp = pred["p125_lr_air"]["phases"]
            checks = [{"vm": abs(r["phases"][k]["vm_mean_v"] - pp[k]["vm_v"]) <= 0.4,
                       "vds": abs(r["phases"][k]["hs_on_vds_mean_v"] - pp[k]["vds_on_v"]) <= 0.5,
                       "ir": abs(r["phases"][k]["ir_max_a"] / pp[k]["ir_max_a"] - 1) <= 0.2
                       and abs(r["phases"][k]["ir_min_a"] / pp[k]["ir_min_a"] - 1) <= 0.2} for k in range(N)]
        else:
            checks = [{"vm": abs(r["phases"][k]["vm_mean_v"] - p125["phases"][k]["vm_mean_v"]) <= 0.4,
                       "vds": abs(r["phases"][k]["hs_on_vds_mean_v"] - p125["phases"][k]["hs_on_vds_mean_v"]) <= 0.5} for k in range(N)]
        sc = scenarios(ref5_d, d, ref5, r, cfg, models5, main_cond[cfg["aux"]["lr_nh"]])
        allok = d["overlaps"] == 0 and all(all(c.values()) for c in checks)
        out["realism"][name] = {"stats": r, "checks": checks, "all": allok, "loss": sc}
        out["loss_scenarios"][name] = sc
        print(f"   {name}: {r['status']}, overlaps {r['overlaps']}, Vo {r['vo_mean_v']:.4f} V; "
              + "; ".join(f"ph{k + 1} Vm {p['vm_mean_v']:.2f} (pp {p['vm_pp_v']:.2f}) V, V_DS {p['hs_on_vds_mean_v']:+.2f} V, i_r {p['ir_max_a']:+.1f}/{p['ir_min_a']:+.1f} A"
                        for k, p in enumerate(r["phases"]))
              + f" | {'MEETS' if allok else 'MISSES'}; net central {sc['bookkeeping_central'][0]:+.2f}..{sc['bookkeeping_central'][1]:+.2f} W")

    print("\n5. loss scenarios on measured quantities (W, four phases, t_f 1 ns; negative = saving)")
    for name in ("p125", "dz_lr100", "dz_vz0"):
        d = load(A101C, name)
        cfg = cfg_of(A101C, name)
        r = stats(d, models5)
        out["loss_scenarios"][f"a101_{name}"] = scenarios(ref5_d, d, ref5, r, cfg, models5, main_cond[cfg["aux"]["lr_nh"]])
    for name, sc in out["loss_scenarios"].items():
        print(f"   {name:12s}: A91 lower {sc['a91_lower']:+.2f}, central {sc['d56_central']:+.2f}, A91 upper {sc['a91_upper']:+.2f}; "
              f"gate supply 50% {sc['gate_50pct']:+.2f}; residual 5 A {sc['residual_5a']:+.2f}")

    print("\n6. 2% against 5%: main conduction (triangle estimate) and hard turn-on (central), W, four phases")
    rows = {"ref_5pct": (ref5_d, ref5, models5), "ref_2pct": (r2d, out["two_pct"].get("ref_2pct", {}).get("stats"), models2)}
    for name, (d, r, models) in rows.items():
        if r is None:
            continue
        ton = np.mean([s["ton_lsb"] for s in d["sections"][-LAST:]]) * LSB_NS
        pc = sum(cond_w(p, ton, r["period_ns"]) for p in r["phases"])
        ph = sum(p["e_hard_on_nj"] for p in r["phases"]) * 1e-9 / (r["period_ns"] * 1e-9)
        out["conduction"][name] = {"cond_w": pc, "hard_on_central_w": ph, "period_ns": r["period_ns"], "ton_ns": ton}
        print(f"   {name}: conduction {pc:.2f} W, hard turn-on {ph:.2f} W, period {r['period_ns']:.1f} ns, Ton {ton:.2f} ns")
    (HERE / "a102_summary.json").write_text(json.dumps(out, indent=1, default=float))
    print("\nwrote a102_summary.json")


if __name__ == "__main__":
    main()
