"""Figures for reports/MEASUREMENT_CASE_2026-11-19.md: what limits the SCB-IVR results now. No new runs; every number is
read from a file in the repository:
  symbolic_derivations/03_P24_native/diagnostics/D85_loss_ledger.json   (loss ledger, D85 with D83's inductor terms)
  experiments/track_A_periodic_steady_state/A178_*/a178_summary.json      (inductance tolerance, plant V5)
  experiments/track_A_periodic_steady_state/A193_*/a193_summary.json      (slow corner below 25 C, plant V5)
  experiments/track_A_periodic_steady_state/A213_*/a213_summary.json      (binding row, plant V6 vs LTspice)
  PYTHONPATH=src python3 reports/figures/make_measurement_case.py   -> reports/figures/fig_mc_losses.png, fig_mc_margin.png
Prints the numbers the report quotes."""
from __future__ import annotations

from make_figures import BLUE, GREY, HERE, ORANGE, ROOT, TA, json, load, plt

DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
SIZE = (8.6, 3.9)


def footer(fig, text, bottom=0.17):
    fig.text(0.01, 0.01, text, fontsize=7.3, color=GREY, wrap=True, va="bottom")
    fig.tight_layout(rect=(0, bottom, 1, 1))


def ledger():
    """D85, N0 board (nominal devices), 25 C, 250 W out per module, chip level (no package terms)."""
    d = json.loads((DIAG / "D85_loss_ledger.json").read_text())["ledgers"]["N0_25C"]
    it, core, eff = d["items_w"], d["core_w"], d["eff_pct"]
    switch = {"conduction": it["conduction_high"] + it["conduction_low"],
              "edges and dead time": it["edges_high"] + it["edges_low"] + it["reverse_dead_time"],
              "gate drive": it["gate_drive"]}
    return d, it, core, eff, switch


def losses():
    d, it, core, eff, switch = ledger()
    sw = sum(switch.values())
    rows = [  # label, low, high, colour, hatch-range
        ("Core loss, κ = 3.07\n(lowest κ in [10] Table V)", core["lo_kV"], core["hi_kV"], ORANGE),
        ("Core loss, κ = 1", core["lo_k1"], core["hi_k1"], ORANGE),
        ("Inductor copper\n([10] R_DC of HBS1 units)", it["inductor_copper"], it["inductor_copper"], ORANGE),
        ("Series-capacitor ESR\n(assumed value)", it["series_caps_esr"], it["series_caps_esr"], ORANGE),
        ("Loop damper\n(50 pH loop spec)", it["loop_damper_50pH"], it["loop_damper_50pH"], GREY),
        ("All switch-side losses\n(conduction, edges, gate drive)", sw, sw, BLUE),
    ]
    fig, ax = plt.subplots(figsize=SIZE)
    for y, (lab, lo, hi, c) in enumerate(rows):
        ax.barh(y, lo, height=0.56, color=c, edgecolor="white", linewidth=2)
        if hi > lo:
            ax.barh(y, hi - lo, left=lo, height=0.56, color="white", edgecolor=c, hatch="////", linewidth=1.2)
        txt = f"{lo:.1f}–{hi:.1f} W" if hi > lo else f"{lo:.1f} W"
        ax.text(hi + 1.5, y, txt, va="center", fontsize=9.5, color="#222")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=9)
    ax.set_xlabel("Loss per 250 W module (W)")
    ax.set_xlim(0, 150)
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=ORANGE), plt.Rectangle((0, 0), 1, 1, color=BLUE),
                       plt.Rectangle((0, 0), 1, 1, fc="white", ec=ORANGE, hatch="////")],
              labels=["passive components: literature or assumed values, not measured",
                      "switches: simulated (gate-level plant, datasheet devices)",
                      "range from the digitised r_acx band of [10] Fig. 8"],
              fontsize=8, loc="upper right", frameon=False)
    footer(fig, "Source: D85 loss ledger (symbolic_derivations/03_P24_native/diagnostics/D85_loss_ledger.json, ledger "
                "N0_25C). Conditions: one module, 2.5 MHz design (1.96 MHz settled), 48 V to 1 V, 250 A, 25 °C, chip "
                "level (no package copper); switch terms from the gate-level plant V6 (A206), inductor terms from [10] "
                "= Alvarez Barros et al., IEEE TCPMT 2021 (P24's ref. [10]). Simulation and literature values; nothing "
                "measured.")
    fig.savefig(HERE / "fig_mc_losses.png")
    plt.close(fig)
    print("fig_mc_losses")
    print(f"  switch-side {sw:.2f} W = " + ", ".join(f"{k} {v:.2f}" for k, v in switch.items()))
    print(f"  core k1 {core['lo_k1']:.1f}-{core['hi_k1']:.1f} W, kV {core['lo_kV']:.1f}-{core['hi_kV']:.1f} W, "
          f"copper {it['inductor_copper']:.2f} W, Cs ESR {it['series_caps_esr']:.2f} W, damper {it['loop_damper_50pH']:.2f} W")
    e = {k: v["chip"] for k, v in eff.items() if isinstance(v, dict) and "chip" in v}
    print("  efficiency chip % " + ", ".join(f"{k} {v:.1f}" for k, v in e.items()))


