"""Regression checks for the P24 shared-ladder first interval."""

from __future__ import annotations

import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
LOG = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04D0_p24_first_interval_shared_ladder.log"
)


def _measurement(text: str, name: str) -> float:
    match = re.search(rf"^{re.escape(name)}:(.*)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"measurement {name} absent from {LOG}")
    values = re.findall(r"=\s*([-+0-9.eE]+)", match.group(1))
    if not values:
        raise ValueError(f"numeric result for {name} absent from {LOG}")
    return float(values[-1])


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    values = {
        name: _measurement(text, name)
        for name in (
            "il1_max",
            "il2_at_ton",
            "vc1_start",
            "vc1_end",
            "vc2_start",
            "vc2_end",
            "q_c1_intv",
            "q_c2_intv",
            "np_explicit",
            "nm_explicit",
            "ton_explicit",
        )
    }
    checks = {
        "phase1_peak_near_125A": abs(values["il1_max"] - 125.0) <= 0.25,
        "adjacent_phase_current_near_minus_11p36A": abs(
            values["il2_at_ton"] + 11.363636
        )
        <= 0.05,
        "c1_receives_positive_charge": values["q_c1_intv"] > 1e-6,
        "c1_charge_matches_voltage_change": abs(
            values["q_c1_intv"]
            - 53.8e-6 * (values["vc1_end"] - values["vc1_start"])
        )
        <= 5e-10,
        "c2_charge_is_negligible": abs(values["q_c2_intv"]) <= 1e-12,
        "nP_is_explicit_4": values["np_explicit"] == 4,
        "nM_is_explicit_1": values["nm_explicit"] == 1,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "P24 interval-1 two-phase subnetwork only; capacitor initial "
            "condition is not a self-balance, startup, full-period or ZVS claim"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D0 regression failed")
