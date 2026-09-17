"""Regression checks for the P24 four-phase local-boundary replay."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT


HERE = PROJECT_ROOT
LOG = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04C_four_phase_local_boundary_replay.log"
)


def _scalar(text: str, name: str) -> float:
    line_match = re.search(
        rf"^{re.escape(name)}:(.*)$", text, re.MULTILINE
    )
    if not line_match:
        raise ValueError(f"measurement {name} absent from {LOG}")
    line = line_match.group(1)
    # LTspice WHEN measurements contain both the trigger expression (for
    # example I(L1)=0) and the actual result after AT.  The AT value must win.
    at_match = re.search(r"\bAT\s+([-+0-9.eE]+)", line)
    if at_match:
        return float(at_match.group(1))
    values = re.findall(r"=([-+0-9.eE]+)", line)
    if not values:
        raise ValueError(f"numeric result for {name} absent from {LOG}")
    return float(values[-1])


def validate_existing_result() -> dict:
    text = LOG.read_text(errors="replace")
    peaks = [_scalar(text, f"p{phase}_imax") for phase in range(1, 5)]
    zero_crossings = [
        _scalar(text, f"p{phase}_tzero") for phase in range(1, 5)
    ]
    negative_events = [
        _scalar(text, f"p{phase}_tneg2") for phase in range(1, 5)
    ]
    zero_shifts = [
        _scalar(text, name)
        for name in (
            "phase12_zero_shift",
            "phase23_zero_shift",
            "phase34_zero_shift",
        )
    ]
    checks = {
        "four_equal_peaks_near_r04a": all(
            abs(value - 125.109191895) <= 1e-6 for value in peaks
        ),
        "zero_crossings_shift_by_T_over_nP": all(
            abs(value - 50e-9) <= 1e-15 for value in zero_shifts
        ),
        "negative_events_shift_by_T_over_nP": all(
            abs((negative_events[index + 1] - negative_events[index]) - 50e-9)
            <= 2e-15
            for index in range(3)
        ),
        "nP_is_explicit_4": _scalar(text, "np_explicit") == 4,
        "nM_is_explicit_1": _scalar(text, "nm_explicit") == 1,
        "phase_spacing_is_50ns": abs(_scalar(text, "dtp_explicit") - 50e-9)
        <= 1e-18,
    }
    return {
        "measurements": {
            "peaks_a": peaks,
            "zero_crossings_s": zero_crossings,
            "negative_events_s": negative_events,
            "zero_crossing_shifts_s": zero_shifts,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "four staggered local analytical phases only; no flying-capacitor "
            "interaction, startup, Coss commutation, ZVS, ripple or loss claim"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04C regression failed")
