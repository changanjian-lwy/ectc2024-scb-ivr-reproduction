"""Cross-check separate P24/P25 interval-2 replays without merging labels."""

from __future__ import annotations

import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
P24_LOG = HERE / "paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.log"
P25_LOG = HERE / "paper_locked/02_ectc2024_main/spice/R04D2B_P25_interval2_extended_np4_GS_plugin.log"


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


def validate_existing_results() -> dict:
    p24 = P24_LOG.read_text(errors="replace")
    p25 = P25_LOG.read_text(errors="replace")
    values = {
        "p24_low_zvs_s": _value(p24, "p24_t_low_zvs", at=True),
        "p24_il_at_low_zvs_a": _value(p24, "p24_il1_at_low_zvs"),
        "p24_t2_current_zero_s": _value(p24, "p24_t2_il1_zero", at=True),
        "p24_freewheel_s": _value(p24, "p24_freewheel_duration"),
        "p25_t2_low_zvs_s": _value(p25, "p25_t2_low_zvs", at=True),
        "p25_il1_at_t2_a": _value(p25, "p25_il1_at_t2"),
        "p25_il2_at_t2_a": _value(p25, "p25_il2_at_t2"),
        "p25_il3_at_t2_a": _value(p25, "p25_il3_at_t2"),
        "p25_il4_at_t2_a": _value(p25, "p25_il4_at_t2"),
    }
    inactive = [values[f"p25_il{phase}_at_t2_a"] for phase in (2, 3, 4)]
    checks = {
        "shared_physical_low_zvs_event": abs(
            values["p24_low_zvs_s"] - values["p25_t2_low_zvs_s"]
        )
        <= 1e-15,
        "shared_active_current_at_low_zvs": abs(
            values["p24_il_at_low_zvs_a"] - values["p25_il1_at_t2_a"]
        )
        <= 1e-5,
        "p24_t2_is_later_current_zero": values["p24_t2_current_zero_s"]
        > values["p24_low_zvs_s"] + 100e-9,
        "p24_duration_identity": abs(
            values["p24_freewheel_s"]
            - (values["p24_t2_current_zero_s"] - values["p24_low_zvs_s"])
        )
        <= 1e-15,
        "p25_extended_inactive_currents_match": max(inactive) - min(inactive)
        <= 1e-9,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "same low-side zero-voltage event, separate published t2 labels; "
            "P25 all-inactive-low command is an nP=4 extension"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_results()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D2 branch regression failed")
