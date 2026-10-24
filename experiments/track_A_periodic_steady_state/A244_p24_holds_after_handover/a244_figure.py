"""A244 figure, arm w (solid) against A240 (dashed) on A240's rows: (a) the peak after 300 us, (b) Vo's extremes and
(d) late fires per re-application against the load's repetition frequency; (c) N0 at 100 kHz, phase 4's peak and
turn-on delay in both arms (records A240 cosim/run_p_N0_100k.json, A244 cosim/run_w_p_N0_100k.json); (e) stage 2:
each row's post-event peak against its reference; (f) the control (BOUNDARY Section 4): each missed
row's post-event peak at k 0 / 2 / 4 of T / 6, arm r (open) and arm w (filled), from a244_control.json.
  python3 a244_figure.py -> a244_holds_after_handover.png"""
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
TRACE, PH, T_A, T_B = "p_N0_100k", 4, 519e-6, 535e-6
BOARDS = ("N0", "N75", "S75h")


def main():
    d = json.loads((HERE / "a244_summary.json").read_text())
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    ax = ax.ravel()
    for k, b in enumerate(BOARDS):
        rows = [x for n, x in d["stage1"].items() if x and n.split("_")[1] == b]
        fk = [float(n.split("_")[2][:-1]) for n, x in d["stage1"].items() if x and n.split("_")[1] == b]
        for arm, ls, lab in (("ref", "--", "A240"), ("w", "-", "A244")):
            ax[0].plot(fk, [x[arm]["peak_after_t0"] for x in rows], "o" + ls, color=f"C{k}", label=f"{b} {lab}")
            ax[1].plot(fk, [x[arm]["vo_max_v"] for x in rows], "^" + ls, color=f"C{k}", label=f"{b} {lab}")
            ax[1].plot(fk, [x[arm]["vo_min_v"] for x in rows], "v" + ls, color=f"C{k}")
            ax[3].plot(fk, [x[arm]["late_after_t0"] / x[arm]["n_reapp"] for x in rows], "s" + ls, color=f"C{k}",
                       label=f"{b} {lab}")
    for a in (ax[0], ax[1], ax[3]):
        a.set_xscale("log"); a.set_xlabel("load repetition frequency (kHz)"); a.legend(fontsize=7, ncol=2)
    ax[0].axhline(200, color="r", lw=1)
    ax[0].set(ylabel="peak after 300 us (A)", title="peak current: A244 (solid) vs A240 (dashed)")
    ax[1].axhline(1.05, color="k", lw=0.7); ax[1].axhline(0.95, color="k", lw=0.7)
    ax[1].set(ylabel="Vo after 300 us (V)", title="Vo extremes (lines: 0.95 / 1.05 V)")
    ax[3].set(ylabel="late fires after 300 us / re-applications", title="late fires per re-application")
    for arm, f, ls in (("A240", TA / "A240_p24_accelerator_load" / "cosim" / f"run_{TRACE}.json", "--"),
                       ("A244", HERE / "cosim" / f"run_w_{TRACE}.json", "-")):
        sw = A37.swing(f, PH, T_A, T_B, 0.25e-6)
        t = [x["t_us"] for x in sw]
        ax[2].plot(t, [x["peak_a"] for x in sw], "r" + ls, label=f"{arm} phase {PH} peak")
        ax[2].plot(t, [10 * x["delay_ns"][0] for x in sw], "g" + ls, label=f"{arm} delay x 10 (ns)")
    ax[2].axhline(200, color="r", lw=0.7)
    ax[2].set(xlabel="t (us)", ylabel="A  /  ns x 10",
              title=f"N0, 100 kHz, phase {PH}: A240 (dashed) / A244 (solid)")
    ax[2].legend(fontsize=7)
    s2 = [(n, x) for n, x in d["stage2"].items() if x and "post_pk" in x["w"] and x["ref"]["post_pk"] >= 100]
    if s2:
        ax[4].plot([x["ref"]["post_pk"] for _, x in s2], [x["w"]["post_pk"] for _, x in s2], "o")
        for n, x in s2:
            ax[4].annotate(n, (x["ref"]["post_pk"], x["w"]["post_pk"]), fontsize=6)
        lo, hi = 130, 220
        ax[4].plot([lo, hi], [lo, hi], "k", lw=0.7); ax[4].plot([lo, hi], [lo + 2, hi + 2], "k:", lw=0.7)
        ax[4].set(xlabel="reference post-event peak (A)", ylabel="A244 post-event peak (A)",
                  title="stage 2: each row against its reference (dotted: +2 A; u_N0 < 100 A off scale)")
        ax[4].set(xlim=(lo, hi), ylim=(lo, hi))
    else:
        ax[4].set_axis_off()
    cf = HERE / "a244_control.json"
    ctl = [(n, x) for n, x in json.loads(cf.read_text()).items() if isinstance(x, dict)] if cf.exists() else []
    if ctl:
        for i, (n, x) in enumerate(ctl):
            for arm, dx, mk in (("r", -0.15, "o"), ("w", 0.15, "o")):
                y = [p["post_pk"] for p in x["positions"][arm].values()]
                ax[5].plot([i + dx] * len(y), y, mk, color="C0" if arm == "r" else "C3",
                           mfc="none" if arm == "r" else "C3", label=("arm r (reference)" if arm == "r" else "arm w") if i == 0 else None)
            ax[5].annotate(f"NEW {max(p['new_after'] for p in x['positions']['r'].values())}/"
                           f"{max(p['new_after'] for p in x['positions']['w'].values())}",
                           (i, min(p["post_pk"] for a in "rw" for p in x["positions"][a].values()) - 3), fontsize=6, ha="center")
        ax[5].set_xticks(range(len(ctl)), [n for n, _ in ctl], rotation=30, fontsize=7)
        ax[5].set(ylabel="post-event peak (A)", title="control: step moved by 0 / 2 / 4 T/6 (NEW: most r / b)")
        ax[5].set_ylim(bottom=min(p["post_pk"] for _, x in ctl for a in "rw" for p in x["positions"][a].values()) - 6)
        ax[5].legend(fontsize=7)
    else:
        ax[5].set_axis_off()
    fig.tight_layout()
    fig.savefig(HERE / "a244_holds_after_handover.png", dpi=120)


if __name__ == "__main__":
    main()
