"""A208 cosim cfgs: A207's rows (final configuration, plant V6, board N0, 25 C; part of the 250 A load released at
300 us, end 450 us) with the loop's lower Ton limit as its own value: cfg "ton_min_ns" (bridge.py, A208) instead of
half of cfg ton_ns (22.24 ns). Row m<p>: p % of 250 A left, ton_min_ns = TON_MIN_NS (low enough to be out of the
loop's way down to about 10 % of the load).
  python3 make_cfgs.py -> cosim/cfg_m*.json, cosim/ORDER.txt"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a207_cfgs", HERE.parent / "A207_p24_load_range" / "make_cfgs.py")
A7 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A7)
COS = HERE / "cosim"
TON_MIN_NS = 2.0
SHARES = (60, 50, 40, 30, 20, 10)


def row(p, ton_min_ns=TON_MIN_NS, tag="m"):
    c = A7.row(p)
    return dict(c, ton_min_ns=ton_min_ns, out=f"run_{tag}{p}.json",
                note=c["note"].replace("A207 f", f"A208 {tag}") + f"; lower Ton limit {ton_min_ns:g} ns (cfg ton_min_ns)")


if __name__ == "__main__":
    COS.mkdir(exist_ok=True)
    for p in SHARES:
        (COS / f"cfg_m{p}.json").write_text(json.dumps(row(p), indent=1) + "\n")
    (COS / "ORDER.txt").write_text("\n".join(f"m{p}" for p in SHARES) + "\n")
    print(len(SHARES), "cfgs; run-equivalents of 900 us:", round(len(SHARES) * A7.T_END / 900.0, 2))
