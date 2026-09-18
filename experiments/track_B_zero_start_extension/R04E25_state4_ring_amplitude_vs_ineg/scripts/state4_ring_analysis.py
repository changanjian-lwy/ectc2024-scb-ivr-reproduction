"""R04E25 state-4 ring-amplitude analysis. New for this experiment (not a
copy of a prior script): for each cell's .raw trace, restricts to the
time window where V(state_mon) is in state 4 (in [3.9,4.1], the same
half-integer bucket convention this project's own .machine construct
uses elsewhere), bounded below by t_neg_target (the 3->4 transition,
passed in from the .log) and above by min(t_high_side_zvs, TSTOP) (all
four cells FAIL t_high_side_zvs, so the upper bound is TSTOP=100us in
every cell here). Within that window, computes min/max of
V(vin,xmod:a1) = V(vin)-V(xmod:a1) (the state-4 exit condition's own
quantity) and the times they occur, plus full-trace IL1 min/max for the
safety check.

USAGE:
  python3 state4_ring_analysis.py <file.raw> --t-neg-target <t> [--t-stop 100e-6]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile


def analyze(path: Path, t_neg_target: float, t_stop: float = 100e-6):
    rf = RawFile(path)
    t_idx = rf.name_to_idx["time"]
    state_idx = rf.name_to_idx["V(state_mon)"]
    vin_idx = rf.name_to_idx["V(vin)"]
    a1_idx = rf.name_to_idx["V(xmod:a1)"]
    il1_idx = rf.name_to_idx["I(xmod:L1)"]

    il1_min_full = float("inf")
    il1_max_full = float("-inf")

    ring_min = float("inf")
    ring_min_t = None
    ring_max = float("-inf")
    ring_max_t = None
    n_state4_points = 0
    state4_first_t = None
    state4_last_t = None

    for row in rf.rows():
        t = row[t_idx]
        state = row[state_idx]
        il1 = row[il1_idx]

        if il1 < il1_min_full:
            il1_min_full = il1
        if il1 > il1_max_full:
            il1_max_full = il1

        if t < t_neg_target or t > t_stop:
            continue
        if not (3.9 <= state <= 4.1):
            continue

        n_state4_points += 1
        if state4_first_t is None:
            state4_first_t = t
        state4_last_t = t

        ring_v = row[vin_idx] - row[a1_idx]
        if ring_v < ring_min:
            ring_min = ring_v
            ring_min_t = t
        if ring_v > ring_max:
            ring_max = ring_v
            ring_max_t = t

    return dict(
        raw_file=str(path),
        n_points=rf.no_points,
        t_neg_target=t_neg_target,
        t_stop_used=t_stop,
        state4_n_points=n_state4_points,
        state4_first_t=state4_first_t,
        state4_last_t=state4_last_t,
        ring_min_v=ring_min,
        ring_min_t=ring_min_t,
        ring_max_v=ring_max,
        ring_max_t=ring_max_t,
        il1_min_full_trace=il1_min_full,
        il1_max_full_trace=il1_max_full,
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("--t-neg-target", type=float, required=True)
    ap.add_argument("--t-stop", type=float, default=100e-6)
    args = ap.parse_args()
    r = analyze(args.raw_file, args.t_neg_target, args.t_stop)
    for k, v in r.items():
        print(f"{k}: {v}")
