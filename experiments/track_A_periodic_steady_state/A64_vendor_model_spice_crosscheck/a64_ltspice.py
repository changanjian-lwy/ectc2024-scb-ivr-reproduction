"""A64 - run one LTspice netlist in a short scratch directory and read results back.

LTspice runs under Wine; the repository path contains spaces and CJK
characters and `.meas` output was lost above ~250 characters (A49), so every
netlist is written to a short work directory (default `/tmp/a64`, override
with `A64_WORKDIR`) together with a copy of the vendor model, run there, and
parsed there. Only parsed numbers come back into the repository.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
PROJECT = TRACK.parent.parent
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"
import a64_netlist as A  # noqa: E402


def workdir() -> Path:
    path = Path(os.environ.get("A64_WORKDIR", "/tmp/a64"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_model(dest: Path) -> None:
    for src in A.MODEL_FILES.values():
        if not src.exists():
            raise FileNotFoundError(f"{src} missing: run fetch_epc2067_model.py first")
        target = dest / src.name
        if not target.exists() or target.read_bytes() != src.read_bytes():
            shutil.copyfile(src, target)


def read_text_any(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff") or (len(raw) > 1 and raw[1:2] == b"\x00"):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("latin-1", errors="replace")


MEAS_RE = re.compile(r"^(\w+):\s.*?=\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")


def parse_log(path: Path) -> tuple[dict, list, str]:
    text = read_text_any(path)
    values: dict[str, float] = {}
    failed: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^Measurement "?(\w+)"? FAIL', line)
        if m:
            failed.append(m.group(1).lower())
            continue
        m = MEAS_RE.match(line)
        if m:
            values[m.group(1).lower()] = float(m.group(2))
    return values, failed, text


def run(text: str, name: str, timeout_s: float = 7200.0) -> dict:
    """Write, run and parse. Returns {'meas','failed','log','raw_path','wall_s'}."""
    wd = workdir()
    ensure_model(wd)
    net = wd / f"{name}.cir"
    for suffix in (".log", ".raw", ".op.raw"):
        stale = wd / f"{name}{suffix}"
        if stale.exists():
            stale.unlink()
    net.write_text(text, encoding="ascii")
    start = time.time()
    # Output goes to a FILE, never to a pipe: the wineserver started by the
    # first LTspice call inherits the caller's descriptors and outlives it, so a
    # captured pipe would never reach EOF while another LTspice is running.
    console = wd / f"{name}.console.txt"
    with open(console, "w") as out:
        proc = subprocess.run(["bash", str(RUNNER), "run", str(net)], stdout=out,
                              stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                              timeout=timeout_s)
    wall = time.time() - start
    log = wd / f"{name}.log"
    if not log.exists():
        raise RuntimeError(f"LTspice produced no log for {name}: rc={proc.returncode} "
                           f"console={console.read_text(errors='replace')[-500:]}")
    meas, failed, log_text = parse_log(log)
    return {"meas": meas, "failed": failed, "log_text": log_text,
            "raw_path": wd / f"{name}.raw", "wall_s": wall, "returncode": proc.returncode}


def load_raw(path: Path, names: list[str] | None = None) -> dict[str, np.ndarray]:
    """Read an LTspice transient .raw (binary, real) into float64 arrays.

    Handles both on-disk layouts: time double + float32 columns (default) and
    all-double (`numdgt` > 6). The header is decoded as A52's parser does.
    """
    raw = path.read_bytes()
    marker = "Binary:\n".encode("utf-16-le")
    idx = raw.find(marker)
    if idx < 0:
        raise ValueError("no Binary: marker")
    header = raw[:idx].decode("utf-16-le")
    body = raw[idx + len(marker):]
    nvars = npts = None
    variables = []
    for line in header.splitlines():
        line = line.rstrip("\r")
        if line.startswith("No. Variables:"):
            nvars = int(line.split(":", 1)[1])
        elif line.startswith("No. Points:"):
            npts = int(line.split(":", 1)[1])
        elif line.startswith("\t"):
            parts = line.strip("\t").split("\t")
            variables.append(parts[1])
    if len(body) == npts * 8 * nvars:
        data = np.frombuffer(body, dtype="<f8").reshape(npts, nvars)
    elif len(body) == npts * (8 + 4 * (nvars - 1)):
        rec = np.dtype([("t", "<f8"), ("v", "<f4", (nvars - 1,))])
        arr = np.frombuffer(body, dtype=rec)
        data = np.empty((npts, nvars))
        data[:, 0] = arr["t"]
        data[:, 1:] = arr["v"]
    else:
        raise ValueError(f"unexpected body length {len(body)} for {npts} x {nvars}")
    index = {v.lower(): i for i, v in enumerate(variables)}
    out = {"time": np.abs(data[:, 0])}
    for n in (names if names is not None else variables[1:]):
        out[n] = data[:, index[n.lower()]].astype(float)
    return out


def raw_variables(path: Path) -> list[str]:
    raw = path.read_bytes()
    marker = "Binary:\n".encode("utf-16-le")
    header = raw[:raw.find(marker)].decode("utf-16-le")
    return [ln.strip("\t").split("\t")[1] for ln in header.splitlines() if ln.startswith("\t")]


__all__ = ["run", "parse_log", "load_raw", "workdir", "raw_variables"]
