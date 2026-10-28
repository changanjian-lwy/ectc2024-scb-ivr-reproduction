"""A259 figure (records: cosim/run_{d,f}_*.json; release records-a259). Time from the fault's start (400 us):
(a) the three shorts: the largest gate-record turn-off current per 0.2 us without a fault path (arm d, dashed) and
    with the trip (arm f, solid), and each trip;
(b) the three overloads above the rating, the same;
(c) Vo in the shorts (sections, then fault_trace after the trip) against the 0.9 V under-voltage level;
(d) the ladder after the trip: max |rail - Vin / 4| in fault_trace, every FAULT row.
  python3 a259_figure.py -> a259_fault_trip.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
T0 = 400e-6
SHORTS = {"sh025_N75": ("#2a78d6", "0.25 mOhm, N75"), "sh1_N75": ("#2f9e6e", "1 mOhm, N75"),
          "sh025_S75h": ("#8a5cc2", "0.25 mOhm, S75h")}
OVER = {"ov150_N75": ("#eb6834", "150 %, N75"), "ov150_S75h": ("#b8860b", "150 %, S75h"),
        "ov200_N75": ("#c0392b", "200 %, N75")}
INK = "#3d3d3a"


def rec(arm, row):
    return json.loads((HERE / "cosim" / f"run_{arm}_{row}.json").read_text())


def binned(d, t_end_us, w=0.2):
    n = int(t_end_us / w)
    pk = np.full(n, np.nan)
    for e in d["gate_offs_last"]:
        x = (e["t_s"] - T0) * 1e6
        if 0 <= x < t_end_us:
            k = int(x / w)
            pk[k] = e["i_max_a"] if np.isnan(pk[k]) else max(pk[k], e["i_max_a"])
    return (np.arange(n) + 0.5) * w, pk


def peaks(ax, rows, t_end, title):
    for row, (c, lab) in rows.items():
        for arm, ls, lw in (("d", "--", 1.0), ("f", "-", 1.8)):
            t, pk = binned(rec(arm, row), t_end)
            ax.plot(t, pk, ls, color=c, lw=lw, label=f"{lab}" if arm == "f" else None)
        f = rec("f", row)["fault"]
        ax.axvline((f["t_s"] - T0) * 1e6, color=c, lw=0.8, ls=":")
        ax.text((f["t_s"] - T0) * 1e6 + 0.08, 108, f"trip: {f['cause']}", color=INK, fontsize=7, rotation=90, va="bottom")
    ax.axhline(200, color=INK, lw=0.8, ls="--")
    ax.set_xlim(0, t_end)
    ax.set_ylim(100, 700)
    ax.set_xlabel("time from the fault (us)")
    ax.set_ylabel("largest turn-off current per 0.2 us (A)")
    ax.set_title(title, fontsize=10, loc="left")
    ax.legend(fontsize=8, loc="upper left", frameon=False, title="solid: with the trip (ends at the shutdown); dashed: without",
              title_fontsize=7.5)


def main():
    fig, ax = plt.subplots(2, 2, figsize=(12, 8.2))
    peaks(ax[0, 0], SHORTS, 6.0, "(a) output shorts from 400 us")
    peaks(ax[0, 1], OVER, 12.0, "(b) resistive overloads above the ~136 % rating")
    a = ax[1, 0]
    for row, (c, lab) in SHORTS.items():
        for arm, ls, lw in (("d", "--", 1.0), ("f", "-", 1.8)):
            d = rec(arm, row)
            pts = [((q["t_s"] - T0) * 1e6, q["vo"]) for q in d["sections"] if q["t_s"] >= T0 - 1e-6]
            pts += [((q["t_s"] - T0) * 1e6, q["vo"]) for q in d.get("fault_trace", [])]
            pts.sort()
            a.plot(*zip(*[p for p in pts if p[0] <= 3.0]), ls, color=c, lw=lw, label=lab if arm == "f" else None)
    a.axhline(0.9, color=INK, lw=0.8, ls="--")
    a.text(2.0, 0.91, "under-voltage level 0.9 V (400 ns)", color=INK, fontsize=8)
    a.set_xlim(-0.2, 3.0)
    a.set_xlabel("time from the fault (us)")
    a.set_ylabel("Vo (V)")
    a.set_title("(c) Vo in the shorts (solid: with the trip)", fontsize=10, loc="left")
    a.legend(fontsize=8, loc="lower left", frameon=False)
    b = ax[1, 1]
    for row, (c, lab) in (SHORTS | OVER).items():
        d = rec("f", row)
        tr, f = d["fault_trace"], d["fault"]
        t = [(s["t_s"] - f["t_off_s"]) * 1e6 for s in tr]
        dev = []
        for s in tr:
            v = [48.0] + s["vcs"] + [0.0]
            dev.append(max(abs(v[q] - v[q + 1] - 12.0) for q in range(4)))
        b.plot(t, dev, color=c, lw=1.6, label=lab)
    b.set_xscale("symlog", linthresh=1.0)
    b.set_xlabel("time from the shutdown (us)")
    b.set_ylabel("ladder: max |rail - Vin / 4| (V)")
    b.set_ylim(0, 3.2)
    b.set_title("(d) the ladder held after the shutdown (all switches off)", fontsize=10, loc="left")
    b.legend(fontsize=8, loc="center right", frameon=False, ncol=2)
    for s in ax.flat:
        s.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(HERE / "a259_fault_trip.png", dpi=150)


if __name__ == "__main__":
    main()
