"""A199 cosim cfgs: three runs of the final configuration (a194 make_cfgs.board: A188 start-up, lead 8 ns, t_il
1.0 ns, nominal devices, 25 C) that record replay snapshots (cfg "snap_us") and every applied gate edge
("debug_edges_us") for scripts/p24_replay.py:
- N0_steady: no event, to 297 us; snapshots in mode S (141.0-142.3 us) and in settled mode P (292.0-296.5 us);
- N0_step:   +4.8 V / 1 us at 500 us, to 531 us; snapshots over 499.4-530.2 us;
- N75_step:  the same on the L x 0.75 board.
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
STEP = {"dv": 4.8, "slew_us": 1.0, "t_us": 500.0}
RUNS = {"N0_steady": ("N0", {"t_end_us": 297.0, "snap_us": [[141.0, 142.3], [292.0, 296.5]], "debug_edges_us": [140.9, 296.9]}),
        "N0_step": ("N0", {"line_step": STEP, "t_end_us": 531.0, "snap_us": [[499.4, 530.2]], "debug_edges_us": [499.3, 530.6]}),
        "N75_step": ("N75", {"line_step": STEP, "t_end_us": 531.0, "snap_us": [[499.4, 530.2]], "debug_edges_us": [499.3, 530.6]})}


def main():
    COS.mkdir(exist_ok=True)
    for name, (b, extra) in RUNS.items():
        c = dict(A194.board(b, "25"), **extra, out=f"run_{name}.json",
                 note=f"A199 {name}: board {b}, 25 C, final configuration, replay snapshots and applied edges recorded")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(RUNS) + "\n")
    print(len(RUNS), "cfgs")


if __name__ == "__main__":
    main()
