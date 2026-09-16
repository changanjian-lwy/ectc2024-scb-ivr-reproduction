"""Analyze R04E14's corrected-Cfly replay of the R02A/R02B passive-precharge
startup module.

Parses each generated case's LTspice `.log` for its non-stepped `.meas`
results (format: "name: EXPR(...)=<value> FROM/AT ..." on a single line --
this is the single-cell, non-.step-param log format, confirmed directly
against R02B's own multi-step log during this experiment's own piloting;
see build_r04e14.py's module docstring), computes the same `LADDER_ERR`
metric R02A/B/R04E6-E8 already use, and writes results.csv/results.json.

Case filenames are `e14_c<CDIV>_t<TRAMP>_f<CFLY>` (values in uF/us, 'p'
for a decimal point) -- kept short per build_r04e14.py's own NAMING NOTE.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

NAME_RE = re.compile(r"e14_c(?P<cdiv>[0-9pP]+)_t(?P<tramp>[0-9pP]+)_f(?P<cfly>[0-9pP]+)")

SCALAR_KEYS = [
    "vc1_final",
    "vc2_final",
    "vc3_final",
    "ratio21",
    "ratio31",
    "ladder_err",
    "iin_pk",
    "id1_pk",
    "id2_pk",
    "id3_pk",
]


def decode(tag: str) -> float:
    return float(tag.replace("p", "."))


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    cdiv_uf = decode(match.group("cdiv"))
    tramp_us = decode(match.group("tramp"))
    cfly_uf = decode(match.group("cfly"))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    if "unable to open database file" in log and not re.search(r"^vc1_final:", log, re.MULTILINE):
        raise RuntimeError(
            f"{cir.name}: LTspice measurement database failed to open and no "
            "measurements were printed (known path-length failure mode -- "
            "see build_r04e14.py NAMING NOTE). This case must be re-run."
        )

    values: dict[str, float | None] = {}
    for key in SCALAR_KEYS:
        found = re.search(rf"^{key}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        values[key] = float(found.group(1)) if found else None

    missing = [k for k, v in values.items() if v is None]
    if missing:
        raise RuntimeError(f"{cir.name}: missing measurements {missing}")

    row = {
        "case": cir.stem,
        "cdiv_uf": cdiv_uf,
        "tramp_us": tramp_us,
        "cfly_uf": cfly_uf,
        "vc1_final_v": values["vc1_final"],
        "vc2_final_v": values["vc2_final"],
        "vc3_final_v": values["vc3_final"],
        "ratio21": values["ratio21"],
        "ratio31": values["ratio31"],
        "ladder_err": values["ladder_err"],
        "iin_pk_a": values["iin_pk"],
        "id1_pk_a": values["id1_pk"],
        "id2_pk_a": values["id2_pk"],
        "id3_pk_a": values["id3_pk"],
    }
    return row


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
    rows = [parse_case(p) for p in sorted(CASES.glob("e14_*.cir"))]
    rows.sort(key=lambda r: (r["cfly_uf"], r["cdiv_uf"], r["tramp_us"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")

    primary = [r for r in rows if abs(r["cfly_uf"] - 3.0) < 1e-9]
    if primary:
        best = min(primary, key=lambda r: r["ladder_err"])
        print(
            "# best primary-grid cell by ladder_err: "
            f"CDIV={best['cdiv_uf']}uF TRAMP={best['tramp_us']}us "
            f"ladder_err={best['ladder_err']:.6f} iin_pk={best['iin_pk_a']:.4f}A"
        )


if __name__ == "__main__":
    main()
