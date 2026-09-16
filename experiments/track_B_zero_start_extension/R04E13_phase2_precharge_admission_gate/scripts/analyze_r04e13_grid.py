"""Analyze R04E13's phase-2-precharge-stacked-on-phase-1 cells. Adapted
directly from R04E12's own `analyze_r04e12_grid.py` (same `.meas`/`.log`
parsing approach, same trajectory/rotation/artifact-flag logic), since this
experiment reuses R04E10/R04E12's own `.meas` block verbatim -- only the
state-name-to-code mapping differs per cell because each (N1_PRECHARGE,
N2_PRECHARGE) cell's two stacked precharge chains shift where CHARGE1..FREE4
start (see scripts/build_r04e13_cases.py).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPDIR = HERE.parent
CASES = EXPDIR / "cases"
sys.path.insert(0, str(HERE))
from verify_precharge_gate2 import state_names_for

NAME_RE = re.compile(r"r04e13_n1_(?P<n1>\d+)_n2_(?P<n2>\d+)")

FRACTIONS = ("20PCT", "40PCT", "60PCT", "80PCT", "100PCT")

SCALAR_KEYS = [
    "state_final",
    "vout_final",
    "vc1_final",
    "vc2_final",
    "vc3_final",
    "il1_max",
    "il1_min",
    "il2_max",
    "il2_min",
    "il3_max",
    "il3_min",
    "il4_max",
    "il4_min",
    "ics1_max",
    "ics1_min",
    "ics2_max",
    "ics2_min",
    "ics3_max",
    "ics3_min",
]

MAX_ROT_SCAN = 60


def get_scalar(log: str, key: str) -> float | None:
    m = re.search(rf"^{key}:.*?=\s*([0-9.eE+-]+)", log, re.MULTILINE)
    return float(m.group(1)) if m else None


def get_when(log: str, key: str) -> float | None:
    m = re.search(rf"^{key}:.*?(?:AT|WHEN)\s+([0-9.eE+-]+)", log, re.MULTILINE)
    return float(m.group(1)) if m else None


def parse_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unrecognized case name: {cir.stem}")
    n1_precharge = int(match.group("n1"))
    n2_precharge = int(match.group("n2"))
    state_names = state_names_for(n1_precharge, n2_precharge)

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    values = {k: get_scalar(log, k) for k in SCALAR_KEYS}
    t_handoff = get_when(log, "t_handoff")
    handoff_reached = t_handoff is not None

    state_final_code = values.get("state_final")
    state_final_name = (
        state_names.get(int(round(state_final_code)), "UNKNOWN")
        if state_final_code is not None
        else "MISSING"
    )

    trajectory = []
    for frac in FRACTIONS:
        vout = get_scalar(log, f"vout_at_{frac.lower()}")
        vc1 = get_scalar(log, f"vc1_at_{frac.lower()}")
        vc2 = get_scalar(log, f"vc2_at_{frac.lower()}")
        vc3 = get_scalar(log, f"vc3_at_{frac.lower()}")
        state_code = get_scalar(log, f"state_at_{frac.lower()}")
        state_name = (
            state_names.get(int(round(state_code)), "UNKNOWN")
            if state_code is not None
            else None
        )
        trajectory.append(
            {
                "fraction": frac,
                "vout_v": vout,
                "vc1_v": vc1,
                "vc2_v": vc2,
                "vc3_v": vc3,
                "state_name": state_name,
            }
        )

    rotations = []
    for j in range(1, MAX_ROT_SCAN + 1):
        t_rot = get_when(log, f"t_rot{j}")
        if t_rot is None:
            break
        rotations.append(
            {
                "rotation": j,
                "t_s": t_rot,
                "vout_v": get_scalar(log, f"vout_rot{j}"),
                "vc1_v": get_scalar(log, f"vc1_rot{j}"),
                "vc2_v": get_scalar(log, f"vc2_rot{j}"),
                "vc3_v": get_scalar(log, f"vc3_rot{j}"),
            }
        )
    n_rotations_completed = len(rotations)

    def trend(key: str) -> dict:
        series = [r[key] for r in rotations if r[key] is not None]
        if len(series) < 2:
            return {"n": len(series), "first": series[0] if series else None,
                     "last": series[-1] if series else None,
                     "monotonic_nondecreasing": None, "net_change": None}
        n_increasing_steps = sum(1 for a, b in zip(series, series[1:]) if b > a)
        n_decreasing_steps = sum(1 for a, b in zip(series, series[1:]) if b < a)
        return {
            "n": len(series),
            "first": series[0],
            "last": series[-1],
            "net_change": series[-1] - series[0],
            "n_increasing_steps": n_increasing_steps,
            "n_decreasing_steps": n_decreasing_steps,
            "monotonic_nondecreasing": all(b >= a for a, b in zip(series, series[1:])),
        }

    trends = {
        "vout": trend("vout_v"),
        "vc1": trend("vc1_v"),
        "vc2": trend("vc2_v"),
        "vc3": trend("vc3_v"),
    }

    ARTIFACT_THRESHOLD_A = 1000.0
    suspected_artifact_branches = [
        name
        for name, key in (
            ("ICS1_MAX", "ics1_max"), ("ICS1_MIN", "ics1_min"),
            ("ICS2_MAX", "ics2_max"), ("ICS2_MIN", "ics2_min"),
            ("ICS3_MAX", "ics3_max"), ("ICS3_MIN", "ics3_min"),
        )
        if values.get(key) is not None and abs(values[key]) > ARTIFACT_THRESHOLD_A
    ]

    row = {
        "case": cir.stem,
        "n1_precharge": n1_precharge,
        "n2_precharge": n2_precharge,
        "i_limit_a": 60.0,
        "t_charge_max_ns": 50.0,
        "t_freewheel_max_ns": 50.0,
        "state_final_code": state_final_code,
        "state_final_name": state_final_name,
        "n_rotations_completed": n_rotations_completed,
        "handoff_reached": handoff_reached,
        "t_handoff_s": t_handoff,
        "vout_final_v": values.get("vout_final"),
        "vc1_final_v": values.get("vc1_final"),
        "vc2_final_v": values.get("vc2_final"),
        "vc3_final_v": values.get("vc3_final"),
        "il1_max_a": values.get("il1_max"),
        "il1_min_a": values.get("il1_min"),
        "il2_max_a": values.get("il2_max"),
        "il2_min_a": values.get("il2_min"),
        "il3_max_a": values.get("il3_max"),
        "il3_min_a": values.get("il3_min"),
        "il4_max_a": values.get("il4_max"),
        "il4_min_a": values.get("il4_min"),
        "ics1_max_a": values.get("ics1_max"),
        "ics1_min_a": values.get("ics1_min"),
        "ics2_max_a": values.get("ics2_max"),
        "ics2_min_a": values.get("ics2_min"),
        "ics3_max_a": values.get("ics3_max"),
        "ics3_min_a": values.get("ics3_min"),
        "vout_trend": trends["vout"],
        "vc1_trend": trends["vc1"],
        "vc2_trend": trends["vc2"],
        "vc3_trend": trends["vc3"],
        "suspected_numeric_artifact_branches": suspected_artifact_branches,
        "grade": "LOCAL_PASS" if handoff_reached else "CONTROLLER_GUARD_PASS",
        "trajectory": trajectory,
        "rotations": rotations,
    }
    return row


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    flat_fields = [
        k for k in rows[0]
        if k not in ("trajectory", "rotations", "vout_trend", "vc1_trend", "vc2_trend", "vc3_trend",
                      "suspected_numeric_artifact_branches")
    ]
    flat_fields.append("suspected_numeric_artifact_branches")
    flat_fields += [
        "vout_first", "vout_last", "vout_net_change", "vout_monotonic",
        "vc1_first", "vc1_last", "vc1_net_change", "vc1_monotonic",
        "vc2_first", "vc2_last", "vc2_net_change", "vc2_monotonic",
        "vc3_first", "vc3_last", "vc3_net_change", "vc3_monotonic",
    ]
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=flat_fields)
        writer.writeheader()
        for row in rows:
            flat = {k: row[k] for k in flat_fields if k in row and k != "suspected_numeric_artifact_branches"}
            flat["suspected_numeric_artifact_branches"] = ";".join(
                row["suspected_numeric_artifact_branches"]
            )
            for key, prefix in (("vout_trend", "vout"), ("vc1_trend", "vc1"),
                                 ("vc2_trend", "vc2"), ("vc3_trend", "vc3")):
                t = row[key]
                flat[f"{prefix}_first"] = t.get("first")
                flat[f"{prefix}_last"] = t.get("last")
                flat[f"{prefix}_net_change"] = t.get("net_change")
                flat[f"{prefix}_monotonic"] = t.get("monotonic_nondecreasing")
            writer.writerow(flat)


def main() -> None:
    rows = [parse_case(p) for p in sorted(CASES.glob("r04e13_n1_*_n2_*.cir"))]
    rows.sort(key=lambda r: (r["n1_precharge"], r["n2_precharge"]))
    write_table(rows, EXPDIR / "results")
    for row in rows:
        flat = {k: v for k, v in row.items() if k not in ("trajectory", "rotations")}
        print(json.dumps(flat))
    print(f"# total cases={len(rows)}")
    n_handoff = sum(1 for r in rows if r["handoff_reached"])
    print(f"# HANDOFF_REACHED: {n_handoff}")
    print(f"# CONTROLLER_GUARD_PASS (no handoff): {len(rows) - n_handoff}")
    for row in rows:
        print(
            f"# {row['case']}: n1_precharge={row['n1_precharge']} "
            f"n2_precharge={row['n2_precharge']} "
            f"rotations={row['n_rotations_completed']} "
            f"final_state={row['state_final_name']} "
            f"vout_final={row['vout_final_v']} vc1_final={row['vc1_final_v']} "
            f"vc2_final={row['vc2_final_v']} vc3_final={row['vc3_final_v']} "
            f"artifacts={row['suspected_numeric_artifact_branches']}"
        )


if __name__ == "__main__":
    main()
