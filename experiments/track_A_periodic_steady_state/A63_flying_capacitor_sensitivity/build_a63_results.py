"""A63 - collect the Cfly points (3 uF = A59) and replay each orbit for the
flying-capacitor voltage ripple. Writes results.json (never overwritten).
"""
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
sys.path.insert(0, str(TRACK / "A62_load_sweep_fixed_deadtime"))
import variant_runner as V  # noqa: E402

N, S, O = V.N, V.S, V.A58.O
OUT = HERE / "results.json"
A59 = TRACK / "A59_nonlinear_coss_epc2067" / "runs"
POINTS = {"zvs": ("zvs_r1.950_f0.650", 1.95, 0.65), "baseline": ("baseline_r2.150_f1.150", 2.15, 1.15)}


def records(design):
    stem, rise, fall = POINTS[design]
    out = [(3.0, json.loads((A59 / f"{stem}.json").read_text()))]
    for c in (1, 2, 6):
        out.append((float(c), json.loads((HERE / "runs" / f"{stem}_C{c}uF.json").read_text())))
    return sorted(out), rise, fall


def cfly_ripple(d, cfly_uf, rise, fall):
    b = N.build_nl_boundary(phase_inductance_h=d["phase_inductance_h"], dead_time_rise_s=rise * 1e-9,
                            dead_time_fall_s=fall * 1e-9, ton_cmd_s=d["regulated"]["ton_cmd_s"])
    b = replace(b, flying_capacitances_f=(cfly_uf * 1e-6,) * 3)
    with S.asym_schedule_context(), N.nonlinear_coss_context():
        _, steps, index = O.accepted_orbit(b, np.array(d["regulated"]["z_star"], float),
                                           coarse_step_s=d["coarse_step_s"], sub_step_s=d["sub_step_s"])
    out = []
    for k in (1, 2, 3):
        vc = np.array([s.state[index[f"a{k}"]] - s.state[index[f"x{k}"]] for s in steps])
        out.append(dict(mean_v=float(vc.mean()), ripple_pp_v=float(vc.max() - vc.min())))
    return out


def main():
    if OUT.exists():
        raise SystemExit("results.json exists")
    table = {}
    for design in POINTS:
        recs, rise, fall = records(design)
        rows = []
        for c, d in recs:
            a = d["accounting"]
            rows.append(dict(cfly_uf=c, source="A59" if c == 3.0 else "A63", ton_cmd_s=d["regulated"]["ton_cmd_s"],
                             p_a_w=a["p_a_w"], p_b_w=a["p_b_w"]["fig8_25C"],
                             missed_capacitive_w=a["missed_capacitive_w"], channel_loss_w=a["channel_loss_w"],
                             high_side_natural_zvs=d["regulated"]["high_side_natural_zvs"],
                             low_side_natural_zvs=d["regulated"]["low_side_natural_zvs"],
                             high_residual_v=[t["residual_v"] for t in sorted(a["transitions"], key=lambda t: t["phase_index"]) if t["side"] == "high"],
                             low_residual_v=[t["residual_v"] for t in sorted(a["transitions"], key=lambda t: t["phase_index"]) if t["side"] == "low"],
                             peak_a=d["regulated"]["maximum_abs_phase_current_a"],
                             flying_capacitors=cfly_ripple(d, c, rise, fall)))
        table[design] = rows
    diff = [dict(cfly_uf=z["cfly_uf"], zvs_minus_baseline_w=z["p_b_w"] - b["p_b_w"])
            for z, b in zip(table["zvs"], table["baseline"])]
    OUT.write_text(json.dumps(dict(experiment="A63", classification="SENSITIVITY_ONLY", points=table,
                                   difference=diff), indent=1) + "\n")
    for design, rows in table.items():
        for r in rows:
            fc = "; ".join(f"VC{k+1} {x['mean_v']:.2f} V pp {x['ripple_pp_v']:.2f}" for k, x in enumerate(r["flying_capacitors"]))
            print(f"{design:8s} C={r['cfly_uf']:g}uF Ton {r['ton_cmd_s']*1e9:.3f} P_A {r['p_a_w']:.3f} P_B {r['p_b_w']:.3f} "
                  f"chan {r['channel_loss_w']:.2f} missC {r['missed_capacitive_w']:.2f} "
                  f"Hres {[round(v,1) for v in r['high_residual_v']]} | {fc}")
    for x in diff:
        print(x)


if __name__ == "__main__":
    main()
