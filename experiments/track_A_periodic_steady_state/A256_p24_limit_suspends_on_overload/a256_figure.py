"""A256 figure (records: cosim/run_s_*.json against A255 run_l_ / run_h_ and A246 run_h_; release records-a256):
(a) o125_S75h, +62.5 A load step at 500 us (125 % load), limit 110 A: the four ladder rails with the limit + n_susp 6
    (colour) and with the limit alone (A255 arm l, grey);
(b) the same row: Vo for the final configuration, the limit alone and the limit + n_susp 6;
(c) the same row: phase 2's turn-off current per period (highoffs_last) with n_susp 6 against the final configuration,
    the limit's fires and the suspension; the two NEW spikes are A142's oracle hits;
(d) a_S75h_d20, +4.8 V / 1 us line step at 153.4 us: rail 1 with n_susp 6 against the final configuration, the
    limit's phase-1 fires, the suspension and s3's ladder threshold (reference maximum + 0.2 V).
  python3 a256_figure.py -> a256_limit_suspends.png"""
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
SUS, LIM, GREY, INK = "#2a78d6", "#eb6834", "#8c8c8c", "#3d3d3a"


def rec(path):
    return json.loads(Path(path).read_text())


def ladder(d):
    S = d["sections"]
    t = np.array([s["t_s"] for s in S]) * 1e6
    r = np.array([[s["vin_v"] - s["vcs_v"][0], s["vcs_v"][0] - s["vcs_v"][1], s["vcs_v"][1] - s["vcs_v"][2], s["vcs_v"][2]]
                  for s in S])
    return t, r, np.array([s["vo"] for s in S]) * 1e3


def offs(d, k, t0, t1):
    y = [(x["t_s"] * 1e6, x["i_a"]) for x in d["highoffs_last"] if x["phase"] == k and t0 <= x["t_s"] * 1e6 <= t1]
    return np.array(y).T


