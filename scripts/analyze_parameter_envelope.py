"""Print deterministic P24/P25 parameter envelopes without fitting unknown data."""

from __future__ import annotations

import json

from scb_ivr.feasibility_envelope import OperatingPoint, envelope_point
from scb_ivr.parameter_contract import ClaimLevel, request_payload


CASES = {
    "P24_4phase_4module": {
        "operating_point": OperatingPoint(48.0, 1.0, 1000.0, 4, 4, 5e6),
        "inductances_h": (1.4666666666666667e-9, 2.68e-9),
        "negative_fractions": (0.01, 0.02, 0.05, 0.08, 0.10),
    },
    "P25_3phase_3module": {
        "operating_point": OperatingPoint(12.0, 1.0, 200.0, 3, 3, 0.5e6),
        "inductances_h": (22e-9, 32.1e-9),
        "negative_fractions": (0.05, 0.08, 0.10),
    },
}


def build_report() -> dict:
    cases = {}
    for case_id, case in CASES.items():
        point = case["operating_point"]
        rows = [
            envelope_point(point, inductance, fraction).as_dict()
            for inductance in case["inductances_h"]
            for fraction in case["negative_fractions"]
        ]
        cases[case_id] = {
            "boundary": (
                "equal-ladder phase voltage and constant-drive triangular ramp; "
                "energy is a local upper budget, not a full-network ZVS proof"
            ),
            "paper_on_time_ns": point.paper_on_time_s * 1e9,
            "equal_ladder_drive_voltage_v": point.equal_ladder_drive_voltage_v,
            "rows": rows,
        }
    return {
        "cases": cases,
        "minimum_information_for_local_zvs": request_payload(ClaimLevel.LOCAL_ZVS),
        "minimum_information_for_periodic_multiphase": request_payload(
            ClaimLevel.PERIODIC_MULTIPHASE
        ),
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
