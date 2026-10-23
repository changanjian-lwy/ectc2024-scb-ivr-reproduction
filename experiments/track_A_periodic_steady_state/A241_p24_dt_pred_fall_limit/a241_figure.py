"""A241 figure, arm f (solid) against A240 (dashed) on A240's rows: (a) the peak after 300 us, (b) Vo's extremes and
(d) late fires per re-application against the load's repetition frequency; (c) N75 at 100 kHz, phase 2's peak and
turn-on delay in both arms (records A240 cosim/run_p_N75_100k.json, A241 cosim/run_f_p_N75_100k.json); (e) stage 2:
each row's post-event peak against its reference, when run.
  python3 a241_figure.py -> a241_fall_limit.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a237_analyze", TA / "A237_p24_true_light_load" / "a237_analyze.py")
A37 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A37)
TRACE, PH, T_A, T_B = "p_N75_100k", 2, 519e-6, 535e-6
BOARDS = ("N0", "N75", "S75h")


def main():
    d = json.loads((HERE / "a241_summary.json").read_text())
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    ax = ax.ravel()
    for k, b in enumerate(BOARDS):
        rows = [x for n, x in d["stage1"].items() if x and n.split("_")[1] == b]
        fk = [float(n.split("_")[2][:-1]) for n, x in d["stage1"].items() if x and n.split("_")[1] == b]
        for arm, ls, lab in (("ref", "--", "A240"), ("f", "-", "A241")):
            ax[0].plot(fk, [x[arm]["peak_after_t0"] for x in rows], "o" + ls, color=f"C{k}", label=f"{b} {lab}")
            ax[1].plot(fk, [x[arm]["vo_max_v"] for x in rows], "^" + ls, color=f"C{k}", label=f"{b} {lab}")
            ax[1].plot(fk, [x[arm]["vo_min_v"] for x in rows], "v" + ls, color=f"C{k}")
            ax[3].plot(fk, [x[arm]["late_after_t0"] / x[arm]["n_reapp"] for x in rows], "s" + ls, color=f"C{k}",
                       label=f"{b} {lab}")
    for a in (ax[0], ax[1], ax[3]):
        a.set_xscale("log"); a.set_xlabel("load repetition frequency (kHz)"); a.legend(fontsize=7, ncol=2)
    ax[0].axhline(200, color="r", lw=1)
    ax[0].set(ylabel="peak after 300 us (A)", title="peak current: A241 (solid) vs A240 (dashed)")
    ax[1].axhline(1.05, color="k", lw=0.7); ax[1].axhline(0.95, color="k", lw=0.7)
    ax[1].set(ylabel="Vo after 300 us (V)", title="Vo extremes (lines: 0.95 / 1.05 V)")
    ax[3].set(ylabel="late fires after 300 us / re-applications", title="late fires per re-application")
    for arm, f, ls in (("A240", TA / "A240_p24_accelerator_load" / "cosim" / f"run_{TRACE}.json", "--"),
                       ("A241", HERE / "cosim" / f"run_f_{TRACE}.json", "-")):
        sw = A37.swing(f, PH, T_A, T_B, 0.25e-6)
        t = [x["t_us"] for x in sw]
        ax[2].plot(t, [x["peak_a"] for x in sw], "r" + ls, label=f"{arm} phase {PH} peak")
        ax[2].plot(t, [10 * x["delay_ns"][0] for x in sw], "g" + ls, label=f"{arm} delay x 10 (ns)")
    ax[2].axhline(200, color="r", lw=0.7)
    ax[2].set(xlabel="t (us)", ylabel="A  /  ns x 10",
              title=f"N75, 100 kHz, phase {PH}: A240 (dashed) / A241 (solid)")
    ax[2].legend(fontsize=7)
    s2 = [(n, x) for n, x in d["stage2"].items() if x and "post_pk" in x["f"]]
    if s2:
        ax[4].plot([x["ref"]["post_pk"] for _, x in s2], [x["f"]["post_pk"] for _, x in s2], "o")
        for n, x in s2:
            ax[4].annotate(n, (x["ref"]["post_pk"], x["f"]["post_pk"]), fontsize=6)
        lo, hi = 130, 220
        ax[4].plot([lo, hi], [lo, hi], "k", lw=0.7); ax[4].plot([lo, hi], [lo + 2, hi + 2], "k:", lw=0.7)
        ax[4].set(xlabel="reference post-event peak (A)", ylabel="A241 post-event peak (A)",
                  title="stage 2: each row against its reference (dotted: +2 A)")
    else:
        ax[4].set_axis_off()
    ax[5].set_axis_off()
    fig.tight_layout()
    fig.savefig(HERE / "a241_fall_limit.png", dpi=120)


if __name__ == "__main__":
    main()
