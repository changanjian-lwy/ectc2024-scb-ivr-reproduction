"""Minimal LTspice .raw binary transient-trace parser, written for R04E11's
own direct raw-trace inspection (the same "parse the raw binary transient
trace at fine time resolution" standard R04E9/R04E10 used, done here with
an explicit, reusable, committed script rather than an ad-hoc one-off).

FORMAT NOTES (determined directly from this project's own LTspice 26.0.2
for MacOS output, not assumed from generic documentation):
  - The text header (up to and including the "Binary:" line) is UTF-16LE
    encoded (this LTspice build's default on macOS), terminated by the
    literal bytes "Binary:\\n" also in UTF-16LE.
  - "Flags: real forward nocompression" -- all traces are real (not
    complex), points are in forward time order, not compressed.
  - The binary data block stores each point as: the first variable
    (time) as an 8-byte IEEE-754 double, followed by all other declared
    variables each as a 4-byte IEEE-754 single float. This was verified
    directly below (see `_verify_layout`) by checking that
    `(filesize - header_len) == no_points * (8 + 4*(no_vars-1))` exactly,
    not assumed from generic LTspice documentation.

USAGE:
  python3 ltspice_raw_parser.py <file.raw> --vars time state_mon timer \\
      --t-from 19.27e-6 --t-to 19.28e-6
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


class RawFile:
    def __init__(self, path: Path):
        self.path = path
        raw = path.read_bytes()
        header_text, binary_start = self._decode_header(raw)
        self.header_text = header_text
        self.vars: list[tuple[int, str, str]] = []
        no_points = None
        for line in header_text.splitlines():
            line = line.rstrip("\r")
            if line.startswith("No. Variables:"):
                self.no_vars = int(line.split(":", 1)[1].strip())
            elif line.startswith("No. Points:"):
                no_points = int(line.split(":", 1)[1].strip())
            elif line.startswith("\t"):
                parts = line.strip("\t").split("\t")
                idx = int(parts[0])
                name = parts[1]
                kind = parts[2] if len(parts) > 2 else ""
                self.vars.append((idx, name, kind))
        assert no_points is not None, "No. Points not found in header"
        self.no_points = no_points
        self.name_to_idx = {name: idx for idx, name, _ in self.vars}

        body = raw[binary_start:]
        rec_bytes = 8 + 4 * (self.no_vars - 1)
        expected = rec_bytes * self.no_points
        if len(body) != expected:
            raise ValueError(
                f"binary body length {len(body)} != expected {expected} "
                f"(no_points={self.no_points}, no_vars={self.no_vars}, "
                f"rec_bytes={rec_bytes}); file may be from a truncated/"
                f"still-running LTspice process, or uses a different "
                f"on-disk layout than assumed here."
            )
        self._body = body
        self._rec_bytes = rec_bytes
        self._struct = struct.Struct("<d" + "f" * (self.no_vars - 1))

    @staticmethod
    def _decode_header(raw: bytes) -> tuple[str, int]:
        marker = "Binary:\n".encode("utf-16-le")
        idx = raw.find(marker)
        if idx == -1:
            # fall back to a plain-ASCII header, in case a different
            # LTspice build/platform writes ASCII headers.
            marker_ascii = b"Binary:\n"
            idx = raw.find(marker_ascii)
            if idx == -1:
                raise ValueError("could not find 'Binary:' header marker")
            header_bytes = raw[: idx + len(marker_ascii)]
            return header_bytes.decode("ascii", errors="replace"), idx + len(
                marker_ascii
            )
        header_bytes = raw[: idx + len(marker)]
        return header_bytes.decode("utf-16-le"), idx + len(marker)

    def rows(self, start: int = 0, stop: int | None = None):
        """Yield decoded rows (tuples of floats, one per variable) for
        point indices [start, stop)."""
        if stop is None:
            stop = self.no_points
        rb = self._rec_bytes
        st = self._struct
        for i in range(start, stop):
            off = i * rb
            yield st.unpack_from(self._body, off)

    def column(self, name: str, start: int = 0, stop: int | None = None):
        idx = self.name_to_idx[name]
        for row in self.rows(start, stop):
            yield row[idx]

    def find_time_window(self, t_from: float, t_to: float) -> tuple[int, int]:
        """Binary-search-free linear scan (transient time is monotonic in
        'forward' flag mode) for the first/last point indices whose time
        falls in [t_from, t_to]. Also returns points OUTSIDE strictly
        monotonic order if the solver re-visited a timestamp (the very
        artifact this experiment is hunting), by scanning fully rather
        than assuming strict monotonicity."""
        idx0 = self.name_to_idx["time"]
        lo = None
        hi = None
        for i, row in enumerate(self.rows()):
            t = row[idx0]
            if t_from <= t <= t_to:
                if lo is None:
                    lo = i
                hi = i
        if lo is None:
            raise ValueError(f"no points found in [{t_from}, {t_to}]")
        return lo, hi + 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("--vars", nargs="+", required=True)
    ap.add_argument("--t-from", type=float, default=None)
    ap.add_argument("--t-to", type=float, default=None)
    ap.add_argument("--start", type=int, default=None)
    ap.add_argument("--stop", type=int, default=None)
    ap.add_argument("--max-rows", type=int, default=500)
    ap.add_argument("--list-vars", action="store_true")
    args = ap.parse_args(argv)

    rf = RawFile(args.raw_file)
    if args.list_vars:
        for idx, name, kind in rf.vars:
            print(f"{idx}\t{name}\t{kind}")
        print(f"no_points={rf.no_points}")
        return 0

    if args.t_from is not None and args.t_to is not None:
        start, stop = rf.find_time_window(args.t_from, args.t_to)
    else:
        start = args.start or 0
        stop = args.stop or rf.no_points

    for name in args.vars:
        if name not in rf.name_to_idx:
            print(f"WARNING: variable {name!r} not in raw file", file=sys.stderr)
    idxs = [rf.name_to_idx[n] for n in args.vars if n in rf.name_to_idx]
    names = [n for n in args.vars if n in rf.name_to_idx]

    print("\t".join(names))
    n_printed = 0
    for row in rf.rows(start, stop):
        print("\t".join(f"{row[i]!r}" for i in idxs))
        n_printed += 1
        if n_printed >= args.max_rows:
            print(f"... truncated at {args.max_rows} rows (of {stop-start})", file=sys.stderr)
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
