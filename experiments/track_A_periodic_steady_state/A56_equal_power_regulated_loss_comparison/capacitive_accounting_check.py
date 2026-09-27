"""A56 BOUNDARY.md S3.4: does A55's branch meter capture hard-switch C discharge?

For every hard-switched turn-on in an accepted orbit (high side: Vds > 0 left
at the window end; low side: V(x) > 0 left at the window end) the enabled
channel discharges the switching-node capacitance with tau = R*C ~ 7-10 ps,
while the first step after the event is one full coarse step (62.5 ps, or
31.25 ps in the refined orbits). This script, per event:

* re-integrates the 500 ps post-event window from the orbit's own window-end
  state with A50's unchanged backward-Euler step at a ladder of steps
  (62.5 ps ... 0.025 ps), metering every enabled channel exactly like A55;
* checks the ladder rung equal to the orbit's own coarse step reproduces the
  orbit's metered energy for that window (same numbers, same meter);
* takes the h -> 0 limit (Richardson on 0.05/0.025 ps) as the physical
  dissipation, subtracts a conduction baseline fitted after 250 ps, measures
  the discharged charge -> C_meas = Q/Vres, and compares with 0.5*C*Vres^2;
* reports the energy the orbit's meter misses: E(h->0) - E(orbit).

It also evaluates the exact backward-Euler energy identity over each orbit,
localizing integrator-removed energy to the post-event windows.

Inputs: runs/*.json regulated states (both step sizes) plus A55's unregulated
nominal_dt_x1 as context. Output: capacitive_accounting.json (never
overwritten).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orbit_diagnostics as O  # noqa: E402
import regulated_boundary as R  # noqa: E402

OUT = HERE / "capacitive_accounting.json"


def orbit_inputs() -> list[dict]:
    items = []
    grid = json.loads((R.A55_DIR / "joint_local_grid.json").read_text())
    probe = next(p for p in grid["probes"] if p["label"] == "nominal_dt_x1")
    items.append(dict(name="A55_context_nominal_dt_x1_unregulated_192W", role="context",
                      phase_inductance_h=probe["phase_inductance_h"],
                      dead_time_s=probe["dead_time_s"], ton_cmd_s=R.NOMINAL_TON_S,
                      z_star=probe["z_star"], coarse_step_s=62.5e-12, sub_step_s=5e-12,
                      metered_channel_loss_w=probe["metrics"]["actual_branch_channel_loss_w"],
                      load_power_w=probe["metrics"]["actual_load_power_w"]))
    for path in sorted((HERE / "runs").glob("*.json")):
        run = json.loads(path.read_text())
        reg = run.get("regulated")
        if not reg:
            continue
        items.append(dict(name=path.stem, role="regulated", label=run["label"],
                          phase_inductance_h=run["phase_inductance_h"],
                          dead_time_s=run["dead_time_s"], ton_cmd_s=reg["ton_cmd_s"],
                          z_star=reg["z_star"], coarse_step_s=run["coarse_step_s"],
                          sub_step_s=run["sub_step_s"],
                          metered_channel_loss_w=reg["metrics"]["actual_branch_channel_loss_w"],
                          load_power_w=reg["metrics"]["actual_load_power_w"]))
    return items


def analyse(item: dict) -> dict:
    b = R.build_regulated_boundary(phase_inductance_h=item["phase_inductance_h"],
                                   dead_time_s=item["dead_time_s"], ton_cmd_s=item["ton_cmd_s"])
    result, steps, index = O.accepted_orbit(b, item["z_star"], coarse_step_s=item["coarse_step_s"],
                                            sub_step_s=item["sub_step_s"])
    channel = O.channel_power_w(b, steps, index)
    same_meter = abs(channel - item["metered_channel_loss_w"]) <= 1e-9 * max(1.0, channel)
    if not same_meter:
        raise RuntimeError(f"{item['name']}: diagnostic meter {channel} != A55 meter "
                           f"{item['metered_channel_loss_w']}")
    f_sw = 1.0 / b.period_s
    events = []
    for event in O.hard_events(b, result, steps):
        state = steps[event.sample_position].state
        orbit_energy = O.orbit_window_energy_j(b, steps, index, event)
        ladder = []
        fine = {}
        for h in O.STEP_LADDER_S:
            keep = h <= 0.025e-12 + 1e-18
            run = O.event_window_energy(b, state, event.window_end_s, h, index, event.branch,
                                        event.resistance_ohm, keep=keep)
            fine[h] = run
            ladder.append(dict(step_s=h, energy_j=run["energy_j"]))
        by_step = {r["step_s"]: r["energy_j"] for r in ladder}
        coarse_rung = by_step.get(item["coarse_step_s"])
        rung_matches_orbit = (coarse_rung is not None and
                              abs(coarse_rung - orbit_energy) <= 1e-9 * abs(orbit_energy))
        e_limit = 2.0 * by_step[0.025e-12] - by_step[0.05e-12]
        finest = fine[0.025e-12]
        p_slope, p_icpt, p_rms = O.conduction_fit(finest["times"], finest["powers"])
        e_cond = p_icpt * O.EVENT_WINDOW_S + 0.5 * p_slope * O.EVENT_WINDOW_S ** 2
        i_slope, i_icpt, i_rms = O.conduction_fit(finest["times"], finest["branch_current"])
        h = finest["step_s"]
        q_excess = float(np.sum(h * (finest["branch_current"] - (i_slope * finest["times"] + i_icpt))))
        vres = event.residual_v
        c_meas = q_excess / vres
        c_struct = O.structural_capacitance_f(b, event)
        with R.asymmetric_ron_context():
            c_a51 = R.M.measure_node_capacitance_f(b, steps[event.window_entry_position],
                                                   phase_index=event.phase_index)
        physical_excess = e_limit - e_cond
        record = dict(
            side=event.side, phase=event.phase_index + 1, window_end_s=event.window_end_s,
            residual_v=vres, switching_branch=list(event.branch),
            branch_resistance_ohm=event.resistance_ohm,
            orbit_metered_window_energy_j=orbit_energy,
            ladder_rung_at_orbit_step_reproduces_orbit=bool(rung_matches_orbit),
            step_ladder=[dict(r, excess_over_conduction_j=r["energy_j"] - e_cond,
                              captured_fraction=(r["energy_j"] - e_cond) / physical_excess)
                         for r in ladder],
            h_to_zero_limit_energy_j=e_limit,
            conduction_baseline_energy_j=e_cond,
            conduction_fit_rms_w=p_rms,
            physical_capacitive_excess_j=physical_excess,
            discharged_charge_c=q_excess,
            c_measured_from_charge_f=c_meas, c_structural_sum_f=c_struct,
            c_a51_measure_node_capacitance_f=c_a51,
            half_c_meas_v2_j=0.5 * c_meas * vres ** 2,
            half_c_struct_v2_j=0.5 * c_struct * vres ** 2,
            half_c_a51_v2_j=0.5 * c_a51 * vres ** 2,
            tau_estimate_s=event.resistance_ohm * c_meas,
            orbit_captured_excess_j=orbit_energy - e_cond,
            orbit_captured_fraction=(orbit_energy - e_cond) / physical_excess,
            missing_from_orbit_meter_j=e_limit - orbit_energy)
        events.append(record)
        print(json.dumps(dict(orbit=item["name"], side=event.side, phase=event.phase_index + 1,
                              vres=round(vres, 4), c_meas_pF=round(c_meas * 1e12, 1),
                              half_cv2_uJ=round(0.5 * c_meas * vres ** 2 * 1e6, 5),
                              excess_uJ=round(physical_excess * 1e6, 5),
                              orbit_frac=round(record["orbit_captured_fraction"], 4),
                              rung_ok=rung_matches_orbit)), flush=True)
    windows = [(e["window_end_s"], e["window_end_s"] + O.EVENT_WINDOW_S) for e in events]
    balance = O.energy_balance(b, steps, index, windows)
    missing_w = f_sw * sum(e["missing_from_orbit_meter_j"] for e in events)
    exposure = O.dead_time_surrogate_exposure(b, result, steps, index)
    return dict(
        name=item["name"], role=item["role"], label=item.get("label"),
        phase_inductance_h=b.phase_inductance_h, dead_time_s=b.dead_time_s,
        ton_cmd_s=b.ton_cmd_s, coarse_step_s=item["coarse_step_s"], sub_step_s=item["sub_step_s"],
        load_power_w=item["load_power_w"],
        a55_meter_channel_loss_w=item["metered_channel_loss_w"],
        diagnostic_meter_reproduces_a55_meter=same_meter,
        hard_switched_events=events, hard_switched_event_count=len(events),
        missing_capacitive_power_w=missing_w,
        channel_loss_plus_missing_capacitive_w=item["metered_channel_loss_w"] + missing_w,
        half_c_meas_v2_fsw_total_w=f_sw * sum(e["half_c_meas_v2_j"] for e in events),
        half_c_struct_v2_fsw_total_w=f_sw * sum(e["half_c_struct_v2_j"] for e in events),
        orbit_captured_capacitive_w=f_sw * sum(e["orbit_captured_excess_j"] for e in events),
        energy_balance=balance, dead_time_surrogate_exposure=exposure)


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; results are never overwritten")
    result = dict(experiment="A56", check="BOUNDARY.md S3.4 hard-switch capacitive energy accounting",
                  event_window_s=O.EVENT_WINDOW_S, step_ladder_s=list(O.STEP_LADDER_S),
                  conduction_fit_start_s=O.FIT_START_S, orbits=[])
    started = time.time()
    for item in orbit_inputs():
        result["orbits"].append(analyse(item))
        tmp = OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(result, indent=1, default=str) + "\n")
        tmp.replace(OUT)
    result["wall_time_s"] = time.time() - started
    result["status"] = "COMPLETED"
    OUT.write_text(json.dumps(result, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
