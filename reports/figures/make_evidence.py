"""Evidence figures: each problem the report names, drawn from the archived record in which it was seen, next to the
record after the fix where one exists (no new runs). Every panel carries its record's file name. The co-simulation
stores one point per switching period, so these are per-period traces, not waveforms inside a period.
  PYTHONPATH=src python3 reports/figures/make_evidence.py [name ...]   -> reports/figures/fig_ev_<name>.png"""
from __future__ import annotations

import sys

from make_figures import BLUE, GREEN, GREY, HERE, ORANGE, PH, RED, TA, json, np, one, plt

OLD = ("Co-simulation (Verilog controller + circuit), one module, 5 MHz design, 5 % negative current, 25 °C, ideal "
       "switches with datasheet Coss.")
NEW = "Co-simulation (Verilog controller + circuit), one module, 2.5 MHz design, 12.5 % negative current, 25 °C"
SIZE = (8.6, 4.5)                                             # landscape: the slide body beside the text is about 7 x 3.7 in


def rec(exp, run, sub="cosim"):
    """A run record and its label 'A92 run_<name>.json'."""
    p = one(TA / f"{exp}_*") / sub / f"run_{run}.json"
    return json.loads(p.read_text()), f"{exp} {p.name}"


def done(fig, name, foot, top=1.0):
    """Footer (conditions and sources) under the axes, then save as fig_ev_<name>.png."""
    fig.text(0.01, 0.008, foot, fontsize=7.5, color=GREY, wrap=True)
    fig.tight_layout(rect=(0, 0.075, 1, top))
    fig.savefig(HERE / f"fig_ev_{name}.png")
    plt.close(fig)
    print("fig_ev_" + name)


def tag(ax, name):
    """The record's file name under the panel."""
    ax.text(0.5, -0.205, name, transform=ax.transAxes, ha="center", va="top", fontsize=6.8, color=GREY, family="monospace")


def points(r, t0, t1):
    """(t_us, phase, current) once per switching period in [t0, t1] us, and whether the current is a section sample:
    the physical channel turn-off current of gate-driven runs, the turn-off command current where the record logs
    turn-offs (A103 on), else the section sample of the four inductor currents (A77-A99; ipk_a is quoted with it)."""
    ev = r.get("gate_offs_last") or r.get("highoffs_last")
    if ev:
        key = "i_max_a" if "i_max_a" in ev[0] else "i_a"
        return [(e["t_s"] * 1e6, e["phase"], e[key]) for e in ev if t0 <= e["t_s"] * 1e6 <= t1], False
    return [(q["t_s"] * 1e6, k + 1, q["i"][k]) for q in r["sections"] for k in range(4) if t0 <= q["t_s"] * 1e6 <= t1], True


def marks(ax, r, t0, t1):
    """Dotted lines at the handover to closed loop and at the registered step, where they fall inside the window."""
    c = r["cfg"]
    st = c.get("line_step") or c.get("load_step")
    for t, lab in (((r.get("t_mode_p_s") or 0) * 1e6, "handover"), (st["t_us"] if st else None, "step")):
        if t and t0 < t < t1:
            ax.axvline(t, color=GREY, ls=":", lw=1.2)
            ax.text(t, 0.02, " " + lab, color=GREY, fontsize=8, va="bottom", transform=ax.get_xaxis_transform())


def panel(ax, exp, run, t0, t1, title, sub="cosim", ylim=(0, 300), limit=200, stop=None, peak=False, since=None):
    """One record's per-period currents in [t0, t1] us, its largest value (from `since` us on) marked; `stop` names an
    overlap stop; `peak` adds the run's largest inductor current (the turn-off command comes a driver delay before it)."""
    r, name = rec(exp, run, sub)
    pts, old = points(r, t0, t1)
    for ph in range(1, 5):
        q = [(t, i) for t, p, i in pts if p == ph]
        ax.plot(*zip(*q), ".", ms=3, color=PH[ph - 1], label=f"phase {ph}")
    t, ph, i = max((q for q in pts if q[0] >= (since or t0)), key=lambda q: q[2])
    over = (r["ipk_a"] if old or peak else i) > limit
    kw = dict(ha="right", va="top", color=RED if over else BLUE, fontsize=10, fontweight="bold")
    if old:
        ax.text(0.98, 0.97, f"largest current\nin the run: {r['ipk_a']:.1f} A", transform=ax.transAxes, **kw)
    else:
        ax.annotate(f"{i:.1f} A (phase {ph})" + (f"\ninductor peak {r['ipk_a']:.1f} A" if peak else ""), (t, min(i, ylim[1])),
                    (0.98, 0.97), textcoords="axes fraction", arrowprops={"arrowstyle": "->", "color": kw["color"]}, **kw)
    if limit:
        ax.axhline(limit, color=RED, ls="--", lw=1.2)
    marks(ax, r, t0, t1)
    if stop:
        ts = r["first_overlap"]["t_s"] * 1e6
        ax.axvline(ts, color=RED, lw=1.6)
        ax.text(ts, ylim[0] + 0.24 * (ylim[1] - ylim[0]), " " + stop, color=RED, fontsize=9, va="center")
    ax.set(title=title, xlabel="time (µs)", xlim=(t0, t1), ylim=ylim)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5, prune="both"))
    ax.title.set_fontsize(10)
    tag(ax, name)


