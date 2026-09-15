"""Analyze R04E8's corrected-Cfly voltage-ratio-gated EPE2019 3-state
charge-redistribution ladder-bootstrap grid.

Parses each generated case's LTspice `.log` for its `.meas` results (same
convention as `analyze_b03...`), determines the actual number of a-b-c
cycles completed, computes `LADDER_ERR` at every completed cycle checkpoint
and at the run's own terminal state, and reports whether the run converged
(`STATE_FINAL==3`, DONE) or hit the safety cap without converging
(`STATE_FINAL==4`, CAPPED). The swept axis here is CFLY (not TOL, which is
fixed at 2% for this whole grid).

`LADDER_ERR` is the SAME metric R02B/R04E6/R04E7 already use:
`|VC1-36|/36 + |VC2-24|/24 + |VC3-12|/12` (0 = perfect; starting from zero
energy this metric starts at 3.0).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E8_corrected_cfly_ratio_gated_startup"
CASES = HERE / "cases"

NAME_RE = re.compile(r"r04e8_cfly_(?P<cfly>[0-9pP]+)uF")

MAX_CYC_SCAN = 60

TARGETS = {"vc1": 36.0, "vc2": 24.0, "vc3": 12.0}

SCALAR_KEYS = [
    "state_final",
    "vc1_final",
    "vc2_final",
    "vc3_final",
    "vout_final",
    "il1_max",
    "il1_min",
    "ics1_max",
    "ics1_min",
    "ics2_max",
    "ics2_min",
    "ics3_max",
    "ics3_min",
]

STATE_NAMES = {0: "STATE_A", 1: "STATE_B", 2: "STATE_C", 3: "DONE", 4: "CAPPED"}


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
    cfly_uf = float(match.group("cfly").replace("p", "."))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    values: dict[str, float | None] = {}
    for key in SCALAR_KEYS:
        found = re.search(rf"^{key}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        values[key] = float(found.group(1)) if found else None
    t_terminal_m = re.search(r"^t_terminal:.*?AT\s+([0-9.eE+-]+)", log, re.MULTILINE)
    values["t_terminal"] = float(t_terminal_m.group(1)) if t_terminal_m else None

    cycles = []
    for j in range(1, MAX_CYC_SCAN + 1):
        vc1_m = re.search(rf"^vc1_cyc{j}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        if vc1_m is None:
            break
        vc2_m = re.search(rf"^vc2_cyc{j}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        vc3_m = re.search(rf"^vc3_cyc{j}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
        t_m = re.search(rf"^t_cyc{j}:.*?AT\s+([0-9.eE+-]+)", log, re.MULTILINE)
        vc1 = float(vc1_m.group(1))
        vc2 = float(vc2_m.group(1)) if vc2_m else None
        vc3 = float(vc3_m.group(1)) if vc3_m else None
        t = float(t_m.group(1)) if t_m else None
        err = ladder_err(vc1, vc2, vc3) if vc2 is not None and vc3 is not None else None
        cycles.append(
            {"cycle": j, "vc1_v": vc1, "vc2_v": vc2, "vc3_v": vc3, "t_s": t, "ladder_err": err}
        )

    ncyc_actual = cycles[-1]["cycle"] if cycles else 0
    state_final = values.get("state_final")
    state_name = STATE_NAMES.get(int(round(state_final)) if state_final is not None else -1, "UNKNOWN")
    converged = state_name == "DONE"
    capped_no_converge = state_name == "CAPPED"

    final_err = None
    if all(values.get(f"{k}_final") is not None for k in ("vc1", "vc2", "vc3")):
        final_err = ladder_err(values["vc1_final"], values["vc2_final"], values["vc3_final"])

    errs = [c["ladder_err"] for c in cycles if c["ladder_err"] is not None]
    monotonic_improving = all(a >= b for a, b in zip(errs, errs[1:])) if len(errs) >= 2 else None

    if converged:
        grade = "LOCAL_PASS"
    elif capped_no_converge:
        grade = "SAFETY_CAP_HIT_NOT_CONVERGED"
    else:
        grade = "MISSING_DATA"

    row = {
        "case": cir.stem,
        "cfly_uf": cfly_uf,
        "state_final_code": state_final,
        "state_final_name": state_name,
        "ncyc_actual": ncyc_actual,
        "t_terminal_s": values.get("t_terminal"),
        "vc1_final_v": values.get("vc1_final"),
        "vc2_final_v": values.get("vc2_final"),
        "vc3_final_v": values.get("vc3_final"),
        "vout_final_v": values.get("vout_final"),
        "ladder_err_final": final_err,
        "ladder_err_cyc1": errs[0] if errs else None,
        "monotonic_improving_every_cycle": monotonic_improving,
        "il1_max_a": values.get("il1_max"),
        "il1_min_a": values.get("il1_min"),
        "ics1_max_a": values.get("ics1_max"),
        "ics1_min_a": values.get("ics1_min"),
        "ics2_max_a": values.get("ics2_max"),
        "ics2_min_a": values.get("ics2_min"),
        "ics3_max_a": values.get("ics3_max"),
        "ics3_min_a": values.get("ics3_min"),
        "converged": converged,
        "safety_cap_hit_without_converging": capped_no_converge,
        "grade": grade,
        "cycles": cycles,
    }
    return row


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    flat_fields = [k for k in rows[0] if k != "cycles"]
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=flat_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in flat_fields})


def main() -> None:
    rows = [parse_case(p) for p in sorted(CASES.glob("*.cir"))]
    rows.sort(key=lambda r: r["cfly_uf"])
    write_table(rows, HERE / "results")
    for row in rows:
        flat = {k: v for k, v in row.items() if k != "cycles"}
        print(json.dumps(flat))
    print(f"# total cases={len(rows)}")
    for grade in ("LOCAL_PASS", "SAFETY_CAP_HIT_NOT_CONVERGED", "MISSING_DATA"):
        count = sum(1 for r in rows if r["grade"] == grade)
        print(f"# {grade}: {count}")


if __name__ == "__main__":
    main()
