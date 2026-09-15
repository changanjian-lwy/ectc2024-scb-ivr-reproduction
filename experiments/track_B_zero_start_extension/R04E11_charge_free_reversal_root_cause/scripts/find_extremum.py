"""Find the exact time index/row where a named trace hits its MAX or MIN
over the whole run, and print a window of rows around it for every
requested variable. Used to locate R04E10's own reported ICS2/ICS3
excursion precisely inside this instrumented re-run, then to inspect the
newly-added reset-gate/timer nodes at that same moment.
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
    ap.add_argument("--target", required=True, help="variable to find extremum of")
    ap.add_argument("--mode", choices=["max", "min"], required=True)
    ap.add_argument("--vars", nargs="+", required=True)
    ap.add_argument("--before", type=int, default=20)
    ap.add_argument("--after", type=int, default=20)
    args = ap.parse_args()

    rf = RawFile(args.raw_file)
    tidx = rf.name_to_idx["time"]
    vidx = rf.name_to_idx[args.target]

    best_i = None
    best_v = None
    for i, row in enumerate(rf.rows()):
        v = row[vidx]
        if best_v is None or (args.mode == "max" and v > best_v) or (
            args.mode == "min" and v < best_v
        ):
            best_v = v
            best_i = i

    print(f"# extremum of {args.target}: {best_v} at row {best_i}, t={rf.rows(best_i, best_i+1).__next__()[tidx]!r}")

    idxs = [rf.name_to_idx[n] for n in args.vars]
    names = args.vars
    start = max(0, best_i - args.before)
    stop = min(rf.no_points, best_i + args.after + 1)
    print("\t".join(["row", "*"] + names))
    for i, row in enumerate(rf.rows(start, stop), start=start):
        marker = "<<<" if i == best_i else ""
        print("\t".join([str(i), marker] + [repr(row[j]) for j in idxs]))


if __name__ == "__main__":
    main()
