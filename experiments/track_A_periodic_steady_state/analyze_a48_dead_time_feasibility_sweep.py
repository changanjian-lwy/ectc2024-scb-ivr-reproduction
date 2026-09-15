"""Analyze A48's fixed-delay dead-time feasibility sweep.

Parses each generated case's LTspice .log for the .meas results and writes
coarse/refinement/fine result tables (CSV+JSON), same layout convention as
A41/A42/A45.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "A48_dead_time_feasibility_sweep"

NAME_RE = re.compile(
    r"a48_(?P<tag>coarse|refine|fine)_(?P<row>01pct|02pct|777bp)_tdead_(?P<td>[0-9p]+)ns"
)

PATTERNS = {
    "release_time_s": re.compile(r"p24_t_ql1_off:.*?AT\s+([0-9.eE+-]+)"),
    "release_current_a": re.compile(r"p24_il1_at_ql1_off:.*?=\s*([0-9.eE+-]+)"),
    "natural_zvs_time_s": re.compile(r"p24_t3_high_vds_zero:.*?AT\s+([0-9.eE+-]+)"),
    "natural_zvs_current_a": re.compile(r"p24_il1_at_t3:.*?=\s*([0-9.eE+-]+)"),
    "commutation_duration_s": re.compile(
        r"p24_commutation_duration:.*?=\s*([0-9.eE+-]+)"
    ),
    "forced_on_time_s": re.compile(r"p24_t_forced_on:.*?AT\s+([0-9.eE+-]+)"),
    "vds_at_forced_on_v": re.compile(r"p24_vds_at_forced_on:.*?=\s*([0-9.eE+-]+)"),
    "il1_at_forced_on_a": re.compile(r"p24_il1_at_forced_on:.*?=\s*([0-9.eE+-]+)"),
    "vds_hs_min_v": re.compile(r"p24_vds_hs_min:.*?=\s*([0-9.eE+-]+)"),
    "t_dead_ns_reported": re.compile(r"t_dead_ns:.*?=\s*([0-9.eE+-]+)"),
    "negative_target_a": re.compile(r"p24_negative_target:.*?=\s*([0-9.eE+-]+)"),
}

ROW_NEG_FRAC = {"01pct": 1.0, "02pct": 2.0, "777bp": 7.77}
ROW_SOURCE = {
    "01pct": "P24_EXPLICIT",
    "02pct": "P24_EXPLICIT",
    "777bp": "A42_NATURAL_ZVS_REFERENCE",
}


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    row = match.group("row")
    tag = match.group("tag")
    t_dead_ns_from_name = float(match.group("td").replace("p", "."))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    values: dict[str, float | None] = {}
    for key, pattern in PATTERNS.items():
        found = pattern.search(log)
        values[key] = float(found.group(1)) if found else None

    release_time_s = values["release_time_s"]
    forced_on_time_s = values["forced_on_time_s"]
    natural_zvs_time_s = values["natural_zvs_time_s"]

    forced_before_natural = None
    if forced_on_time_s is not None and natural_zvs_time_s is not None:
        forced_before_natural = forced_on_time_s < natural_zvs_time_s
    elif forced_on_time_s is not None and natural_zvs_time_s is None:
        forced_before_natural = True  # natural crossing never happens in-window

    row_dict = {
        "case": cir.stem,
        "tag": tag,
        "row": row,
        "negative_fraction_pct": ROW_NEG_FRAC[row],
        "source_region": ROW_SOURCE[row],
        "t_dead_ns_requested": t_dead_ns_from_name,
        "t_dead_ns_reported": values["t_dead_ns_reported"],
        "release_time_ns": (
            release_time_s * 1e9 if release_time_s is not None else None
        ),
        "release_current_a": values["release_current_a"],
        "natural_zvs_occurs_in_window": natural_zvs_time_s is not None,
        "natural_zvs_time_ns": (
            natural_zvs_time_s * 1e9 if natural_zvs_time_s is not None else None
        ),
        "commutation_duration_ns": (
            values["commutation_duration_s"] * 1e9
            if values["commutation_duration_s"] is not None
            else None
        ),
        "forced_on_time_ns": (
            forced_on_time_s * 1e9 if forced_on_time_s is not None else None
        ),
        "forced_on_before_natural_zvs": forced_before_natural,
        "vds_at_forced_on_v": values["vds_at_forced_on_v"],
        "il1_at_forced_on_a": values["il1_at_forced_on_a"],
        "vds_hs_min_v": values["vds_hs_min_v"],
        "negative_target_a": values["negative_target_a"],
    }
    return row_dict


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    coarse_rows = [parse_case(p) for p in sorted((HERE / "cases").glob("*.cir"))]
    refinement_rows = [
        parse_case(p) for p in sorted((HERE / "refinement_cases").glob("*.cir"))
    ]
    fine_rows = [parse_case(p) for p in sorted((HERE / "fine_cases").glob("*.cir"))]

    write_table(coarse_rows, HERE / "coarse_results")
    write_table(refinement_rows, HERE / "refinement_results")
    write_table(fine_rows, HERE / "fine_results")

    for row in coarse_rows:
        print(json.dumps(row))
    print(f"# coarse={len(coarse_rows)} refinement={len(refinement_rows)} "
          f"fine={len(fine_rows)}")


if __name__ == "__main__":
    main()
