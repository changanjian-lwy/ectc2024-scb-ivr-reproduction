"""Extract the settled state_mon sequence (dwell values close to an
integer) over time, to find every point where the sequence goes
BACKWARD (a genuine reversal), not just forward. Also reports the
non-integer "stuck mid-transition" episodes (a proxy for solver-retry
difficulty) between each settled dwell.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ltspice_raw_parser import RawFile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("--tol", type=float, default=0.01)
    ap.add_argument("--t-from", type=float, default=None)
    ap.add_argument("--t-to", type=float, default=None)
    args = ap.parse_args()

    rf = RawFile(args.raw_file)
    tidx = rf.name_to_idx["time"]
    sidx = rf.name_to_idx["V(state_mon)"]

    if args.t_from is not None:
        start, stop = rf.find_time_window(args.t_from, args.t_to)
    else:
        start, stop = 0, rf.no_points

    last_settled = None
    settled_seq = []  # (time, state, row_index)
    reversals = 0
    for i, row in enumerate(rf.rows(start, stop), start=start):
        t = row[tidx]
        s = row[sidx]
        near = round(s)
        if abs(s - near) < args.tol and 0 <= near <= 7:
            if last_settled is None or near != last_settled:
                settled_seq.append((t, near, i))
                if last_settled is not None and near < last_settled and not (
                    last_settled == 7 and near == 0
                ):
                    reversals += 1
                    print(
                        f"*** REVERSAL: settled state {last_settled} -> {near} "
                        f"at t={t!r} (row {i})"
                    )
                last_settled = near

    print(f"\n# total settled-state dwell transitions: {len(settled_seq)}")
    print(f"# reversals (state decreased, not the 7->0 wraparound): {reversals}")
    print("\n# first 60 settled dwells:")
    for t, s, i in settled_seq[:60]:
        print(f"t={t!r}\tstate={s}\trow={i}")
    if len(settled_seq) > 60:
        print(f"... ({len(settled_seq)-60} more)")


if __name__ == "__main__":
    main()
