"""A246 figure, A244's record (arm w, grey / open) against arm h (+ hold_floor_ns 3.0, colour / filled): (a) N0 at
100 kHz, phase 4's learned delay (records A244 cosim/run_w_p_N0_100k.json, cosim/run_h_p_N0_100k.json); (b) its peak per
re-application (A240's peak measure, gate_offs i_max_a; line: q4, 171.5 A); (c) g10, the same row with the train moved by k T / 6; (d) every stage-1 row's
peak after 300 us; (e) Vo's minimum after 300 us; (f) c1 on the g9 row (S75h at 100 kHz), Vo's minimum at k 0 / 2 / 4.
(c)-(f) from a246_summary.json.
  python3 a246_figure.py -> a246_held_report_floor.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a246_analyze", HERE / "a246_analyze.py")
AN = importlib.util.module_from_spec(_s)
_s.loader.exec_module(AN)
ROW, PH, Q4 = "p_N0_100k", 4, 171.5
ARMS = (("w", "A244 (arm w)", "0.45", "none"), ("h", "arm h (floor 3 ns)", "C3", "C3"))


def peaks_per_period(rec):
    lp = rec["cfg"]["load_pulse"]
    t0, per = lp["t_us"], 1e3 / lp["f_khz"]
    out = {}
    for x in rec["gate_offs_last"]:
        t = x["t_s"] * 1e6
        if t0 <= t < lp["t_stop_us"] + per:
            k = int((t - t0) // per)
            out[k] = max(out.get(k, 0.0), x["i_max_a"])
    return [t0 + (k + 0.5) * per for k in sorted(out)], [out[k] for k in sorted(out)]


def pair(a, x, ys, key):
    for arm, lab, col, mfc in ARMS:
        a.plot(x, [y[arm][key] if isinstance(y[arm], dict) else y[arm] for y in ys], "o", color=col, mfc=mfc, ms=6, label=lab)


def main():
    d = json.loads((HERE / "a246_summary.json").read_text())
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    ax = ax.ravel()
    recs = {"w": json.loads((AN.W / f"run_w_{ROW}.json").read_text()), "h": json.loads((AN.COS / f"run_h_{ROW}.json").read_text())}
    for arm, lab, col, mfc in ARMS:
        seq = AN._seq(recs[arm], PH)
        ax[0].plot([x["t_s"] * 1e6 for _, x in seq], [dl for dl, _ in seq], "." if arm == "h" else "x", ms=2.5, color=col,
                   label=lab)
        t, pk = peaks_per_period(recs[arm])
        ax[1].plot(t, pk, "o-", color=col, mfc=mfc, ms=5, lw=1, label=lab)
    lp = recs["h"]["cfg"]["load_pulse"]
    ax[0].set(xlim=(lp["t_us"] - 10, lp["t_stop_us"] + 10), ylim=(0, 22), xlabel="time (us)",
              ylabel=f"phase {PH} turn-on delay (ns)", title=f"{ROW}: phase {PH}, every learned turn-on")
    ax[0].legend(fontsize=7, markerscale=3)
    ax[1].axhline(Q4, color="k", lw=0.7, ls="--")
    ax[1].text(lp["t_us"], Q4 + 1, "A240 q4: 171.5 A", fontsize=7)
    ax[1].set(xlabel="time (us)", ylabel="peak per load period (A)", title=f"{ROW}: peak at each re-application")
    ax[1].legend(fontsize=7)
    pos = d["control"]["positions"]
    ks = sorted(pos["h"], key=int)
    for arm, lab, col, mfc in ARMS:
        ax[2].plot([int(k) for k in ks], [pos[arm][k]["peak_after_t0"] for k in ks], "o", color=col, mfc=mfc, ms=8, label=lab)
    ax[2].axhline(Q4, color="k", lw=0.7, ls="--")
    ax[2].set(xticks=[0, 2, 4], xlabel="train moved by k T / 6", ylabel="peak after 300 us (A)",
              title=f"g10: {ROW} at three step positions")
    ax[2].legend(fontsize=7)
    s1 = d["stage1"]
    rows = list(s1)
    x = range(len(rows))
    for a, key, lab in ((ax[3], "peak_after_t0", "peak after 300 us (A)"), (ax[4], "vo_min_v", "Vo minimum after 300 us (V)")):
        pair(a, x, [s1[r] for r in rows], key)
        a.set_xticks(list(x)); a.set_xticklabels(rows, rotation=70, fontsize=7); a.set_ylabel(lab); a.legend(fontsize=7)
    ax[3].set_title("stage 1: peak (1 MHz rows excepted from g2)")
    ax[4].set_title("stage 1: Vo minimum (g9: no more than 1 mV lower)")
    c1 = {r: v for r, v in d.get("c1", {}).items() if v}
    if c1:
        r, v = next(iter(c1.items()))
        ks = sorted(v["positions"]["h"], key=int)
        for arm, lab, col, mfc in ARMS:
            ax[5].plot([int(k) for k in ks], [v["positions"][arm][k]["vo_min_v"] for k in ks], "o", color=col, mfc=mfc, ms=8,
                       label=lab)
        ax[5].axhline(v["worst_vo_min"]["w"] - 1e-3, color="k", lw=0.7, ls="--")
        ax[5].text(0, v["worst_vo_min"]["w"] - 0.9e-3, "arm w's worst - 1 mV", fontsize=7)
        ax[5].set(xticks=[0, 2, 4], xlabel="train moved by k T / 6", ylabel="Vo minimum after 300 us (V)",
                  title=f"c1: {r} at three step positions")
        ax[5].legend(fontsize=7)
    fig.suptitle("A246: a report with positive current lifts a delay far below the other phases' (plant V7, final "
                 "configuration + rev_n 16)")
    fig.tight_layout()
    fig.savefig(HERE / "a246_held_report_floor.png", dpi=110)


if __name__ == "__main__":
    main()
