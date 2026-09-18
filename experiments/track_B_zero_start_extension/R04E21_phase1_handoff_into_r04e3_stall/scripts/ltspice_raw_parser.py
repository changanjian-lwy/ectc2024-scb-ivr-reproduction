"""Minimal LTspice .raw binary transient-trace parser. Copied unchanged
(byte-for-byte identical logic) from R04E18/R04E19's own committed
`scripts/ltspice_raw_parser.py` (itself unchanged from R04E11/R04E12/
R04E13's own), reused here rather than re-derived, per this project's
own standing convention of not re-inventing an already-verified
raw-format parser. See those scripts' own docstring for the original
format-determination notes (LTspice 26.0.2 for MacOS, UTF-16LE text
header terminated by "Binary:\\n", real/forward/nocompression flags,
time as 8-byte double + remaining vars as 4-byte singles per point).

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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw_file", type=Path)
    ap.add_argument("--vars", nargs="+", required=True)
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

    start = args.start or 0
    stop = args.stop or rf.no_points

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
