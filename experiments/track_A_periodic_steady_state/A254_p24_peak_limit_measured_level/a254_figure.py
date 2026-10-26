"""A254 figure (records: cosim/run_l_*.json against A246 run_h_; release records-a254):
(a) p_N75_1000k, A240's 1 MHz train: the largest gate-record turn-off current in each 1 us period, with the limit
    (110 A) against the final configuration;
(b) the same for p_S75h_1000k;
(c) k_N0, +62.5 A load step at 500 us (125 % load), limit 125 A: the four ladder rails, with the limit (colour) and
    without (grey);
(d) the same run: Vo, with the limit against without, and the limit's first fire.
  python3 a254_figure.py -> a254_peak_limit.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "A246_p24_held_report_floor" / "cosim"
RAIL = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
LIM, GREY, INK = "#2a78d6", "#8c8c8c", "#3d3d3a"


def load(row):
    return json.loads((HERE / "cosim" / f"run_l_{row}.json").read_text()), json.loads((REF / f"run_h_{row}.json").read_text())


def per_period(d, t0=300e-6, per=1e-6):
    g = [(e["t_s"], e["i_max_a"]) for e in d["gate_offs_last"] if e["t_s"] >= t0]
    k = np.array([int((t - t0) // per) for t, _ in g])
    i = np.array([x for _, x in g])
    n = k.max() + 1
    pk = np.full(n, np.nan)
    np.fmax.at(pk, k, i)
    return 1e6 * (t0 + per * (np.arange(n) + 0.5)), pk


def ladder(d):
    S = d["sections"]
    t = np.array([s["t_s"] for s in S]) * 1e6
    r = np.array([[s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1], s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2]]
                  for s in S])
    return t, r, np.array([s["vo"] for s in S]) * 1e3


def train(ax, row, title):
    a, b = load(row)
    for d, c, lab, lw in ((b, GREY, "final configuration", 1.0), (a, LIM, "with the limit", 1.2)):
        t, pk = per_period(d)
        ax.plot(t, pk, color=c, lw=lw, label=lab)
    ax.axhline(200, color=INK, ls="--", lw=0.8)
    ax.text(398, 203, "200 A budget", color=INK, fontsize=8, va="bottom", ha="right",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    ax.set(title=title, xlabel="t (us)", ylabel="largest turn-off current per period (A)", xlim=(300, 400), ylim=(90, 255))
    ax.legend(fontsize=8, loc="lower center", ncol=2, frameon=False)


def main():
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.5), constrained_layout=True)
    train(ax[0, 0], "p_N75_1000k", "(a) N75, 1 MHz train: limit 110 A")
    train(ax[0, 1], "p_S75h_1000k", "(b) S75h, 1 MHz train: limit 110 A")
    a, b = load("k_N0")
    (ta, ra, va), (tb, rb, vb) = ladder(a), ladder(b)
    m, n = (ta >= 480) & (ta <= 620), (tb >= 480) & (tb <= 620)
    for k in range(4):
        ax[1, 0].plot(tb[n], rb[n, k], color=GREY, lw=0.8, label="without the limit" if k == 0 else None)
        ax[1, 0].plot(ta[m], ra[m, k], color=RAIL[k], lw=1.2, label=f"rail {k + 1}, with the limit")
    t_fire = 1e6 * min(x["t_s"] for x in a["ocp_fires"])
    for x in (ax[1, 0], ax[1, 1]):
        x.axvline(500, color=INK, ls=":", lw=0.8)
        x.axvline(t_fire, color=INK, ls="--", lw=0.8)
    ax[1, 0].text(501, 7.0, "+62.5 A step", fontsize=8, color=INK)
    ax[1, 0].text(t_fire + 1, 5.2, f"first fire {t_fire:.1f} us", fontsize=8, color=INK)
    ax[1, 0].set(title="(c) N0, 125 % load step: ladder rails (limit 125 A)", xlabel="t (us)", ylabel="rail (V)")
    ax[1, 0].legend(fontsize=8, loc="upper left", frameon=False)
    ax[1, 1].plot(tb[n], vb[n], color=GREY, lw=1.0, label="without the limit")
    ax[1, 1].plot(ta[m], va[m], color=LIM, lw=1.2, label="with the limit")
    ax[1, 1].set(title="(d) N0, 125 % load step: Vo", xlabel="t (us)", ylabel="Vo (mV)")
    ax[1, 1].legend(fontsize=8, loc="lower left", frameon=False)
    fig.suptitle("A254: cycle-by-cycle peak limit, plant V7, one module (records cosim/run_l_*.json, A246 run_h_*.json)",
                 fontsize=10, color=INK)
    fig.savefig(HERE / "a254_peak_limit.png", dpi=130)


if __name__ == "__main__":
    main()
