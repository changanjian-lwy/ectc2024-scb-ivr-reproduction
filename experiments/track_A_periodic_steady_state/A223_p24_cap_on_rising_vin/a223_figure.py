"""A223 figure from the records: N0, +200 A at 380 us from 20 % (run_w20_N0_off.json, run_w20_N0_g25.json) - Vo, the
loop's Ton register, phase 1's high-side on-time against phase 2's, and each phase's low-side turn-off current.
    python3 a223_figure.py -> a223_w20.png"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
T0, T1 = 377e-6, 405e-6


def load(arm):
    r = json.loads((HERE / "cosim" / f"run_w20_N0_{arm}.json").read_text())
    sec = [q for q in r["sections"] if T0 <= q["t_s"] <= T1]
    on = {k: [] for k in range(1, 5)}
    offs = {k: np.array(sorted(h["t_s"] for h in r["highoffs_last"] if h["phase"] == k)) for k in range(1, 5)}
    for x in r["turnons_last"]:
        if T0 <= x["t_s"] <= T1:
            j = np.searchsorted(offs[x["phase"]], x["t_s"], side="right")
            if j < len(offs[x["phase"]]):
                on[x["phase"]].append((x["t_s"], (offs[x["phase"]][j] - x["t_s"]) * 1e9))
    lo = {k: [(q["t_s"], q["i_a"]) for q in r["lowoffs_last"] if q["phase"] == k and T0 <= q["t_s"] <= T1] for k in range(1, 5)}
    return sec, on, lo


fig, ax = plt.subplots(4, 2, figsize=(12, 10), sharex=True)
for j, arm in enumerate(("off", "g25")):
    sec, on, lo = load(arm)
    t = np.array([q["t_s"] for q in sec]) * 1e6
    ax[0, j].plot(t, [q["vo"] for q in sec], lw=0.8)
    ax[0, j].set_title(f"run_w20_N0_{arm}.json: " + ("as adopted" if arm == "off" else "cap only while Vin rises (rel_gate 25)"), fontsize=9)
    ax[0, j].set_ylabel("Vo (V)")
    ax[1, j].plot(t, [q["ton_lsb"] / 32 for q in sec], lw=0.8)
    ax[1, j].set_ylabel("loop Ton (ns)")
    for k, c in ((1, "C3"), (2, "C0")):
        a = np.array(on[k])
        ax[2, j].plot(a[:, 0] * 1e6, a[:, 1], ".", ms=2, color=c, label=f"phase {k}")
    ax[2, j].set_ylabel("high-side on-time (ns)")
    ax[2, j].legend(fontsize=7)
    for k in range(1, 5):
        a = np.array(lo[k])
        ax[3, j].plot(a[:, 0] * 1e6, a[:, 1], ".", ms=2, label=f"phase {k}")
    ax[3, j].axhline(-15.625, color="k", lw=0.5)
    ax[3, j].set_ylabel("low-side turn-off current (A)")
    ax[3, j].set_xlabel("t (us)")
    ax[3, j].legend(fontsize=7, ncol=4)
fig.suptitle("A223: N0, plant V7, final configuration, 20 % -> +200 A at 380 us", fontsize=10)
fig.tight_layout()
fig.savefig(HERE / "a223_w20.png", dpi=130)
print("a223_w20.png")
