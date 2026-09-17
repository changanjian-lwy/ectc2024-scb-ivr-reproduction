"""Analyze R04E17's 2x2 factorial isolation grid (divider present/absent
x fast/slow Vin ramp) crossing R04E16's own already-completed divider-
ABSENT cells with this experiment's two NEW divider-PRESENT cells.

Parses the two new cells' LTspice .log files (cases/e17_div_f3_t1.cir,
cases/e17_div_f3_t68p61.cir) for their non-stepped .meas results (same
single-cell log format as R04E14/R04E15/R04E16's own analyze scripts),
merges in R04E16's own two already-published divider-ABSENT cells by
reference (read from R04E16's own committed results.json, NOT re-run),
and writes results.csv/results.json for the complete 4-cell 2x2 table.

Case filenames: e17_div_f<CFLY>_t<TRAMP> (values in uF/us, 'p' for a
decimal point) for the new cells this experiment ran.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"
R04E16_RESULTS = (
    HERE.parent
    / "R04E16_roberts_softstart_fixed_timing"
    / "results.json"
)

NAME_RE = re.compile(r"e17_div_f(?P<cfly>[0-9pP]+)_t(?P<tramp>[0-9pP]+)")

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

REUSED_R04E16_CASES = {
    "e16_ctrl_f3_t1": {"divider": "absent", "ramp": "fast"},
    "e16_g1_f3_t68p61": {"divider": "absent", "ramp": "slow"},
}


def decode(tag: str) -> float:
    return float(tag.replace("p", "."))


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    cfly_uf = decode(match.group("cfly"))
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
    max_il = max(
        abs(values["il1_max"]), abs(values["il1_min"]),
        abs(values["il2_max"]), abs(values["il2_min"]),
        abs(values["il3_max"]), abs(values["il3_min"]),
        abs(values["il4_max"]), abs(values["il4_min"]),
    )

    ramp = "fast" if abs(tramp_us - 1.0) < 1e-6 else "slow"

    row = {
        "case": cir.stem,
        "divider": "present",
        "ramp": ramp,
        "cfly_uf": cfly_uf,
        "tramp_us": tramp_us,
        "tstop_target_us": tstop_target_us,
        "wall_clock_s": elapsed_s,
        "reused_by_reference": False,
        **{k: values[k] for k in SCALAR_KEYS},
        "max_abs_il_a": max_il,
        "within_250a_bound": max_il <= 250.0,
    }
    return row


def load_reused_r04e16_rows() -> list[dict]:
    if not R04E16_RESULTS.exists():
        raise RuntimeError(f"R04E16 results.json not found at {R04E16_RESULTS}")
    all_rows = json.loads(R04E16_RESULTS.read_text())
    by_case = {r["case"]: r for r in all_rows}
    out = []
    for case, meta in REUSED_R04E16_CASES.items():
        if case not in by_case:
            raise RuntimeError(f"expected reused case {case} not found in R04E16 results.json")
        src = by_case[case]
        row = {
            "case": src["case"],
            "divider": meta["divider"],
            "ramp": meta["ramp"],
            "cfly_uf": src["cfly_uf"],
            "tramp_us": src["tramp_us"],
            "tstop_target_us": src["tstop_target_us"],
            "wall_clock_s": None,
            "reused_by_reference": True,
            **{k: src[k] for k in SCALAR_KEYS},
            "max_abs_il_a": src["max_abs_il_a"],
            "within_250a_bound": src["within_250a_bound"],
        }
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
    for p in sorted(CASES.glob("e17_div_*.cir")):
        try:
            rows.append(parse_case(p))
        except RuntimeError as exc:
            print(f"SKIP {p.name}: {exc}")
    rows.extend(load_reused_r04e16_rows())
    rows.sort(key=lambda r: (r["divider"], r["ramp"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")


if __name__ == "__main__":
    main()