def main():
    s = rec(HERE / "cosim" / "run_s_o125_S75h.json")
    l = rec(TA / "A255_p24_overload_on_2p2nh" / "cosim" / "run_l_o125_S75h.json")
    h = rec(TA / "A255_p24_overload_on_2p2nh" / "cosim" / "run_h_o125_S75h.json")
    t_sus = 1e6 * s["ocp_susp"][0]["t_s"]
    fig, ax = plt.subplots(2, 2, figsize=(11, 7.5), constrained_layout=True)
    (ts, rs, vs), (tl, rl, vl), (th, rh, vh) = ladder(s), ladder(l), ladder(h)
    m = lambda t: (t >= 480) & (t <= 620)                         # noqa: E731
    for k in range(4):
        ax[0, 0].plot(tl[m(tl)], rl[m(tl), k], color=GREY, lw=0.8, label="limit alone (A255)" if k == 0 else None)
        ax[0, 0].plot(ts[m(ts)], rs[m(ts), k], color=RAIL[k], lw=1.2, label=f"rail {k + 1}, limit + n_susp 6")
    ax[0, 0].axvline(500, color=INK, ls=":", lw=0.8)
    ax[0, 0].text(501, 1.5, "+62.5 A step", fontsize=8, color=INK)
    ax[0, 0].set(title="(a) S75h, 125 % load step: ladder rails (limit 110 A)", xlabel="t (us)", ylabel="rail (V)",
                 ylim=(0, 30))
    ax[0, 0].legend(fontsize=8, loc="upper left", frameon=False, ncol=2)
    for t, v, c, lab, lw in ((th, vh, GREY, "final configuration", 1.0), (tl, vl, LIM, "limit alone (A255)", 1.0),
                             (ts, vs, SUS, "limit + n_susp 6", 1.2)):
        ax[0, 1].plot(t[m(t)], v[m(t)], color=c, lw=lw, label=lab)
    ax[0, 1].axvline(500, color=INK, ls=":", lw=0.8)
    ax[0, 1].text(560, 985, "limit + n_susp 6 lies on the final configuration", fontsize=8, color=INK, ha="center")
    ax[0, 1].set(title="(b) S75h, 125 % load step: Vo", xlabel="t (us)", ylabel="Vo (mV)")
    ax[0, 1].legend(fontsize=8, loc="lower left", frameon=False)
    a, b = offs(h, 2, 500, 512), offs(s, 2, 500, 512)
    ax[1, 0].plot(a[0], a[1], color=GREY, lw=1.0, marker="o", ms=3, label="final configuration")
    ax[1, 0].plot(b[0], b[1], color=SUS, lw=1.2, marker="o", ms=3, label="limit + n_susp 6")
    fires = [1e6 * x["t_s"] for x in s["ocp_fires"] if x["phase"] == 2 and x["t_s"] > 500e-6]
    ax[1, 0].plot(fires, [152] * len(fires), ls="none", marker="|", ms=10, color=LIM, label="phase-2 limit fires")
    for t_n in (505.9237, 506.7629):                             # A142 oracle NEW (spike) hits, a256 RESULTS Section 0
        i = b[1][np.argmin(abs(b[0] - t_n))]
        ax[1, 0].annotate("NEW spike", (t_n, i), (t_n + 0.6, i + 4), fontsize=8, color=INK,
                          arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6})
    ax[1, 0].axvline(t_sus, color=INK, ls="--", lw=0.8)
    ax[1, 0].text(t_sus + 0.1, 150, f"suspended {t_sus:.2f} us", fontsize=8, color=INK)
    ax[1, 0].set(title="(c) S75h, 125 % load step: phase 2 turn-off current", xlabel="t (us)",
                 ylabel="turn-off current (A)", ylim=(145, 185))
    ax[1, 0].legend(fontsize=8, loc="lower right", frameon=False)
    s2 = rec(HERE / "cosim" / "run_s_a_S75h_d20.json")
    h2 = rec(TA / "A246_p24_held_report_floor" / "cosim" / "run_h_a_S75h_d20.json")
    (t2, r2, _), (t3, r3, _) = ladder(s2), ladder(h2)
    w = lambda t: (t >= 150) & (t <= 165)                         # noqa: E731
    ax[1, 1].plot(t3[w(t3)], r3[w(t3), 0], color=GREY, lw=1.0, marker="o", ms=2.5, label="final configuration")
    ax[1, 1].plot(t2[w(t2)], r2[w(t2), 0], color=SUS, lw=1.2, marker="o", ms=2.5, label="limit + n_susp 6")
    after = w(t2) & (t2 >= 153.404)
    vin = np.array([x["vin_v"] for x in s2["sections"]])[after]
    dev_h = max(abs(r3[w(t3) & (t3 >= 153.404)] - (np.array([x["vin_v"] for x in h2["sections"]])[w(t3) & (t3 >= 153.404)] / 4)[:, None]).max(1))
    ax[1, 1].plot(t2[after], vin / 4 + dev_h + 0.2, color=INK, ls="--", lw=0.8, label="s3 threshold (Vin / 4 + ref max + 0.2 V)")
    f1 = [1e6 * x["t_s"] for x in s2["ocp_fires"] if x["phase"] == 1 and 150e-6 <= x["t_s"] <= 165e-6]
    ax[1, 1].plot(f1, [11.2] * len(f1), ls="none", marker="|", ms=10, color=LIM, label="phase-1 limit fires")
    t_s2 = 1e6 * s2["ocp_susp"][0]["t_s"]
    ax[1, 1].axvline(153.404, color=INK, ls=":", lw=0.8)
    ax[1, 1].axvline(t_s2, color=INK, ls="--", lw=0.8)
    ax[1, 1].text(t_s2 + 0.2, 17.2, f"suspended {t_s2:.1f} us", fontsize=8, color=INK)
    ax[1, 1].set(title="(d) S75h, +4.8 V / 1 us line step (item 2): rail 1", xlabel="t (us)", ylabel="rail 1 (V)",
                 ylim=(11, 17.5))
    ax[1, 1].legend(fontsize=8, loc="lower right", frameon=False)
    fig.suptitle("A256: peak limit 110 A with n_susp 6, plant V7, one module (records cosim/run_s_*.json, "
                 "A255 run_l_ / run_h_, A246 run_h_)", fontsize=10, color=INK)
    fig.savefig(HERE / "a256_limit_suspends.png", dpi=130)


if __name__ == "__main__":
    main()
