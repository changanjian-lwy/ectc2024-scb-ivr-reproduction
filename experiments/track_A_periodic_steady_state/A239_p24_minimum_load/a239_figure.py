"""A239 figure: (a) the four rails after a start-up into 5 A (u5_N75h) against a full-load start-up (A231 N75h_100);
(b) Vo of the same two; (c) each release's return time against Co (V_pk - 1.01 V) / I.
  python3 a239_figure.py -> a239_minimum_load.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
TA = HERE.parent
RUNS = {"start into 5 A (A239 u5_N75h)": HERE / "cosim" / "run_u5_N75h.json",
        "start into 100 % (A231 u_N75h_100_lead)": TA / "A231_p24_lead_per_corner" / "cosim" / "run_u_N75h_100_lead.json"}


def rails(f):
    r = json.loads(Path(f).read_text())
    s = r["sections"]
    ts = np.array([q["t_s"] for q in s]) * 1e6
    vin = np.array([q["vin_v"] for q in s]); vcs = np.array([q["vcs_v"] for q in s])
    rl = np.column_stack([vin - vcs[:, 0], vcs[:, 0] - vcs[:, 1], vcs[:, 1] - vcs[:, 2], vcs[:, 2]])
    return ts, rl, np.array([q["vo"] for q in s]), r["t_mode_p_s"] * 1e6


def main():
    summ = json.loads((HERE / "a239_summary.json").read_text())["rows"]
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    for (lab, f), ls in zip(RUNS.items(), ("-", ":")):
        ts, rl, vo, tp = rails(f)
        for k in range(4):
            ax[0].plot(ts, rl[:, k], ls, color=f"C{k}", lw=1, label=f"rail {k + 1}" if ls == "-" else None)
        ax[0].axvline(tp, color="k", ls=ls, lw=0.8)
        ax[1].plot(ts, vo, ls, lw=1, label=lab)
    ax[0].axvline(137.22, color="grey", lw=0.6)
    ax[0].text(138, 21, "input ramp ends", fontsize=8, color="grey")
    ax[0].set(xlim=(80, 300), xlabel="t (us)", ylabel="rail (V)",
              title="N75, 125 C: rails (solid: 5 A, dotted: 100 %; vertical: mode P)")
    ax[0].legend(fontsize=8)
    ax[1].axhspan(0.99, 1.01, color="g", alpha=0.1)
    ax[1].set(xlim=(80, 300), ylim=(0.96, 1.06), xlabel="t (us)", ylabel="Vo (V)", title="Vo, same runs")
    ax[1].legend(fontsize=8)
    for row, x in summ.items():
        m = x["m"]
        if row.startswith("c"):
            ax[2].plot(m["pred_back_us"], m["back_from_pk_us"], "o")
            ax[2].annotate(row, (m["pred_back_us"], m["back_from_pk_us"]), fontsize=8, xytext=(4, -10), textcoords="offset points")
    ax[2].plot([0, 100], [0, 100], "k--", lw=0.8)
    ax[2].set(xlabel="Co (V_pk - 1.01 V) / I (us)", ylabel="record: peak to last exit from 1 % (us)",
              title="release to a constant current: return time")
    fig.tight_layout()
    fig.savefig(HERE / "a239_minimum_load.png", dpi=130)


if __name__ == "__main__":
    main()
