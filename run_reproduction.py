"""Generate the first reproducible design-space sweep for the 2024 paper."""

from __future__ import annotations

import csv
from pathlib import Path

from ivr_framework import SystemSpec, evaluate_converter, evaluate_embedded_inductor


PHASES = (4, 6, 8, 16)
MODULES = (2, 4, 8, 16, 32, 64)
FREQUENCIES_MHZ = (1, 5, 10, 50, 100)
TABLE3_FREQUENCIES_MHZ = (1, 5, 10)
INDUCTOR_PEAK_RATINGS_A = (5, 10)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_plots(output_dir: Path, table1_rows: list[dict]) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    spec = SystemSpec()

    maximum_frequency = {
        phases: phases * spec.vout_v / (spec.vin_v * spec.minimum_on_time_s) / 1e6
        for phases in PHASES
    }
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar([str(p) for p in PHASES], maximum_frequency.values())
    ax.set_xlabel("Number of phases per module")
    ax.set_ylabel("Maximum frequency from minimum on-time (MHz)")
    ax.set_title("2024 ECTC IVR on-time feasibility boundary")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "maximum_feasible_frequency.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    for modules in MODULES:
        points = [
            row
            for row in table1_rows
            if row["phases"] == 4 and row["modules"] == modules
        ]
        ax.loglog(
            [row["switching_frequency_mhz"] for row in points],
            [row["critical_inductance_nh"] for row in points],
            marker="o",
            label=f"nM={modules}",
        )
    ax.set_xlabel("Switching frequency (MHz)")
    ax.set_ylabel("Critical inductance per phase (nH)")
    ax.set_title("Critical inductance sweep for four-phase configurations")
    ax.grid(which="both", alpha=0.25)
    ax.legend(ncol=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "critical_inductance_sweep.png", dpi=180)
    plt.close(fig)
    return True


def main() -> None:
    spec = SystemSpec()
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    table1_rows = []
    for phases in PHASES:
        for modules in MODULES:
            for frequency_mhz in FREQUENCIES_MHZ:
                result = evaluate_converter(
                    spec, phases, modules, frequency_mhz * 1e6
                )
                table1_rows.append(result.as_dict())

    table3_rows = []
    # Table 3 in the paper fixes the converter to four phases.
    for modules in MODULES:
        for frequency_mhz in TABLE3_FREQUENCIES_MHZ:
            for peak_rating_a in INDUCTOR_PEAK_RATINGS_A:
                result = evaluate_embedded_inductor(
                    spec,
                    phases=4,
                    modules=modules,
                    switching_frequency_hz=frequency_mhz * 1e6,
                    peak_rating_a=peak_rating_a,
                )
                table3_rows.append(result.as_dict())

    write_csv(output_dir / "table1_reproduced.csv", table1_rows)
    write_csv(output_dir / "table3_reproduced.csv", table3_rows)
    plotted = make_plots(output_dir, table1_rows)

    example = evaluate_converter(spec, phases=4, modules=8, switching_frequency_hz=5e6)
    embedded = evaluate_embedded_inductor(
        spec,
        phases=4,
        modules=8,
        switching_frequency_hz=5e6,
        peak_rating_a=5,
    )
    print("Reproduction completed.")
    print(f"Output directory: {output_dir}")
    print("Example: 4 phases, 8 modules, 5 MHz")
    print(f"  duty cycle       = {example.duty_cycle * 100:.3f} %")
    print(f"  high-side Ton    = {example.high_side_on_time_s * 1e9:.3f} ns")
    print(f"  IL peak          = {example.inductor_peak_current_a:.3f} A")
    print(f"  Lcrit            = {example.critical_inductance_h * 1e9:.3f} nH")
    print(f"  on-time feasible = {example.feasible_on_time}")
    print("Embedded inductor, 5-A unit rating:")
    print(f"  exact count      = {embedded.parallel_inductors_exact:.3f}")
    print(f"  ceiling count    = {embedded.parallel_inductors_engineering}")
    print(f"  unit inductance  = {embedded.unit_inductance_h * 1e9:.3f} nH")
    if embedded.parallel_inductors_exact != embedded.parallel_inductors_engineering:
        print("  NOTE: the paper reports 12 units here; Eq. (5) gives 12.5, so a")
        print("        conservative implementation needs 13 units.")
    if not plotted:
        print("Plots were skipped because matplotlib is not installed.")


if __name__ == "__main__":
    main()

