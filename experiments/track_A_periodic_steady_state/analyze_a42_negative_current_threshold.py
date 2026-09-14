"""Analyze the fixed A42 zero-snubber threshold sweep."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
HERE = TRACK / "A42_zero_snubber_negative_current_threshold"
CASES = HERE / "cases"
NAME_RE = re.compile(r"a42_(?P<pct>\d{2})pct_zero_snubber$")
REFINE_RE = re.compile(r"a42_(?:refine|fine)_(?P<bp>\d{3})bp_zero_snubber$")
RELEASE_RE = re.compile(r"p24_t_ql1_off:.*?AT\s+([0-9.eE+-]+)")
RELEASE_I_RE = re.compile(r"p24_il1_at_ql1_off:.*?=\s*([0-9.eE+-]+)")
ZVS_RE = re.compile(r"p24_t3_high_vds_zero:.*?AT\s+([0-9.eE+-]+)")
ZVS_I_RE = re.compile(r"p24_il1_at_t3:.*?=\s*([0-9.eE+-]+)")


def wave(raw: RawRead, name: str) -> np.ndarray:
    return np.real(raw.get_trace(name).get_wave(0))


def source_label(pct: float) -> str:
    if pct <= 2:
        return "P24_EXPLICIT"
    if pct <= 4:
        return "DIAGNOSTIC_BRIDGE"
    return "P25_SUPPLEMENT"


def analyze_case(cir: Path) -> dict:
    match = NAME_RE.fullmatch(cir.stem)
    refine_match = REFINE_RE.fullmatch(cir.stem)
    if match is not None:
        pct = float(match.group("pct"))
    elif refine_match is not None:
        pct = int(refine_match.group("bp")) / 100
    else:
        raise ValueError(cir.stem)
    log = cir.with_suffix(".log").read_text(errors="replace")
    release = RELEASE_RE.search(log)
    release_i = RELEASE_I_RE.search(log)
    if release is None or release_i is None:
        raise RuntimeError(f"release event missing in {cir.name}")
    t_release = float(release.group(1))

    raw = RawRead(str(cir.with_suffix(".raw")))
    time = wave(raw, "time")
    vds_high = wave(raw, "V(vin)") - wave(raw, "V(a1)")
    current = wave(raw, "I(L1)")
    gh1 = wave(raw, "V(gh1)")
    post = np.flatnonzero(time >= t_release)
    start = int(post[0])
    min_idx = start + int(np.argmin(vds_high[start:]))

    zvs = ZVS_RE.search(log)
    zvs_i = ZVS_I_RE.search(log)
    t_zvs = float(zvs.group(1)) if zvs else None
    return {
        "case": cir.stem,
        "negative_fraction_pct": pct,
        "source_region": source_label(pct),
        "negative_target_a": 1.25 * pct,
        "release_time_ns": t_release * 1e9,
        "release_current_a": float(release_i.group(1)),
        "minimum_vds_high_after_release_v": float(vds_high[min_idx]),
        "time_of_minimum_vds_ns": float(time[min_idx] * 1e9),
        "natural_zvs_after_release": t_zvs is not None,
        "zvs_time_ns": None if t_zvs is None else t_zvs * 1e9,
        "commutation_duration_ns": None if t_zvs is None else (t_zvs - t_release) * 1e9,
        "current_at_zvs_a": None if zvs_i is None else float(zvs_i.group(1)),
        "high_side_admitted": bool(np.any(gh1[start:] >= 2.5)),
        "current_at_minimum_vds_a": float(current[min_idx]),
    }


def main() -> None:
    rows = [analyze_case(path) for path in sorted(CASES.glob("*.cir"))]
    if len(rows) != 10:
        raise RuntimeError(f"expected 10 cases, found {len(rows)}")
    (HERE / "coarse_results.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (HERE / "coarse_results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    refinement_rows = [
        analyze_case(path)
        for directory in (HERE / "refinement_cases", HERE / "fine_cases")
        for path in sorted(directory.glob("*.cir"))
    ]
    (HERE / "refinement_results.json").write_text(
        json.dumps(refinement_rows, indent=2) + "\n"
    )
    with (HERE / "refinement_results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(refinement_rows[0]))
        writer.writeheader()
        writer.writerows(refinement_rows)
    for row in rows:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
