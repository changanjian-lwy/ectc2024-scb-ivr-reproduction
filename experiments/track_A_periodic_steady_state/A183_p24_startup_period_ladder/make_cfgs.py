"""A183 cosim cfgs: the mode-S (open-loop start-up) period t0 against the Cs-ladder split found in A181's records.
Only t0_ns and the board's start-up trim ton_ns change; plant V5 (all switches gate-driven, threshold interlock
1.0 ns), RTL and every other cfg value as A181.
  python3 make_cfgs.py screen   stage 1: cosim_screen/cfg_t<t0>_n<ton>.json - the slow-corner L x 0.75 board (A181's
                                S75) at 25 C, start-ups to 170 us (mode P from 144 us, the 20 us lead ramp included),
                                t0 200 / 250 / 300 / 500 ns x three trims each around the volt-second guess"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
SCREEN = HERE / "cosim_screen"
A181 = TA / "A181_p24_locked_trim_joint_corner"
L0 = 2.9333333199999997e-09
T_IL = 1.0
T_END_SCREEN = 170.0
# volt-second guess (BOUNDARY Section 3): ton = 1.035 V x t0 / 12 V + on-time change at turn-on (all hard: +16 ns
# lost, A181 S75 phase 1 at t0 400; all ZVS: -4 ns, phases 3-4); three trims 2 ns apart (3 ns at the mixed 300 / 500)
SCREEN_TONS = {200: (31.3, 33.3, 35.3), 250: (35.6, 37.6, 39.6), 300: (37.0, 40.0, 43.0), 500: (38.0, 41.0, 44.0)}


def s75(t0, ton, t_end):
    """A181's S75 board at 25 C (its cfg_S75_25_p0, slow corner, L x 0.75, t_il 1.0 ns) with mode-S period t0."""
    c = json.loads((A181 / "cosim" / "cfg_S75_25_p0.json").read_text())
    assert c["circuit"]["L"] == L0 * 0.75 and c["gate"]["t_il_ns"] == T_IL and c["t0_ns"] == 400.0
    return dict(c, t0_ns=float(t0), ton_ns=float(ton), t_end_us=t_end)


def name(t0, ton):
    return f"t{t0}_n{ton:.3f}".replace(".", "p")


def screen():
    SCREEN.mkdir(exist_ok=True)
    order = []
    for t0, tons in SCREEN_TONS.items():
        for ton in tons:
            n = name(t0, ton)
            c = dict(s75(t0, ton, T_END_SCREEN), out=f"run_{n}.json",
                     note=f"A183 stage 1: S75 board (slow corner, L x 0.75) at 25 C, mode-S period {t0} ns, ton {ton} ns, "
                          f"start-up to {T_END_SCREEN} us")
            (SCREEN / f"cfg_{n}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(n)
    (SCREEN / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "screen cfgs")


if __name__ == "__main__":
    {"screen": screen}[sys.argv[1]]()
