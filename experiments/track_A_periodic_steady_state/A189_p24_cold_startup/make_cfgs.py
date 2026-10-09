"""A189 cosim cfgs: the adopted start-up (A188: 200 ns mode S at its own 25 C trim, bumpless seed, handover at Vo >=
1.045 V or 144 us) below 25 C, trims and seeds locked at 25 C. Boards S75, S0, N0, F0, N13 at 0 and -40 C, start-up to
200 us (no step). Comparison: the 400 ns start-up (A164 / A173 trims) on N0 and S0 at -40 C. The gate model's
temperature factors are linear from 25 C; below 25 C they are an extrapolation.
  python3 make_cfgs.py   cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
T_END = 200.0
NEW = {"S75": TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_S75_25_p0.json",
       "S0": TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_S0_25_p0.json",
       "N0": TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_N0_25_p0.json",
       "F0": TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_F0_25_p0.json",
       "N13": TA / "A186_p24_vo_triggered_handover" / "cosim" / "cfg_N13_25_p0.json"}
OLD = {"N0": TA / "A181_p24_locked_trim_joint_corner" / "cosim" / "cfg_N0_hot_p0.json",
       "S0": TA / "A181_p24_locked_trim_joint_corner" / "cosim" / "cfg_S0_hot_p0.json"}


def at(c, temp, note, out):
    g = dict(c["gate"], temp=temp)
    return dict(c, gate=g, t_end_us=T_END, out=out, note=note)


def main():
    COS.mkdir(exist_ok=True)
    order = []
    for temp in (0.0, -40.0):
        for b, f in NEW.items():
            c = json.loads(f.read_text())
            c = dict(c, hand_vo_v=1.045)
            run = f"{b}_{'m40' if temp < 0 else 'c0'}"
            order.append(run)
            (COS / f"cfg_{run}.json").write_text(json.dumps(at(c, temp, f"A189 {run}: A188 start-up (mode-S trim {c['ton_s_ns']} ns, seed "
                                                                    f"{c['ton_ns']} ns, request 1.045 V; set at 25 C, locked) at {temp:g} C, to {T_END} us",
                                                                    f"run_{run}.json"), indent=1) + "\n")
    for b, f in OLD.items():
        c = json.loads(f.read_text())
        run = f"old{b}_m40"
        order.append(run)
        (COS / f"cfg_{run}.json").write_text(json.dumps(at(c, -40.0, f"A189 {run}: the 400 ns start-up (trim {c['ton_ns']} ns, set at 25 C, "
                                                               f"locked) at -40 C, to {T_END} us", f"run_{run}.json"), indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
