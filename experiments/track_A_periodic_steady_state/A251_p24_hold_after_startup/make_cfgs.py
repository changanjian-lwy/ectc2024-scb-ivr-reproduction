"""A251 cfgs (BOUNDARY Section 1). Arm z = the final configuration + "dt_hold_periods" HOLD_N: phases 2..N keep the
dt_pred they have learnt from HOLD_N phase-1 turn-ons in mode P on.
- matrix: A246's 46 rows (cfg_h_<row>, the final configuration; out run_z_<row>) and its 4 position rows
  (cfg_ch_<row>_k<k>; out run_cz_<row>_k<k>); references A246's run_h_ / run_ch_;
- start-ups: A245's 20 rows (cfg_r_<row> + hold_floor_ns 3.0 = the final configuration, never run on start-ups) in
  arm h (out run_h_<row>) and arm z (run_z_<row>).
QUEUE: the decision rows first (BOUNDARY Section 4), then the other stage-1 rows, the start-ups, stage 2.
  python3 make_cfgs.py -> cosim/cfg_*.json, cosim/queue.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
A46 = TA / "A246_p24_held_report_floor"
A45 = TA / "A245_p24_reverse_conduction_delay"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


M46 = _load("a246_make_cfgs", A46 / "make_cfgs.py")
M45 = _load("a245_make_cfgs", A45 / "make_cfgs.py")
STAGE1, STAGE2, START = M46.STAGE1, M46.STAGE2, tuple(M45.STAGE1)
POS = {"p_N0_100k": (2, 4), "p_S75h_100k": (2, 4)}
HOLD_N, FLOOR_NS = 256, 3.0
FIRST = ("z_p_N0_100k", "cz_p_N0_100k_k2", "cz_p_N0_100k_k4", "z_p_N75_1000k", "z_p_S75h_1000k", "z_p_S75h_100k",
         "cz_p_S75h_100k_k2", "cz_p_S75h_100k_k4", "h_u_S75h_30", "z_u_S75h_30")


def write(src, arm, name, extra):
    c = json.loads(Path(src).read_text())
    c.update(extra)
    c.update(out=f"run_{arm}_{name}.json", note=f"A251 arm {arm}: {Path(src).relative_to(TA)} + {extra}")
    (COS / f"cfg_{arm}_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
    return f"{arm}_{name}"


def main():
    COS.mkdir(exist_ok=True)
    z = {"dt_hold_periods": HOLD_N}
    names = [write(A46 / "cosim" / f"cfg_h_{r}.json", "z", r, z) for r in STAGE1 + STAGE2]
    names += [write(A46 / "cosim" / f"cfg_ch_{r}_k{k}.json", "cz", f"{r}_k{k}", z) for r, ks in POS.items() for k in ks]
    for r in START:
        names.append(write(A45 / "cosim" / f"cfg_r_{r}.json", "h", r, {"hold_floor_ns": FLOOR_NS}))
        names.append(write(A45 / "cosim" / f"cfg_r_{r}.json", "z", r, {"hold_floor_ns": FLOOR_NS} | z))
    s1 = [n for n in names if n.startswith("z_p_")]
    st = [n for n in names if n.split("_", 1)[1] in START]
    order = list(FIRST) + [n for n in s1 + st + names if n not in FIRST]
    order = list(dict.fromkeys(order))
    assert sorted(order) == sorted(names)
    (COS / "queue.txt").write_text("\n".join(f"cfg_{n}.json" for n in order) + "\n")
    print(len(names), "cfgs")


if __name__ == "__main__":
    main()
