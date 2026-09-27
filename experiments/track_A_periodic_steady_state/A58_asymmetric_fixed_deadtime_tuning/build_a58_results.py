"""A58 - collect runs/*.json into results.json and print the grid tables.

Best point per design = lowest P_B among regulated points inside the +/-250 A
screen (orbit and probes), separately for each reverse-drop model. Never
overwrites results.json unless --replace is given (the grid may be extended).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results.json"
MODELS = ("fig8_25C", "fig8_125C", "table_floor_1p2V")
SCREEN_A = 250.0


def rows():
    out = []
    for path in sorted((HERE / "runs").glob("*.json")):
        d = json.loads(path.read_text())
        row = dict(name=path.stem, design=d["design"], rise_ns=round(d["dead_time_rise_s"] * 1e9, 4),
                   fall_ns=round(d["dead_time_fall_s"] * 1e9, 4), status=d["status"],
                   step_ps=round(d["coarse_step_s"] * 1e12, 4), stop_reason=d.get("stop_reason"))
        reg, acc = d.get("regulated"), d.get("accounting")
        if reg and acc:
            tr = acc["transitions"]

            def side(s, key):
                return [t[key] for t in sorted(tr, key=lambda t: t["phase_index"]) if t["side"] == s]
            row.update(
                ton_cmd_ns=reg["ton_cmd_s"] * 1e9, load_power_w=reg["load_power_w"],
                h_zvs="".join("T" if x else "F" for x in reg["high_side_natural_zvs"]),
                l_zvs="".join("T" if x else "F" for x in reg["low_side_natural_zvs"]),
                peak_a=reg["maximum_abs_phase_current_a"], probe_peak_a=reg["max_probe_abs_current_a"],
                within_screen=(reg["maximum_abs_phase_current_a"] <= SCREEN_A
                               and reg["max_probe_abs_current_a"] <= SCREEN_A),
                p_a_w=acc["p_a_w"], p_b_w=acc["p_b_w"], recharge_w=acc["recharge_estimate_w"],
                missed_capacitive_w=acc["missed_capacitive_w"], exposure_a=acc["exposure_a"],
                source_minus_load_coarse_w=acc["source_minus_load_coarse_w"],
                high_transition_ns=[None if x is None else x * 1e9 for x in side("high", "transition_s")],
                low_transition_ns=[None if x is None else x * 1e9 for x in side("low", "transition_s")],
                high_residual_reverse_ns=[x * 1e9 for x in side("high", "residual_reverse_s")],
                low_residual_reverse_ns=[x * 1e9 for x in side("low", "residual_reverse_s")],
                high_residual_v=side("high", "residual_v"), low_residual_v=side("low", "residual_v"))
        out.append(row)
    return out


def main():
    table = rows()
    ok = [r for r in table if r.get("within_screen") and r["step_ps"] == 62.5]
    best = {}
    for design in ("zvs", "baseline"):
        mine = [r for r in ok if r["design"] == design]
        if not mine:
            continue
        best[design] = {m: min(mine, key=lambda r: r["p_b_w"][m])["name"] for m in MODELS}
        best[design]["adaptive_p_a"] = min(mine, key=lambda r: r["p_a_w"])["name"]
    by_name = {r["name"]: r for r in table}
    comparison = {}
    if len(best) == 2:
        for m in MODELS:
            z, b = by_name[best["zvs"][m]], by_name[best["baseline"][m]]
            comparison[m] = dict(best_zvs=z["name"], best_baseline=b["name"],
                                 zvs_p_b_w=z["p_b_w"][m], baseline_p_b_w=b["p_b_w"][m],
                                 zvs_minus_baseline_w=z["p_b_w"][m] - b["p_b_w"][m],
                                 with_recharge_w=(z["p_b_w"][m] + z["recharge_w"][m])
                                 - (b["p_b_w"][m] + b["recharge_w"][m]))
    # Timing tolerance (fig8_25C): both designs at their best d_rise; d_fall
    # moved by the same delta from each design's own best d_fall (linear
    # interpolation along the grid line; None outside the swept range).
    tolerance = []
    if len(best) == 2:
        series = {}
        for design in ("zvs", "baseline"):
            b0 = by_name[best[design]["fig8_25C"]]
            line = sorted((r for r in ok if r["design"] == design and r["rise_ns"] == b0["rise_ns"]),
                          key=lambda r: r["fall_ns"])
            series[design] = (b0["fall_ns"], [r["fall_ns"] for r in line],
                              [r["p_b_w"]["fig8_25C"] for r in line])

        def at(design, delta):
            f0, xs, ys = series[design]
            x = f0 + delta
            if x < xs[0] - 1e-9 or x > xs[-1] + 1e-9:
                return None
            for (xa, ya), (xb, yb) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
                if xa - 1e-9 <= x <= xb + 1e-9:
                    return ya + (yb - ya) * (x - xa) / (xb - xa)
            return ys[0]
        for delta in (-0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
            z, b = at("zvs", delta), at("baseline", delta)
            tolerance.append(dict(delta_fall_ns=delta, zvs_p_b_w=z, baseline_p_b_w=b,
                                  zvs_minus_baseline_w=None if None in (z, b) else z - b))
    if OUT.exists() and "--replace" not in sys.argv:
        print("results.json exists; pass --replace to rebuild it")
    else:
        OUT.write_text(json.dumps(dict(experiment="A58_asymmetric_fixed_deadtime_tuning",
                                       classification="SENSITIVITY_ONLY", points=table, best=best,
                                       tuned_comparison=comparison, equal_fall_timing_error=tolerance), indent=1) + "\n")
    for design in ("zvs", "baseline"):
        print(f"\n== {design} ==  rise fall | Ton  H    L    | P_A    P_B25  P_B125 P_B1.2 | peak  | low trans / resid rev (ns) | high trans / resid rev / Vres")
        for r in sorted((r for r in table if r["design"] == design), key=lambda r: (-r["rise_ns"], -r["fall_ns"], r["step_ps"])):
            if "p_a_w" not in r:
                print(f"   {r['rise_ns']:.3f} {r['fall_ns']:.3f} | {r['status']} {r.get('stop_reason')}")
                continue
            lt = "/".join("-" if x is None else f"{x:.2f}" for x in r["low_transition_ns"])
            lr = "/".join(f"{x:.2f}" for x in r["low_residual_reverse_ns"])
            ht = "/".join("-" if x is None else f"{x:.2f}" for x in r["high_transition_ns"])
            hr = "/".join(f"{x:.2f}" for x in r["high_residual_reverse_ns"])
            hv = "/".join(f"{x:.1f}" for x in r["high_residual_v"])
            print(f"   {r['rise_ns']:.3f} {r['fall_ns']:.3f} | {r['ton_cmd_ns']:.3f} {r['h_zvs']} {r['l_zvs']} | "
                  f"{r['p_a_w']:.3f} {r['p_b_w']['fig8_25C']:.3f} {r['p_b_w']['fig8_125C']:.3f} "
                  f"{r['p_b_w']['table_floor_1p2V']:.3f} | {r['peak_a']:.0f}{'' if r['within_screen'] else '!'} | "
                  f"{lt} / {lr} | {ht} / {hr} / {hv}" + (f"  [step {r['step_ps']}ps]" if r['step_ps'] != 62.5 else ""))
    print("\nbest:", json.dumps(best, indent=1))
    print("tuned comparison:", json.dumps(comparison, indent=1))
    print("equal d_fall timing error:")
    for t in tolerance:
        print("   ", t)


if __name__ == "__main__":
    main()
