"""Parameter-only closure audit for the P25 reported prototype point."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from apec2025_supplements import inductance_for_negative_peak_fraction
from ivr_framework import SystemSpec, duty_cycle, high_side_on_time, inductor_peak_current


OUT = Path(__file__).parent / "numerical_runs/01_full_ring_calibration"


def main():
    spec = SystemSpec(vin_v=12.0, vout_v=1.0, pout_w=200.0)
    np_, nm, fsw = 3, 3, 0.5e6
    alpha = 0.05
    d = duty_cycle(spec, np_)
    ton = high_side_on_time(spec, np_, fsw)
    peak = inductor_peak_current(spec, np_, nm)
    negative = alpha * peak
    phase_rail = spec.vin_v / np_
    net_v = phase_rail - spec.vout_v
    l_direct = net_v * ton / (peak + negative)
    l_eq20 = inductance_for_negative_peak_fraction(
        spec, np_, nm, fsw, alpha).value
    l_prototype = 22e-9
    peak_from_22n = -negative + net_v * ton / l_prototype
    ton_for_22n = (peak + negative) * l_prototype / net_v
    fsw_for_22n_at_d = d / ton_for_22n
    net_v_for_22n = (peak + negative) * l_prototype / ton
    payload = {
        "duty_from_conversion_ratio": d,
        "ton_ns": ton * 1e9,
        "ideal_phase_peak_a": peak,
        "five_percent_negative_a": negative,
        "ideal_phase_rail_v": phase_rail,
        "ideal_net_inductor_voltage_v": net_v,
        "inductance_direct_ramp_nh": l_direct * 1e9,
        "inductance_p25_eq20_nh": l_eq20 * 1e9,
        "prototype_inductance_nh": l_prototype * 1e9,
        "ideal_peak_with_22nh_a": peak_from_22n,
        "ton_required_with_22nh_ns": ton_for_22n * 1e9,
        "frequency_required_with_22nh_and_d_hz": fsw_for_22n_at_d,
        "net_voltage_required_with_22nh_v": net_v_for_22n,
        "phase_rail_required_ignoring_losses_v": net_v_for_22n + spec.vout_v,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "operating_point_closure.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
