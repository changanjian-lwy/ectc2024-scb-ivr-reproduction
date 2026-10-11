"""A198 cosim cfgs: the worst known row, +4.8 V / 1 us, placed 2 / 10 / 20 / 40 / 80 us after the handover on the
final configuration (a194 make_cfgs.board: A188 start-up, lead by class, t_il 1.0 ns). Boards: S75 at 125 C (mode P
entered at 131.404 us), S75 at 25 C and N0 at 25 C (144.004 us). End 200 us after the step.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a194cfg", HERE.parent / "A194_p24_final_plant_random_stimuli" / "make_cfgs.py")
A194 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A194)
COS = HERE / "cosim"
ENTRY_US = {("S75", "hot"): 131.404, ("S75", "25"): 144.004, ("N0", "25"): 144.004}     # t_mode_p in A194's records
AFTER_US, POST, STEP = (2, 10, 20, 40, 80), 200.0, {"dv": 4.8, "slew_us": 1.0}


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for (b, tk), entry in ENTRY_US.items():
        for d in AFTER_US:
            name, t = f"{b}_{tk}_d{d}", round(entry + d, 4)
            c = A194.board(b, tk)
            c = dict(c, line_step=dict(STEP, t_us=t), t_end_us=round(t + POST, 4), out=f"run_{name}.json",
                     note=f"A198 {name}: board {b}, {A194.TEMPS[tk]:g} C, adopted start-up, lead {c['driver']['hs_on_lead_ns']:g} ns, "
                          f"+4.8 V / 1 us at {t} us = {d} us after mode P's entry ({entry} us)")
            (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs; run-equivalents of 900 us:", round(sum(ENTRY_US[k] + d + POST for k in ENTRY_US for d in AFTER_US) / 900.0, 1))


if __name__ == "__main__":
    main()
