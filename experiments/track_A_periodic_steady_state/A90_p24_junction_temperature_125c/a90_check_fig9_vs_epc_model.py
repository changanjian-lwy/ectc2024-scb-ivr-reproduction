"""A90 independent check of the digitised EPC2067 Fig. 9 against EPC's public SPICE model.

The model's forward channel equation with its temperature coefficients and series resistances, evaluated at
VGS = 5 V, ID = 37 A (Fig. 9's conditions), gives RDS(on)(T); its ratio to 25 C is compared with Fig. 9. The library
is read from a local path and is not in this repository; the parameter parser is A87's (read-only import).
Also records whether any capacitance expression of the EPC2067 subcircuit depends on Temp.

Usage: python3 a90_check_fig9_vs_epc_model.py <path/to/EPCGaNLibrary.lib>
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "A87_p24_reverse_conduction_drop"))
from a87_check_fig8_vs_epc_model import parse  # noqa: E402

FIG9_CSV = HERE / "epc2067_fig9_rdson_vs_tj.csv"


def rds_on(P, temp_c, vgs=5.0, i=37.0):
    t = temp_c - 25.0
    rd = (1 - P["rpara_s_factor"]) * P["rpara"] * (1 - P["arTc"] * t)
    rs = P["rpara_s_factor"] * P["rpara"] * (1 - P["arTc"] * t)
    a1, k2 = P["A1"] * (1 - P["aITc"] * t), P["k2"] * (1 - P["k2Tc"] * t)
    x0, x1 = P["x0_0"] * (1 - P["x0_0_TC"] * t), P["x0_1"] * (1 - P["x0_1_TC"] * t)
    vgs_i = vgs - i * rs                                   # internal gate-source (gate current ~ 0)
    f = lambda v: a1 * math.log1p(math.exp((vgs_i - k2) / P["k3"])) * v / (1 + (x0 + x1 * vgs_i) * v) - i
    return (brentq(f, 1e-9, 1.0) + i * (rd + rs)) / i


def main(lib_path):
    raw = Path(lib_path).read_bytes()
    text = raw.decode(errors="ignore")
    P = parse(text)
    sub = text[text.index(".subckt EPC2067 "):]
    sub = sub[:sub.index(".ends")] if ".ends" in sub else sub[:6000]
    cap_lines = [ln for ln in sub.splitlines() if ln.strip().upper().startswith("C_")]
    cap_temp = any("temp" in ln.lower() for ln in cap_lines)
    tj, k = np.loadtxt(FIG9_CSV, delimiter=",", skiprows=1, unpack=True)
    k25_fig = float(np.interp(25, tj, k)); r25 = rds_on(P, 25.0)
    rows = []
    for t in (0, 25, 50, 75, 100, 125, 150):
        rm = rds_on(P, float(t))
        rows.append({"tj_c": t, "model_mohm": rm * 1e3, "model_ratio_to_25c": rm / r25,
                     "fig9_ratio_to_25c": float(np.interp(t, tj, k)) / k25_fig})
        print(f"{t:4d} C  model {rm * 1e3:.3f} mOhm  ratio {rm / r25:.4f}  Fig. 9 {rows[-1]['fig9_ratio_to_25c']:.4f}")
    out = {"model_library_sha256": hashlib.sha256(raw).hexdigest(), "vgs_v": 5.0, "id_a": 37.0, "rows": rows,
           "capacitance_lines_depend_on_temp": cap_temp, "capacitance_lines": len(cap_lines)}
    print("capacitance expressions depend on Temp:", cap_temp, f"({len(cap_lines)} lines)")
    (HERE / "a90_fig9_vs_epc_model.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
