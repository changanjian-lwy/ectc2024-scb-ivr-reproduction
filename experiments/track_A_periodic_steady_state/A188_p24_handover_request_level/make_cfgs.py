"""A188 cosim cfgs: A186's Vo-requested handover moved from 1.03 to 1.045 V, above every 25 C board's mode-S Vo
before 144 us (A185 maxima 1.0321-1.0358 V), below the hot drift (N0 1.049, S0 1.127, S75 1.130 V). The 25 C runs
are then A185's, bit for bit (the latch never sets); one check run (S0, the highest 25 C maximum) to 150 us shows it.
Hot runs: N0 / S0 / F0 to 500 us and S75 full (+4.8 V / 1 us at 500 us), from A186's cfgs.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A186 = TA / "A186_p24_vo_triggered_handover" / "cosim"
COS = HERE / "cosim"
HAND_VO = 1.045


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for cond in ("S75_hot", "S0_hot", "N0_hot", "F0_hot", "S0_25"):
        c = json.loads((A186 / f"cfg_{cond}_p0.json").read_text())
        c = dict(c, hand_vo_v=HAND_VO, out=f"run_{cond}_p0.json", note=c["note"].replace("A186", "A188").replace("1.03 V", f"{HAND_VO} V"))
        if cond == "S0_25":
            c.update(t_end_us=150.0, note=c["note"] + "; identity check against A185 to 150 us")
        (COS / f"cfg_{cond}_p0.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(f"{cond}_p0")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
