"""Check that the previously successful R04A result remains reproducible."""

from __future__ import annotations

import re
from validation.paths import PROJECT_ROOT

from scb_ivr.assembly_planner import assemble
from scb_ivr.experiment_profiles import R04A_LOCAL_BOUNDARY_REPLAY


HERE = PROJECT_ROOT
NETLIST = (
    HERE
    / "paper_locked/02_ectc2024_main/spice/"
    "R04A_single_phase_latched_boundary_two_L_cases.cir"
)
LOG = NETLIST.with_suffix(".log")


def _measurement(log_text: str, name: str) -> list[float]:
    match = re.search(
        rf"Measurement: {re.escape(name)}\s+.*?(?=\nMeasurement:|\Z)",
        log_text,
        re.DOTALL,
    )
    if not match:
        raise ValueError(f"measurement {name} absent from {LOG}")
    values = []
    for line in match.group(0).splitlines():
        row = re.match(r"\s+\d+\s+([-+0-9.eE]+)", line)
        if row:
            values.append(float(row.group(1)))
    return values


def validate_existing_result() -> dict:
    plan = assemble(R04A_LOCAL_BOUNDARY_REPLAY)
    plan.require_ready()
    text = LOG.read_text(errors="replace")
    peaks = _measurement(text, "i_max")
    ton = _measurement(text, "ton_num")
    if len(peaks) != 2 or len(ton) != 2:
        raise AssertionError("R04A must retain exactly two non-fitted L branches")
    checks = {
        "equation_L_peak_near_125A": abs(peaks[0] - 125.0) <= 0.25,
        "table_L_peak_near_68p5A": abs(peaks[1] - 68.5) <= 0.25,
        "both_use_p24_Ton": all(abs(x - 16.6666666667e-9) <= 1e-13 for x in ton),
    }
    return {
        "assembly_ready": plan.ready,
        "selected_modules": [m.module_id for m in plan.selected_modules],
        "measurements": {"i_max_a": peaks, "ton_s": ton},
        "checks": checks,
        "passed": all(checks.values()),
        "claim_boundary": (
            "single-phase analytical state replay only; no full topology, "
            "startup, Coss commutation, ZVS, loss or hardware claim"
        ),
    }


if __name__ == "__main__":
    result = validate_existing_result()
    print(result)
    if not result["passed"]:
        raise SystemExit("R04A regression failed")
