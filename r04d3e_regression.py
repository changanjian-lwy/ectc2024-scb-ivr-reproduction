"""Acceptance checks for the calibrated R04D3 ZVS exit."""

from __future__ import annotations

import re
from pathlib import Path


LOG = Path(__file__).resolve().parent / "paper_locked/02_ectc2024_main/spice/R04D3E_calibrated_ZVS_exit_acceptance.log"


def _value(text: str, name: str, *, at: bool = False) -> float:
    line = re.search(rf"^{re.escape(name)}:(.*)$", text, re.MULTILINE)
    if not line:
        raise ValueError(f"measurement {name} absent")
    if at:
        match = re.search(r"\bAT\s+([-+0-9.eE]+)", line.group(1))
        if match:
            return float(match.group(1))
    values = re.findall(r"=\s*([-+0-9.eE]+)", line.group(1))
    if not values:
        raise ValueError(f"numeric result for {name} absent")
    return float(values[-1])


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    values = {
        "low_off_s": _value(text, "t_ql1_gate_off", at=True),
        "il_low_off_a": _value(text, "il1_at_ql1_gate_off"),
        "high_zero_s": _value(text, "t_high_vds_zero", at=True),
        "il_high_zero_a": _value(text, "il1_at_high_vds_zero"),
        "high_on_s": _value(text, "t_qh1_gate_on", at=True),
        "il_high_on_a": _value(text, "il1_at_qh1_gate_on"),
        "dead_interval_s": _value(text, "dead_interval"),
        "event_delay_s": _value(text, "event_to_gate_delay"),
        "gate_overlap_v2": _value(text, "gate_overlap_max"),
        "low_gate_after_v": _value(text, "vgl1_after_qh1_on"),
        "high_gate_after_v": _value(text, "vgh1_after_qh1_on"),
        "vds_after_v": _value(text, "vds_hs_after_qh1_on"),
        "fraction": _value(text, "calibrated_neg_frac"),
    }
    checks = {
        "library_default_used": abs(values["fraction"] - 0.08) <= 1e-12,
        "event_order": values["low_off_s"] < values["high_zero_s"] <= values["high_on_s"],
        "negative_at_zero": values["il_high_zero_a"] < 0,
        "negative_at_high_gate_on": values["il_high_on_a"] < 0,
        "no_gate_overlap": abs(values["gate_overlap_v2"]) <= 1e-12,
        "latched_gate_state": values["low_gate_after_v"] == 0 and values["high_gate_after_v"] == 5,
        "high_side_clamped_near_zero": abs(values["vds_after_v"]) < 20e-3,
        "positive_dead_interval": values["dead_interval_s"] > 0,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "margin_note": "8% ideal operating point leaves about 2.38 A negative-current margin at QH1 gate-on",
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D3E exit acceptance failed")
