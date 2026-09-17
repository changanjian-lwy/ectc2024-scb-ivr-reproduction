"""Validate the two deliberately separate interval-3 experiment outcomes."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT


HERE = PROJECT_ROOT
SPICE = HERE / "paper_locked/02_ectc2024_main/spice"
P24_LOG = SPICE / "R04D3A_P24_interval3_same_phase_ZVS.log"
P25_LOG = SPICE / "R04D3B_P25_mode3_np4_chained_attempt.log"


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
        "p24_ql1_off_s": _value(p24, "p24_t_ql1_off", at=True),
        "p24_il1_off_a": _value(p24, "p24_il1_at_ql1_off"),
        "p24_vds_min_after_2ns_v": _value(p24, "p24_vds_hs_min_after_2ns"),
        "p24_x1_max_v": _value(p24, "p24_vds_ls_max"),
        "p25_il2_start_a": _value(p25, "p25_il2_start"),
        "p25_il2_end_a": _value(p25, "p25_il2_end"),
    }
    checks = {
        "p24_negative_target_observed": abs(values["p24_il1_off_a"] + 1.25) <= 1e-6,
        "p24_zvs_not_reached_with_selected_device_plugin": (
            'Measurement "p24_t3_high_vds_zero" FAIL\'ed' in p24
            and values["p24_vds_min_after_2ns_v"] > 0
        ),
        "p25_mode3_enters_with_wrong_current_sign": values["p25_il2_start_a"] < 0,
        "p25_current_moves_away_from_zero": values["p25_il2_end_a"] < values["p25_il2_start_a"],
        "p25_t3_not_observed": 'Measurement "p25_t3_il2_zero" FAIL\'ed' in p25,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "accepted failure characterization only: P24 1% negative-current target "
            "does not complete ZVS with the selected GS61008T scalar-capacitance plug-in; "
            "the isolated predecessor gives P25 Mode 3 the wrong iL2 entrance sign"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_results()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D3 accepted-failure regression changed")
