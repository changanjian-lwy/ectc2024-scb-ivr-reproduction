"""Scan only P25's published 5%-10% negative-current design interval."""
import csv
from pathlib import Path
import numpy as np

from p25_native_fixed_slot_ring import documented_seed, ring


OUT = Path(__file__).parent / "numerical_runs/01_full_ring_calibration"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # P25's ideal phase peak from 2*Io/(nP*nM) is 44.444 A.
    ideal_peak = 2.0 * 200.0 / (3.0 * 3.0)
    rows = []
    # Coarse 0.25-percentage-point scan first; refine only around a crossing.
    for fraction in np.linspace(0.05, 0.10, 21):
        target = fraction * ideal_peak
        result = ring(documented_seed(target), negative_target=target)
        first = result.history[0]
        rows.append({
            "fraction": fraction,
            "target_a": target,
            "handoffs_reached": len(result.history),
            "ring_passed": result.passed,
            "first_peak_a": first.get("peak_a", float("nan")),
            "first_vds_slot_v": first.get("next_vds_slot_v", float("nan")),
            "first_release_ns": first.get("next_low_release_ns", float("nan")),
            "first_failure": first.get("failure", ""),
            "last_failure": result.history[-1].get("failure", "") if result.history else "",
        })
    with (OUT / "target_scan.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

    admissible = [r for r in rows if np.isfinite(r["first_vds_slot_v"])
                  and r["first_vds_slot_v"] <= 1e-3]
    print("ideal_peak_A", ideal_peak)
    if admissible:
        print("first fixed-slot admission", admissible[0])
        print("last fixed-slot admission", admissible[-1])
    else:
        print("no first-handoff fixed-slot admission in 5%-10% interval")
    max_handoffs = max(r["handoffs_reached"] for r in rows)
    print("maximum_handoffs_reached", max_handoffs)
    for r in rows:
        if r["handoffs_reached"] == max_handoffs:
            print("representative_max_handoff_case", r)
            break


if __name__ == "__main__":
    main()
