"""Analyze R04E9's unified inductor-mediated four-phase bootstrap grid.

Parses each generated case's LTspice `.log` for its `.meas` results,
determines the final machine state (which CHARGE_k/FREE_k the machine is
latched in at TSTOP), extracts the 20/40/60/80/100% trajectory checkpoints
for Vout/VC1/VC2/VC3, whether/when the handoff condition (T_HANDOFF) was
ever reached, how many full phase rotations completed (T_ROT1..8), and
peak/min currents for every inductor and flying-capacitor branch (the
latter windowed from 1 ns to exclude the known t=0 ideal-switch numerical
startup spike, same convention as R04E6/R04E8).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TRACK = Path(__file__).resolve().parent
HERE = TRACK / "R04E9_unified_inductor_mediated_bootstrap"
CASES = HERE / "cases"

NAME_RE = re.compile(r"r04e9_ilimit_(?P<ilimit>\d+)a_tfw_(?P<tfw>\d+)ns")

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

MAX_ROT_SCAN = 8


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
    t_fw_ns = float(match.group("tfw"))

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

    row = {
        "case": cir.stem,
        "i_limit_a": i_limit,
        "t_freewheel_max_ns": t_fw_ns,
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
        "grade": "CONTROLLER_GUARD_PASS" if not handoff_reached else "LOCAL_PASS",
        "trajectory": trajectory,
        "rotations": rotations,
    }
    return row


def write_table(rows: list[dict], out_stem: Path) -> None:
    if not rows:
        return
    out_stem.with_suffix(".json").write_text(json.dumps(rows, indent=2) + "\n")
    flat_fields = [k for k in rows[0] if k not in ("trajectory", "rotations")]
    with out_stem.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=flat_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in flat_fields})


def main() -> None:
    rows = [parse_case(p) for p in sorted(CASES.glob("*.cir"))]
    rows.sort(key=lambda r: (r["i_limit_a"], r["t_freewheel_max_ns"]))
    write_table(rows, HERE / "results")
    for row in rows:
        flat = {k: v for k, v in row.items() if k not in ("trajectory", "rotations")}
        print(json.dumps(flat))
    print(f"# total cases={len(rows)}")
    n_handoff = sum(1 for r in rows if r["handoff_reached"])
    print(f"# HANDOFF_REACHED: {n_handoff}")
    print(f"# CONTROLLER_GUARD_PASS (no handoff): {len(rows) - n_handoff}")


if __name__ == "__main__":
    main()
