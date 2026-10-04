"""A137 configurations: A136's arm q (relative cap on ton's low-pass, rel_q8 320, rel_lp 1; steps at 1000 us) with the
feed-forward's low-passes restarted at mode P's entry (cfg vff seed 1, scb_vff A137), on m3n, m1n, n0, l_p48_1us,
l_p48_5us, s_p62 at L x 0.7 / 1.0 / 1.3. `ident`: A136's q100_m3n (seed absent) -> tmp/identity_a137/.
Writes cosim/cfg_s<mmm>_<row>.json, ORDER.txt."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("a136_cfgs", HERE.parent / "A136_p24_relative_cap_lowpass" / "make_cfgs.py")
A136 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A136)
ROWS = ("m3n", "m1n", "n0", "l_p48_1us", "l_p48_5us", "s_p62")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "ident":
        out = PROJECT / "tmp" / "identity_a137"
        out.mkdir(parents=True, exist_ok=True)
        src = HERE.parent / "A136_p24_relative_cap_lowpass" / "cosim" / "cfg_q100_m3n.json"
        (out / src.name).write_text(src.read_text())
        print("1 identity cfg")
        return
    order = []
    (HERE / "cosim").mkdir(exist_ok=True)
    for m in (0.7, 1.0, 1.3):
        for row in ROWS:
            _, c = A136.cfg(m, row)
            c["vff"] = dict(c["vff"], seed=1)
            name = f"s{round(m * 100):03d}_{row}"
            c["note"] = c["note"].replace("A136 q", "A137 s") + ", low-passes restarted at mode P (seed 1)"
            c["out"] = f"run_{name}.json"
            (HERE / "cosim" / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
            order.append(name)
    (HERE / "cosim" / "ORDER.txt").write_text("\n".join(order) + "\n")
    print(len(order), "cfgs")


if __name__ == "__main__":
    main()
