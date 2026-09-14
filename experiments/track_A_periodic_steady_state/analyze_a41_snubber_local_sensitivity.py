"""Analyze the fixed A41 P24 local snubber sweep without retuning it."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
HERE = TRACK / "A41_p24_snubber_local_sensitivity"
CASES = HERE / "cases"

NAME_RE = re.compile(
    r"a41_(?P<pct>[12])pct_(?P<branch>high_only|symmetric)_(?P<cap>\d+)pf$"
)
RELEASE_RE = re.compile(r"p24_t_ql1_off:.*?AT\s+([0-9.eE+-]+)")
RELEASE_I_RE = re.compile(r"p24_il1_at_ql1_off:.*?=\s*([0-9.eE+-]+)")


def wave(raw: RawRead, name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


def analyze_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    if match is None:
        raise ValueError(f"unexpected A41 case name: {cir.stem}")

    log_text = cir.with_suffix(".log").read_text(errors="replace")
    release_match = RELEASE_RE.search(log_text)
    release_i_match = RELEASE_I_RE.search(log_text)
    if release_match is None or release_i_match is None:
        raise RuntimeError(f"release event missing in {cir.name}")

    t_release = float(release_match.group(1))
    i_release_meas = float(release_i_match.group(1))
    raw = RawRead(str(cir.with_suffix(".raw")))
    time = wave(raw, "time")
    vin = wave(raw, "V(vin)")
    a1 = wave(raw, "V(a1)")
    x1 = wave(raw, "V(x1)")
    current = wave(raw, "I(L1)")
    gh1 = wave(raw, "V(gh1)")
    vds_high = vin - a1

    # Evaluate only after the measured low-side release. The raw trace starts
    # from a P24 t2 state where high-side Vds is zero, so a full-window minimum
    # would be a false ZVS positive for the later commutation event.
    post = np.flatnonzero(time >= t_release)
    if not len(post):
        raise RuntimeError(f"no samples after release in {cir.name}")
    start = int(post[0])
    local = int(np.argmin(vds_high[start:]))
    min_idx = start + local
    high_gate_on = bool(np.any(gh1[start:] >= 2.5))
    reached_zvs = bool(np.any(vds_high[start:] <= 1e-3))

    pct = int(match.group("pct"))
    target = -1.25 if pct == 1 else -2.5
    return {
        "case": cir.stem,
        "negative_fraction_pct": pct,
        "branch": match.group("branch"),
        "added_snubber_pf": int(match.group("cap")),
        "release_time_ns": t_release * 1e9,
        "release_current_a": i_release_meas,
        "release_error_ma": (i_release_meas - target) * 1e3,
        "vds_high_at_release_v": float(np.interp(t_release, time, vds_high)),
        "minimum_vds_high_after_release_v": float(vds_high[min_idx]),
        "time_of_minimum_vds_ns": float(time[min_idx] * 1e9),
        "commutated_voltage_drop_v": float(
            np.interp(t_release, time, vds_high) - vds_high[min_idx]
        ),
        "maximum_vds_low_after_release_v": float(np.max(x1[start:])),
        "current_at_minimum_vds_a": float(current[min_idx]),
        "vds_high_at_50ns_v": float(vds_high[-1]),
        "current_at_50ns_a": float(current[-1]),
        "natural_zvs_after_release": reached_zvs,
        "high_side_admitted": high_gate_on,
        "controller_guard_pass": (not reached_zvs) and (not high_gate_on),
    }


def main() -> None:
    rows = [analyze_case(path) for path in sorted(CASES.glob("*.cir"))]
    if len(rows) != 28:
        raise RuntimeError(f"expected 28 A41 cases, found {len(rows)}")

    (HERE / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (HERE / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({
        "cases": len(rows),
        "zvs_cases": sum(row["natural_zvs_after_release"] for row in rows),
        "guard_passes": sum(row["controller_guard_pass"] for row in rows),
        "worst_release_error_ma": max(abs(row["release_error_ma"]) for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
