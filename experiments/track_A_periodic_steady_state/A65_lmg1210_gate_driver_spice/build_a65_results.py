"""A65 (copy of A64) - collect every run record into results.json (never overwrites; writes results_vN.json then).

Also prints the tables RESULTS.md is written from.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
GRID_KINDS = ("center", "sweep", "transfer")
MAXSTEP_PS = 50.0
A59 = {"zvs_p_b_w": 28.670537244169573, "baseline_p_b_w": 33.25495505048852,
       "zvs_minus_baseline_w": -4.584417806318946,
       "zvs_p_a_w": 28.357780131263258, "baseline_p_a_w": 33.07286882976342,
       "zvs_channel_w": 28.169625391616112, "baseline_channel_w": 18.936952297449615,
       "zvs_missed_capacitive_w": 0.18815473964714513, "baseline_missed_capacitive_w": 14.135916532313809,
       "zvs_reverse_fig8_25C_w": 0.32231096007800053, "baseline_reverse_fig8_25C_w": 0.18719625390770678,
       "zvs_other_resistive_w": 0.3887039527514844, "baseline_other_resistive_w": 0.37232000094348905,
       "source": "A59 results.json tuned_comparison fig8_25C and runs/{zvs_r1.950_f0.650,baseline_r2.150_f1.150}.json"}


def case_tag(case):
    driver = case.get("driver", "R")
    if driver != "R":
        return f"{driver}_T{case['temp_c']:.0f}"
    return f"R{case['r_drv_ohm']:.1f}_T{case['temp_c']:.0f}"


def a64_reference():
    """A64's comparison block (read only): the resistor-driver cases."""
    path = HERE.parent / "A64_vendor_model_spice_crosscheck" / "results.json"
    comp = json.loads(path.read_text())["comparison"]
    return {case: {"zvs_p_loss_w": e["zvs"]["optimum_p_loss_w"], "baseline_p_loss_w": e["baseline"]["optimum_p_loss_w"],
                   "zvs_minus_baseline_w": e["zvs_minus_baseline_w"],
                   "zvs_timing_ns": e["zvs"]["optimum_timing_ns"], "baseline_timing_ns": e["baseline"]["optimum_timing_ns"]}
            for case, e in comp.items()}


def _ns(v):
    return None if v is None else v * 1e9


def point_row(rec, name):
    f = rec["final"]
    cs = f["channel_summary"]
    dec = f.get("decomposition") or {}
    return {
        "file": name, "kind": rec["kind"], "design": rec["design"], "case": case_tag(rec["case"]),
        "status": rec["status"],
        "dead_time_rise_ns": rec["dead_time_rise_s"] * 1e9, "dead_time_fall_ns": rec["dead_time_fall_s"] * 1e9,
        "ton_cmd_ns": rec["ton_cmd_s"] * 1e9,
        "max_step_ps": rec["chunks"][-1]["max_step_s"] * 1e12,
        "p_in_w": f["p_in_w"], "p_out_w": f["p_out_w"], "power_relative_error": f["power_relative_error"],
        "p_loss_w": f["p_loss_w"], "p_loss_corr_w": f["p_loss_corr_w"],
        "stored_energy_rate_w": f["stored_energy_rate_w"],
        "p_loss_tail_estimate_w": f.get("p_loss_tail_estimate_w"),
        "ltspice_meas_p_loss_w": f.get("ltspice_meas_p_loss_w"),
        "p_passive_resistive_w": f["p_passive_resistive_w"], "p_device_w": f["p_device_w"],
        "p_switch_sum_w": f["p_switch_sum_w"], "closure_w": f["closure_w"],
        "p_gate_total_w": f["p_gate_total_w"], "p_total_with_gate_w": f["p_total_with_gate_w"],
        "p_conduction_reff_w": dec.get("p_conduction_equiv_w"),
        "p_edge_excess_w": dec.get("p_edge_excess_w"),
        "rel_change": f["rel_change"], "periods_total": rec["periods_total"], "chunks": rec["chunks_total"],
        "final_chunk_plain_periods": rec["final_chunk_plain_periods"],
        "max_abs_phase_current_a": f["max_abs_phase_current_a"],
        "channel_dead_time_rise_mean_ns": _ns(cs["rise"]["channel_dead_time_mean_s"]),
        "channel_dead_time_fall_mean_ns": _ns(cs["fall"]["channel_dead_time_mean_s"]),
        "channel_dead_time_rise_min_max_ns": [_ns(cs["rise"]["channel_dead_time_min_s"]),
                                              _ns(cs["rise"]["channel_dead_time_max_s"])],
        "channel_dead_time_fall_min_max_ns": [_ns(cs["fall"]["channel_dead_time_min_s"]),
                                              _ns(cs["fall"]["channel_dead_time_max_s"])],
        "turn_off_delay_rise_ns": _ns(cs["rise"]["turn_off_delay_mean_s"]),
        "turn_on_delay_rise_ns": _ns(cs["rise"]["turn_on_delay_mean_s"]),
        "turn_off_delay_fall_ns": _ns(cs["fall"]["turn_off_delay_mean_s"]),
        "turn_on_delay_fall_ns": _ns(cs["fall"]["turn_on_delay_mean_s"]),
        "vds_in_at_channel_on_rise_v": cs["rise"]["vds_in_at_channel_on_v"],
        "vds_in_at_channel_on_fall_v": cs["fall"]["vds_in_at_channel_on_v"],
        "zvs_count_rise": cs["rise"]["zvs_count"], "zvs_count_fall": cs["fall"]["zvs_count"],
        "reverse_before_on_fall_ns": [_ns(e.get("reverse_before_on_s")) for e in f["edges"] if e["edge"] == "fall"],
        "inductor_current_at_fall_cmd_a": [e["inductor_current_at_cmd_off_a"] for e in f["edges"] if e["edge"] == "fall"],
        "inductor_current_at_rise_cmd_a": [e["inductor_current_at_cmd_off_a"] for e in f["edges"] if e["edge"] == "rise"],
        "symmetry": f.get("symmetry"),
        "log_warnings": f.get("log_warnings"),
    }


