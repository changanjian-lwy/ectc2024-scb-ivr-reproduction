"""A166 cosim cfgs: A165's spec (50 pH, 3.0 / 0.3 ohm +-20 %, per-board start-up trim, the lead as a pulse shift) with
an interlock-safe lead per board: lead = the shortest high-side turn-on delay seen in the board's calibration start-up
(A164 cosim_cal, gate_stats delay_on min: command to channel start) minus 1 ns. With dt_pred >= 0 the high-side channel
then cannot start before the low side's turn-off command + 1 ns, whatever the valley learning does (A165 pre: a fixed
8 or 12 ns lead let phase 4's channel start under a conducting low side at the slow corner when its dt_pred fell to 0).
Rows: A165's, less ff s_p62, hot s_p62 and nom l_m80_10us. Writes cosim/cfg_*.json, cosim/ORDER.txt, leads.json."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
A4D, A5D = HERE.parent / "A164_p24_gate_drive_spread", HERE.parent / "A165_p24_gate_lead_pulse"
MARGIN_NS = 1.0
BOARD = {"m4_nom_l_p48_1us": "nom_L0", "nom_l_p48_1us": "nom_L0", "nom_s_p62": "nom_L0", "nom_slew4": "nom_L0",
         "nom_L07_l_p48_1us": "nom_L07", "nom_L13_l_p48_1us": "nom_L13", "ff_l_p48_1us": "ff_L0",
         "ff_l_m80_10us": "ff_L0", "ss_l_p48_1us": "ss_L0", "ss_s_p62": "ss_L0", "ss_l_m80_10us": "ss_L0",
         "ss_slew4": "ss_L0", "hot_l_p48_1us": "hot_L0"}


def leads():
    out = {}
    for b in sorted(set(BOARD.values())):
        r = json.loads((A4D / "cosim_cal" / f"run_{b}.json").read_text())
        d = r["gate_stats"]["delay_on_s"][0] * 1e9
        out[b] = {"delay_min_ns": round(d, 3), "lead_ns": round(max(0.0, d - MARGIN_NS), 2)}
    return out


def main():
    ld = leads()
    (HERE / "leads.json").write_text(json.dumps(ld, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []
    for name, b in BOARD.items():
        cfg = json.loads((A5D / "cosim" / f"cfg_{name}.json").read_text())
        cfg = dict(cfg, driver=dict(cfg["driver"], hs_on_lead_ns=ld[b]["lead_ns"]), out=f"run_{name}.json",
                   note=cfg["note"].replace("A165", "A166") + f", per-board lead {ld[b]['lead_ns']} ns")
        (COS / f"cfg_{name}.json").write_text(json.dumps(cfg, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs;", {b: v["lead_ns"] for b, v in ld.items()})


if __name__ == "__main__":
    main()
