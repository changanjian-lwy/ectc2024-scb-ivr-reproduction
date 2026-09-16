"""Analyze R04E16's 6-cell grid (Roberts' PhD dissertation Sec. 3.5
soft-start mechanism applied to P24's fixed-timing four-phase PWM).

Parses each case's LTspice .log for its non-stepped .meas results
(same single-cell log format as R04E14/R04E15's own analyze scripts),
and writes results.csv/results.json for all committed cases.

Case filenames: e16_<tag>_f<CFLY>_t<TRAMP> (tag in {g1,g2,ctrl}, values
in uF/us, 'p' for a decimal point).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CASES = HERE / "cases"

NAME_RE = re.compile(r"e16_(?P<tag>g1|g2|ctrl)_f(?P<cfly>[0-9pP]+)_t(?P<tramp>[0-9pP]+)")

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


def decode(tag: str) -> float:
    return float(tag.replace("p", "."))


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    tag = match.group("tag")
    cfly_uf = decode(match.group("cfly"))
    tramp_us = decode(match.group("tramp"))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

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

    row = {
        "case": cir.stem,
        "grid": tag,
        "cfly_uf": cfly_uf,
        "tramp_us": tramp_us,
        "tstop_target_us": tstop_target_us,
        **{k: values[k] for k in SCALAR_KEYS},
        "max_abs_il_a": max_il,
        "within_250a_bound": max_il <= 250.0,
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
    rows = []
    for p in sorted(CASES.glob("e16_*.cir")):
        if "pilot" in p.stem:
            continue
        try:
            rows.append(parse_case(p))
        except RuntimeError as exc:
            print(f"SKIP {p.name}: {exc}")
    rows.sort(key=lambda r: (r["grid"], r["cfly_uf"], r["tramp_us"]))
    write_table(rows, HERE / "results")
    for row in rows:
        print(json.dumps(row))
    print(f"# total cases={len(rows)}")


if __name__ == "__main__":
    main()