def decomp_row(rec, name):
    f = rec["final"]
    sd = f["state_decomposition"]
    groups = sd["groups"]
    r_full = {k: g["r_full_gate_per_device_ohm"] for k, g in groups.items()}
    return {
        "file": name, "source_record": rec["source_record"], "design": rec["design"],
        "case": case_tag(rec["case"]),
        "dead_time_rise_ns": rec["dead_time_rise_s"] * 1e9, "dead_time_fall_ns": rec["dead_time_fall_s"] * 1e9,
        "p_loss_corr_w": f["p_loss_corr_w"], "source_p_loss_corr_w": rec["source_p_loss_corr_w"],
        "p_passive_resistive_w": f["p_passive_resistive_w"], "p_switch_sum_w": f["p_switch_sum_w"],
        "p_gate_total_w": f["p_gate_total_w"],
        "coss_corrected": sd.get("coss_corrected"),
        "dissipative_totals_w": sd.get("dissipative_totals_w"),
        "dissipative_by_side_w": sd.get("dissipative_by_side_w"),
        "dissipative_sum_w": sd.get("dissipative_sum_w"),
        "terminal_totals_w": sd["totals_w"], "terminal_sum_w": sd["sum_w"],
        "a59_style_conduction_w": sd["a59_style_conduction_w"],
        "vendor_conduction_like_w": sd["vendor_conduction_like_w"],
        "r_full_gate_per_device_mohm": {k: (v * 1e3 if v else None) for k, v in r_full.items()},
        "thresholds": sd["thresholds"],
        "third_quadrant_time_ns": {k: g["third_quadrant_time_s"] * 1e9 for k, g in groups.items()},
    }


def main(dry=False):
    points, decomps, brutes, others, comparison = collect(RUNS)
    xchecks = []
    for p in sorted(RUNS.glob("*_xcheck*.json")):
        rec = json.loads(p.read_text())
        xchecks.append({k: rec[k] for k in ("source_record", "model", "source_p_loss_corr_w", "p_loss_corr_w",
                                            "source_p_out_w", "p_out_w", "rel_change",
                                            "channel_dead_time_rise_mean_s", "channel_dead_time_fall_mean_s",
                                            "source_channel_dead_time_rise_mean_s",
                                            "source_channel_dead_time_fall_mean_s")}
                       | {"file": p.name, "delta_p_loss_w": rec["p_loss_corr_w"] - rec["source_p_loss_corr_w"]})
    model_check = None
    checks = sorted(RUNS.glob("model_check*.json"))
    if checks:
        model_check = json.loads(checks[-1].read_text()) | {"file": checks[-1].name}
    write(dry, points, decomps, brutes, others, comparison, model_check, xchecks)


