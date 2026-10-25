"""A247 figure (records tmp/a247_records.npz from the V7 runs A229-A246, D57 table tmp/a247_window.npz; release
records-a247): (a) D57's soft windows (V_DS <= 2 V, corrected by the post hoc shift / offset) against the low-side
turn-off current, N0 (2.933 nH) and N75 (2.2 nH) at 12 V, phases 2-3, with the one delay per board and the learner's
actual delays on N0 at 11.5-12.5 V; (b) recorded V_DS at the actual turn-on against D57 corrected; (c) the residual
record - D57 by delay, raw and corrected (the shift's signature); (d) where the learner's delay is more than 2 ns off
the fixed one: recorded V_DS against the corrected model's at the fixed delay.
  python3 a247_figure.py -> a247_zvs_window.png"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a247_analyze", HERE / "a247_analyze.py")
AN = importlib.util.module_from_spec(_s)
_s.loader.exec_module(AN)
MODEL, REC = "C3", "0.45"


def main():
    d = json.loads((HERE / "a247_summary.json").read_text())
    sf = d["post_hoc"]["shift_fit"]
    sh, off = sf["shift_ns"], sf["offset_v"]
    tab = AN.Table(AN.PROJECT / "tmp" / "a247_window.npz")
    R, _ = AN.load_records()
    sel = R["i_off_a"] <= AN.I_NEG
    last = R["phase"] == 4
    fig, ax = plt.subplots(2, 2, figsize=(13, 9.5))
    ax = ax.ravel()
    j12 = int(np.argmin(np.abs(tab.rails - 12.0)))
    for a, (lf, col) in enumerate(((2.9333, MODEL), (2.2, "C0"))):
        ai = int(np.argmin(np.abs(tab.lf * 1e9 - lf)))
        v = tab.tr[ai, 0, j12] + off
        cur = tab.cur[tab.cur <= AN.I_NEG]
        ws = [np.flatnonzero(v[list(tab.cur).index(c)] <= AN.V_SOFT) for c in cur]
        ok = [w.size > 0 for w in ws]
        lo = np.array([tab.t[w[0]] + sh if w.size else np.nan for w in ws])
        hi = np.array([tab.t[w[-1]] + sh if w.size else np.nan for w in ws])
        ax[0].fill_between(cur, lo, hi, color=col, alpha=0.18, lw=0, label=f"D57 window, L {lf:.3f} nH")
        fixed = AN.bin_delays(tab, ai, 0, np.array([float(np.quantile(R["i_off_a"][sel], 0.01)), AN.I_NEG]), [j12],
                              AN.V_SOFT - off)[0] + sh
        ax[0].axhline(fixed, color=col, lw=1.2, ls="--", label=f"one delay, L {lf:.3f} nH: {fixed:.2f} ns")
        if not all(ok):
            ax[0].axvspan(cur[~np.array(ok)].min(), AN.I_NEG, color="0.9", lw=0)
    m = sel & ~last & (np.abs(R["lf_nh"] - 2.9333) < 1e-3) & (np.abs(R["rail_v"] - 12.0) <= 0.5) & (R["temp_c"] == 25.0)
    idx = np.random.default_rng(0).choice(np.flatnonzero(m), min(20000, int(m.sum())), replace=False)
    ax[0].plot(R["i_off_a"][idx], R["delay_ns"][idx], ".", ms=1, color=REC, alpha=0.4, label="learner, N0 11.5-12.5 V")
    ax[0].set(xlim=(-100, AN.I_NEG), ylim=(0, 30), xlabel="low-side turn-off current (A)", ylabel="delay after the turn-off (ns)",
              title="(a) soft windows nest: one delay per board serves every negative current")
    ax[0].legend(fontsize=7, markerscale=6, loc="upper left")
    idx = np.random.default_rng(1).choice(np.flatnonzero(sel), 200000, replace=False)
    vm = tab.v(R["lf_nh"][idx], last[idx], R["rail_v"][idx], R["i_off_a"][idx], R["delay_ns"][idx])
    vc = tab.v(R["lf_nh"][idx], last[idx], R["rail_v"][idx], R["i_off_a"][idx], R["delay_ns"][idx] - sh) + off
    vr = R["vds_act_v"][idx]
    ok = np.isfinite(vc)
    ax[1].hist2d(vc[ok], vr[ok], bins=120, range=[[-4, 16], [-4, 16]], cmap="Greys", norm=matplotlib.colors.LogNorm())
    ax[1].plot([-4, 16], [-4, 16], color=MODEL, lw=1)
    ax[1].set(xlabel=f"D57 corrected V_DS at the actual delay (V) (shift {sh} ns, offset {off:.2f} V)",
              ylabel="recorded V_DS at the actual turn-on (V)",
              title=f"(b) c1 after the correction: RMSE {sf['rmse_d57_v']:.2f} -> {sf['rmse_corrected_v']:.2f} V")
    dl = R["delay_ns"][idx]
    edges = np.arange(0, 22, 1.0)
    for v, lab, col in ((vm, "D57 as registered", REC), (vc, "D57 corrected", MODEL)):
        e = vr - v
        med = [np.nanmedian(e[(dl >= a) & (dl < b)]) if ((dl >= a) & (dl < b)).sum() > 100 else np.nan
               for a, b in zip(edges[:-1], edges[1:])]
        ax[2].plot(edges[:-1] + 0.5, med, "o-", color=col, ms=4, lw=1, label=lab)
    ax[2].axhline(0, color="k", lw=0.5)
    ax[2].set(xlabel="actual delay (ns)", ylabel="median residual, record - model (V)",
              title="(c) the residual by delay: a late swing start plus a loss")
    ax[2].legend(fontsize=8)
    fd = d["post_hoc"]["fixed_delay_where_learner_off_by_2ns"]
    names = ("p50", "p90", "p99")
    x = np.arange(3)
    ax[3].bar(x - 0.18, fd["recorded_vds_p50_p90_p99_v"], 0.34, color=REC, label="learner (recorded)")
    ax[3].bar(x + 0.18, fd["fixed_vds_p50_p90_p99_v"], 0.34, color=MODEL, label="one delay per board (corrected D57)")
    ax[3].set_xticks(x); ax[3].set_xticklabels(names)
    ax[3].set(ylabel="V_DS at the turn-on (V)",
              title=f"(d) where the learner is > 2 ns off ({fd['rows']} turn-ons, {fd['learner_shorter']:.0%} shorter)")
    ax[3].legend(fontsize=8)
    fig.suptitle("A247: the soft turn-on window against the low-side turn-off current (plant V7 records A229-A246, D57)")
    fig.tight_layout()
    fig.savefig(HERE / "a247_zvs_window.png", dpi=110)


if __name__ == "__main__":
    main()
