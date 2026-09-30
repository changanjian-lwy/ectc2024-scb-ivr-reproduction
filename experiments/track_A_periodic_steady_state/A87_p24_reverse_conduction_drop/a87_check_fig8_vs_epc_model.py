"""A87 independent check of the digitised EPC2067 Fig. 8 (A57) against EPC's public SPICE model (BOUNDARY Section 2).

EPC's model (EPCGaNLibrary.lib, subcircuit EPC2067) is not in this repository. The script reads a local copy, parses
the subcircuit's parameters at run time and evaluates its channel equation in the third quadrant with VGS = 0 V: the
gate is at the source terminal, the channel is opened by the gate-drain voltage, and the parasitic drain and source
resistances are in series. Output: a87_fig8_vs_epc_model.json (numbers, the library's SHA-256 and version line).

Usage: python3 a87_check_fig8_vs_epc_model.py <path/to/EPCGaNLibrary.lib>
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
FIG8_CSV = HERE.parent / "A57_datasheet_reverse_conduction_pricing" / "epc2067_fig8_reverse_characteristics.csv"
NAMES = ("A1", "k2", "k3", "rpara", "rpara_s_factor", "aITc", "arTc", "k2Tc", "x0_0", "x0_0_TC", "x0_1", "x0_1_TC")


def parse(lib_text):
    blk = lib_text[lib_text.index(".subckt EPC2067 "):]
    blk = blk[:blk.index("\nrd ")]                     # the .param block ends before the first resistor line
    raw = {m.group(1): m.group(2) for m in re.finditer(r"(\w+)\s*=\s*([-+0-9.eE]+|\{[^}]*\})", blk)}

    def val(k, depth=0):
        v = raw[k]
        if not v.startswith("{"):
            return float(v)
        expr = v[1:-1]
        for kk in sorted(raw, key=len, reverse=True):
            if kk != k and re.search(rf"\b{kk}\b", expr):
                expr = re.sub(rf"\b{kk}\b", f"({val(kk, depth + 1)})", expr)
        return float(eval(expr, {"__builtins__": {}}))
    return {k: val(k) for k in NAMES}


def model_current(P, v_sd, temp_c):
    """Third-quadrant current (source -> drain, A) at terminal V_SD with VGS = 0 V."""
    t = temp_c - 25.0
    rd = (1 - P["rpara_s_factor"]) * P["rpara"] * (1 - P["arTc"] * t)
    rs = P["rpara_s_factor"] * P["rpara"] * (1 - P["arTc"] * t)
    a1, k2 = P["A1"] * (1 - P["aITc"] * t), P["k2"] * (1 - P["k2Tc"] * t)
    x0, x1 = P["x0_0"] * (1 - P["x0_0_TC"] * t), P["x0_1"] * (1 - P["x0_1_TC"] * t)

    def f(i):
        vgd, vsd_int = v_sd - i * rd, v_sd - i * (rd + rs)
        return a1 * math.log1p(math.exp((vgd - k2) / P["k3"])) * vsd_int / (1 + (x0 + x1 * vgd) * vsd_int) - i
    hi = v_sd / (rd + rs) * (1 - 1e-9)
    return brentq(f, 0.0, hi) if f(0.0) > 0 else 0.0


def model_voltage(P, i, temp_c):
    return brentq(lambda v: model_current(P, v, temp_c) - i, 1e-6, 6.0)   # the model's valid range covers Fig. 8's 0-5 V


def main(lib_path):
    raw = Path(lib_path).read_bytes()
    text = raw.decode(errors="ignore")
    version = [ln.strip() for ln in text.splitlines() if re.match(r"\*\s+1\.\d+:", ln)][-1]
    P = parse(text)
    fig = {25: [], 125: []}
    with open(FIG8_CSV) as fh:
        for row in csv.DictReader(fh):
            fig[int(row["temperature_c"])].append((float(row["isd_a_per_device"]), float(row["vsd_v"])))
    out = {"model_library_sha256": hashlib.sha256(raw).hexdigest(), "model_library_last_version_line": version,
           "fig8_csv_sha256": hashlib.sha256(FIG8_CSV.read_bytes()).hexdigest(), "vgs_v": 0.0, "rows": {}}
    for temp in (25, 125):
        i_fig, v_fig = np.array(sorted(fig[temp])).T
        rows = []
        for i in (0.5, 1, 2, 5, 10, 25, 50, 75, 100, 150, 200, 300, 400):
            vf = float(np.interp(i, i_fig, v_fig)); vm = model_voltage(P, i, temp)
            rows.append({"i_a": i, "fig8_v": vf, "model_v": vm, "diff_v": vm - vf})
            print(f"{temp:3d} C  {i:6.1f} A  Fig. 8 {vf:.3f} V  model {vm:.3f} V  diff {1e3 * (vm - vf):+6.1f} mV")
        out["rows"][str(temp)] = rows
    (HERE / "a87_fig8_vs_epc_model.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
