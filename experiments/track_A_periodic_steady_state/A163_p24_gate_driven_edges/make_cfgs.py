"""A163 cosim cfgs: the package drive as gate resistances (D79) on A152's robustness matrix, with the plant's
gate-driven high-side edges (cfg "gate", EPC2067 model; low sides keep A152's edges).
A: S50 = 50 pH (Q 7), r_on 2.5 / r_off 0.3 ohm per device, start-up ton from D79's calibration, A152's 13 rows and
   four modules.
B: S50 with the device / driver spread of D79 (threshold -0.3 / +1.5 V, C_ISS x 1.5, driver resistance x 0.7) on
   l_p48_1us and s_p62.
C: S50 with the valley measured at the gate command ("meas" "cmd") on l_p48_1us and s_p62 (diagnostic).
D: S75 = 75 pH, r_on 3.5 / r_off 0.3 ohm on five rows.
Writes cosim/cfg_*.json and cosim/ORDER.txt (four modules first)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TA = HERE.parent
_spec = importlib.util.spec_from_file_location("a152_make_cfgs", TA / "A152_p24_drive_spec_robustness" / "make_cfgs.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

# point: (loop pH, r_on, r_off, start-up ton ns = 36.5 + (1.015 - Vo(143.5 us) at 36.5) / 0.0283, D79 Section 5)
POINTS = {"S50": (50, 2.5, 0.3, 37.887), "S75": (75, 3.5, 0.3, 39.485)}
SPREAD = {"vthmin": {"dk2": -0.3}, "vthmax": {"dk2": 1.5}, "cissmax": {"cg_scale": 1.5}, "r07": {"r_scale": 0.7}}
D_ROWS = ("l_p48_1us", "s_p62", "L13_l_p48_1us", "l_m80_10us", "slew2")


def gate_cfg(cfg, point, extra=None, meas="act"):
    l_ph, r_on, r_off, ton = POINTS[point]
    rp = round(M.E.q_rp(l_ph * 1e-12, 7), 4)
    g = {"dev": "EPC2067", "r_on": r_on, "r_off": r_off, "meas": meas}
    for k, v in (extra or {}).items():
        if k == "r_scale":
            g["r_on"], g["r_off"] = round(r_on * v, 4), round(r_off * v, 4)
        else:
            g[k] = v
    return dict(M.package(cfg, l_ph, rp, 36.0, ton), gate=g)


def row_cfg(row):
    cfg = json.loads((M.A143C / f"cfg_{M.ROWS[row]}.json").read_text())
    if row.startswith("slew") and row != "slew5":
        cfg = dict(cfg, line_step=dict(cfg["line_step"], slew_us=float(row[4:])))
    return cfg


def main():
    COS.mkdir(exist_ok=True)
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A163 {name}: {note}"),
                                                         indent=1) + "\n")
        order.append(name)
    m4 = json.loads((M.A143C / "cfg_g5_l_p48_1us_k4.json").read_text())
    put("m4_s50_l_p48_1us", gate_cfg(m4, "S50"), "four modules, 50 pH, gate 2.5 / 0.3 ohm")
    for row in M.ROWS:
        put(f"s50_{row}", gate_cfg(row_cfg(row), "S50"), f"A143 {M.ROWS[row]}, 50 pH Q 7, gate 2.5 / 0.3 ohm")
    for tag, sp in SPREAD.items():
        for row in ("l_p48_1us", "s_p62"):
            put(f"s50{tag}_{row}", gate_cfg(row_cfg(row), "S50", sp), f"{row}, 50 pH, gate 2.5 / 0.3 ohm, spread {sp}")
    for row in ("l_p48_1us", "s_p62"):
        put(f"s50cmd_{row}", gate_cfg(row_cfg(row), "S50", meas="cmd"), f"{row}, 50 pH, valley measured at the command")
    for row in D_ROWS:
        put(f"s75_{row}", gate_cfg(row_cfg(row), "S75"), f"A143 {M.ROWS[row]}, 75 pH Q 7, gate 3.5 / 0.3 ohm")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
