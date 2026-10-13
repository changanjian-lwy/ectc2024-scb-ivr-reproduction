"""A207 figure, drawn from the cosim records (cosim/run_f*.json): Vo and the controller's Ton register against the
time after the load release, one line per remaining share of the 250 A load.
  python3 a207_figure.py -> a207_vo.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SHARES = (75, 60, 55, 50, 45, 40, 30, 10)


def main():
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.4, 7.2), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    cm = plt.get_cmap("viridis")
    lim = None
    for k, p in enumerate(SHARES):
        r = json.loads((HERE / "cosim" / f"run_f{p}.json").read_text())
        t0 = r["cfg"]["load_step"]["t_us"]
        ts = np.array([q["t_s"] for q in r["sections"]]) * 1e6 - t0
        m = ts >= -10.0
        col = cm(k / (len(SHARES) - 1) * 0.92)
        a.plot(ts[m], [q["vo"] for q, ok in zip(r["sections"], m) if ok], color=col, lw=1.3, label=f"{p} % ({2.5 * p:g} A)")
        b.plot(ts[m], np.array([q["ton_lsb"] for q, ok in zip(r["sections"], m) if ok]) * r["lsb_s"] * 1e9, color=col, lw=1.3)
        lim = round(0.5 * r["cfg"]["ton_ns"] * 1e-9 / r["lsb_s"]) * r["lsb_s"] * 1e9
    a.axhspan(0.99, 1.01, color="0.85", zorder=0, label="1 V +- 10 mV")
    a.set_ylabel("Vo (V)"); a.legend(title="load left after the release", ncol=3, fontsize=8, title_fontsize=8, loc="upper left")
    a.set_title("A207: final configuration, plant V6, board N0, 25 C - part of the 250 A load released at t = 0\n"
                "records: A207_p24_load_range/cosim/run_f*.json", fontsize=9)
    b.axhline(lim, color="k", ls="--", lw=0.9); b.text(148, lim + 0.25, f"limit {lim:.2f} ns = 0.5 x cfg ton_ns", ha="right", fontsize=8)
    b.set_ylabel("Ton register (ns)"); b.set_xlabel("time after the release (us)"); b.set_xlim(-10, 150)
    for ax in (a, b):
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "a207_vo.png", dpi=130)


if __name__ == "__main__":
    main()
