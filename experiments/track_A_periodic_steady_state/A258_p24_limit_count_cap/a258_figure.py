"""A258 figure (records: cosim/run_{s,c}_*.json; release records-a258):
(a) pr_N75: +62.5 A (125 %) from 200 to 290 us, then A240's 1 MHz train from 300 us; the largest gate-record turn-off
    current per 1 us with A256's count (arm s) and with the ceiling n_cap 6 (arm c), and each arm's re-arm;
(b) the same for pr_S75h;
(c) ro_S75h: the 100 kHz train with 125 % highs, the largest turn-off current per 1 us in both arms;
(d) the same row: the ladder's deviation max |rail - Vin / 4| in both arms.
  python3 a258_figure.py -> a258_count_cap.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ARM = {"s": ("#eb6834", "A256's count (arm s)", 1.0), "c": ("#2a78d6", "count ceiling n_cap 6 (arm c)", 1.2)}
INK = "#3d3d3a"


def rec(arm, row):
    return json.loads((HERE / "cosim" / f"run_{arm}_{row}.json").read_text())


def per_us(d, t0, t1):
    g = [(e["t_s"] * 1e6, e["i_max_a"]) for e in d["gate_offs_last"] if t0 <= e["t_s"] * 1e6 < t1]
    pk = np.full(int(t1 - t0), np.nan)
    for t, i in g:
        k = int(t - t0)
        pk[k] = i if np.isnan(pk[k]) else max(pk[k], i)
    return t0 + np.arange(len(pk)) + 0.5, pk


def rearm(d, after):
    return [1e6 * x["t_s"] for x in d.get("ocp_susp", []) if x["on"] == 0 and x["t_s"] >= after * 1e-6]


def dev(d):
    S = d["sections"]
    t = np.array([s["t_s"] for s in S]) * 1e6
    r = np.array([[s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1], s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2]]
                  for s in S])
    return t, np.abs(r - np.array([s["vin_v"] for s in S])[:, None] / 4).max(1)


def train(ax, row, title):
    for arm in ("s", "c"):
        d = rec(arm, row)
        c, lab, lw = ARM[arm]
        t, pk = per_us(d, 180, 420)
        ax.plot(t, pk, color=c, lw=lw, label=lab)
        for x in rearm(d, 290)[:1]:
            ax.axvline(x, color=c, ls="--", lw=0.8)
            ax.text(x + 1, 112 if arm == "c" else 104, f"re-arm {x:.1f} us", color=c, fontsize=8)
    ax.axvspan(200, 290, color="#8c8c8c", alpha=0.15, lw=0)
    ax.text(202, 272, "+62.5 A (125 %)", fontsize=8, color=INK)
    ax.axvline(300, color=INK, ls=":", lw=0.8)
    ax.text(302, 272, "1 MHz train", fontsize=8, color=INK)
    ax.axhline(200, color=INK, ls="--", lw=0.8)
    ax.set(title=title, xlabel="t (us)", ylabel="largest turn-off current per 1 us (A)", xlim=(180, 420), ylim=(100, 285))
    ax.legend(fontsize=8, loc="lower left", frameon=False)


def main():
    fig, ax = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    train(ax[0, 0], "pr_N75", "(a) N75: overload, then the 1 MHz train (limit 110 A)")
    train(ax[0, 1], "pr_S75h", "(b) S75h: overload, then the 1 MHz train (limit 110 A)")
    for arm in ("s", "c"):
        d = rec(arm, "ro_S75h")
        c, lab, lw = ARM[arm]
        t, pk = per_us(d, 290, 420)
        ax[1, 0].plot(t, pk, color=c, lw=lw, label=lab)
        td, dv = dev(d)
        w = (td >= 290) & (td <= 620)
        ax[1, 1].plot(td[w], dv[w], color=c, lw=lw, label=lab)
    ax[1, 0].axhline(200, color=INK, ls="--", lw=0.8)
    ax[1, 0].set(title="(c) S75h: 100 kHz train with 125 % highs", xlabel="t (us)",
                 ylabel="largest turn-off current per 1 us (A)", ylim=(50, 225))
    ax[1, 0].legend(fontsize=8, loc="lower right", frameon=False)
    for a in ax[1]:
        a.text(0.02, 0.97, "the arms are identical here (0.0 A, 0.0 V); arm c re-arms up to 1.04 us earlier,\n"
               "inside the low levels, where the limit has nothing to cut", transform=a.transAxes, fontsize=8, color=INK,
               va="top")
    ax[1, 1].set(title="(d) S75h, 125 % highs: ladder deviation max |rail - Vin / 4|", xlabel="t (us)",
                 ylabel="deviation (V)", ylim=(0, 1.6))
    ax[1, 1].legend(fontsize=8, loc="upper right", bbox_to_anchor=(1.0, 0.86), frameon=False)
    fig.suptitle("A258: the limit's count with and without a ceiling, plant V7, one module (records cosim/run_{s,c}_*.json)",
                 fontsize=10, color=INK)
    fig.savefig(HERE / "a258_count_cap.png", dpi=130)


if __name__ == "__main__":
    main()
