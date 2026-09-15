"""Analyze R04E5's ramped-duty, event-gated zero-start sensitivity grid.

Parses each generated case's LTspice .log for its .meas results, grades the
cell against the safety/bootstrap definitions fixed in BOUNDARY.md, and
writes a combined CSV+JSON result table.

Grading (see BOUNDARY.md Sections 6-7 for the exact numeric definitions):
  - PHYSICAL_BOUNDARY_FAIL: I(L1) left [-250, 250] A (2x the P24 Eq.-2
    125-A phase-peak target) at any point in the run.
  - LOCAL_PASS: current stayed inside the bound AND Vout at the end of the
    run is within 5% of 1 V ([0.95, 1.05] V).
  - CONTROLLER_GUARD_PASS: current stayed inside the bound, Vout did not
    reach the 5% band, but the late-window (last 20% of the run) current
    swing is negligible (<0.05 A) -- the machine safely parked in one
    state rather than chattering or diverging.
  - EXPECTED_FAILURE: current stayed inside the bound but Vout did not
    reach the 5% band and the machine kept cycling (not parked) --
    the stalled-bootstrap outcome.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E5_ramped_duty_event_gated_zero_start"
CASES = HERE / "cases"

NAME_RE = re.compile(
    r"r04e5_tsoft_(?P<tsoft>[0-9p]+)us_ilimit_(?P<ilim>[0-9p]+)a"
)

PATTERNS = {
    "state_final": re.compile(r"state_final:.*?=\s*([0-9.eE+-]+)"),
    "vout_final_v": re.compile(r"vout_final:.*?=\s*([0-9.eE+-]+)"),
    "vout_at_25pct_v": re.compile(r"vout_at_25pct:.*?=\s*([0-9.eE+-]+)"),
    "vout_at_50pct_v": re.compile(r"vout_at_50pct:.*?=\s*([0-9.eE+-]+)"),
    "vout_at_75pct_v": re.compile(r"vout_at_75pct:.*?=\s*([0-9.eE+-]+)"),
    "vout_at_tsoft_v": re.compile(r"vout_at_tsoft:.*?=\s*([0-9.eE+-]+)"),
    "vout_peak_v": re.compile(r"vout_peak:.*?=\s*([0-9.eE+-]+)"),
    "il1_max_a": re.compile(r"il1_max:.*?=\s*([0-9.eE+-]+)"),
    "il1_min_a": re.compile(r"il1_min:.*?=\s*([0-9.eE+-]+)"),
    "il1_max_late_a": re.compile(r"il1_max_late:.*?=\s*([0-9.eE+-]+)"),
    "il1_min_late_a": re.compile(r"il1_min_late:.*?=\s*([0-9.eE+-]+)"),
    "vc1_final_v": re.compile(r"vc1_final:.*?=\s*([0-9.eE+-]+)"),
}

CURRENT_BOUND_A = 250.0  # 2x P24 Eq.-2 125-A phase-peak target.
VOUT_BAND = (0.95, 1.05)
LATE_WINDOW_PARKED_A = 0.05


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    tsoft_us = float(match.group("tsoft").replace("p", "."))
    i_limit_a = float(match.group("ilim").replace("p", "."))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    values: dict[str, float | None] = {}
    for key, pattern in PATTERNS.items():
        found = pattern.search(log)
        values[key] = float(found.group(1)) if found else None

    il1_max = values["il1_max_a"]
    il1_min = values["il1_min_a"]
    vout_final = values["vout_final_v"]
    il1_max_late = values["il1_max_late_a"]
    il1_min_late = values["il1_min_late_a"]

    within_bound = (
        il1_max is not None
        and il1_min is not None
        and il1_max <= CURRENT_BOUND_A
        and il1_min >= -CURRENT_BOUND_A
    )
    vout_ok = (
        vout_final is not None
        and VOUT_BAND[0] <= vout_final <= VOUT_BAND[1]
    )
    late_swing = None
    if il1_max_late is not None and il1_min_late is not None:
        late_swing = il1_max_late - il1_min_late
    parked = late_swing is not None and late_swing < LATE_WINDOW_PARKED_A

    if not within_bound:
        grade = "PHYSICAL_BOUNDARY_FAIL"
    elif vout_ok:
        grade = "LOCAL_PASS"
    elif parked:
        grade = "CONTROLLER_GUARD_PASS"
    else:
        grade = "EXPECTED_FAILURE"

    row = {
        "case": cir.stem,
        "tsoft_us": tsoft_us,
        "i_limit_a": i_limit_a,
        "state_final": values["state_final"],
        "vout_at_25pct_v": values["vout_at_25pct_v"],
        "vout_at_50pct_v": values["vout_at_50pct_v"],
        "vout_at_75pct_v": values["vout_at_75pct_v"],
        "vout_at_tsoft_v": values["vout_at_tsoft_v"],
        "vout_final_v": vout_final,
        "vout_peak_v": values["vout_peak_v"],
        "il1_max_a": il1_max,
        "il1_min_a": il1_min,
        "il1_max_late_a": il1_max_late,
        "il1_min_late_a": il1_min_late,
        "late_window_current_swing_a": late_swing,
        "vc1_final_v": values["vc1_final_v"],
        "within_current_bound": within_bound,
        "vout_within_5pct_of_1v": vout_ok,
        "machine_parked_late": parked,
        "grade": grade,
    }
    return row


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = [parse_case(p) for p in sorted(CASES.glob("*.cir"))]
    rows.sort(key=lambda r: (r["tsoft_us"], r["i_limit_a"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")
    for grade in ("LOCAL_PASS", "CONTROLLER_GUARD_PASS", "EXPECTED_FAILURE", "PHYSICAL_BOUNDARY_FAIL"):
        count = sum(1 for r in rows if r["grade"] == grade)
        print(f"# {grade}: {count}")


if __name__ == "__main__":
    main()
