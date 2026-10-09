"""A180 figure: rail 1 and phase 1's per-period current peak around the +4.8 V / 1 us step (row up1).

Run from the project root after a180_run.py: python3 extensions/lscb_ladder/experiments/A180_lscb_ladder_open_loop/a180_figure.py
Writes a180_up1.png. Palette: the dataviz reference categorical slots 1-4 in order (validated: CVD worst adjacent
dE 9.1, normal 22.9; aqua / yellow below 3:1 on the light surface -> every line is labelled directly).
"""
import json
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SERIES = [("base", "P24 as is", "#2a78d6", "P24 as is"),
          ("d07_c20", "LSCB ladder, 0.7 V diode (as in the paper)", "#eb6834", "0.7 V diode"),
          ("act_c20", "ladder + switched clamp, C_DC 20 uF", "#1baf7a", "clamp, 20 uF"),
          ("act_c60", "ladder + switched clamp, C_DC 60 uF", "#eda100", "clamp, 60 uF")]
# direct labels: text position (time us, value) per variant, an arrow to the curve's maximum; rail / current panel
LBL_R = {"base": (42.6, 16.35), "d07_c20": (38.3, 15.4), "act_c20": (44.5, 14.15), "act_c60": (44.5, 12.75)}
LBL_I = {"base": (44.6, 240), "d07_c20": (46.0, 198), "act_c20": (46.0, 168), "act_c60": (44.2, 128.5)}
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"


def main():
    data = {v: json.loads((HERE / "runs" / f"{v}_up1.json").read_text()) for v, _, _, _ in SERIES}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), facecolor=SURF)
    t_lo, t_hi = 38.0, 62.0
    for ax in axes:
        ax.set_facecolor(SURF)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(INK2)
        ax.tick_params(colors=INK2, labelsize=10)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_xlim(t_lo, t_hi)
        ax.set_xlabel("time (us)", color=INK2, fontsize=11)
    ax0, ax1 = axes
    for v, label, col, short in SERIES:
        tr = data[v]["trace"]
        t = np.array(tr["t_us"])
        n = int(round(data[v]["params"]["T"] / 20e-9))                  # one switching period on the 20 ns grid
        r1 = np.convolve(tr["rails"][0], np.ones(n) / n, mode="same")
        keep = (t >= t_lo) & (t <= t_hi)
        ax0.plot(t[keep], r1[keep], color=col, linewidth=2, label=label)
        pp = tr["period_peak"]
        pk = [(x, y) for x, y in zip(pp["t0_us"], pp["il"][0]) if y is not None and t_lo <= x <= t_hi]
        ax1.plot([a for a, _ in pk], [b for _, b in pk], color=col, linewidth=2)
        arrow = dict(arrowstyle="-", color=INK2, linewidth=0.8)
        i0 = int(np.argmax(np.where(keep, r1, -np.inf)))
        ax0.annotate(short, xy=(t[i0], r1[i0]), xytext=LBL_R[v], color=INK, fontsize=9, arrowprops=arrow)
        j0 = max(range(len(pk)), key=lambda j: pk[j][1])
        ax1.annotate(f"{short}: {data[v]['post']['il_peak'][0]:.0f} A", xy=pk[j0], xytext=LBL_I[v], color=INK,
                     fontsize=9, arrowprops=arrow)
    ax0.axhline(13.2, color=INK2, linewidth=1, linestyle=(0, (4, 3)))
    ax0.text(53.0, 13.0, "ideal: 52.8 V / 4 = 13.2 V", color=INK2, fontsize=9, va="top")
    ax0.set_ylabel("rail 1 = Vin - Vcs1, period average (V)", color=INK2, fontsize=11)
    ax0.set_title("Rail 1 after a +4.8 V input step in 1 us", color=INK, fontsize=12, loc="left")
    ax1.set_ylabel("phase-1 current peak per period (A)", color=INK2, fontsize=11)
    ax1.set_title("Phase 1's current peak", color=INK, fontsize=12, loc="left")
    ax1.set_ylim(126, 250)
    leg = ax0.legend(loc="upper right", fontsize=9, frameon=False)
    for txt in leg.get_texts():
        txt.set_color(INK)
    fig.text(0.01, 0.01, "A180: open-loop LTspice power stage of one P24 module (48 V -> 1 V, 250 A, 2.2 MHz), ideal "
             "feed-forward; not the closed-loop controller.", color=INK2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.03, 0.97, 1))
    fig.savefig(HERE / "a180_up1.png", dpi=160, facecolor=SURF)


if __name__ == "__main__":
    main()
