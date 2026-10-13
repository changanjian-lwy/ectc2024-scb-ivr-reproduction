"""A211 figure from a211_summary.json (itself from the cosim records): the plant's semiconductor loss books and
Pout / (Pout + loss) against the module current for three boards; hollow markers are rows that miss a criterion
or do not complete their high-side turn-ons.
  python3 a211_figure.py -> a211_curves.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
NAME = {"N0_25": "nominal, L0 (N0)", "N75_25": "nominal, 0.75 L0 (N75)", "S75_25": "slow, 0.75 L0 (S75)"}
COL = {"N0_25": "tab:blue", "N75_25": "tab:green", "S75_25": "tab:red"}


def main():
    s = json.loads((HERE / "a211_summary.json").read_text())
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.2))
    for k, pts in s["curves"].items():
        x = [p["i_a"] for p in pts]
        ok = [p["works"] and not p["hs_incomplete_share"] for p in pts]
        for a, key, sc in ((ax[0], "loss_w", 1.0), (ax[1], "eff_books", 100.0), (ax[2], "edges_high_w", 1.0)):
            y = [sc * p[key] for p in pts]
            a.plot(x, y, color=COL[k], lw=1.2, label=NAME[k])
            a.scatter([xi for xi, o in zip(x, ok) if o], [yi for yi, o in zip(y, ok) if o], color=COL[k], s=22, zorder=3)
            a.scatter([xi for xi, o in zip(x, ok) if not o], [yi for yi, o in zip(y, ok) if not o], facecolors="none", edgecolors=COL[k], s=34, zorder=3)
    ax[0].set_ylabel("semiconductor loss in the plant's books (W)"); ax[1].set_ylabel("Pout / (Pout + loss) (%)")
    ax[2].set_ylabel("of it: high-side edges (W)")
    for a in ax:
        a.set_xlabel("module current (A); 250 A = full load"); a.grid(alpha=0.3); a.set_xlim(40, 260)
    ax[0].legend(fontsize=8)
    fig.suptitle("A211: final configuration, plant V6, 25 C, one module, ton_min_ns 4.0 ns - records of A206-A208, A210, A211 "
                 "(hollow: a criterion missed, or high sides not fully on)", fontsize=9)
    fig.tight_layout()
    fig.savefig(HERE / "a211_curves.png", dpi=130)


if __name__ == "__main__":
    main()
