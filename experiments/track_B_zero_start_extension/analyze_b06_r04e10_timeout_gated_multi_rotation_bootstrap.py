"""Analyze R04E10's timeout-gated multi-rotation bootstrap grid.

Parses each generated case's LTspice `.log` for its `.meas` results,
determines the final machine state, extracts the 20/40/60/80/100%
trajectory checkpoints for Vout/VC1/VC2/VC3, whether/when the handoff
condition (T_HANDOFF) was ever reached, how many full phase rotations
completed (T_ROT1..60), the per-rotation Vout/VC1/VC2/VC3 trend (to answer
this experiment's central question: does the ladder visibly progress
upward over rotations, or plateau/oscillate?), and peak/min currents for
every inductor and flying-capacitor branch (windowed from 2 ns to exclude
the known t=0 ideal-switch numerical startup spike, same convention as
R04E6/R04E8/R04E9).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E10_timeout_gated_multi_rotation_bootstrap"
CASES = HERE / "cases"

NAME_RE = re.compile(r"r04e10_ilimit_(?P<ilimit>\d+)a_tchg_(?P<tchg>\d+)ns")

STATE_NAMES = {
    0: "CHARGE1",
    1: "FREE1",
    2: "CHARGE2",
    3: "FREE2",
    4: "CHARGE3",
    5: "FREE3",
    6: "CHARGE4",
    7: "FREE4",
}

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
    i_limit = float(match.group("ilimit"))
    t_chg_ns = float(match.group("tchg"))

    log_path = cir.with_suffix(".log")
    if not log_path.exists():
        raise RuntimeError(f"missing log for {cir.name} -- was it simulated?")
    log = log_path.read_text(errors="replace")

    values = {k: get_scalar(log, k) for k in SCALAR_KEYS}
    t_handoff = get_when(log, "t_handoff")
    handoff_reached = t_handoff is not None

    state_final_code = values.get("state_final")
    state_final_name = (
        STATE_NAMES.get(int(round(state_final_code)), "UNKNOWN")
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
            STATE_NAMES.get(int(round(state_code)), "UNKNOWN")
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

    # Multi-rotation trend classification: compare the first and last
    # completed rotation's Vout (and VC1/VC2/VC3) to see whether the
    # ladder is monotonically progressing, plateauing, or oscillating
    # without net progress. Uses simple first-vs-last and a monotonicity
    # check across all completed rotations.
    def trend(key: str) -> dict:
        series = [r[key] for r in rotations if r[key] is not None]
        if len(series) < 2:
            return {"n": len(series), "first": series[0] if series else None,
                     "last": series[-1] if series else None,
                     "monotonic_nondecreasing": None, "net_change": None}
        n_increasing_steps = sum(
            1 for a, b in zip(series, series[1:]) if b > a
        )
        n_decreasing_steps = sum(
            1 for a, b in zip(series, series[1:]) if b < a
        )
        return {
            "n": len(series),
            "first": series[0],
            "last": series[-1],
            "net_change": series[-1] - series[0],
            "n_increasing_steps": n_increasing_steps,
            "n_decreasing_steps": n_decreasing_steps,
            "monotonic_nondecreasing": all(
                b >= a for a, b in zip(series, series[1:])
            ),
        }

    trends = {
        "vout": trend("vout_v"),
        "vc1": trend("vc1_v"),
        "vc2": trend("vc2_v"),
        "vc3": trend("vc3_v"),
    }

    # Suspected-numerical-artifact flag: a diagnostic case (I_LIMIT=30A,
    # T_CHARGE_MAX=20ns) showed an ICS2/ICS3 excursion to ~233 kA at a
    # single simulated instant, confirmed by direct raw-trace inspection
    # to coincide with repeated identical timestamps, an unchanging
    # VC1-3/IL1-4 state, and a non-integer "state" value -- the classic
    # fingerprint of a solver-convergence retry artifact, not a real
    # current (R04E9's own inductor-mediated mechanism never exceeded
    # ~35 A anywhere in its 9-cell grid; even R04E6/E7/E8's structurally
    # DIFFERENT switch-only mechanism never exceeded ~4.6 kA). Any
    # ICSk_max/min magnitude above this threshold is flagged, not
    # silently trusted as a physical result.
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
        "i_limit_a": i_limit,
        "t_charge_max_ns": t_chg_ns,
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
    rows = [parse_case(p) for p in sorted(CASES.glob("*.cir"))]
    rows.sort(key=lambda r: (r["i_limit_a"], r["t_charge_max_ns"]))
    write_table(rows, HERE / "results")
    for row in rows:
        flat = {k: v for k, v in row.items() if k not in ("trajectory", "rotations")}
        print(json.dumps(flat))
    print(f"# total cases={len(rows)}")
    n_handoff = sum(1 for r in rows if r["handoff_reached"])
    print(f"# HANDOFF_REACHED: {n_handoff}")
    print(f"# CONTROLLER_GUARD_PASS (no handoff): {len(rows) - n_handoff}")
    for row in rows:
        print(
            f"# {row['case']}: rotations={row['n_rotations_completed']} "
            f"final_state={row['state_final_name']} "
            f"vout_first={row['vout_trend'].get('first')} "
            f"vout_last={row['vout_trend'].get('last')} "
            f"vout_monotonic={row['vout_trend'].get('monotonic_nondecreasing')}"
        )


if __name__ == "__main__":
    main()
