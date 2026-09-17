"""Regression checks for the bounded R04D1-B capacitance sensitivity."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT


HERE = PROJECT_ROOT
LOG = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04D1B_t1_symbolic_cap_commutation_sweep.log"
)


def _stepped_values(text: str, name: str) -> list[float]:
    block = re.search(
        rf"Measurement: {re.escape(name)}\s+(.*?)(?=\nMeasurement:|\Z)",
        text,
        re.DOTALL,
    )
    if not block:
        raise ValueError(f"measurement {name} absent from {LOG}")
    values: list[float] = []
    for line in block.group(1).splitlines():
        row = re.match(r"\s+\d+\s+([-+0-9.eE]+)", line)
        if row:
            values.append(float(row.group(1)))
    if len(values) != 3:
        raise ValueError(f"measurement {name} must contain three sweep rows")
    return values


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    values = {
        name: _stepped_values(text, name)
        for name in (
            "t_low_vds_zero",
            "il1_at_low_zero",
            "high_vds_at_low_zero",
            "vc1_at_low_zero",
            "il1_start",
            "ccomm_used",
            "np_explicit",
            "nm_explicit",
        )
    }
    times = values["t_low_vds_zero"]
    checks = {
        "declared_sweep_is_0p1_1_10nF": values["ccomm_used"]
        == [0.1e-9, 1e-9, 10e-9],
        "zero_time_increases_with_capacitance": times[0] < times[1] < times[2],
        "approximately_decade_timing_sensitivity": 8 < times[1] / times[0] < 12
        and 8 < times[2] / times[1] < 12,
        "high_side_is_charged_to_phase_voltage": all(
            abs(value - 11.9807) <= 0.01
            for value in values["high_vds_at_low_zero"]
        ),
        "incoming_current_is_continuous": all(
            abs(value - 124.932724) <= 0.05 for value in values["il1_start"]
        ),
        "architecture_counts_remain_explicit": values["np_explicit"]
        == [4.0, 4.0, 4.0]
        and values["nm_explicit"] == [1.0, 1.0, 1.0],
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "CH1=CL1 sensitivity only through the first low-side zero-voltage "
            "event; values are not P24 device data and post-zero overshoot is invalid"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D1-B regression failed")
