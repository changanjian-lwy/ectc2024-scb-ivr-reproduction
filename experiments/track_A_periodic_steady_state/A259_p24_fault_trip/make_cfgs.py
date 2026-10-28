"""A259 cfgs (BOUNDARY Section 1): the final configuration + the fault trip (bridge cfg "fault", latched off).
- FAULT rows, arm f: make_diag_cfgs' rows (0.25 / 1 mOhm shorts, 150 / 200 % resistive overloads from 400 us) + FAULT;
  their arm d (no fault path) ran before the BOUNDARY;
- IDENT rows, arm f: final-configuration rows closest to each detector + FAULT; each must equal its record:
  a_S75h_d2 (largest legit peak, 211.8 A), p_N75_60k (low Vo, 0.958 V), o125_S75h (125 % overload, suspended),
  pr_N75 (overload, re-arm, then the 1 MHz train).
  python3 make_cfgs.py -> cosim/cfg_f_*.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
FAULT = {"i_a": 220.0, "n": 3, "uv_v": 0.9, "uv_ns": 400.0, "uv_mask_us": 0.0, "iavg_a": 350.0, "avg_us": 10.0}
CAP = {"n_susp": 6, "n_cap": 6}
C58, C54 = TA / "A258_p24_limit_count_cap" / "cosim", TA / "A254_p24_peak_limit_measured_level" / "cosim"
IDENT = {"a_S75h_d2": (C58 / "cfg_c_a_S75h_d2.json", C58 / "run_c_a_S75h_d2.json"),
         "p_N75_60k": (C54 / "cfg_l_p_N75_60k.json", C54 / "run_l_p_N75_60k.json"),
         "o125_S75h": (C58 / "cfg_c_o125_S75h.json", C58 / "run_c_o125_S75h.json"),
         "pr_N75": (C58 / "cfg_c_pr_N75.json", C58 / "run_c_pr_N75.json")}


def _diag():
    s = importlib.util.spec_from_file_location("a259_diag", HERE / "make_diag_cfgs.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


FAULT_ROWS = tuple(_diag().ROWS)


def main():
    n = 0
    for row in FAULT_ROWS:
        c = json.loads((HERE / "cosim" / f"cfg_d_{row}.json").read_text())
        c.update(fault=FAULT, out=f"run_f_{row}.json", note=f"A259 arm f: {row} + fault {FAULT}")
        (HERE / "cosim" / f"cfg_f_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        n += 1
    for row, (cfg, _) in IDENT.items():
        c = json.loads(cfg.read_text())
        c["ocp"] = dict(c["ocp"]) | CAP                       # A254's rows predate the count (none of them reached 6)
        c.update(fault=FAULT, out=f"run_f_{row}.json", note=f"A259 arm f: {row} (final configuration) + fault {FAULT}")
        (HERE / "cosim" / f"cfg_f_{row}.json").write_text(json.dumps(c, indent=1) + "\n")
        n += 1
    print(n, "cfgs")


if __name__ == "__main__":
    main()
