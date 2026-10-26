"""A249 figure (records: cosim/run_[so]_*.json, A246 run_h_p_S75h_100k, A245 run_r_u_S75h_30; release records-a249):
(a) p_S75h_100k, A240's train: Vo, fixed delay (arms s / o) against the learner (the final configuration);
(b) the same window: actual delay (t_act - t_lo) of phases 3-4's learned turn-ons;
(c) u_S75h_30, 75 A start-up (30 % load): the ladder's deviation max |rail - Vin / 4| after mode P;
(d) the same run: actual delay of phases 2-4's learned turn-ons (a turn-on that was not deferred: its command;
    the slope at 96-112 us is the driver lead ramping in over 20 us after mode P).
  python3 a249_figure.py -> a249_fixed_delay_oracle.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a249_trace", HERE / "a249_trace.py")
TR = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TR)
STYLE = {"s": ("#2a78d6", "-", "fixed, arm s (learner's settled value)"),
         "o": ("#eb6834", "--", "fixed, arm o (A248's window)"),
         "ref": ("#5c5c5c", "-", "learner (final configuration)")}


def series(ax, runs, x, y, **kw):
    for k, (xs, ys) in runs.items():
        c, ls, lab = STYLE[k]
        ax.plot(xs, ys, color=c, ls=ls, lw=1.2, label=lab, **kw)


def delays(d, phases, t0, t1):
    pts = [t for ph in phases for t in TR.turnons(d, ph) if t0 <= t[0] * 1e6 < t1]
    return np.array([p[0] * 1e6 for p in pts]), np.array([p[1] for p in pts])


def main():
    tr = {k: json.loads(f.read_text()) for k, f in TR.TRAIN.items()}
    st = {k: json.loads(f.read_text()) for k, f in TR.START.items()}
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    ax = ax.ravel()

    vo = {k: ([x["t_s"] * 1e6 for x in d["sections"] if 300e-6 <= x["t_s"] <= 345e-6],
              [x["vo"] * 1e3 for x in d["sections"] if 300e-6 <= x["t_s"] <= 345e-6]) for k, d in tr.items()}
    series(ax[0], vo, None, None)
    for k, (t, v) in vo.items():
        i = int(np.argmin(v))
        if k != "o":
            ax[0].annotate(f"{v[i]:.1f} mV", (t[i], v[i]), xytext=(8, -2), textcoords="offset points", fontsize=8,
                           color="k")
    ax[0].set(xlabel="time (us)", ylabel="Vo (mV)",
              title="(a) S75h, 100 kHz train 75 <-> 250 A: Vo (load back at 310 + 10 n us)")
    ax[0].legend(fontsize=8, loc="upper right")

    for k in ("ref", "s"):
        t, dl = delays(tr[k], (3, 4), 300, 345)
        c, _, lab = STYLE[k]
        ax[1].plot(t, dl, ".", ms=3, color=c, label=lab)
    ax[1].axvspan(305, 310, color="0.92", zorder=0)
    ax[1].text(305.2, 1.0, "first release", fontsize=8, color="0.3")
    ax[1].set(xlabel="time (us)", ylabel="actual delay t_act - t_lo (ns)", ylim=(0, 16),
              title="(b) same window: phases 3-4's actual turn-on delay")
    ax[1].legend(fontsize=8, loc="lower right")

    dev = {}
    for k, d in st.items():
        rows = [(x["t_s"] * 1e6, float(np.max(np.abs(TR.rails(x) - x["vin_v"] / 4)))) for x in d["sections"]
                if x["t_s"] >= d["t_mode_p_s"]]
        dev[k] = ([r[0] for r in rows], [r[1] for r in rows])
    series(ax[2], dev, None, None)
    ax[2].axhline(1.0, color="0.6", lw=0.8, ls=":")
    ax[2].text(290, 1.1, "c2: 1 V at the end", fontsize=8, color="0.3", ha="right")
    ax[2].set(xlabel="time (us)", ylabel="max |rail - Vin / 4| (V)",
              title="(c) S75h, 75 A start-up (30 % load; Vin 48 V from 140 us): ladder deviation after mode P")
    ax[2].legend(fontsize=8, loc="upper right")

    for k in ("ref", "s"):
        t, dl = delays(st[k], (2, 3, 4), 95, 300)
        c, _, lab = STYLE[k]
        ax[3].plot(t, dl, ".", ms=2, color=c, label=lab)
    ax[3].set(xlabel="time (us)", ylabel="actual delay t_act - t_lo (ns)", ylim=(0, 20),
              title="(d) same run: phases 2-4's actual turn-on delay (not deferred: the command)")
    ax[3].legend(fontsize=8, loc="lower right")

    for a in ax:
        a.grid(color="0.9", lw=0.6)
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("A249 (plant V7, single module): one fixed turn-on delay per board for phases 2-4, closed loop", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "a249_fixed_delay_oracle.png", dpi=130)


if __name__ == "__main__":
    main()
