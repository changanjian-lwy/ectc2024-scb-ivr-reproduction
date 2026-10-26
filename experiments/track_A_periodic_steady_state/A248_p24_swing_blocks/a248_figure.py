"""A248 figure (harness tmp/a248_swing.npz; A247's records tmp/a247_records.npz; release records-a248):
(a) h2: each variant's shift and offset against D57 as a fraction of the full plant's (full, one block dropped, bare);
(b) h1: the full harness's V_DS at the actual delay minus the record's, the rail from the sections against the rail
from the edge's own command V_DS;
(c) the full harness's soft windows (V_DS <= 2 V) at 12 V, phases 2-3, N0 / N75 / N13, with one delay per board;
(d) where the learner's delay is more than 2 ns off that delay: recorded V_DS against the harness's at it.
  python3 a248_figure.py -> a248_swing_blocks.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a248_analyze", HERE / "a248_analyze.py")
AN = importlib.util.module_from_spec(_s)
_s.loader.exec_module(AN)
MODEL, REC = "C3", "0.45"


def main():
    d = json.loads((HERE / "a248_summary.json").read_text())
    H = AN.harness()
    R, _ = AN.A47.load_records()
    fig, ax = plt.subplots(2, 2, figsize=(13, 9.5))
    ax = ax.ravel()
    var = d["h2"]["variants"]
    names = ["full", "gate", "miller", "r_core", "loop", "edge", "bare"]
    x = np.arange(len(names))
    fs, fo = var["full"]["shift_ns"], var["full"]["offset_v"]
    ax[0].bar(x - 0.18, [var[n]["shift_ns"] / fs for n in names], 0.34, color=REC, label=f"shift (full: {fs:.2f} ns)")
    ax[0].bar(x + 0.18, [var[n]["offset_v"] / fo for n in names], 0.34, color=MODEL, label=f"offset (full: {fo:.2f} V)")
    ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set_xticks(x); ax[0].set_xticklabels(["full"] + [f"no {n}" for n in names[1:-1]] + ["bare"], fontsize=8)
    ax[0].set(ylabel="against D57, as a fraction of the full plant's", title="(a) h2: which block makes the swing late and shallow")
    ax[0].legend(fontsize=8)
    rows, rails, va, key = AN.own_rail(H, R, n=20000)
    bl = list(H["boards"])
    vs = np.array([AN.trilinear(H, bl.index(key[j]), 0, int(R["phase"][j] == 4), R["rail_v"][j:j + 1],
                                R["i_off_a"][j:j + 1], R["delay_ns"][j:j + 1])[0] for j in rows])
    y = R["vds_act_v"][rows]
    bins = np.linspace(-1.5, 1.0, 101)
    ax[1].hist(vs - y, bins, color=REC, alpha=0.7, label=f"rail from the sections (RMSE {np.sqrt(np.nanmean((vs - y) ** 2)):.2f} V)")
    ax[1].hist(va - y, bins, color=MODEL, alpha=0.7, label=f"rail from its own command (RMSE {np.sqrt(np.mean((va - y) ** 2)):.3f} V)")
    ax[1].set(xlabel="harness - record, V_DS at the actual turn-on (V)", ylabel="turn-ons",
              title="(b) h1: the residual was the rail's sampling, not the swing")
    ax[1].legend(fontsize=8)
    t, j12 = H["t_ns"], int(np.argmin(np.abs(H["rails"] - 12.0)))
    for name, col in (("N0", MODEL), ("N75", "C0"), ("N13", "C2")):
        b = bl.index(name)
        tr = H["traces"][b, 0, 0, j12]
        lo = [t[np.flatnonzero(v <= 2.0)[0]] if (v <= 2.0).any() else np.nan for v in tr]
        hi = [t[np.flatnonzero(v <= 2.0)[-1]] if (v <= 2.0).any() else np.nan for v in tr]
        ax[2].fill_between(H["currents"], lo, hi, color=col, alpha=0.2, lw=0, label=f"{name} window")
        fx = d["post_hoc"]["windows"]["at_12v"][f"{name}, phases 2-3"]["fixed_ns"]
        ax[2].axhline(fx, color=col, lw=1.2, ls="--", label=f"{name}: one delay {fx:.2f} ns")
    ax[2].set(xlabel="low-side turn-off current (A)", ylabel="delay after the turn-off command (ns)", ylim=(0, 30),
              title="(c) the plant's soft windows at 12 V nest (phases 2-3)")
    ax[2].legend(fontsize=7, ncol=2)
    fd = d["post_hoc"]["fixed_against_learner"]["learner_off_by_2ns"]
    xx = np.arange(3)
    ax[3].bar(xx - 0.18, fd["recorded_p50_p90_p99_v"], 0.34, color=REC, label="learner (recorded)")
    ax[3].bar(xx + 0.18, fd["fixed_p50_p90_p99_v"], 0.34, color=MODEL, label="one delay per board (plant harness)")
    ax[3].set_xticks(xx); ax[3].set_xticklabels(["p50", "p90", "p99"])
    ax[3].set(ylabel="V_DS at the turn-on (V)",
              title=f"(d) where the learner is > 2 ns off ({fd['rows']} of {d['post_hoc']['own_rail']['rows']} turn-ons)")
    ax[3].legend(fontsize=8)
    fig.suptitle("A248: the plant's own single edge against D57 and the V7 records (A229-A246)")
    fig.tight_layout()
    fig.savefig(HERE / "a248_swing_blocks.png", dpi=110)


if __name__ == "__main__":
    main()
