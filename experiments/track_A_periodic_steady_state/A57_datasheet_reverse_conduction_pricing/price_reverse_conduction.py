"""A57: price A56's dead-time conduction with EPC2067 Fig. 8 (fixed dead time).

Scenario A (A56 as computed): the channel turns on at the natural Vds=0
crossing, so the rest of each commanded dead window conducts through Ron.
Scenario B (fixed dead time): the gate waits for the window end, so that
same current-time flows through the OFF device's reverse channel at VSD(I).

    P_B = P_A - P_channel_metered_in_intervals + f_sw * sum VSD(I_mean/n) * Q

First-order: orbits are not re-solved with the -VSD clamp. Read-only use of
A56 files; see BOUNDARY.md.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A56 = HERE.parent / "A56_equal_power_regulated_loss_comparison"
PROJECT = HERE.parents[2]
OUT = HERE / "results.json"
CURVE_CSV = HERE / "epc2067_fig8_reverse_characteristics.csv"
BASELINE = "nominal_dt_x1"
BEST_ZVS = ("old_critical_dt_x1", "old_critical_dt_x2", "new_passing_dt_x1", "new_passing_dt_x2")
TABLE_FLOOR_V = 1.2  # datasheet table, IS = 0.5 A, VGS = 0 V, typ
C_NODE_F = 13.0e-9  # A56 measured high-side node capacitance (approximation for every event)

sys.path.insert(0, str(A56))
sys.path.insert(0, str(PROJECT / "src"))
import regulated_boundary as R  # noqa: E402
from scb_ivr.device_library import EPC2067, P24_EPC2067_POPULATION  # noqa: E402

REF = R.build_regulated_boundary(phase_inductance_h=R.L_ROWS[2][1], dead_time_s=2.15e-9,
                                 ton_cmd_s=R.NOMINAL_TON_S)
F_SW = 1.0 / REF.period_s
N_PAR = dict(high=P24_EPC2067_POPULATION.high_side_parallel,
             low=P24_EPC2067_POPULATION.low_side_parallel)
RON = dict(high=REF.high_side_on_resistance_ohm, low=REF.low_side_on_resistance_ohm)
for _side in RON:  # the dynamics' Ron must be the per-device value shared by n devices
    assert abs(RON[_side] - EPC2067.rds_on_typ_ohm / N_PAR[_side]) < 1e-12, _side


def load_curves(path=CURVE_CSV):
    curves = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            curves.setdefault(int(row["temperature_c"]), []).append(
                (float(row["isd_a_per_device"]), float(row["vsd_v"])))
    out = {}
    for temp, pts in curves.items():
        pts = np.array(pts)
        # VSD(ISD): keep the last voltage for each current on the flat ISD=0 run
        current = np.unique(pts[:, 0])
        last = [np.max(np.flatnonzero(pts[:, 0] == c)) for c in current]
        out[temp] = (current, pts[last, 1])
    return out


def vsd_model(name, curves):
    if name.startswith("fig8_"):
        current, volts = curves[int(name.split("_")[1].rstrip("C"))]
        return lambda i: float(np.interp(i, current, volts))
    if name == "table_floor_1p2V":
        return lambda i: TABLE_FLOOR_V
    raise ValueError(name)


def events_of(orbit):
    for e in orbit["dead_time_surrogate_exposure"]["events"]:
        if e["admitted_duration_s"] > 0:
            yield e


def price_orbit(orbit, proxy_a_w, model):
    metered = rev = rev_rms = recharge = 0.0
    per_event = []
    for e in events_of(orbit):
        side, dur, q, i2 = e["side"], e["admitted_duration_s"], e["abs_charge_c"], e["i2_dt_a2s"]
        n = N_PAR[side]
        i_mean, i_rms = q / dur, (i2 / dur) ** 0.5
        v_mean, v_rms = model(i_mean / n), model(i_rms / n)
        metered += RON[side] * i2 * F_SW
        rev += v_mean * q * F_SW
        rev_rms += v_rms * q * F_SW
        recharge += 0.5 * C_NODE_F * v_mean ** 2 * F_SW
        per_event.append(dict(side=side, phase_index=e["phase_index"], duration_ns=dur * 1e9,
                              branch_mean_current_a=i_mean, per_device_current_a=i_mean / n,
                              vsd_v=v_mean, reverse_loss_w=v_mean * q * F_SW,
                              ron_loss_replaced_w=RON[side] * i2 * F_SW))
    return dict(scenario_a_proxy_w=proxy_a_w, channel_metered_in_intervals_w=metered,
                reverse_loss_w=rev, reverse_loss_rms_eval_w=rev_rms,
                scenario_b_proxy_w=proxy_a_w - metered + rev,
                scenario_b_proxy_rms_eval_w=proxy_a_w - metered + rev_rms,
                turn_on_recharge_estimate_w=recharge, events=per_event)


def residual_time_slope(orbit, model):
    """dP/dt_r (W per second of residual reverse time on every admitted edge)."""
    slope = 0.0
    for e in events_of(orbit):
        side, i = e["side"], e["abs_charge_c"] / e["admitted_duration_s"]
        slope += (model(i / N_PAR[side]) * i - RON[side] * i * i) * F_SW
    return slope


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT.name}")
    cap = json.loads((A56 / "capacitive_accounting.json").read_text())
    res = json.loads((A56 / "results.json").read_text())
    rows = {r["label"]: r for r in res["comparison_at_250w"]["ranked_by_partial_loss_proxy"]}
    ladder = {lv["name"]: lv for lad in res["step_refinement"]["ladder"].values() for lv in lad["levels"]}
    orbits = [o for o in cap["orbits"] if o["role"] == "regulated"]
    curves = load_curves()
    models = ("fig8_25C", "fig8_125C", "table_floor_1p2V")

    table = []
    for o in orbits:
        proxy = ladder[o["name"]]["partial_loss_proxy_w"] if o["name"] in ladder \
            else rows[o["name"]]["partial_loss_proxy_w"]
        coarse = o["name"] == o["label"]
        if coarse:  # the A56 breakdown must be reproduced before anything is added
            assert abs(price_orbit(o, proxy, vsd_model(models[0], curves))["channel_metered_in_intervals_w"]
                       - rows[o["label"]]["channel_loss_metered_inside_surrogate_intervals_w"]) < 1e-9
        entry = dict(name=o["name"], label=o["label"], step_s=o["coarse_step_s"],
                     phase_inductance_nh=o["phase_inductance_h"] * 1e9, dead_time_ns=o["dead_time_s"] * 1e9,
                     all_eight_zvs=rows[o["label"]]["all_eight_zvs"],
                     exposure_a=o["dead_time_surrogate_exposure"]["mean_abs_current_time_per_second_a"],
                     priced={m: price_orbit(o, proxy, vsd_model(m, curves)) for m in models},
                     residual_time_slope_w_per_ns={m: residual_time_slope(o, vsd_model(m, curves)) * 1e-9
                                                   for m in models})
        table.append(entry)

    by_name = {t["name"]: t for t in table}
    comparisons = []
    for m in models:
        base = by_name[BASELINE]["priced"][m]["scenario_b_proxy_w"]
        for label in BEST_ZVS:
            z = by_name[label]
            zb = z["priced"][m]["scenario_b_proxy_w"]
            za = z["priced"][m]["scenario_a_proxy_w"]
            ba = by_name[BASELINE]["priced"][m]["scenario_a_proxy_w"]
            ds = z["residual_time_slope_w_per_ns"][m] - by_name[BASELINE]["residual_time_slope_w_per_ns"][m]
            comparisons.append(dict(
                model=m, zvs_label=label,
                scenario_a_delta_w=za - ba,
                scenario_b_delta_w=zb - base,
                scenario_b_delta_with_recharge_w=(zb + z["priced"][m]["turn_on_recharge_estimate_w"])
                - (base + by_name[BASELINE]["priced"][m]["turn_on_recharge_estimate_w"]),
                scenario_b_delta_rms_eval_w=z["priced"][m]["scenario_b_proxy_rms_eval_w"]
                - by_name[BASELINE]["priced"][m]["scenario_b_proxy_rms_eval_w"],
                break_even_residual_reverse_time_ns=(ba - za) / ds if ds > 0 else None))

    ladder_check = []
    for label in (BASELINE, "old_critical_dt_x1"):
        for name in (label, f"{label}_step2p5ps", f"{label}_step1p25ps"):
            ladder_check.append(dict(name=name, step_ps=by_name[name]["step_s"] * 1e12,
                                     **{m: by_name[name]["priced"][m]["scenario_b_proxy_w"] for m in models}))

    OUT.write_text(json.dumps(dict(
        experiment="A57_datasheet_reverse_conduction_pricing",
        classification="SENSITIVITY_ONLY (post-processing of A56) + EXTERNAL_DEVICE_DATA",
        scenario_a="A56 as computed: gate follows the natural zero crossing with zero delay (ideal adaptive)",
        scenario_b="fixed symmetric dead time: remainder of each window conducted at VSD(I) of the OFF device",
        first_order=True, orbits_resolved_with_clamp=False,
        f_sw_hz=F_SW, parallel_devices=N_PAR, ron_ohm=RON, c_node_for_recharge_estimate_f=C_NODE_F,
        curve_source=json.loads((HERE / "epc2067_fig8_digitization.json").read_text()),
        candidates=table, comparisons_vs_baseline=comparisons, step_ladder_scenario_b=ladder_check),
        indent=1) + "\n")

    print(f"{'orbit':34s} {'L nH':>6s} {'DT':>5s} {'ZVS':>5s} {'A':>7s} {'B 25C':>7s} {'B 125C':>7s} {'B 1.2V':>7s}")
    for t in table:
        p = t["priced"]
        print(f"{t['name']:34s} {t['phase_inductance_nh']:6.4f} {t['dead_time_ns']:5.3f} {str(t['all_eight_zvs']):>5s} "
              f"{p['fig8_25C']['scenario_a_proxy_w']:7.3f} {p['fig8_25C']['scenario_b_proxy_w']:7.3f} "
              f"{p['fig8_125C']['scenario_b_proxy_w']:7.3f} {p['table_floor_1p2V']['scenario_b_proxy_w']:7.3f}")
    for c in comparisons:
        print(c)


if __name__ == "__main__":
    main()
