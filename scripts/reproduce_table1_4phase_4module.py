"""Audit the 4-phase, 4-module row of Table 1 in the 2024 ECTC paper."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from scb_ivr.ivr_framework import (
    SystemSpec,
    critical_inductance,
    duty_cycle,
    high_side_on_time,
    inductor_peak_current,
)


NPHASES = 4
NMODULES = 4
FREQUENCIES_MHZ = (1, 5, 10, 50, 100)
TABLE1_TON_NS = (83.4, 16.7, 8.4, 1.7, 0.840)
TABLE1_LCRIT_NH = (13.44, 2.68, 1.34, 0.28, 0.14)
NUMERICAL_AGREEMENT_LIMIT_PERCENT = 2.0


def build_audit() -> dict:
    spec = SystemSpec()
    duty = duty_cycle(spec, NPHASES)
    power_per_module = spec.pout_w / NMODULES
    peak_current = inductor_peak_current(spec, NPHASES, NMODULES)
    rows = []

    for f_mhz, table_ton_ns, table_l_nh in zip(
        FREQUENCIES_MHZ, TABLE1_TON_NS, TABLE1_LCRIT_NH
    ):
        frequency = f_mhz * 1e6
        ton_ns = high_side_on_time(spec, NPHASES, frequency) * 1e9
        equation4_l_nh = (
            critical_inductance(spec, NPHASES, NMODULES, frequency) * 1e9
        )
        ton_error = 100 * (ton_ns - table_ton_ns) / table_ton_ns
        lcrit_error = 100 * (equation4_l_nh - table_l_nh) / table_l_nh
        rows.append(
            {
                "frequency_mhz": f_mhz,
                "power_per_module_w": power_per_module,
                "duty_percent_calculated": 100 * duty,
                "phase_peak_current_a_calculated": peak_current,
                "ton_ns_calculated": ton_ns,
                "ton_ns_table1": table_ton_ns,
                "ton_error_percent": ton_error,
                "ton_status": (
                    "PASS"
                    if abs(ton_error) <= NUMERICAL_AGREEMENT_LIMIT_PERCENT
                    else "FAIL"
                ),
                "ton_meets_3p4ns": ton_ns >= spec.minimum_on_time_s * 1e9,
                "lcrit_nh_equation4": equation4_l_nh,
                "lcrit_nh_table1": table_l_nh,
                "table1_over_equation4": table_l_nh / equation4_l_nh,
                "lcrit_error_percent_vs_table": lcrit_error,
                "lcrit_status": (
                    "CONFLICT"
                    if abs(lcrit_error) > NUMERICAL_AGREEMENT_LIMIT_PERCENT
                    else "PASS"
                ),
            }
        )
    return {
        "scope": "2024 ECTC Table I, 4-phase/4-module row",
        "units": "SI internally; ns/nH only in report fields",
        "numerical_agreement_limit_percent": NUMERICAL_AGREEMENT_LIMIT_PERCENT,
        "boundary_policy": (
            "Paper equations are evaluated literally. A mismatch is reported "
            "as CONFLICT and is never removed by fitting."
        ),
        "inputs": {
            "vin_v": spec.vin_v,
            "vout_v": spec.vout_v,
            "pout_w": spec.pout_w,
            "phases": NPHASES,
            "modules": NMODULES,
            "minimum_on_time_ns": spec.minimum_on_time_s * 1e9,
        },
        "summary": {
            "eq1_duty_percent": 100 * duty,
            "eq2_peak_current_a": peak_current,
            "eq3_all_rows_pass_tolerance": all(
                r["ton_status"] == "PASS" for r in rows
            ),
            "eq4_matches_table1": all(r["lcrit_status"] == "PASS" for r in rows),
            "overall_status": "PARTIAL_WITH_DOCUMENTED_CONFLICT",
        },
        "rows": rows,
    }


def main() -> None:
    report = build_audit()
    rows = report["rows"]
    output = (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "table1_4phase_4module_audit.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    json_output = output.with_suffix(".json")
    json_output.write_text(json.dumps(report, indent=2) + "\n")
    print(output)
    print(json_output)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