def row(name, runs, t0, t1, foot, **kw):
    """Panels of `runs` (exp, run, title[, panel keywords]) side by side on one current axis; saved as fig_ev_<name>."""
    fig, ax = plt.subplots(1, len(runs), figsize=SIZE, sharey=True)
    for a, run in zip(ax, runs):
        panel(a, run[0], run[1], t0, t1, run[2], **{**kw, **(run[3] if len(run) > 3 else {})})
    ax[0].set_ylabel("current (A)")
    fig.legend(*ax[0].get_legend_handles_labels(), fontsize=8.5, ncol=4, frameon=False, loc="upper center", markerscale=3)
    done(fig, name, foot, top=0.95)


def shoot_through():
    """A89: the predicted low-side turn-on without blanking (r1, 773.6 A) and with 20 ns of blanking (r2)."""
    row("shoot_through", [("A89", "r1_device_low_pred", "predicted low-side turn-on, no blanking"),
                          ("A89", "r2_device_low_pred_blank", "the same with 20 ns of blanking")], 85, 115,
        OLD + " Points: each phase's inductor current, sampled once per period. Source: A89.", ylim=(-50, 500))


def mismatch():
    """A91 / A92: how far each run got before the overlap detector stopped it (both switches of one phase on),
    against the driver's high-side / low-side delay mismatch; A91 = corrector on the command time, A92 = on the error."""
    rows = [("-3.4 ns", "m3n_s45_startup_dead_4p5ns", "m3n_mismatch_minus3p4ns"),
            ("-1 ns", "m1n_mismatch_minus1ns", "m1n_mismatch_minus1ns"), ("+1 ns", "m1p_mismatch_plus1ns", "m1p_mismatch_plus1ns"),
            ("+3.4 ns", "m3p_s45_startup_dead_4p5ns", "m3p_mismatch_plus3p4ns")]
    fig, a = plt.subplots(figsize=SIZE)
    for k, (lab, r91, r92) in enumerate(rows):
        for exp, run, dy, c in (("A91", r91, 0.2, GREY), ("A92", r92, -0.2, BLUE)):
            r, _ = rec(exp, run)
            end = r["sections"][-1]["t_s"] * 1e6
            a.barh(k + dy, end, 0.36, color=c, label={"A91": "before: correction added to the command time (A91)",
                                                      "A92": "after: correction on the measured error (A92)"}[exp] if k == 0 else None)
            fo = r["first_overlap"]
            if fo:
                a.plot([end], [k + dy], "X", color=RED, ms=11)
                a.text(end + 8, k + dy, f"stopped at {fo['t_s'] * 1e6:.1f} µs: phase {fo['phase']}, both switches on",
                       color=RED, fontsize=9.5, va="center")
            else:
                a.text(end - 6, k + dy, f"completed, {r['overlaps']} overlaps", color="w", fontsize=9.5, va="center", ha="right")
    a.set_yticks(range(4))
    a.set_yticklabels([r[0] for r in rows])
    a.set(xlabel="time the run reached (µs)", ylabel="high-side minus low-side\ndriver delay", xlim=(0, 400),
          title="Driver delay mismatch: where the run stopped")
    a.grid(axis="y", visible=False)
    a.legend(fontsize=8.5, frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.15), ncol=2)
    done(fig, "mismatch", OLD + " Start-up dead time 4.5 ns (2.15 ns on A91's ±1 ns rows). Records: A91 / A92 run_m*.json.")


