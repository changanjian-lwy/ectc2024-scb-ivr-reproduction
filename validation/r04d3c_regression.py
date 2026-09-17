"""Lock the R04D3C five-percent cross-paper threshold result."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT


LOG = PROJECT_ROOT / "paper_locked/02_ectc2024_main/spice/R04D3C_P25_5pct_threshold_mapped_to_P24_commutation.log"


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
        "low_side_off_s": _value(text, "t_low_side_off", at=True),
        "negative_current_a": _value(text, "il1_at_low_side_off"),
        "high_side_vds_min_v": _value(text, "vds_hs_min_after_off"),
        "switch_node_max_v": _value(text, "vx1_max"),
        "negative_target_a": _value(text, "negative_target"),
    }
    checks = {
        "five_percent_target_is_6p25a": abs(values["negative_target_a"] - 6.25) <= 1e-9,
        "target_event_observed": abs(values["negative_current_a"] + 6.25) <= 1e-6,
        "zvs_not_reached": (
            'Measurement "t_high_vds_zero" FAIL\'ed' in text
            and values["high_side_vds_min_v"] > 0
        ),
        "partial_commutation_observed": values["switch_node_max_v"] > 8.0,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": "P25 5% control target mapped to the unchanged P24 local commutation model; not a P24 reproduction claim",
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D3C regression changed")
