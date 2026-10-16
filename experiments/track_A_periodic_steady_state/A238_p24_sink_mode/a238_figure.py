"""A238 against A237 from the records: the release to 0 A on N0 (sink works) and N75 (sink latches), Vo and each
phase's current at its low-side turn-offs (N0: s_cw5_N0, where phase 4 ratchets; N75: s_c0_N75).
    python3 a238_figure.py -> a238_sink.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
A37C, COS = HERE.parent / "A237_p24_true_light_load" / "cosim", HERE / "cosim"
T0 = 296e-6


def rec(path):
    return json.loads(path.read_text())


def vo(r, t1):
    s = [q for q in r["sections"] if T0 <= q["t_s"] <= t1]
    return [q["t_s"] * 1e6 for q in s], [q["vo"] for q in s]


fig, ax = plt.subplots(2, 2, figsize=(11.0, 7.0))
for col, (board, t1, vrow) in enumerate((("N0", 340e-6, "s_cw5_N0"), ("N75", 450e-6, "s_c0_N75"))):
    a, b = rec(A37C / f"run_c0_{board}.json"), rec(COS / f"run_s_c0_{board}.json")
    ax[0, col].plot(*vo(a, t1), color="0.5", lw=0.8, label=f"A237 c0_{board} (no sink)")
    ax[0, col].plot(*vo(b, t1), color="C3", lw=0.8, label=f"A238 s_c0_{board} (+ sink)")
    for t, s in b["sink_log"]:
        ax[0, col].axvline(t * 1e6, color="C3", lw=0.5, ls="--" if s else ":")
    ax[0, col].axhline(1.05, color="k", lw=0.5, ls="--"); ax[0, col].axhline(1.01, color="k", lw=0.5, ls=":")
    ax[0, col].set_ylabel("Vo (V)"); ax[0, col].legend(fontsize=7)
    ax[0, col].set_title(f"{board}, plant V7: 250 A -> 0 A (constant current) at 300 us; dashed: sink set", fontsize=9)
    v = rec(COS / f"run_{vrow}.json")
    tv = 312e-6 if board == "N0" else 330e-6
    for k in range(1, 5):
        pts = [(x["t_s"] * 1e6, x["i_a"]) for x in v["lowoffs_last"] if x["phase"] == k and T0 <= x["t_s"] <= tv]
        ax[1, col].plot(*zip(*pts), ".", ms=3, label=f"phase {k}")
    for t, s in v["sink_log"]:
        if t <= tv:
            ax[1, col].axvline(t * 1e6, color="C3", lw=0.5, ls="--" if s else ":")
    ax[1, col].axhline(-40.0, color="k", lw=0.5); ax[1, col].legend(fontsize=7, ncol=4)
    ax[1, col].set_ylabel("current at each low-side\nturn-off (A)"); ax[1, col].set_xlabel("t (us)")
    ax[1, col].set_title(f"A238 cosim/run_{vrow}.json (sink target -40 A)", fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "a238_sink.png", dpi=130)
print("a238_sink.png")
