"""Report figures from the archived records (no new runs). Every figure is a simulation result; the source experiment
is in each function's docstring. Run records (experiments/*/cosim/run_*.json) are local or in the GitHub releases
records-aXXX; summaries are in the repository.
  PYTHONPATH=src python3 reports/figures/make_figures.py [name ...]   -> reports/figures/fig_<name>.png"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
TC = ROOT / "experiments" / "track_C_multi_module"
ML = ROOT / "extensions" / "ml_design_assist" / "experiments"
BLUE, ORANGE, GREY, RED, GREEN = "#0F477E", "#EE7D11", "#7F7F7F", "#C0392B", "#2E8B57"
PH = ["#0F477E", "#EE7D11", "#2E8B57", "#8E44AD"]          # phases 1-4, the same everywhere
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.dpi": 100, "savefig.dpi": 200, "font.family": "DejaVu Sans"})


def one(pattern):
    f = glob.glob(str(pattern))
    assert f, pattern
    return Path(sorted(f)[0])


def load(pattern):
    return json.loads(one(pattern).read_text())


def save(fig, name):
    fig.tight_layout()
    fig.savefig(HERE / f"fig_{name}.png")
    plt.close(fig)
    print("fig_" + name)


def zvs():
    """High-side turn-on V_DS and efficiency against the negative-current target. A110 (5 MHz, closed loop, six targets),
    the 2 % point from D51's orbit (event map), the energy balance's 26.7 % from D57. Two figures."""
    s = load(TA / "A110_*" / "*summary*.json")
    pct = [5, 10, 15, 20, 25, 30]
    v = np.array([s[f"n{p}"]["hs_on_vds_v"] for p in pct])
    eff = [s[f"n{p}"]["efficiency_pct"] for p in pct]
    d51 = json.loads((ROOT / "symbolic_derivations/03_P24_native/diagnostics/D51_orbit_2p0pct_m0p0.json").read_text())
    fig, a = plt.subplots(figsize=(7.4, 4.6))
    a.axvspan(1, 2, color=ORANGE, alpha=0.25, lw=0)
    a.text(1.5, 11.6, "P24:\n1-2 %", ha="center", va="top", color=ORANGE, fontsize=10, fontweight="bold")
    a.errorbar(pct, v.mean(1), yerr=[v.mean(1) - v.min(1), v.max(1) - v.mean(1)], fmt="o-", color=BLUE, capsize=3,
               label="closed-loop co-simulation\n(mean and range of 4 phases)")
    a.plot([2], [np.mean(d51["turnon_vds"])], "s", color=GREEN, ms=7, label="event-map model at 2 %")
    a.axvline(26.7, color=GREY, ls="--", lw=1.2)
    a.text(27.0, 5.2, "energy\nbalance:\n26.7 %", color=GREY, fontsize=9.5)
    a.axhline(0, color="k", lw=0.8)
    a.annotate("first zero voltage: 25 %", (25, v[4].mean()), (13.0, 1.0), arrowprops={"arrowstyle": "->", "color": BLUE},
               color=BLUE, fontsize=10)
    a.annotate("30 %: node clamps at the rail,\nvalley timing fails (236 A)", (30, v[5].mean()), (14.0, -2.7),
               arrowprops={"arrowstyle": "->", "color": RED}, color=RED, fontsize=9.5)
    a.set(xlabel="negative-current target (% of the 125 A peak)", ylabel="high-side V_DS at turn-on (V)", xlim=(0, 32),
          ylim=(-3.2, 12), title="Turn-on voltage of the high side")
    a.legend(loc="upper left", fontsize=9, frameon=False, bbox_to_anchor=(0.33, 1.0))
    fig.text(0.01, 0.005, "Simulation, 5 MHz design, 25 °C, ideal switches + datasheet Coss. Sources: A110, D51, D57.",
             fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "zvs_turn_on_voltage")
    fig, b = plt.subplots(figsize=(6.2, 4.4))
    b.plot(pct, eff, "o-", color=BLUE)
    b.annotate("best: 20 %\n(+2.25 points)", (20, eff[3]), (8.5, 90.25), arrowprops={"arrowstyle": "->", "color": BLUE},
               color=BLUE, fontsize=10)
    b.set(xlabel="negative-current target (%)", ylabel="estimated efficiency (%)", xlim=(0, 32), ylim=(87.5, 90.6),
          title="Efficiency (loss model on the waveforms)")
    fig.text(0.01, 0.005, "Simulation, 5 MHz design, inductor at 79 µΩ/nH. Sources: A110, D62.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "zvs_efficiency")


def scaling():
    """Needed negative current against sqrt(L C_node) / Ton for the two papers' operating points (A67's table)."""
    fig, a = plt.subplots(figsize=(6.6, 4.3))
    x = np.logspace(-2.2, -0.3, 50)
    a.loglog(x * 100, x * 100, "-", color=GREY, lw=1.2, label=r"needed fraction $\approx \sqrt{L\,C_{node}}\,/\,T_{on}$")
    for name, flip, ton, need, said, c in (("P25 prototype\n12 V, 0.5 MHz", (6.7, 9.0), 500.0, (1.5, 2.0), (5, 10), GREEN),
                                           ("P24 design point\n48 V, 5 MHz", (3.7, 4.4), 16.7, (22, 26), (1, 2), RED)):
        xs = [100 * f / ton for f in flip]
        a.fill_between(xs, [need[0]] * 2, [need[1]] * 2, color=c, alpha=0.85, lw=0)
        a.fill_between([xs[0] * 0.8, xs[1] * 1.25], [said[0]] * 2, [said[1]] * 2, color=ORANGE, alpha=0.35, lw=0)
        a.text(np.mean(xs) * 1.45, np.mean(need), f"needs {need[0]}-{need[1]} %", color=c, fontsize=10, va="center")
        a.text(np.mean(xs) * 1.45, np.sqrt(said[0] * said[1]), f"paper: {said[0]}-{said[1]} %", color=ORANGE, fontsize=10,
               va="center")
        a.text(np.mean(xs), 0.62, name, ha="center", va="bottom", fontsize=9.5)
    a.set(xlabel=r"$\sqrt{L\,C_{node}}\,/\,T_{on}$  (%)", ylabel="negative current, % of the peak", xlim=(0.6, 60),
          ylim=(0.55, 60), title="One scaling law for both papers")
    a.legend(loc="upper left", fontsize=9, frameon=False)
    fig.text(0.01, 0.005, "Source: A67 (flip time 6.7-9.0 ns / 500 ns; 3.7-4.4 ns / 16.7 ns).", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "scaling_law")


def losses():
    """Loss breakdown per module at 5 / 2.5 / 1 MHz (D62's budget on the simulated waveforms: A110 n5 and n20, A124,
    A115 n10) and the 2.5 MHz efficiency as its inductor assumptions were checked (D72, D76). Two figures."""
    a110 = load(TA / "A110_*" / "*summary*.json")
    rows = [("5 MHz\n5 % neg. current", a110["n5"]["budget_w"]), ("5 MHz\n20 %", a110["n20"]["budget_w"]),
            ("2.5 MHz\n12.5 %", load(TA / "A124_*" / "*summary*.json")["p125_n0"]["budget_w"]),
            ("1 MHz\n10 %", load(TA / "A115_*" / "*summary*.json")["n10"]["budget_w"])]
    n = len(rows)
    parts = [("switch conduction", ("switch_conduction",), BLUE), ("inductor copper", ("inductor_copper",), ORANGE),
             ("series capacitors", ("series_caps",), GREY),
             ("switching (hard turn-on, turn-off, gate)", ("hard_turn_on", "turn_off_overlap", "gate_drive"), RED)]
    fig, a = plt.subplots(figsize=(7.4, 4.7))
    bot = np.zeros(n)
    for lab, keys, c in parts:
        h = np.array([sum(r[1][k] for k in keys) for r in rows])
        a.bar(range(n), h, bottom=bot, color=c, label=lab, width=0.6)
        for i, (hh, bb) in enumerate(zip(h, bot)):
            if hh > 1.2:
                a.text(i, bb + hh / 2, f"{hh:.1f}", ha="center", va="center", color="w", fontsize=9.5, fontweight="bold")
        bot += h
    for i, r in enumerate(rows):
        a.text(i, bot[i] + 0.6, f"{bot[i]:.1f} W\n{100 * r[1]['efficiency']:.1f} %", ha="center", fontsize=10)
    a.set_xticks(range(n))
    a.set_xticklabels([r[0] for r in rows])
    a.set(ylabel="loss per 250 W module (W)", ylim=(0, 50), title="Where the loss goes (inductor at 79 µΩ/nH)")
    a.legend(fontsize=8.5, frameon=False, loc="upper center", ncol=2)
    a.grid(axis="x", visible=False)
    fig.text(0.01, 0.005, "Simulated waveforms + loss model, 25 °C, ideal edges, no package. Sources: D62, A110, A115, A124.",
             fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.2)
    save(fig, "loss_breakdown")
    steps = [("first estimate\n(500 nH-unit R/L)", 90.6, 90.6), ("current-rated\ninductor array", 86.6, 87.7),
             ("+ core loss", 78.0, 85.0)]
    fig, b = plt.subplots(figsize=(6.6, 4.5))
    for i, (lab, lo, hi) in enumerate(steps):
        b.bar(i, hi - lo if hi > lo else 0.25, bottom=lo, color=BLUE if i == 0 else ORANGE, width=0.5)
        b.text(i, hi + 0.35, f"{lo:g} %" if hi == lo else f"{lo:g}-{hi:g} %", ha="center", fontsize=10.5)
    b.set_xticks(range(3))
    b.set_xticklabels([s[0] for s in steps])
    b.set(ylabel="estimated efficiency (%)", ylim=(76, 93), title="2.5 MHz design: the number after two checks")
    b.grid(axis="x", visible=False)
    fig.text(0.01, 0.005, "Per module, 25 °C, before package and gate-edge losses. Sources: A124, D72, D76.", fontsize=8,
             color=GREY)
    fig.subplots_adjust(bottom=0.2)
    save(fig, "efficiency_checks")


def _step_panel(ax_v, ax_i, path, title):
    r = json.loads(Path(path).read_text())
    ts = r["cfg"]["load_step"]["t_us"]
    sec = [(q["t_s"] * 1e6 - ts, (q["vo"] - 1.0) * 1e3) for q in r["sections"] if ts - 10 <= q["t_s"] * 1e6 <= ts + 40]
    ax_v.plot(*zip(*sec), color=BLUE, lw=1.3)
    ax_v.axhspan(-10, 10, color=GREEN, alpha=0.12, lw=0)
    ax_v.set(ylabel="Vo - 1 V (mV)", title=title, ylim=(-22, 22))
    for ph in range(1, 5):
        pts = [(e["t_s"] * 1e6 - ts, e["i_a"]) for e in r["highoffs_last"] if e["phase"] == ph and ts - 10 <= e["t_s"] * 1e6 <= ts + 40]
        ax_i.plot(*zip(*pts), ".", ms=3, color=PH[ph - 1], label=f"phase {ph}")
    ax_i.axhline(200, color=RED, ls="--", lw=1.2)
    ax_i.set(xlabel="time after the load step (µs)", ylabel="peak current at turn-off (A)", ylim=(60, 210), xlim=(-10, 40))


def load_step():
    """Frozen single-module design (A143, lo_learn 4), +-62.5 A load steps: Vo and each phase's turn-off current, one
    point per switching period."""
    d = one(TA / "A143_*") / "cosim"
    fig, ax = plt.subplots(2, 2, figsize=(11, 5.6), sharex=True)
    _step_panel(ax[0, 0], ax[1, 0], d / "run_g4_s100_s_p62_k4.json", "+62.5 A load step")
    _step_panel(ax[0, 1], ax[1, 1], d / "run_g4_s100_s_m62_k4.json", "-62.5 A load step")
    ax[1, 0].legend(fontsize=8.5, ncol=4, frameon=False, loc="lower right", markerscale=3)
    ax[1, 1].text(39, 202, "200 A budget", color=RED, ha="right", va="bottom", fontsize=9)
    ax[0, 1].text(39, 11, "±1 % band", color=GREEN, ha="right", va="bottom", fontsize=9)
    fig.text(0.01, 0.005, "Co-simulation (Verilog controller + circuit), one module, 2.5 MHz, 25 °C, ideal switches, no package. "
             "One point per switching period. Source: A143.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.12)
    save(fig, "load_step")


def overshoot():
    """Largest switch V_DS after +4.8 V / 1 us against x = L_loop x di/dt_on (D68's collapse; rows from A145, A151,
    A152 in diagnostics/D68_slow_turn_on.json)."""
    d = json.loads((ROOT / "diagnostics" / "D68_slow_turn_on.json").read_text())
    fig, a = plt.subplots(figsize=(7.2, 4.4))
    mk = {50: "o", 100: "s", 150: "^"}
    for l in (50, 100, 150):
        pts = [(r["x_v"], r["vds_max_v"]) for r in d["overshoot_rows"] if r["l_ph"] == l]
        a.plot(*zip(*sorted(pts)), mk[l], ms=8, color={50: BLUE, 100: ORANGE, 150: GREEN}[l], label=f"loop {l} pH", ls="")
    c = d["overshoot_curve"]
    a.plot([p[0] for p in c], [p[1] for p in c], "-", color=GREY, lw=1.2, zorder=0)
    a.axhline(40, color=RED, ls="--", lw=1.2)
    a.text(0.75, 40.4, "EPC2067 rating, 40 V", color=RED, fontsize=9.5)
    a.axvline(d["x_star_v"], color=GREY, ls=":", lw=1.2)
    a.text(d["x_star_v"] + 0.1, 33.3, f"limit: {d['x_star_v']:.1f} V", color=GREY, fontsize=9.5)
    a.set(xlabel=r"$L_{loop} \times (di/dt)_{turn\text{-}on}$  (V)", ylabel="largest switch V_DS (V)",
          title="Overshoot after a +4.8 V / 1 µs input step", xlim=(0.6, 7.6), ylim=(33, 52))
    a.legend(fontsize=9.5, frameon=False, loc="lower right")
    fig.text(0.01, 0.005, "Co-simulation with loop inductance (ring Q 7) and linear-ramp edges, turn-off 72 A/ns. Sources: A145, "
             "A151, A152, D68.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "overshoot_law")


def copper():
    """Lateral output / ground copper loss per 250 W module against the copper thickness per layer (D65: 30.7 W at
    35 um, inversely proportional to the thickness)."""
    t = np.logspace(np.log10(25), np.log10(600), 100)
    p = 30.7 * 35.0 / t
    fig, a = plt.subplots(figsize=(7.2, 4.4))
    a.loglog(t, p / 250 * 100, color=BLUE, lw=1.8)
    for tt, lab in ((35, "35 µm: 12.3 %\n(30.7 W)"), (86, "86 µm: 5 %"), (429, "429 µm: 1 %")):
        y = 30.7 * 35 / tt / 250 * 100
        a.plot([tt], [y], "o", color=ORANGE, ms=8)
        a.text(tt * 1.12, y * 1.08, lab, fontsize=10, color=ORANGE)
    a.axhline(25.9 / 250 * 100, color=GREY, ls="--", lw=1.2)
    a.text(120, 25.9 / 250 * 100 * 1.07, "the converter's own loss (25.9 W)", fontsize=9.5, color=GREY)
    a.set(xlabel="copper thickness per layer (µm)", ylabel="lateral copper loss (% of 250 W)", xlim=(25, 600), ylim=(0.6, 25),
          title="Output routing of P24 Fig. 5: lateral copper loss")
    a.set_xticks([35, 86, 200, 429])
    a.set_xticklabels(["35", "86", "200", "429"])
    a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a.set_yticks([1, 2, 5, 10, 20])
    a.set_yticklabels(["1", "2", "5", "10", "20"])
    fig.text(0.01, 0.005, "First-principles budget on the steady waveforms, one layer each way. Source: D65.", fontsize=8,
             color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "copper_loss")


def _startup_panel(ax_r, ax_i, path, title):
    r = json.loads(Path(path).read_text())
    t = np.array([q["t_s"] for q in r["sections"]]) * 1e6
    vin = np.array([q["vin_v"] for q in r["sections"]])
    vc = np.array([q["vcs_v"] for q in r["sections"]])
    rails = [vin - vc[:, 0], vc[:, 0] - vc[:, 1], vc[:, 1] - vc[:, 2], vc[:, 2]]
    m = t <= 200
    for k in range(4):
        ax_r.plot(t[m], rails[k][m], color=PH[k], lw=1.3, label=f"rail {k + 1}")
    tp = r["t_mode_p_s"] * 1e6
    for a in (ax_r, ax_i):
        a.axvline(tp, color=GREY, ls=":", lw=1.2)
    ax_r.set(ylabel="rail voltage (V)", title=title, ylim=(0, 18))
    ev = r.get("gate_offs_last") or r["highoffs_last"]
    key = "i_max_a" if "i_max_a" in ev[0] else "i_a"
    for ph in range(1, 5):
        pts = [(e["t_s"] * 1e6, e[key]) for e in ev if e["phase"] == ph and e["t_s"] * 1e6 <= 200]
        ax_i.plot(*zip(*pts), ".", ms=2.5, color=PH[ph - 1])
    ax_i.axhline(200, color=RED, ls="--", lw=1.2)
    ax_i.set(xlabel="time (µs)", ylabel="peak current (A)", ylim=(0, 300), xlim=(0, 200))
    return tp


def startup():
    """Start-up of the slow-device, L x 0.75 board at 25 C before (A181: 400 ns open-loop period) and after (A185: 200 ns,
    own trim, bumpless seed): the four rail voltages and each phase's peak current. Three figures."""
    before = one(TA / "A181_*") / "cosim" / "run_S75_25_p0.json"
    after = one(TA / "A185_*") / "cosim" / "run_S75_25_p0.json"
    note = "Co-simulation, final plant (gate-level EPC2067 model), slow devices, L x 0.75, 25 °C. Rails ideal: 12 V each."
    fig, ax = plt.subplots(2, 2, figsize=(11, 5.8), sharex=True)
    _startup_panel(ax[0, 0], ax[1, 0], before, "before: open-loop period 400 ns")
    tp = _startup_panel(ax[0, 1], ax[1, 1], after, "after: 200 ns + own trim + bumpless seed")
    ax[0, 0].legend(fontsize=8.5, ncol=4, frameon=False, loc="upper left")
    ax[0, 1].text(tp + 2, 16.3, "handover to\nclosed loop", color=GREY, fontsize=9, va="top")
    ax[1, 0].text(4, 206, "200 A budget", color=RED, fontsize=9, va="bottom")
    fig.text(0.01, 0.005, note + " Sources: A181, A185.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.12)
    save(fig, "startup_before_after")
    for name, path, title, src in (("startup_before", before, "before: open-loop period 400 ns", "A181"),
                                   ("startup_after", after, "after: 200 ns + own trim + bumpless seed", "A185")):
        fig, ax = plt.subplots(2, 1, figsize=(6.4, 6.2), sharex=True)
        tp = _startup_panel(ax[0], ax[1], path, title)
        ax[0].legend(fontsize=8.5, ncol=4, frameon=False, loc="upper left")
        ax[0].text(tp + 2, 3.2, "handover to\nclosed loop", color=GREY, fontsize=9, va="top")
        ax[1].text(4, 206, "200 A budget", color=RED, fontsize=9, va="bottom")
        fig.text(0.01, 0.005, f"Co-simulation, final plant, slow devices, L x 0.75, 25 °C. Source: {src}.", fontsize=8, color=GREY)
        fig.subplots_adjust(bottom=0.11)
        save(fig, name)


def sharing():
    """Four modules: the largest post-step peak against the inductor spread (C14 co-simulation; D66's estimate)."""
    c = load(TC / "C14_*" / "*summary.json")["runs"]
    grp = [("nominal", "nom"), ("±5 %\nworst case", "w5"), ("one module\n-10 %", "o10"), ("±10 %\nworst case", "w10")]
    val = []
    for _, k in grp:
        val.append(max(v["peak_post"] for kk, v in c.items() if kk.startswith(k + "_") and v.get("peak_post")))
    fig, a = plt.subplots(figsize=(6.8, 4.3))
    a.bar(range(4), val, color=[BLUE, BLUE, ORANGE, RED], width=0.55)
    for i, v in enumerate(val):
        a.text(i, v + 1.2, f"{v:.1f} A", ha="center", fontsize=10.5)
    a.axhline(200, color=RED, ls="--", lw=1.2)
    a.text(-0.4, 201, "200 A budget", color=RED, fontsize=9.5, va="bottom")
    a.set_xticks(range(4))
    a.set_xticklabels([g[0] for g in grp])
    a.set(ylabel="largest peak current after a step (A)", ylim=(150, 216),
          title="Passive sharing: the smaller-L module binds the peak")
    a.grid(axis="x", visible=False)
    fig.text(0.01, 0.005, "Co-simulation, four modules, common on-time, 25 °C, ideal switches. Sources: C14, D66.", fontsize=8,
             color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "current_sharing")


def interleave():
    """16-phase output-current ripple before / after referencing every slot to phase 1's low-side turn-off (C01, C02)."""
    r = load(TC / "C01_*" / "c01_summary.json")["m4_n0"]["ripple"]
    val = [("no module\ninterleave", r["no_module_interleave"]["rms_ac_a"], GREY),
           ("first design\n(9.4 ns slot offset)", r["actual"]["rms_ac_a"], RED), ("slots referenced to\nphase 1's turn-off", 6.75, BLUE),
           ("ideal uniform\ngrid", r["uniform"]["rms_ac_a"], GREEN)]
    fig, a = plt.subplots(figsize=(6.8, 4.3))
    a.bar(range(4), [v[1] for v in val], color=[v[2] for v in val], width=0.55)
    for i, v in enumerate(val):
        a.text(i, v[1] + 2, f"{v[1]:.1f} A", ha="center", fontsize=10.5)
    a.set_xticks(range(4))
    a.set_xticklabels([v[0] for v in val], fontsize=9.5)
    a.set(ylabel="output current ripple (A rms, on 1 kA)", ylim=(0, 128), title="16 phases: a small slot error becomes a large ripple")
    a.grid(axis="x", visible=False)
    fig.text(0.01, 0.005, "Co-simulation, four modules, 5 MHz design. Sources: C01, C02.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.2)
    save(fig, "interleave_ripple")


def feedforward():
    """Post-step peak current per input row without (A124) and with (A129) the Vin feed-forward and its slope gate."""
    s = load(ML / "A129_*" / "*summary*.json")["stage1"]
    rows = [("p125_l_p48_1us", "+4.8 V\n1 µs"), ("p125_l_m48_1us", "-4.8 V\n1 µs"), ("p125_l_p48_5us", "+4.8 V\n5 µs"),
            ("p125_l_m48_5us", "-4.8 V\n5 µs"), ("p125_l_m80_10us", "-8 V\n10 µs"), ("p125_s_p62", "+62.5 A\nload"),
            ("p125_s_m62", "-62.5 A\nload")]
    rows = [(k, lab) for k, lab in rows if k in s and s[k].get("a124_peak_a")]
    x = np.arange(len(rows))
    fig, a = plt.subplots(figsize=(8.2, 4.3))
    a.bar(x - 0.2, [s[k]["a124_peak_a"] for k, _ in rows], 0.38, color=GREY, label="without feed-forward")
    a.bar(x + 0.2, [s[k]["peak_after_a"] for k, _ in rows], 0.38, color=BLUE, label="with feed-forward")
    for i, (k, _) in enumerate(rows):
        a.text(i - 0.2, s[k]["a124_peak_a"] + 1.5, f"{s[k]['a124_peak_a']:.0f}", ha="center", fontsize=9)
        a.text(i + 0.2, s[k]["peak_after_a"] + 1.5, f"{s[k]['peak_after_a']:.0f}", ha="center", fontsize=9, color=BLUE)
    a.axhline(200, color=RED, ls="--", lw=1.2)
    a.text(len(rows) - 0.55, 201, "200 A", color=RED, fontsize=9.5, va="bottom", ha="right")
    a.set_xticks(x)
    a.set_xticklabels([lab for _, lab in rows])
    a.set(ylabel="peak current after the step (A)", ylim=(140, 228), title="Input feed-forward (learned, then reduced to a 6-parameter rule)")
    a.legend(fontsize=9.5, frameon=False, loc="upper right")
    a.grid(axis="x", visible=False)
    fig.text(0.01, 0.005, "Co-simulation, one module, 2.5 MHz, 25 °C, ideal switches. Sources: A124, A128, A129.", fontsize=8,
             color=GREY)
    fig.subplots_adjust(bottom=0.2)
    save(fig, "feedforward")


def ring():
    """Single-edge harness (A145 / A151): phase 1's high side turned on hard at 17 V (its state after a +4.8 V / 1 us
    step, A147) and the next high side's V_DS, for a fast (72 A/ns) and a slowed (36 A/ns) turn-on. Loop 50 pH, ring Q 7."""
    import dataclasses
    sys.path.insert(0, str(one(TA / "A145_*")))
    import a145_edge as E
    from scb_ivr.cosim.circuit import Sim

    fig, a = plt.subplots(figsize=(7.2, 4.4))
    for didt, c, lab in ((72, RED, "fast turn-on, 72 A/ns"), (36, BLUE, "slowed turn-on, 36 A/ns")):
        p = dataclasses.replace(E.params(50, E.q_rp(50e-12, 7), 10e-12), edge_didt_off=72e9, edge_didt_on=didt * 1e9)
        y = E.y0(p, 0.0)
        s = Sim(p)
        a1 = 48.0 - 17.0
        y[s.idx["a1"]], y[s.idx["x1"]] = a1, a1 - E.VCS[0]
        if s.nlp:
            y[s.idx["h2"]] = a1
            y[s.nv + 4 + s.na] = 0.0
        pl, tr, ts, el, st = E.run_edge(p, y, [False] * 4, [False, True, True, True], None, 0, True, (0, 1), E.FastPlant)
        a.plot(ts * 1e9, tr[1], color=c, lw=1.6, label=f"{lab}: peak {tr[1].max():.1f} V")
    a.axhline(40, color=RED, ls="--", lw=1.2)
    a.text(0.3, 40.5, "EPC2067 rating, 40 V", color=RED, fontsize=9.5)
    a.set(xlabel="time after the turn-on command (ns)", ylabel="V_DS of the next high side (V)", xlim=(0, 20),
          title="Mechanism: a hard turn-on rings the next high-side switch", ylim=(8, 44))
    a.legend(fontsize=9.5, frameon=False, loc="lower right")
    fig.text(0.01, 0.005, "Single-edge model, 50 pH, Q 7. Mechanism only: the full co-simulation gives 41.8 V and 37.1 V. "
             "Sources: A145, A151.", fontsize=8, color=GREY)
    fig.subplots_adjust(bottom=0.17)
    save(fig, "overshoot_waveform")


FIGS = {f.__name__: f for f in (zvs, scaling, losses, load_step, overshoot, copper, startup, sharing, interleave, feedforward,
                                ring)}

if __name__ == "__main__":
    for n in (sys.argv[1:] or FIGS):
        FIGS[n]()
