"""A208 figure, drawn from the cosim records: Vo and the controller's Ton register against the time after the load
release. Solid: lower limit 2.0 ns (cosim/run_m*.json); dashed: the proposed 4.0 ns (run_v*.json); grey: A207's
60 % row with the old limit (22.25 ns) for comparison.
  python3 a208_figure.py -> a208_vo.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROWS = [("m", p) for p in (60, 50, 40, 30, 20, 10)] + [("v", 20), ("v", 10)]
OLD = HERE.parent / "A207_p24_load_range" / "cosim" / "run_f60.json"


def series(path):
    r = json.loads(Path(path).read_text())
    t0 = r["cfg"]["load_step"]["t_us"]
    ts = np.array([q["t_s"] for q in r["sections"]]) * 1e6 - t0
    m = ts >= -10.0
    return ts[m], np.array([q["vo"] for q in r["sections"]])[m], np.array([q["ton_lsb"] for q in r["sections"]])[m] * r["lsb_s"] * 1e9


def main():
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.4, 7.2), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    cm = plt.get_cmap("viridis")
    if OLD.exists():
        t, vo, tl = series(OLD)
        a.plot(t, vo, color="0.6", lw=1.0, label="60 %, old limit 22.25 ns (A207)"); b.plot(t, tl, color="0.6", lw=1.0)
    for tag, p in ROWS:
        f = HERE / "cosim" / f"run_{tag}{p}.json"
        if not f.exists():
            continue
        t, vo, tl = series(f)
        col = cm((60 - p) / 50 * 0.92)
        ls = "-" if tag == "m" else "--"
        a.plot(t, vo, color=col, lw=1.3, ls=ls, label=f"{p} % ({2.5 * p:g} A), limit {'2.0' if tag == 'm' else '4.0'} ns")
        b.plot(t, tl, color=col, lw=1.3, ls=ls)
    a.axhspan(0.99, 1.01, color="0.88", zorder=0)
    a.set_ylim(0.955, 1.12); a.set_ylabel("Vo (V)"); a.legend(ncol=2, fontsize=7.5, loc="upper right")
    a.set_title("A208: final configuration, plant V6, board N0, 25 C - part of the 250 A load released at t = 0,\n"
                "lower Ton limit as its own value (cfg ton_min_ns); records: A208_p24_ton_lower_limit/cosim/run_m*.json, run_v*.json", fontsize=9)
    for y in (2.0, 4.0):
        b.axhline(y, color="k", ls=":", lw=0.8)
    b.set_ylabel("Ton register (ns)"); b.set_xlabel("time after the release (us)"); b.set_xlim(-10, 150); b.set_ylim(0, 34)
    for ax in (a, b):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "a208_vo.png", dpi=130)


if __name__ == "__main__":
    main()