def slots():
    """A92 / A93 / A97, driver mismatch -3.4 ns: fixed slots (826.9 A), slots following the measured period, slots
    from the two-period average."""
    row("slots", [("A92", "m3n_mismatch_minus3p4ns", "fixed slots for phases 2-4"),
                  ("A93", "m3n_both", "slots follow the measured period"),
                  ("A97", "m3n_avg_guard", "slots from a two-period average")], 85, 125,
        OLD + " Driver mismatch -3.4 ns. Points: each phase's inductor current, sampled once per period. Sources: A92, A93, A97.",
        ylim=(-50, 450))


def startup_vo():
    """A103: Vo during start-up with the load arriving at the handover (c0) and with the load from t = 0, the handover
    at 72 us and the retuned on-time (c1d)."""
    fig, a = plt.subplots(figsize=SIZE)
    for run, c, lab in (("c0_reference", RED, "open loop without load, load at the handover"),
                        ("c1d_load_from_0_hand_72_ton568", BLUE, "load from t = 0 (sequence changed only)")):
        r, name = rec("A103", run)
        t = np.array([q["t_s"] for q in r["sections"]]) * 1e6
        v = np.array([q["vo"] for q in r["sections"]])
        m = t <= 300
        a.plot(t[m], v[m], color=c, lw=1.6, label=f"{lab}\n{name}")
        a.axvline(r["t_mode_p_s"] * 1e6, color=c, ls=":", lw=1.1)
        for k in ((int(np.argmax(v)), int(np.argmin(np.where(t > r["t_mode_p_s"] * 1e6, v, 9)))) if c == RED else (int(np.argmax(v)),)):
            a.annotate(f"{v[k]:.3f} V", (t[k], v[k]), (t[k] + 22, v[k] + (0.04 if v[k] > 1 else -0.05)), color=c, fontsize=11,
                       fontweight="bold", arrowprops={"arrowstyle": "->", "color": c})
    a.axhspan(0.99, 1.01, color=GREEN, alpha=0.15, lw=0)
    a.text(298, 1.012, "±1 % band", color=GREEN, ha="right", va="bottom", fontsize=9)
    a.set(xlabel="time (µs)", ylabel="output voltage (V)", xlim=(0, 300), ylim=(0, 1.4), title="Start-up: the output voltage")
    a.legend(fontsize=8.5, frameon=False, loc="lower right")
    done(fig, "startup_vo", OLD + " Dotted: each run's handover to closed loop. Source: A103.")


def line_step():
    """A106 / A109: +4.8 V in 1 us at 400 us on the integrated single module (206.6 A), and the same row with the valley
    trim of the slotted phases (still above 200 A: the hypothesis was falsified)."""
    row("line_step", [("A106", "pi100_p48_1us", "+4.8 V in 1 µs: phase 1 above the budget"),
                      ("A109", "s1_p48_1us", "the same step, valley trim on phases 2-4")], 395, 425,
        OLD + " Points: each phase's current at the turn-off command, once per period. Sources: A106, A109.",
        ylim=(100, 240), peak=True)