def frequency_table():
    """D83 as corrected 2026-10-21 (D85's d83_corrected): three design records, 25 C, no package."""
    d = json.loads((DIAG / "D85_loss_ledger.json").read_text())["d83_corrected"]
    print("frequency table (efficiency %, r_acx band hi-lo):")
    for f in ("1MHz", "2.5MHz", "5MHz"):
        r = d[f]
        print(f"  {f}: no core {r['eff_no_core']:.1f} | k1 {r['hi_k1_eq1']:.1f}-{r['lo_k1_eq1']:.1f} | "
              f"kV {r['hi_kV_eq1']:.1f}-{r['lo_kV_eq1']:.1f}")


def margin():
    a178 = load(TA / "A178_*" / "a178_summary.json")["boards"]
    a193 = load(TA / "A193_*" / "a193_summary.json")
    a213 = load(TA / "A213_*" / "a213_summary.json")
    l80 = list(a178["L080"]["post"].values())
    l75 = list(a178["L075"]["post"].values())
    cold = [v["peak_post"] for k, v in a193.items() if "l9p5" in k]
    plant = a213["plant_peak"]["a"]
    peak_rows = [k for k, v in a213["replays"].items() if abs(v["peak_max"]["plant_a"] - plant) < 1e-6]
    lt = [a213["replays"][k]["peak_max"]["lt_a"] for k in peak_rows]
    di = [abs(x) for k in ("P_k0", "P_k1", "P_k2", "T_k8", "T_k9") for x in a213["replays"][k]["di"]]
    rows = [  # label, values, colour
        ("Nominal devices, L × 0.80\n25 °C (A178, plant V5)", l80, BLUE),
        ("Nominal devices, L × 0.75\n25 °C (A178, plant V5)", l75, BLUE),
        ("Slow devices, L × 0.75\n0 / −40 °C (A193, plant V5)", cold, BLUE),
        ("Slow devices, L × 0.75\n125 °C (A213, plant V6)", [plant], BLUE),
        ("Same row replayed\nin LTspice (A213)", lt, ORANGE),
    ]
    fig, ax = plt.subplots(figsize=SIZE)
    for y, (lab, v, c) in enumerate(rows[::-1]):
        lo, hi = min(v), max(v)
        ax.plot([lo, hi], [y, y], color=c, lw=2, solid_capstyle="round")
        ax.plot(v, [y] * len(v), "o", ms=8, color=c, mec="white", mew=2)
        ax.text(lo - 0.3, y, f"{hi:.1f} A" if hi - lo < 0.05 else f"{lo:.1f}–{hi:.1f} A", va="center", ha="right",
                fontsize=9.5)
    ax.axvline(200, color="#222", lw=1.2, ls="--")
    ax.text(200.15, (len(rows) - 1) / 2, "200 A\nbudget", fontsize=9, va="center")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]], fontsize=9)
    ax.set_xlabel("Largest phase current after the step (A)")
    ax.set_xlim(185.5, 202.5)
    ax.set_ylim(-0.5, len(rows) - 0.1)
    ax.grid(axis="y", visible=False)
    ax.text(185.7, len(rows) - 0.4, f"Plant minus LTspice on the 125 °C row: {min(di):.2f}–{max(di):.2f} A per period "
                          "(settled and at the step, A213)", fontsize=8.5, color="#222")
    footer(fig, "Sources: a178_summary.json, a193_summary.json (rows with the adopted 9.5 ns lead), a213_summary.json "
                "(experiments/track_A_periodic_steady_state/). Conditions: one module, 2.5 MHz design, +4.8 V input step "
                "in 1 µs, worst peak over 3-5 step positions; 'slow devices' = the slow corner of A164 (threshold +1.0 V, "
                "Q_G × 1.29, driver × 1.2), L × k = every phase inductor scaled by k. Co-simulation (Verilog controller + circuit model) and "
                "LTspice replays from the plant's state; no hardware.", bottom=0.2)
    fig.savefig(HERE / "fig_mc_margin.png")
    plt.close(fig)
    print("fig_mc_margin")
    print(f"  L x 0.80 {min(l80):.1f}-{max(l80):.1f}, L x 0.75 {min(l75):.1f}-{max(l75):.1f}, "
          f"A193 cold {min(cold):.1f}-{max(cold):.1f} ({len(cold)} runs), A213 plant {plant:.2f}, LTspice "
          f"{min(lt):.2f}-{max(lt):.2f}, plant-LTspice per period {min(di):.2f}-{max(di):.2f} A")


if __name__ == "__main__":
    losses()
    frequency_table()
    margin()