def collect(run_dir):
    points, decomps, brutes, others = [], [], [], {}
    for p in sorted(run_dir.glob("*.json")):
        rec = json.loads(p.read_text())
        kind = rec.get("kind")
        if kind in GRID_KINDS + ("literal", "step"):
            points.append(point_row(rec, p.name))
        elif kind == "decomp" and p.name.endswith("_decompc.json"):
            decomps.append(decomp_row(rec, p.name))
        elif kind == "brute":
            brutes.append({"file": p.name, "design": rec["design"], "status": rec["status"],
                           "dead_time_rise_ns": rec["dead_time_rise_s"] * 1e9,
                           "dead_time_fall_ns": rec["dead_time_fall_s"] * 1e9,
                           "ton_cmd_ns": rec["ton_cmd_s"] * 1e9, "periods_total": rec["periods_total"],
                           "first_period_below_1e-3": rec["first_period_below_1e-3"],
                           "p_loss_corr_w": rec["final_p_loss_corr_w"], "p_out_w": rec["final_p_out_w"],
                           "compare_to": rec["compare_to"],
                           "rel_change_per_period": [q["rel_change"] for ch in rec["chunks"] for q in ch["periods"]]})
        elif kind in ("static", "static_coss"):
            others[kind] = {k: v for k, v in rec.items() if k not in ("v_grid_v", "c_per_device_f",
                                                                       "q_per_device_c", "e_per_device_j")}
        elif kind in ("centre_search",):
            others.setdefault("centre_search", []).append(
                {"file": p.name, "design": rec["design"], "case": case_tag(rec["case"]), "status": rec["status"],
                 "dead_time_rise_ns": rec["dead_time_rise_s"] * 1e9,
                 "dead_time_fall_ns": rec["dead_time_fall_s"] * 1e9,
                 "periods_total": rec["periods_total"]})
        elif kind == "decomp":
            others.setdefault("decomp_uncorrected", []).append(p.name)
    grid = [r for r in points if r["kind"] in GRID_KINDS and r["status"] == "REGULATED_TO_250W"
            and abs(r["max_step_ps"] - MAXSTEP_PS) < 1e-6]
    comparison = {}
    for case in sorted({r["case"] for r in grid}):
        entry = {}
        for design in ("zvs", "baseline"):
            pts = [r for r in grid if r["case"] == case and r["design"] == design]
            if not pts:
                continue
            best = min(pts, key=lambda r: r["p_loss_corr_w"])
            centre = [r for r in pts if r["kind"] == "center"]
            entry[design] = {"optimum": best["file"], "optimum_p_loss_w": best["p_loss_corr_w"],
                             "optimum_p_device_w": best["p_device_w"],
                             "optimum_p_total_with_gate_w": best["p_total_with_gate_w"],
                             "optimum_timing_ns": [best["dead_time_rise_ns"], best["dead_time_fall_ns"]],
                             "centre": centre[0]["file"] if centre else None,
                             "centre_p_loss_w": centre[0]["p_loss_corr_w"] if centre else None,
                             "points_regulated": len(pts),
                             "points_failed": sum(1 for r in points if r["case"] == case and r["design"] == design
                                                  and r["kind"] in GRID_KINDS and r["status"] != "REGULATED_TO_250W")}
        if "zvs" in entry and "baseline" in entry:
            z, b = entry["zvs"], entry["baseline"]
            entry["zvs_minus_baseline_w"] = z["optimum_p_loss_w"] - b["optimum_p_loss_w"]
            entry["zvs_minus_baseline_device_w"] = z["optimum_p_device_w"] - b["optimum_p_device_w"]
            entry["zvs_minus_baseline_with_gate_w"] = (z["optimum_p_total_with_gate_w"]
                                                       - b["optimum_p_total_with_gate_w"])
            if z["centre_p_loss_w"] is not None and b["centre_p_loss_w"] is not None:
                entry["zvs_minus_baseline_centre_w"] = z["centre_p_loss_w"] - b["centre_p_loss_w"]
            entry["a59_zvs_minus_baseline_w"] = A59["zvs_minus_baseline_w"]
            entry["change_vs_a59_w"] = entry["zvs_minus_baseline_device_w"] - A59["zvs_minus_baseline_w"]
        comparison[case] = entry
    return points, decomps, brutes, others, comparison