def lock():
    """A133 / A134 / A136, +62.5 A load step with the absolute phase-1 cap at L x 1.1 (lock: rail 1 16.4 V, Vo -17 mV)
    and L x 1.2 (Vo 0.905 V), and at L x 1.3 with the adopted relative cap."""
    fig, ax = plt.subplots(1, 2, figsize=SIZE)
    for exp, run, c, lab in (("A134", "fl110_s_p62", ORANGE, "absolute cap, L x 1.1"), ("A133", "fl12_s_p62", RED, "absolute cap, L x 1.2"),
                             ("A136", "q130_s_p62", BLUE, "relative cap, L x 1.3")):
        r, name = rec(exp, run)
        ts = r["cfg"]["load_step"]["t_us"]
        t = np.array([q["t_s"] for q in r["sections"]]) * 1e6 - ts
        m = (t >= -50) & (t <= 380)
        vo = np.array([q["vo"] for q in r["sections"]])
        rail = np.array([q["vin_v"] - q["vcs_v"][0] for q in r["sections"]])
        ax[0].plot(t[m], vo[m], color=c, lw=1.4)
        ax[1].plot(t[m], rail[m], color=c, lw=1.4, label=f"{lab}\n{name}")
        if c == RED:
            k = int(np.argmin(np.where(m, vo, 9)))
            ax[0].annotate(f"L x 1.2: {vo[k]:.3f} V,\nand it stays", (t[k], vo[k]), (150, 0.972), color=RED, fontsize=10,
                           fontweight="bold", va="top", arrowprops={"arrowstyle": "->", "color": RED})
        if c == ORANGE:
            ax[0].text(378, 0.981, f"L x 1.1: {vo[m][-1]:.3f} V", color=ORANGE, fontsize=10, ha="right", va="top", fontweight="bold")
    ax[0].axhspan(0.99, 1.01, color=GREEN, alpha=0.15, lw=0)
    ax[0].set(xlabel="time after the load step (µs)", ylabel="output voltage (V)", xlim=(-50, 380), ylim=(0.88, 1.03),
              title="Output voltage after a +62.5 A load step")
    ax[1].axhline(12, color=GREY, ls=":", lw=1.2)
    ax[1].text(375, 12.08, "balanced: 12 V", color=GREY, fontsize=8.5, ha="right", va="bottom")
    ax[1].set(xlabel="time after the load step (µs)", ylabel="rail 1 = Vin - V(Cs1) (V)", xlim=(-50, 380), ylim=(11, 17.5),
              title="Rail 1: locked near 16.5 V")
    for a in ax:
        a.title.set_fontsize(10)
    ax[1].legend(fontsize=7.5, frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.42))
    done(fig, "lock", NEW + ", ideal switches. Sources: A133, A134 (cause), A136 (fix).")


def random_defect():
    """A142 / A143: +4.8 V in 4 us at 295 us, while phase 1 is still on its comparator (254.2 A), and the same draw
    with the comparator phase cut from 1024 to 4 periods."""
    row("random_defect", [("A142", "R_dv4.8_s4_L100", "comparator phase 1024 periods: oscillation"),
                          ("A143", "g1_R_dv4.8_s4_L100_k4", "comparator phase 4 periods: the same draw")], 285, 360,
        NEW + ", ideal switches. Input +4.8 V in 4 µs, 151 µs after the handover. Points: current at the turn-off command. "
        "Sources: A142, A143.", ylim=(60, 290))


def duplicate():
    """A140 / A141: +4.8 V in 10 us at L x 0.7, the duplicate phase-1 turn-on (213.4 A) and the same row with the late
    floor report honoured."""
    row("duplicate", [("A140", "B_L070_p4.8_s10.0", "a report two clocks late is ignored"),
                      ("A141", "F_L070_p4.8_s10.0", "the late report is honoured")], 995, 1050,
        NEW + ", ideal switches, L x 0.7. Input +4.8 V in 10 µs. Points: current at the turn-off command. Sources: A140, A141.",
        ylim=(100, 245))


def vds_loop():
    """A144: the largest switch V_DS in each section with a 50 pH damped commutation loop (47.1 V at start-up, 58.5 V
    after +4.8 V / 1 us) against the same row without loop inductance; whole run and the 40 us around the step."""
    fig, ax = plt.subplots(1, 2, figsize=SIZE, sharey=True)
    for run, c, lab in (("b_l_p48_1us", GREY, "no loop inductance"), ("q7_l50_l_p48_1us", RED, "50 pH loop, ring Q 7")):
        r, name = rec("A144", run)
        t = np.array([q["t_s"] for q in r["sections"]]) * 1e6
        v = np.array([max(q["vds_win_v"]) for q in r["sections"]])
        ax[0].plot(t, v, color=c, lw=0.9, label=f"{lab}  ({name})")
        m = (t >= 990) & (t <= 1030)
        ax[1].plot(t[m], v[m], ".-", color=c, lw=0.9, ms=3)
        for a, sel, xy in ((ax[0], t < 300, (300, 52)), (ax[1], m, (1008, 61))) if c == RED else ():
            k = int(np.argmax(np.where(sel, v, 0)))
            a.annotate(f"{v[k]:.1f} V", (t[k], v[k]), xy, color=RED, fontsize=11, fontweight="bold",
                       arrowprops={"arrowstyle": "->", "color": RED})
    for a in ax:
        a.axhline(40, color=RED, ls="--", lw=1.2)
        a.set(xlabel="time (µs)", ylim=(20, 65))
        a.title.set_fontsize(10)
    ax[0].text(980, 40.6, "EPC2067 rating, 40 V", color=RED, fontsize=9, ha="right")
    ax[0].text(150, 21.2, "start-up", color=GREY, fontsize=8.5)
    ax[0].set(xlim=(0, 1400), xticks=[0, 400, 800, 1200], ylabel="largest switch V_DS (V)", title="whole run")
    ax[1].axvline(1000, color=GREY, ls=":", lw=1.2)
    ax[1].text(1000, 21.2, " +4.8 V in 1 µs", color=GREY, fontsize=8.5)
    ax[1].set(xlim=(990, 1030), xticks=[1000, 1010, 1020, 1030], title="around the input step")
    fig.legend(*ax[0].get_legend_handles_labels(), fontsize=8, frameon=False, loc="upper center", ncol=2)
    done(fig, "vds_loop", NEW + ", instantaneous edges. One value per switching period (the peak since the previous one). "
         "Source: A144.", top=0.95)


