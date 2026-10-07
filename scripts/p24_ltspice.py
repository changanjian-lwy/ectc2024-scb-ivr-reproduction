"""D79 / A163: run LTspice (macOS build in its CrossOver bottle) in batch mode and read its results.

Environment: SCB_LT_CX (the bundle's ltspice support folder, default /Applications/LTspice.app/Contents/SharedSupport/
ltspice), SCB_LT_WORK (a work folder with an ASCII path, default ~/.scb_ltspice_work; never inside the repository:
netlists there include vendor model text). Vendor subcircuits are copied into the work folder at run time from
scb_ivr.p24_gate_model.lib_path().

run(name, text) writes <work>/<name>.net (OPTIONS added), runs LTspice -b, and returns
{"meas": {name: value}, "raw": (names, array) or None, "log": text}.
"""
from __future__ import annotations

import os
import re
import struct
import subprocess
from pathlib import Path

import numpy as np

from scb_ivr.p24_gate_model import _subckt, lib_path

CX = Path(os.environ.get("SCB_LT_CX", "/Applications/LTspice.app/Contents/SharedSupport/ltspice"))
WORK = Path(os.environ.get("SCB_LT_WORK", str(Path.home() / ".scb_ltspice_work")))
EXE = r"C:\Program Files\ADI\LTspice\LTspice.exe"
# LTspice's default charge tolerance mis-integrates the EPC model's charge-defined capacitances (D79: the datasheet
# gate-charge test gives Q_G 14.4 nC at the defaults, 10.2 nC with a 0.1 ns step, 17.23 nC with these; datasheet 17.1)
OPTIONS = ".options plotwinsize=0 numdgt=15 reltol=1e-5 abstol=1e-12 chgtol=1e-17"


def available():
    return (CX / "bin" / "wine").exists()


def vendor_include(names=("EPC2067",)):
    """Write the named vendor subcircuits to <work>/vendor.lib; returns the .include line."""
    WORK.mkdir(parents=True, exist_ok=True)
    text = lib_path().read_text(errors="replace")
    (WORK / "vendor.lib").write_text("\n".join(_subckt(text, n) for n in names) + "\n")
    return ".include vendor.lib"


_NODE = re.compile(r"\b(gatein|drainin|sourcein|gate|drain|source)\b", re.I)


def flat_device(name="EPC2067"):
    """The vendor subcircuit split into (.param lines, element lines with join()ed continuations) for flattening."""
    body = _subckt(lib_path().read_text(errors="replace"), name).splitlines()[1:-1]
    logical = []
    for ln in body:
        st = ln.strip()
        if not st or st.startswith("*"):
            continue
        if st.startswith("+") and logical:
            logical[-1] += " " + st[1:]
        else:
            logical.append(st)
    params = [x for x in logical if x.lower().startswith(".param")]
    elems = [x for x in logical if not x.lower().startswith(".")]
    return params, elems


def instance(elems, inst, g, d, s, k2=None):
    """Element lines of one device instance: element names suffixed, pins mapped to (g, d, s), internal nodes
    <inst>_g / _d / _s (gate, drain, source after rg / rd / rs). k2 (V) gives this instance its own threshold
    parameter (a mismatch case; returned lines then start with its .param)."""
    m = {"gatein": g, "drainin": d, "sourcein": s, "gate": f"{inst}_g", "drain": f"{inst}_d", "source": f"{inst}_s"}
    out = [f".param k2_{inst}={k2}"] if k2 is not None else []
    for e in elems:
        nm, rest = e.split(None, 1)
        rest = _NODE.sub(lambda k: m[k.group(1).lower()], rest)
        if k2 is not None:
            rest = re.sub(r"\bk2\b", f"k2_{inst}", rest)
        out.append(f"{nm}_{inst} " + rest)
    return out


def _winpath(p):
    return "Z:" + str(p).replace("/", "\\")


def read_raw(path):
    """LTspice binary .raw (transient, real): names and an (npoints, nvars) float64 array; |time|."""
    b = path.read_bytes()
    k = b.find("Binary:\n".encode("utf-16-le"))
    head = b[:k].decode("utf-16-le")
    data = b[k + len("Binary:\n".encode("utf-16-le")):]
    nv = int(re.search(r"No\. Variables:\s*(\d+)", head).group(1))
    npt = int(re.search(r"No\. Points:\s*(\d+)", head).group(1))
    dbl = "double" in re.search(r"Flags:(.*)", head).group(1)
    names = re.findall(r"^\s*\d+\s+(\S+)\s+\S+", head.split("\nVariables:")[1], re.M)[:nv]
    if dbl:
        arr = np.frombuffer(data[:8 * nv * npt], dtype="<f8").reshape(npt, nv)
    else:
        rec = np.dtype([("t", "<f8")] + [(f"v{i}", "<f4") for i in range(nv - 1)])
        r = np.frombuffer(data[:rec.itemsize * npt], dtype=rec)
        arr = np.column_stack([r["t"]] + [r[f"v{i}"].astype(float) for i in range(nv - 1)])
    arr = arr.copy()
    arr[:, 0] = np.abs(arr[:, 0])
    return names, arr


def run(name, text, raw=True, timeout=900):
    WORK.mkdir(parents=True, exist_ok=True)
    net = WORK / f"{name}.net"
    body = text.rstrip()
    if body.lower().endswith(".end"):
        body = body[:-4].rstrip()
    net.write_text(body + "\n" + OPTIONS + "\n.end\n")
    for ext in (".log", ".raw"):
        (WORK / f"{name}{ext}").unlink(missing_ok=True)
    env = dict(os.environ, CX_ROOT=str(CX))
    subprocess.run([str(CX / "bin" / "wine"), "--bottle", "ltspice", "--cx-app", EXE, "-b", _winpath(net)],
                   cwd=WORK, env=env, capture_output=True, timeout=timeout)
    log_p = WORK / f"{name}.log"
    log = log_p.read_text(errors="replace") if log_p.exists() else ""
    if not log:
        raise RuntimeError(f"LTspice wrote no log for {name}")
    meas = {}
    for ln in log.splitlines():                                   # "n: V(x)=2  AT t" (WHEN), "n: V(x) =v at t" (FIND),
        m = re.match(r"^(\w+):\s.*\sAT\s+([-+0-9.eE]+)\s*$", ln)      # "n: MAX(V(x))=v FROM a TO b"
        if m:
            meas[m.group(1).lower()] = float(m.group(2)); continue
        m = re.match(r"^(\w+):.*?=\s*([-+0-9.eE]+)", ln)
        if m:
            meas[m.group(1).lower()] = float(m.group(2))
    rp = WORK / f"{name}.raw"
    return {"meas": meas, "raw": read_raw(rp) if (raw and rp.exists()) else None, "log": log}
