"""A60 - collect runs/*.json into results.json (never overwritten) and print the table."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results.json"


def main():
    if OUT.exists():
        raise SystemExit("results.json exists")
    points = []
    for f in sorted((HERE / "runs").glob("*.json")):
        r = json.loads(f.read_text())
        a = r["accounting"]
        points.append(dict(name=f.stem, design=r["design"], tj_c=r["tj_c"], rds_on_device_ohm=r["rds_on_device_ohm"],
                           dead_time_rise_s=r["dead_time_rise_s"], dead_time_fall_s=r["dead_time_fall_s"],
                           ton_cmd_s=r["regulated"]["ton_cmd_s"], p_a_w=a["p_a_w"],
                           p_b_temperature_interpolated_w=a["p_b_temperature_interpolated_w"],
                           channel_loss_w=a["channel_loss_w"], missed_capacitive_w=a["missed_capacitive_w"],
                           high_side_natural_zvs=r["regulated"]["high_side_natural_zvs"],
                           low_side_natural_zvs=r["regulated"]["low_side_natural_zvs"],
                           peak_a=r["regulated"]["maximum_abs_phase_current_a"]))
    by = {p["name"]: p for p in points}
    diff = []
    for t in ("T25C", "T60C", "T100C", "T125C"):
        z, b = by[f"zvs_r1.950_f0.650_{t}"], by[f"baseline_r2.150_f1.150_{t}"]
        diff.append(dict(tj_c=z["tj_c"], zvs_p_b_w=z["p_b_temperature_interpolated_w"],
                         baseline_p_b_w=b["p_b_temperature_interpolated_w"],
                         zvs_minus_baseline_w=z["p_b_temperature_interpolated_w"] - b["p_b_temperature_interpolated_w"]))
    a, b = diff[2], diff[3]
    crossing = a["tj_c"] + (b["tj_c"] - a["tj_c"]) * (-a["zvs_minus_baseline_w"]) / (b["zvs_minus_baseline_w"] - a["zvs_minus_baseline_w"])
    OUT.write_text(json.dumps(dict(experiment="A60", classification="SENSITIVITY_ONLY", points=points,
                                   tuned_difference_vs_tj=diff, break_even_tj_c_linear=crossing), indent=1) + "\n")
    for d in diff:
        print(d)
    print("break-even Tj (linear between 100 and 125 C): %.1f C" % crossing)
    for p in points:
        print("%-36s chan %.2f missC %.2f P_B %.3f" % (p["name"], p["channel_loss_w"], p["missed_capacitive_w"], p["p_b_temperature_interpolated_w"]))


if __name__ == "__main__":
    main()
