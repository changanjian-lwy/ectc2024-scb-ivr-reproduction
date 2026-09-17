"""Regression checks for the GS61008T device-only commutation branch."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT

from scb_ivr.device_library import (
    CapacitanceView,
    GS61008T,
    P25_GS61008T_POPULATION,
)


HERE = PROJECT_ROOT
LOG = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04D1B2_GS61008T_device_only_commutation.log"
)


def _value(text: str, name: str) -> float:
    line = re.search(rf"^{re.escape(name)}:(.*)$", text, re.MULTILINE)
    if not line:
        raise ValueError(f"measurement {name} absent from {LOG}")
    at_value = re.search(r"\bAT\s+([-+0-9.eE]+)", line.group(1))
    if at_value and name == "t_low_vds_zero":
        return float(at_value.group(1))
    values = re.findall(r"=\s*([-+0-9.eE]+)", line.group(1))
    if not values:
        raise ValueError(f"numeric result for {name} absent from {LOG}")
    return float(values[-1])


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    values = {
        name: _value(text, name)
        for name in (
            "t_low_vds_zero",
            "il1_at_low_zero",
            "high_vds_at_low_zero",
            "vc1_at_low_zero",
            "ch_device_used",
            "cl_device_used",
            "rhs_eq_used",
            "rls_eq_used",
            "np_explicit",
            "nm_explicit",
        )
    }
    population = P25_GS61008T_POPULATION
    expected_ch = GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, population.high_side_parallel
    )
    expected_cl = GS61008T.capacitance(
        CapacitanceView.TIME_EQUIVALENT, population.low_side_parallel
    )
    checks = {
        "spice_uses_library_high_side_cotr": values["ch_device_used"]
        == expected_ch,
        "spice_uses_two_parallel_low_side_cotr": values["cl_device_used"]
        == expected_cl,
        "spice_records_expected_parallel_rds": values["rhs_eq_used"] == 7e-3
        and values["rls_eq_used"] == 3.5e-3,
        "low_side_reaches_zero": 0 < values["t_low_vds_zero"] < 1e-9,
        "high_side_charges_to_phase_voltage": abs(
            values["high_vds_at_low_zero"] - 11.9806
        )
        <= 0.01,
        "incoming_current_remains_near_boundary_peak": abs(
            values["il1_at_low_zero"] - 125.0
        )
        <= 0.5,
        "architecture_counts_remain_explicit": values["np_explicit"] == 4
        and values["nm_explicit"] == 1,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "GS61008T CO(TR) device-only first-order timing estimate; excludes "
            "nonlinear 12-V Coss, external snubber, dead time and hardware loss"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D1-B2 regression failed")
