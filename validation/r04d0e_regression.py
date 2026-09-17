"""Regression checks for the P25 all-inactive-low four-phase extension."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT

from scb_ivr.inactive_low_side_branches import P25_EXPANDED_TO_FOUR_PHASE


HERE = PROJECT_ROOT
LOG = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04D0E_p25_all_inactive_lows_four_phase_extension.log"
)


def _value(text: str, name: str) -> float:
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
        name: _value(text, name)
        for name in (
            "il1_at_ton",
            "il2_at_ton",
            "il3_at_ton",
            "il4_at_ton",
            "q_c1_intv",
            "q_c2_intv",
            "q_c3_intv",
            "np_explicit",
            "nm_explicit",
        )
    }
    inactive = [values[f"il{phase}_at_ton"] for phase in (2, 3, 4)]
    checks = {
        "branch_commands_all_inactive_lows": P25_EXPANDED_TO_FOUR_PHASE.commanded_on
        == ("SH1", "SL2", "SL3", "SL4"),
        "branch_is_not_mislabeled_p24": P25_EXPANDED_TO_FOUR_PHASE.evidence.value
        == "CROSS_PAPER_EXTENSION",
        "phase1_matches_p24_minimal_branch": abs(values["il1_at_ton"] - 124.782991351)
        <= 1e-6,
        "all_inactive_currents_match": max(inactive) - min(inactive) <= 1e-9,
        "all_inactive_currents_fall": all(value < -11.3 for value in inactive),
        "only_c1_moves_charge_in_this_interval": values["q_c1_intv"] > 1e-6
        and abs(values["q_c2_intv"]) < 1e-12
        and abs(values["q_c3_intv"]) < 1e-12,
        "architecture_counts_remain_explicit": values["np_explicit"] == 4
        and values["nm_explicit"] == 1,
    }
    return {
        "measurements": values,
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "P25 three-phase all-inactive-low rule extended to nP=4; "
            "not an explicit P24 gate-vector claim"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04D0E regression failed")
