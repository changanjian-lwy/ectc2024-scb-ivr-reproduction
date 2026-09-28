"""A62 - collect runs/*.json into results.json (never overwritten) and print the table."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results.json"


def main():
    if OUT.exists():
        raise SystemExit("results.json exists")
    table = {}
    for f in sorted((HERE / "runs").glob("*.json")):
        r = json.loads(f.read_text())
        a = r["accounting"]
        tr = sorted(a["transitions"], key=lambda t: t["phase_index"])
        table.setdefault(r["design"], []).append(dict(
            power_w=r["target_power_w"], name=f.stem, ton_cmd_s=r["regulated"]["ton_cmd_s"],
            load_power_w=r["regulated"]["load_power_w"], p_a_w=a["p_a_w"], p_b_w=a["p_b_w"]["fig8_25C"],
            channel_loss_w=a["channel_loss_w"], missed_capacitive_w=a["missed_capacitive_w"],
            reverse_loss_w=a["reverse_loss_w"]["fig8_25C"],
            efficiency_proxy=r["target_power_w"] / (r["target_power_w"] + a["p_b_w"]["fig8_25C"]),
            high_side_natural_zvs=r["regulated"]["high_side_natural_zvs"],
            low_side_natural_zvs=r["regulated"]["low_side_natural_zvs"],
            high_residual_v=[t["residual_v"] for t in tr if t["side"] == "high"],
            low_residual_v=[t["residual_v"] for t in tr if t["side"] == "low"],
            peak_a=r["regulated"]["maximum_abs_phase_current_a"]))
    for rows in table.values():
        rows.sort(key=lambda x: -x["power_w"])
    diff = [dict(power_w=z["power_w"], zvs_minus_baseline_w=z["p_b_w"] - b["p_b_w"])
            for z, b in zip(table["zvs"], table["baseline"])]
    cross = None
    for hi, lo in zip(diff, diff[1:]):
        if hi["zvs_minus_baseline_w"] < 0 <= lo["zvs_minus_baseline_w"]:
            cross = lo["power_w"] + (hi["power_w"] - lo["power_w"]) * lo["zvs_minus_baseline_w"] / (
                lo["zvs_minus_baseline_w"] - hi["zvs_minus_baseline_w"])
    OUT.write_text(json.dumps(dict(experiment="A62", classification="SENSITIVITY_ONLY", points=table,
                                   difference=diff, crossover_power_w_linear=cross,
                                   note="225 W points were added after the declared grid to locate the crossover"),
                              indent=1) + "\n")
    for design, rows in table.items():
        for x in rows:
            print("%-8s %5.0f W Ton %.3f P_B %.3f eff %.1f%% chan %.2f missC %.2f rev %.2f H %s L %s Hres %s Lres %s pk %.0f" % (
                design, x["power_w"], x["ton_cmd_s"] * 1e9, x["p_b_w"], 100 * x["efficiency_proxy"], x["channel_loss_w"],
                x["missed_capacitive_w"], x["reverse_loss_w"],
                "".join("T" if v else "F" for v in x["high_side_natural_zvs"]),
                "".join("T" if v else "F" for v in x["low_side_natural_zvs"]),
                [round(v, 1) for v in x["high_residual_v"]], [round(v, 1) for v in x["low_residual_v"]], x["peak_a"]))
    print(diff)
    print("crossover (linear):", cross)


if __name__ == "__main__":
    main()