def write(dry, points, decomps, brutes, others, comparison, model_check, xchecks):
    out = {
        "experiment": "A65",
        "driver": "TI LMG1210 typical output I-V (datasheet Figs. 1-2), lmg1210_output_iv.csv",
        "classification": "SENSITIVITY_ONLY",
        "vendor_model": {"subckt": "EPC2067 (EPCGaNLibrary.lib, (C) Efficient Power Conversion Corp.)",
                         "block_sha256_prefix": "b1d201cc7ab403f7", "block_chars": 2734,
                         "mirrors": ["vgreff/LTSpiceLibraries", "hadibadri/GaN-Power-Converter",
                                     "adml-upm/ESA_parallel_GaN", "Blade87/LTspice"],
                         "committed": False, "evidence": "EXTERNAL_DEVICE_DATA",
                         "simulated": "EPC2067 block as distributed (all sweeps)",
                         "check_variant": "EPC2067X: the same block with C_CGS1/C_CGD1/C_CSD1 charge "
                                          "expressions written in x (fetch_epc2067_model.x_form), re-run at "
                                          "the accepted points (xchecks)",
                         "ltspice": "LTspice 26.0.2 for MacOS (Wine)"},
        "a59_reference": A59,
        "a64_reference": a64_reference(),
        "model_check": model_check,
        "xchecks": xchecks,
        "comparison": comparison,
        "decompositions": decomps,
        "brute_force": brutes,
        "static_checks": others,
        "points": points,
    }
    if dry:
        print(f"(dry run) {len(points)} points, {len(decomps)} decompositions, {len(brutes)} brute")
    else:
        path = HERE / "results.json"
        k = 2
        while path.exists():
            path = HERE / f"results_v{k}.json"
            k += 1
        path.write_text(json.dumps(out, indent=1))
        print(f"wrote {path.name}: {len(points)} points, {len(decomps)} decompositions, {len(brutes)} brute")
    for case, entry in comparison.items():
        print(f"\n== {case}")
        for design in ("zvs", "baseline"):
            if design in entry:
                e = entry[design]
                print(f"  {design:8s} opt {e['optimum_timing_ns']} P_loss={e['optimum_p_loss_w']:.3f} "
                      f"device={e['optimum_p_device_w']:.3f} +gate={e['optimum_p_total_with_gate_w']:.3f} "
                      f"centre={e['centre_p_loss_w']} n={e['points_regulated']} failed={e['points_failed']}")
        for key in ("zvs_minus_baseline_w", "zvs_minus_baseline_device_w", "zvs_minus_baseline_with_gate_w",
                    "zvs_minus_baseline_centre_w", "change_vs_a59_w"):
            if key in entry:
                print(f"  {key}: {entry[key]:+.3f} W")
    for case, e in a64_reference().items():
        print(f"\n== A64 {case}: zvs {e['zvs_p_loss_w']:.3f} baseline {e['baseline_p_loss_w']:.3f} "
              f"diff {e['zvs_minus_baseline_w']:+.3f} W")
    print("\n== decompositions (dissipative, Coss-corrected; W)")
    for dr in decomps:
        tot = dr["dissipative_totals_w"] or {}
        print(f"  {dr['source_record']}: " + " ".join(f"{k}={v:.2f}" for k, v in tot.items())
              + f" | a59_style_cond={dr['a59_style_conduction_w']:.2f} Rfull={dr['r_full_gate_per_device_mohm']}")
    print("\n== x-form checks")
    for x in xchecks:
        print(f"  {x['source_record']}: {x['source_p_loss_corr_w']:.3f} -> {x['p_loss_corr_w']:.3f} W "
              f"(delta {x['delta_p_loss_w']:+.3f})")


if __name__ == "__main__":
    import sys
    main(dry="--dry" in sys.argv)
