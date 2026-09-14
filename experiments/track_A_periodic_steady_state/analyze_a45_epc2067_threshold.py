"""Analyze A45's EPC2067-candidate negative-current sweep (all stages).

Mirrors analyze_a42_negative_current_threshold.py's exact extraction pattern
(regex over the LTspice .log text for WHEN/FIND measurements, plus a
spicelib RawRead pass for the post-release Vds minimum), extended to A45's
four case directories: cases/ (1%-10% coarse, matching A42's convention),
wide_bracket_cases/ (15%-40%, needed because 1%-10% never reached ZVS),
refinement_cases/ (22.00%-23.00% in 0.1% steps) and fine_cases/
(22.00%-22.10% in 0.01% steps).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
HERE = TRACK / "A45_epc2067_table3_candidate_commutation"

NAME_RE = re.compile(r"a45_(?P<pct>\d{2})pct_epc2067$")
WIDE_RE = re.compile(r"a45_wide_(?P<pct>\d+(?:p\d+)?)pct_epc2067$")
REFINE_RE = re.compile(r"a45_refine_(?P<bp>\d{4})bp_epc2067$")
FINE_RE = re.compile(r"a45_fine_(?P<bp>\d{4})bp_epc2067$")

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


def _pct_of(cir: Path) -> float:
    if (m := NAME_RE.fullmatch(cir.stem)) is not None:
        return float(m.group("pct"))
    if (m := WIDE_RE.fullmatch(cir.stem)) is not None:
        return float(m.group("pct").replace("p", "."))
    if (m := REFINE_RE.fullmatch(cir.stem)) is not None:
        return int(m.group("bp")) / 100
    if (m := FINE_RE.fullmatch(cir.stem)) is not None:
        return int(m.group("bp")) / 100
    raise ValueError(cir.stem)


def analyze_case(cir: Path) -> dict:
    pct = _pct_of(cir)
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


def _dump(rows: list[dict], json_path: Path, csv_path: Path) -> None:
    json_path.write_text(json.dumps(rows, indent=2) + "\n")
    if not rows:
        return
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    coarse = [analyze_case(p) for p in sorted((HERE / "cases").glob("*.cir"))]
    if len(coarse) != 10:
        raise RuntimeError(f"expected 10 coarse cases, found {len(coarse)}")
    _dump(coarse, HERE / "coarse_results.json", HERE / "coarse_results.csv")

    wide = [analyze_case(p) for p in sorted((HERE / "wide_bracket_cases").glob("*.cir"))]
    wide.sort(key=lambda r: r["negative_fraction_pct"])
    _dump(wide, HERE / "wide_bracket_results.json", HERE / "wide_bracket_results.csv")

    refinement_rows = [
        analyze_case(path)
        for directory in ("refinement_cases", "fine_cases")
        for path in sorted((HERE / directory).glob("*.cir"))
    ]
    _dump(
        refinement_rows,
        HERE / "refinement_results.json",
        HERE / "refinement_results.csv",
    )

    for row in coarse + wide + refinement_rows:
        print(json.dumps(row))


if __name__ == "__main__":
    main()
