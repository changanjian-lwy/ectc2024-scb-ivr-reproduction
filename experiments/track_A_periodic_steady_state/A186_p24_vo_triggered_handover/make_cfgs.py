"""A186 cosim cfgs: A185 (200 ns mode S at its own Ton, bumpless loop seed) with the handover requested once a
phase-1 Vo sample reaches HAND_VO (bridge cfg "hand_vo_v"), or at 144 us, whichever is first. The F0 125 C run (not
in A185) is A184's with A185's F0 seed.
  python3 make_cfgs.py   cosim/cfg_<cond>_p0.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A185 = TA / "A185_p24_bumpless_loop_seed"
COS = HERE / "cosim"
HAND_VO = 1.03


def main():
    seeds = json.loads((A185 / "seeds.json").read_text())
    COS.mkdir(exist_ok=True)
    order = []
    conds = [f.stem[4:-3] for f in sorted((A185 / "cosim").glob("cfg_*_p0.json"))] + ["F0_hot"]
    for cond in conds:
        src = A185 / "cosim" / f"cfg_{cond}_p0.json"
        if src.exists():
            c = json.loads(src.read_text())
        else:
            c = json.loads((TA / "A184_p24_startup_own_ton" / "cosim" / f"cfg_{cond}_p0.json").read_text())
            c = dict(c, ton_ns=seeds[cond.split("_")[0]]["seed_ns"])
        note = (f"A186 {cond}_p0: as A185 (mode-S period 200 ns at {c.get('ton_s_ns')} ns, bumpless loop seed {c['ton_ns']} ns, "
                f"set at 25 C and locked) with the handover requested at Vo >= {HAND_VO} V or 144 us")
        c = dict(c, hand_vo_v=HAND_VO, out=f"run_{cond}_p0.json", note=note)
        (COS / f"cfg_{cond}_p0.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(f"{cond}_p0")
    order.insert(0, order.pop(order.index("M4_25_p0")))
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
