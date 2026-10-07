"""A165 cosim cfgs: A164's matrix (50 pH, r_on 3.0 / r_off 0.3 ohm +-20 %, 8 ns lead, the same per-board trims from
A164's trims.json, the same corners and rows) with the lead as a pulse shift (bridge driver lead_mode "pulse": the
lead-moved predictive turn-on moves its pulse's turn-off and the following low-side turn-on too, as a controller with a
signed dt_pred would). Writes cosim/cfg_*.json and cosim/ORDER.txt (four modules first)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A4D = HERE.parent / "A164_p24_gate_drive_spread"
_s = importlib.util.spec_from_file_location("a164_make_cfgs", A4D / "make_cfgs.py")
A4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A4)


def pulse(cfg):
    if "driver" in cfg and cfg["driver"].get("hs_on_lead_ns"):
        cfg = dict(cfg, driver=dict(cfg["driver"], lead_mode="pulse"))
    return cfg


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for name in (A4D / "cosim" / "ORDER.txt").read_text().split():
        if "lead0" in name:                                   # A164's controls without a lead are not rerun
            continue
        cfg = json.loads((A4D / "cosim" / f"cfg_{name}.json").read_text())
        cfg = dict(pulse(cfg), out=f"run_{name}.json", note=cfg["note"].replace("A164", "A165") + ", lead as a pulse shift")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
