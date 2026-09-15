"""Analyze R04E6's EPE2019 3-state charge-redistribution ladder-bootstrap grid.

Parses each generated case's LTspice .log for its .meas results, computes
the same LADDER_ERR metric R02B already uses
(`abs(VC1-36)/36+abs(VC2-24)/24+abs(VC3-12)/12`) at the end of cycle 1 and
at the end of the run, grades each cell, and writes a combined CSV+JSON
table.

Grading (documented here, not a paper-given threshold -- see BOUNDARY.md
Section 8; this experiment's OWN working definition, exactly like R04E5's
"within 5% of 1 V" convention):
  - LOCAL_PASS: LADDER_ERR strictly decreases from end-of-cycle-1 to
    end-of-run AND the end-of-run LADDER_ERR is below 0.15 (aggregate 15%
    across the three capacitors).
  - SENSITIVITY_ONLY: LADDER_ERR decreases (or the cell has only 1 cycle,
    so no trend is observable) but does not reach the 0.15 band.
  - NOT_CONVERGING: LADDER_ERR does not decrease cycle-over-cycle (the
    ladder is not approaching the target with more cycles at this hold
    time).

No pass/fail threshold is adopted for peak current (BOUNDARY.md Section 4,
item 4 -- the source gives none). Peak currents are reported as plain
numbers plus a qualitative `current_note` flag for anything exceeding
1000 A (10x the P24 Eq.-2 125-A single-phase peak reference used
elsewhere in this project) -- descriptive only, not a grade.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E6_epe2019_charge_redistribution_startup"
CASES = HERE / "cases"

NAME_RE = re.compile(r"r04e6_th_(?P<th>[0-9p]+)ns_ncyc_(?P<ncyc>[0-9]+)")

SCALAR_KEYS = [
    "vout_final",
    "il1_max",
    "il1_min",
    "il2_max",
    "il2_min",
    "il3_max",
    "il3_min",
    "ics1_max",
    "ics1_min",
    "ics2_max",
    "ics2_min",
    "ics3_max",
    "ics3_min",
    "ics1_inrush_cyc1",
    "ics1_stateb_cyc1_max",
    "ics1_stateb_cyc1_min",
    "ics2_stateb_cyc1_max",
    "ics2_stateb_cyc1_min",
    "ics2_statec_cyc1_max",
    "ics2_statec_cyc1_min",
    "ics3_statec_cyc1_max",
    "ics3_statec_cyc1_min",
]

CURRENT_FLAG_A = 1000.0
TARGETS = {"vc1": 36.0, "vc2": 24.0, "vc3": 12.0}


def build_patterns(ncyc: int) -> dict[str, re.Pattern]:
    patterns = {key: re.compile(rf"{key}:.*?=\s*([0-9.eE+-]+)") for key in SCALAR_KEYS}
    for j in range(1, ncyc + 1):
        for k in ("vc1", "vc2", "vc3"):
            key = f"{k}_cyc{j}"
            patterns[key] = re.compile(rf"{key}:.*?=\s*([0-9.eE+-]+)")
    return patterns


def ladder_err(vc1: float, vc2: float, vc3: float) -> float:
    return (
        abs(vc1 - TARGETS["vc1"]) / TARGETS["vc1"]
        + abs(vc2 - TARGETS["vc2"]) / TARGETS["vc2"]
        + abs(vc3 - TARGETS["vc3"]) / TARGETS["vc3"]
    )


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    th_ns = float(match.group("th").replace("p", "."))
    ncyc = int(match.group("ncyc"))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    patterns = build_patterns(ncyc)
    values: dict[str, float | None] = {}
    for key, pattern in patterns.items():
        found = pattern.search(log)
        values[key] = float(found.group(1)) if found else None

    cyc1_err = None
    final_err = None
    if all(values.get(f"{k}_cyc1") is not None for k in ("vc1", "vc2", "vc3")):
        cyc1_err = ladder_err(values["vc1_cyc1"], values["vc2_cyc1"], values["vc3_cyc1"])
    last_key = f"cyc{ncyc}"
    if all(values.get(f"{k}_{last_key}") is not None for k in ("vc1", "vc2", "vc3")):
        final_err = ladder_err(
            values[f"vc1_{last_key}"], values[f"vc2_{last_key}"], values[f"vc3_{last_key}"]
        )

    if ncyc == 1:
        trend = "SINGLE_CYCLE_NO_TREND"
    elif final_err is not None and cyc1_err is not None:
        trend = "IMPROVING" if final_err < cyc1_err else "NOT_IMPROVING"
    else:
        trend = "UNKNOWN"

    if final_err is None:
        grade = "MISSING_DATA"
    elif trend == "NOT_IMPROVING":
        grade = "NOT_CONVERGING"
    elif final_err < 0.15:
        grade = "LOCAL_PASS"
    else:
        grade = "SENSITIVITY_ONLY"

    peak_currents = [
        values.get(k)
        for k in (
            "il1_max", "il1_min", "il2_max", "il2_min", "il3_max", "il3_min",
            "ics1_max", "ics1_min", "ics2_max", "ics2_min", "ics3_max", "ics3_min",
        )
        if values.get(k) is not None
    ]
    max_abs_current = max((abs(v) for v in peak_currents), default=None)
    current_note = (
        f"peak |I| = {max_abs_current:.3g} A exceeds {CURRENT_FLAG_A:g} A "
        "(descriptive flag only, no source-given threshold)"
        if max_abs_current is not None and max_abs_current > CURRENT_FLAG_A
        else ""
    )

    row = {
        "case": cir.stem,
        "th_ns": th_ns,
        "ncyc": ncyc,
        "vc1_cyc1_v": values.get("vc1_cyc1"),
        "vc2_cyc1_v": values.get("vc2_cyc1"),
        "vc3_cyc1_v": values.get("vc3_cyc1"),
        "vc1_final_v": values.get(f"vc1_{last_key}"),
        "vc2_final_v": values.get(f"vc2_{last_key}"),
        "vc3_final_v": values.get(f"vc3_{last_key}"),
        "ladder_err_cyc1": cyc1_err,
        "ladder_err_final": final_err,
        "trend": trend,
        "vout_final_v": values.get("vout_final"),
        "il1_max_a": values.get("il1_max"),
        "il1_min_a": values.get("il1_min"),
        "il2_max_a": values.get("il2_max"),
        "il2_min_a": values.get("il2_min"),
        "il3_max_a": values.get("il3_max"),
        "il3_min_a": values.get("il3_min"),
        "ics1_max_a": values.get("ics1_max"),
        "ics1_min_a": values.get("ics1_min"),
        "ics2_max_a": values.get("ics2_max"),
        "ics2_min_a": values.get("ics2_min"),
        "ics3_max_a": values.get("ics3_max"),
        "ics3_min_a": values.get("ics3_min"),
        "ics1_inrush_cyc1_a": values.get("ics1_inrush_cyc1"),
        "ics1_stateb_cyc1_max_a": values.get("ics1_stateb_cyc1_max"),
        "ics1_stateb_cyc1_min_a": values.get("ics1_stateb_cyc1_min"),
        "ics2_stateb_cyc1_max_a": values.get("ics2_stateb_cyc1_max"),
        "ics2_stateb_cyc1_min_a": values.get("ics2_stateb_cyc1_min"),
        "ics2_statec_cyc1_max_a": values.get("ics2_statec_cyc1_max"),
        "ics2_statec_cyc1_min_a": values.get("ics2_statec_cyc1_min"),
        "ics3_statec_cyc1_max_a": values.get("ics3_statec_cyc1_max"),
        "ics3_statec_cyc1_min_a": values.get("ics3_statec_cyc1_min"),
        "max_abs_current_a": max_abs_current,
        "current_note": current_note,
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
    rows.sort(key=lambda r: (r["th_ns"], r["ncyc"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")
    for grade in ("LOCAL_PASS", "SENSITIVITY_ONLY", "NOT_CONVERGING", "MISSING_DATA"):
        count = sum(1 for r in rows if r["grade"] == grade)
        print(f"# {grade}: {count}")


if __name__ == "__main__":
    main()
