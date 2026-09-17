"""Analyze R04E20's four new (CDIV, Tramp) cells testing the parallel
math-model effort's own charge-conservation law (Tramp_threshold =
CDIV*Vin/(4*250A)), and merge in R04E18's own two already-completed
CDIV=300uF cells (e18_div_f3_t5, e18_div_f3_t22p87) by reference, to
produce the complete 6-row table BOUNDARY.md Section 3 calls for.

Parses the four new cells' LTspice .log files for their non-stepped
.meas results (same single-cell log format as R04E14-R04E19's own
analyze scripts), merges in R04E18's own two already-published
divider-PRESENT CDIV=300uF cells (read from R04E18's own committed
results.json, NOT re-run), computes the CORRECTED per-phase hazard
measure max(|IL_min|,IL_max) for all six rows (R04E19's own Section 3
correction -- IL_max alone understates hazard for phases whose largest
excursion is on the negative side), and writes results.csv/results.json
for the complete 6-row table plus predicted-vs-actual columns.

Case filenames: e20_c<CDIV>_t<TRAMP> (values in uF/us, 'p' for a
decimal point) for the new cells this experiment ran.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"
R04E18_RESULTS = (
    HERE.parent
    / "R04E18_divider_present_tramp_boundary"
    / "results.json"
)

VIN = 48.0
ILIMIT = 250.0

NAME_RE = re.compile(r"e20_c(?P<cdiv>[0-9pP]+)_t(?P<tramp>[0-9pP]+)")

SCALAR_KEYS = [
    "vc1_init", "vc2_init", "vc3_init",
    "vc1_at_tramp", "vc2_at_tramp", "vc3_at_tramp", "vout_at_tramp",
    "vc1_final", "vc2_final", "vc3_final", "vout_final",
    "vout_pk", "vout_min", "vout_overshoot",
    "iin_pk",
    "il1_min", "il1_max", "il2_min", "il2_max",
    "il3_min", "il3_max", "il4_min", "il4_max",
    "vout_err", "vc1_err", "vc2_err", "vc3_err", "ladder_err",
]

REUSED_R04E18_CASES = ["e18_div_f3_t5", "e18_div_f3_t22p87"]


def decode(tag: str) -> float:
    return float(tag.replace("p", "."))


def predicted_threshold_us(cdiv_uf: float) -> float:
    # Idiv = (CDIV/4) * Vin / Tramp = ILIMIT  =>  Tramp = CDIV*Vin/(4*ILIMIT)
    # cdiv_uf in uF, result in us (uF*V/A = us, dimensionally consistent
    # since 1uF*1V/1A = 1us).
    return cdiv_uf * VIN / (4.0 * ILIMIT)


def hazards(values: dict) -> dict:
    out = {}
    for k in (1, 2, 3, 4):
        out[f"il{k}_hazard"] = max(abs(values[f"il{k}_min"]), abs(values[f"il{k}_max"]))
    return out


def add_derived(row: dict, values: dict, cdiv_uf: float, tramp_us: float) -> dict:
    hz = hazards(values)
    row.update(hz)
    row["max_abs_il_a"] = max(hz.values())
    row["within_250a_bound"] = row["max_abs_il_a"] <= ILIMIT
    for k in (1, 2, 3, 4):
        row[f"il{k}_over_250"] = hz[f"il{k}_hazard"] > ILIMIT
    thr = predicted_threshold_us(cdiv_uf)
    row["predicted_threshold_us"] = thr
    row["predicted_direction"] = "unsafe" if tramp_us < thr else "safe"
    row["actual_direction"] = "unsafe" if row["max_abs_il_a"] > ILIMIT else "safe"
    row["prediction_matched"] = row["predicted_direction"] == row["actual_direction"]
    return row


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    cdiv_uf = decode(match.group("cdiv"))
    tramp_us = decode(match.group("tramp"))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    if "Total elapsed time" not in log:
        raise RuntimeError(f"{cir.name}: .log has no 'Total elapsed time' -- run not complete")

    elapsed_match = re.search(r"Total elapsed time:\s*([0-9.]+)\s*seconds", log)
    elapsed_s = float(elapsed_match.group(1)) if elapsed_match else None

    values: dict[str, float | None] = {}
    for key in SCALAR_KEYS:
        found = re.search(rf"^{key}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        values[key] = float(found.group(1)) if found else None

    missing = [k for k, v in values.items() if v is None]
    if missing:
        raise RuntimeError(f"{cir.name}: missing measurements {missing} -- run not complete")

    tstop_target_us = tramp_us + 300.0

    row = {
        "case": cir.stem,
        "divider": "present",
        "cfly_uf": 3.0,
        "cdiv_uf": cdiv_uf,
        "tramp_us": tramp_us,
        "tstop_target_us": tstop_target_us,
        "wall_clock_s": elapsed_s,
        "reused_by_reference": False,
        **{k: values[k] for k in SCALAR_KEYS},
    }
    row = add_derived(row, values, cdiv_uf, tramp_us)
    return row


def load_reused_r04e18_rows() -> list[dict]:
    if not R04E18_RESULTS.exists():
        raise RuntimeError(f"R04E18 results.json not found at {R04E18_RESULTS}")
    all_rows = json.loads(R04E18_RESULTS.read_text())
    by_case = {r["case"]: r for r in all_rows}
    out = []
    for case in REUSED_R04E18_CASES:
        if case not in by_case:
            raise RuntimeError(f"expected reused case {case} not found in R04E18 results.json")
        src = by_case[case]
        cdiv_uf = 300.0
        tramp_us = src["tramp_us"]
        values = {k: src[k] for k in SCALAR_KEYS}
        row = {
            "case": src["case"],
            "divider": "present",
            "cfly_uf": src["cfly_uf"],
            "cdiv_uf": cdiv_uf,
            "tramp_us": tramp_us,
            "tstop_target_us": src["tstop_target_us"],
            "wall_clock_s": src["wall_clock_s"],
            "reused_by_reference": True,
            **values,
        }
        row = add_derived(row, values, cdiv_uf, tramp_us)
        out.append(row)
    return out


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    fields = list(rows[0].keys())
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    rows = []
    for p in sorted(CASES.glob("e20_c*.cir")):
        try:
            rows.append(parse_case(p))
        except RuntimeError as exc:
            print(f"SKIP {p.name}: {exc}")
    rows.extend(load_reused_r04e18_rows())
    rows.sort(key=lambda r: (r["cdiv_uf"], r["tramp_us"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")


if __name__ == "__main__":
    main()
