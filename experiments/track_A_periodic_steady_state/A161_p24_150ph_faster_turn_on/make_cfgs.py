"""A161 cosim cfgs: 150 pH with a faster turn-on (x_on 3.0 V), on A152's robustness matrix. Point S150: loop 150 pH (Q 7), turn-on
20 A/ns (x_on = 3.0 V, the voltage limit), turn-off 72 A/ns (x_off 10.8 V), start-up ton by A155's law (V_T 1.015 V).
Rows = A152's 13 (A143 references; slew rows from A150's c00_slew*) as s150_<row>, and four modules (m4_s150_l_p48_1us).
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

L_PH, D_ON, D_OFF = 150, 20.0, 72.0


def ton_law():
    f = json.loads((TA / "A155_p24_startup_ton_law" / "a155_fit.json").read_text())
    return round(35.5 + (1.015 - f["c0"] + f["a"] * D_ON ** -0.5 + f["b"] * L_PH * 1e-3 - f["c"] * D_OFF ** -0.5) / f["s"], 3)


def main():
    COS.mkdir(exist_ok=True)
    rp, ton = round(M.E.q_rp(L_PH * 1e-12, 7), 4), ton_law()
    order = []

    def put(name, cfg, note):
        (COS / f"cfg_{name}.json").write_text(json.dumps(dict(cfg, out=f"run_{name}.json", note=f"A161 {name}: {note}"), indent=1) + "\n")
        order.append(name)
    m4 = json.loads((M.A143C / "cfg_g5_l_p48_1us_k4.json").read_text())
    put("m4_s150_l_p48_1us", M.package(m4, L_PH, rp, D_ON, ton), f"four modules, {L_PH} pH, on {D_ON:g} / off 72 A/ns, ton {ton}")
    for row, ref in M.ROWS.items():
        cfg = json.loads((M.A143C / f"cfg_{ref}.json").read_text())
        if row.startswith("slew") and row != "slew5":
            cfg = dict(cfg, line_step=dict(cfg["line_step"], slew_us=float(row[4:])))
        put(f"s150_{row}", M.package(cfg, L_PH, rp, D_ON, ton), f"A143 {ref}, {L_PH} pH Q 7, on {D_ON:g} / off 72 A/ns, ton {ton}")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs, rp", rp, "ton", ton)


if __name__ == "__main__":
    main()
