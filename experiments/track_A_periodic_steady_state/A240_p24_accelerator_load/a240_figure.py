"""A240 figure: (a) Vo's extremes and (b) the peak current against the load's repetition frequency per board, with the
single-event references; (c) N75 at 100 kHz: phase 2's valley, peak and turn-on delay through two load periods
(record cosim/run_p_N75_100k.json), the load drawn underneath; (d) late fires after 300 us per re-application against
the single re-application in A237 (cw5_N0 0, cw5_N75 53, c30_S75h 162, counted 380-430 us).
  python3 a240_figure.py -> a240_accelerator_load.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a237_analyze", TA / "A237_p24_true_light_load" / "a237_analyze.py")
A37 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A37)
_s = importlib.util.spec_from_file_location("a240_analyze", HERE / "a240_analyze.py")
A40 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A40)
TRACE, PH, T_A, T_B = "p_N75_100k", 2, 519e-6, 535e-6
REF_LATE = {"N0": 0, "N75": 53, "S75h": 162}                   # A237 single re-application, late fires 380-430 us


def main():
    rows = json.loads((HERE / "a240_summary.json").read_text())["rows"]
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))
    ax = ax.ravel()
    for k, b in enumerate(A40.MC.BOARDS):
        pts = [(x["f_khz"], x["m"]) for x in rows.values() if x and x["board"] == b]
        if not pts:
            continue
        f = np.array([p[0] for p in pts])
        ax[0].plot(f, [p[1]["vo_max_v"] for p in pts], "^-", color=f"C{k}", label=f"{b} max")
        ax[0].plot(f, [p[1]["vo_min_v"] for p in pts], "v--", color=f"C{k}", label=f"{b} min")
        ax[1].plot(f, [p[1]["peak_after_t0"] for p in pts], "o-", color=f"C{k}", label=b)
        ax[1].axhline(A40.REF_PK[b], color=f"C{k}", lw=0.7, ls=":")
        ax[3].plot(f, [p[1]["late_after_t0"] / p[1]["n_reapp"] for p in pts], "s-", color=f"C{k}", label=b)
        ax[3].axhline(REF_LATE[b], color=f"C{k}", lw=0.7, ls=":")
    for a in (ax[0], ax[1], ax[3]):
        a.set_xscale("log"); a.set_xlabel("load repetition frequency (kHz)")
    ax[0].axhline(1.05, color="k", lw=0.7); ax[0].axhline(0.95, color="k", lw=0.7)
    ax[0].set(ylabel="Vo after 300 us (V)", title="Vo extremes (lines: 0.95 / 1.05 V)")
    ax[0].legend(fontsize=7, ncol=2)
    ax[1].axhline(200, color="r", lw=1)
    ax[1].set(ylabel="peak after 300 us (A)", title="peak current (dotted: single re-application, A237)")
    ax[1].legend(fontsize=8)
    sw = A37.swing(HERE / "cosim" / f"run_{TRACE}.json", PH, T_A, T_B, 0.25e-6)
    t = np.array([x["t_us"] for x in sw])
    ax[2].plot(t, [x["peak_a"] for x in sw], "r.-", label=f"phase {PH} peak")
    ax[2].plot(t, [x["valley_a"][0] for x in sw], "b.-", label=f"phase {PH} valley")
    ax[2].axhline(200, color="r", lw=0.7)
    a2 = ax[2].twinx()
    a2.plot(t, [x["delay_ns"][0] for x in sw], "g.-", label="turn-on delay (ns)")
    a2.set_ylabel("turn-on delay after the low-side turn-off (ns)", color="g")
    cfg = json.loads((HERE / "cosim" / f"cfg_{TRACE}.json").read_text())
    lp = cfg["load_pulse"]
    from scb_ivr.cosim.circuit import CircuitParams
    per = 1e-3 / lp["f_khz"]; tr = (lp["i_hi_a"] - lp["i_lo_a"]) / (lp["slew_a_us"] * 1e6)
    cp = CircuitParams(pulse_t0=lp["t_us"] * 1e-6, pulse_t1=lp["t_stop_us"] * 1e-6, pulse_lo=lp["i_lo_a"],
                       pulse_hi=lp["i_hi_a"], pulse_T=per, pulse_th=lp["duty"] * per, pulse_tr=tr)
    tt = np.linspace(T_A, T_B, 800)
    ax[2].plot(tt * 1e6, [cp.pulse_at(x) / 4 for x in tt], color="grey", lw=1, label="load / 4 (A)")
    ax[2].set(xlabel="t (us)", ylabel="A", title=f"N75, 100 kHz: phase {PH} (record run_{TRACE}.json)")
    ax[2].legend(fontsize=7, loc="upper left")
    ax[3].set(ylabel="late fires after 300 us / re-applications",
              title="late fires per re-application (dotted: single re-application, A237)")
    ax[3].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / "a240_accelerator_load.png", dpi=130)


if __name__ == "__main__":
    main()