def handover():
    """A151 / A152, 100 pH loop and an 18 A/ns turn-on: the start-up handover with the original open-loop on-time
    (224.0 A) and with the on-time compensated for the slow turn-on."""
    row("handover", [("A151", "on18_l100_n0", "turn-on 18 A/ns, start-up on-time 35.5 ns"),
                     ("A152", "s100_l_p48_1us", "start-up on-time compensated: 37.5 ns")], 125, 165,
        NEW + ", 100 pH loop (Q 7), linear-ramp edges 18 / 72 A/ns. Points: current at the turn-off command. Sources: A151, A152.",
        ylim=(0, 260))


def gate_spread():
    """A163 start-up diagnostics: a nominal EPC2067 gate, a threshold 1.0 V higher at the same open-loop on-time
    (376.0 A at the handover), and that device with the on-time raised to 42.5 ns."""
    row("gate_spread", [("A163", "nom_t37.887", "nominal device\nstart-up on-time 37.887 ns"),
                        ("A163", "vth10_t37.887", "threshold +1.0 V\nthe same on-time"),
                        ("A163", "vth10_t42.5", "threshold +1.0 V\non-time trimmed to 42.5 ns")], 125, 170,
        NEW + ", 50 pH loop, EPC's gate-level device model on the high sides (r_on 2.5 Ω). Points: channel turn-off current. "
        "Marked: the largest after the handover. Source: A163 (cosim_diag).", sub="cosim_diag", ylim=(0, 420), since=144)


def lead():
    """A164 / A167 / A169 on the L x 0.7 board: the 8 ns high-side lead applied at the handover (218.6 A), ramped in over
    20 us, and the ramped lead with gate-driven low sides (stopped on a shoot-through at 152.5 us)."""
    row("lead", [("A164", "nom_L07_l_p48_1us", "8 ns lead switched on\nat the handover"),
                 ("A167", "nom_L07_l_p48_1us", "lead ramped in\nover 20 µs"),
                 ("A169", "nom_L07_l_p48_1us", "ramped lead,\nlow sides gate-driven too", {"stop": "stopped:\n shoot-through"})],
        125, 170, NEW + ", L x 0.7, 50 pH loop, gate-level EPC2067 model (3.0 / 0.3 Ω). Marked: the largest current after the "
        "handover (A167's registered 140-160 µs window reads 191.5 A at 140 µs, still open loop). The 196-203 A before the handover "
        "is this board's open-loop start-up, an open item. Sources: A164, A167, A169.", ylim=(0, 300), since=144)


def interlock():
    """A170 / A171 on the L x 0.7 board after +4.8 V / 1 us: the gate-hold interlock (214.3 A) and the threshold form."""
    row("interlock", [("A170", "S50_nom_L07_l_p48_1us", "form 1: gate held at 0 V until the complement is off"),
                      ("A171", "S50_nom_L07_l_p48_1us", "form 2: only a channel about to start is held")], 990, 1090,
        NEW + ", L x 0.7, 50 pH loop, gate-level EPC2067 model on all switches. Input +4.8 V in 1 µs. Sources: A170, A171.",
        ylim=(100, 245))


FIGS = {f.__name__: f for f in (shoot_through, mismatch, slots, startup_vo, line_step, lock, random_defect, duplicate, vds_loop,
                                handover, gate_spread, lead, interlock)}

if __name__ == "__main__":
    for n in (sys.argv[1:] or FIGS):
        FIGS[n]()
