"""A257 figure (records: cosim/run_{h,s}_*.json, A235's run_r_N13_lp48.json; release records-a257):
(a) o125_N13, +62.5 A at 500 us (125 % load), N13 (3.813 nH), limit 140 A: the largest turn-off current (highoffs_last)
    per 0.5 us, with the limit + n_susp 6 against the final configuration, the limit's fires and the suspension;
(b) the same row: the four ladder rails, with the limit (colour) and without (grey);
(c) lp48_N13, +4.8 V / 1 us at 500 us: the ladder's deviation max |rail - Vin / 4| for the final configuration, for
    A235's record of the same row (V7, before A244-A246) and n1's registered 1 V.
  python3 a257_figure.py -> a257_limit_on_n13.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
TA = HERE.parent
RAIL = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
SUS, OLD, LIM, GREY, INK = "#2a78d6", "#eb6834", "#eb6834", "#8c8c8c", "#3d3d3a"


def rec(path):
    return json.loads(Path(path).read_text())


def ladder(d):
    S = d["sections"]
    t = np.array([s["t_s"] for s in S]) * 1e6
    r = np.array([[s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1], s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2]]
                  for s in S])
    return t, r, np.abs(r - np.array([s["vin_v"] for s in S])[:, None] / 4).max(1)


def per_bin(d, t0, t1, w=0.5):
    y = [(x["t_s"] * 1e6, x["i_a"]) for x in d["highoffs_last"] if t0 <= x["t_s"] * 1e6 < t1]
    n = int((t1 - t0) / w)
    pk = np.full(n, np.nan)
    for t, i in y:
        k = int((t - t0) / w)
        pk[k] = i if np.isnan(pk[k]) else max(pk[k], i)
    return t0 + w * (np.arange(n) + 0.5), pk


def main():
    h, s = rec(HERE / "cosim" / "run_h_o125_N13.json"), rec(HERE / "cosim" / "run_s_o125_N13.json")
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), constrained_layout=True)
    for d, c, lab, lw in ((h, GREY, "final configuration", 1.0), (s, SUS, "limit 140 A + n_susp 6", 1.2)):
        t, pk = per_bin(d, 495, 575)
        ax[0].plot(t, pk, color=c, lw=lw, label=lab)
    fires = [1e6 * x["t_s"] for x in s["ocp_fires"]]
    ax[0].plot(fires, [150] * len(fires), ls="none", marker="|", ms=10, color=LIM, label="limit fires")
    t_sus = 1e6 * s["ocp_susp"][0]["t_s"]
    ax[0].axvline(500, color=INK, ls=":", lw=0.8)
    ax[0].axvline(t_sus, color=INK, ls="--", lw=0.8)
    ax[0].text(t_sus + 0.8, 147, f"suspended {t_sus:.2f} us", fontsize=8, color=INK)
    ax[0].text(501, 186, "+62.5 A step", fontsize=8, color=INK)
    ax[0].set(title="(a) N13, 125 % load: largest turn-off current per 0.5 us", xlabel="t (us)", ylabel="current (A)",
              ylim=(140, 190))
    ax[0].legend(fontsize=8, loc="lower right", frameon=False)
    (th, rh, _), (ts, rs, _) = ladder(h), ladder(s)
    m = lambda t: (t >= 480) & (t <= 620)                         # noqa: E731
    for k in range(4):
        ax[1].plot(th[m(th)], rh[m(th), k], color=GREY, lw=2.2, label="final configuration" if k == 0 else None)
        ax[1].plot(ts[m(ts)], rs[m(ts), k], color=RAIL[k], lw=1.0, label=f"rail {k + 1}, limit + n_susp 6")
    ax[1].axvline(500, color=INK, ls=":", lw=0.8)
    ax[1].set(title="(b) N13, 125 % load: ladder rails", xlabel="t (us)", ylabel="rail (V)", ylim=(11, 13))
    ax[1].legend(fontsize=8, loc="upper right", frameon=False, ncol=2)
    a = rec(HERE / "cosim" / "run_h_lp48_N13.json")
    b = rec(next(TA.glob("A235_*/cosim/run_r_N13_lp48.json")))
    for d, c, lab, ls_ in ((b, OLD, "A235's record (V7, before A244-A246)", "--"), (a, SUS, "final configuration (A257 arm h)", "-")):
        t, _, dev = ladder(d)
        w = (t >= 495) & (t <= 620)
        ax[2].plot(t[w], dev[w], color=c, lw=1.2, ls=ls_, label=lab)
    ax[2].axhline(1.0, color=INK, ls=":", lw=0.8, label="n1's registered 1 V")
    ax[2].axvline(500, color=INK, ls=":", lw=0.8)
    ax[2].set(title="(c) N13, +4.8 V / 1 us: ladder deviation max |rail - Vin / 4|", xlabel="t (us)",
              ylabel="deviation (V)")
    ax[2].legend(fontsize=8, loc="upper right", frameon=False)
    fig.suptitle("A257: the adopted limit on N13 (3.813 nH, 140 A), plant V7, one module, 25 C "
                 "(records cosim/run_{h,s}_*.json, A235 run_r_N13_lp48.json)", fontsize=10, color=INK)
    fig.savefig(HERE / "a257_limit_on_n13.png", dpi=130)


if __name__ == "__main__":
    main()
