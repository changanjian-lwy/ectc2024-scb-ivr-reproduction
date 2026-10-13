"""A207 cosim cfgs: the final configuration on plant V6 with part of the load released.
Base: A206's cfg_E_N0_steady_ls0p3_t (board N0, 25 C, switches at the datasheet maximum, low sides 0.3 ohm, A206's
start-up trim). Row f<p>: cfg "load_step" {"t_us": 300, "i_a": -(1 - p / 100) 250}: the 4 mOhm load stays and the
step feeds that current back into the output, so p % of 250 A remain at Vo = 1 V. End 450 us; every gate edge of the
last 13 us is logged for the loss books (a206_analyze.whole).
  python3 make_cfgs.py -> cosim/cfg_f*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "A206_p24_low_side_zvs_turn_on" / "cosim" / "cfg_E_N0_steady_ls0p3_t.json"
COS = HERE / "cosim"
I_FULL = 250.0
SHARES = (75, 60, 55, 50, 45, 40, 30, 10)          # % of 250 A left after the step
T_STEP, T_END = 300.0, 450.0


def row(p, t_step=T_STEP, t_end=T_END):
    c = json.loads(BASE.read_text())
    i_a = -I_FULL * (100 - p) / 100.0
    return dict(c, load_step={"t_us": t_step, "i_a": i_a}, t_end_us=t_end, snap_us=[[t_end - 2.0, t_end - 0.5]],
                debug_edges_us=[t_end - 13.0, t_end - 0.1], out=f"run_f{p}.json",
                note=f"A207 f{p}: A206's E_N0_steady_ls0p3_t (final configuration, plant V6, N0, 25 C) with {i_a:g} A "
                     f"drawn from {t_step:g} us on: {p} % of {I_FULL:g} A remain")


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for p in SHARES:
        (COS / f"cfg_f{p}.json").write_text(json.dumps(row(p), indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(f"f{p}" for p in SHARES) + "\n")
    print(len(SHARES), "cfgs; run-equivalents of 900 us:", round(len(SHARES) * T_END / 900.0, 2))
