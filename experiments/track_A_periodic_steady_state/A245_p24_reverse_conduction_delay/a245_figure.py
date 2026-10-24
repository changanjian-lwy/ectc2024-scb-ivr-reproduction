"""A245 figure, arm f (final configuration, dashed / open) against arm r (+ rev_n 16, solid / filled): (a) S75 at
125 C into 30 %, the four rails against Vin / 4 (records cosim/run_f_u_S75h_30.json, run_r_u_S75h_30.json); (b) its
phase 3's turn-on V_DS at the command, every learned report (<= 0: the swing had finished); (c) Vo of the same row and
of the lead arm, whose lock releases by itself in arm f (run_f_u_S75h_30_l.json); (d) every stage-1 row's ladder
deviation at the end; (e) Vo's minimum after mode P's entry (line: 0.99 V); (f) edge + reverse-conduction loss over
the last 50 us. (d)-(f) from a245_summary.json.
  python3 a245_figure.py -> a245_reverse_conduction.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
COS = HERE / "cosim"
TRACE, PH = "u_S75h_30", 3


def rails(s):
    v = [s["vin_v"]] + list(s["vcs_v"]) + [0.0]
    return [v[q] - v[q + 1] for q in range(4)]


def main():
    d = json.loads((HERE / "a245_summary.json").read_text())
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    ax = ax.ravel()
    for arm, ls in (("f", "--"), ("r", "-")):
        rec = json.loads((COS / f"run_{arm}_{TRACE}.json").read_text())
        S = rec["sections"]
        t = [s["t_s"] * 1e6 for s in S]
        for q in range(4):
            ax[0].plot(t, [rails(s)[q] - s["vin_v"] / 4 for s in S], ls, color=f"C{q}", lw=1,
                       label=f"rail {q + 1} ({arm})")
        on = [x for x in rec["turnons_last"] if x["phase"] == PH and "early" in x]
        ax[1].plot([x["t_s"] * 1e6 for x in on], [x["vds_v"] for x in on], "." if arm == "r" else "x",
                   ms=2, color="C3" if arm == "r" else "0.5", label=f"arm {arm}")
        ax[2].plot(t, [s["vo"] for s in S], ls, color="C0", lw=1, label=f"125 C base, arm {arm}")
    lead = json.loads((COS / f"run_f_{TRACE}_l.json").read_text())["sections"]
    ax[2].plot([s["t_s"] * 1e6 for s in lead], [s["vo"] for s in lead], ":", color="C1", lw=1,
               label="125 C lead, arm f (releases by itself)")
    ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set(xlabel="time (us)", ylabel="rail - Vin / 4 (V)", title=f"{TRACE}: ladder, arm f (dashed) vs r (solid)")
    ax[0].legend(fontsize=6, ncol=2)
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set(xlabel="time (us)", ylabel="V_DS at the turn-on command (V)",
              title=f"{TRACE}: phase {PH}, every learned report")
    ax[1].legend(fontsize=7)
    ax[2].axhline(0.99, color="r", lw=0.7)
    ax[2].set(xlim=(90, 300), ylim=(0.975, 1.055), xlabel="time (us)", ylabel="Vo (V)", title="Vo after the start")
    ax[2].legend(fontsize=7)
    rows = list(d["stage1"])
    x = range(len(rows))
    s1 = d["stage1"]
    for k, (key, lab) in enumerate((("dev_end_v", "ladder deviation at the end (V)"), ("vo_min", "Vo minimum after mode P (V)"))):
        a = ax[3 + k]
        a.plot(x, [s1[r]["f"][key] for r in rows], "o", mfc="none", color="0.4", label="arm f")
        a.plot(x, [s1[r]["r"][key] for r in rows], "o", color="C3", label="arm r (rev_n 16)")
        a.set_xticks(list(x)); a.set_xticklabels(rows, rotation=70, fontsize=7); a.set_ylabel(lab); a.legend(fontsize=7)
    ax[3].axhline(1.0, color="r", lw=0.7); ax[3].set_title("g1: every rail within 1 V of Vin / 4")
    ax[4].axhline(0.99, color="r", lw=0.7); ax[4].set_title("g3: Vo after mode P's entry")
    loss = {arm: [s1[r][arm]["edge_w_tail"] + s1[r][arm]["rev_w_tail"] for r in rows] for arm in "fr"}
    ax[5].plot(x, loss["f"], "s", mfc="none", color="0.4", label="arm f")
    ax[5].plot(x, loss["r"], "s", color="C3", label="arm r")
    ax[5].set_xticks(list(x)); ax[5].set_xticklabels(rows, rotation=70, fontsize=7)
    ax[5].set(ylabel="edge + reverse-conduction loss, last 50 us (W)", title="loss at the end of each run")
    ax[5].legend(fontsize=7)
    fig.suptitle("A245: lowering a turn-on delay that keeps finding the swing finished (plant V7, final configuration)")
    fig.tight_layout()
    fig.savefig(HERE / "a245_reverse_conduction.png", dpi=110)


if __name__ == "__main__":
    main()
