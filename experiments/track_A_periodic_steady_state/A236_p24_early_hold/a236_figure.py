"""Item 3's mechanism from the records: A235 run_r_N13_lm48.json (final configuration, plant V7, N13, -4.8 V / 1 us at
500 us) and, once it exists, A236's run_h_r_N13_lm48.json (+ early_hold_a 0) over it.
    python3 a236_figure.py -> a236_item3.png"""
from __future__ import annotations

import bisect
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
TA = HERE.parent
REF = TA / "A235_p24_v7_corner_boards" / "cosim" / "run_r_N13_lm48.json"
ARM = HERE / "cosim" / "run_h_r_N13_lm48.json"
P, T0, T1 = 4, 495e-6, 560e-6


def series(path):
    r = json.loads(path.read_text())
    lead = r["driver"].get("hs_on_lead_ns", 0.0) if r.get("driver") else 0.0
    sec = [q for q in r["sections"] if T0 <= q["t_s"] <= T1]
    rails = [[q["vin_v"] - q["vcs_v"][0], q["vcs_v"][0] - q["vcs_v"][1], q["vcs_v"][1] - q["vcs_v"][2], q["vcs_v"][2]]
             for q in sec]
    lo = sorted((x for x in r["lowoffs_last"] if x["phase"] == P), key=lambda x: x["t_s"])
    lt = [x["t_s"] for x in lo]
    on = [x for x in r["turnons_last"] if x["phase"] == P and T0 <= x["t_s"] <= T1]
    dly, rs = [], []
    for x in on:
        j = bisect.bisect_left(lt, x["t_s"]) - 1
        d = (x["t_s"] - lt[j]) * 1e9
        (rs if x["how"] == 3 else dly).append((x["t_s"] * 1e6, d if x["how"] == 3 else d + lead))
    g = [(e["t_s"] * 1e6, e["i_max_a"]) for e in r["gate_offs_last"] if e["phase"] == P and T0 <= e["t_s"] <= T1]
    return {"ts": [q["t_s"] * 1e6 for q in sec], "rails": rails,
            "valley": [(x["t_s"] * 1e6, x["i_a"]) for x in lo if T0 <= x["t_s"] <= T1], "dly": dly, "rs": rs, "pk": g}


ref = series(REF)
arm = series(ARM) if ARM.exists() else None
fig, ax = plt.subplots(4, 1, figsize=(8.0, 9.0), sharex=True)
for k in range(4):
    ax[0].plot(ref["ts"], [x[k] for x in ref["rails"]], lw=1.2, label=f"rail {k + 1}")
ax[0].set_ylabel("rail (V)"); ax[0].legend(ncol=4, fontsize=8)
ax[0].set_title(f"N13, -4.8 V / 1 us at 500 us, phase {P}\nA235 cosim/run_r_N13_lm48.json"
                + (" (grey) vs A236 cosim/run_h_r_N13_lm48.json (blue)" if arm else ""), fontsize=9)
for s, c, lab in ((ref, "0.45", "final"), (arm, "C0", "+ early hold")):
    if s is None:
        continue
    ax[1].plot(*zip(*s["valley"]), ".", ms=3, color=c, label=lab)
    ax[2].plot(*zip(*s["dly"]), ".", ms=3, color=c, label=lab)
    if s["rs"]:
        ax[2].plot(*zip(*s["rs"]), "x", ms=8, color="C3", label="restart (K3)")
    ax[3].plot(*zip(*s["pk"]), ".", ms=3, color=c, label=lab)
ax[1].axhline(0.0, color="k", lw=0.6); ax[1].set_ylabel(f"phase {P} current at\nlow-side turn-off (A)")
ax[2].axhline(28.28, color="C3", lw=0.6, ls="--"); ax[2].set_ylabel("turn-on delay after\nlow-side turn-off (ns)")
ax[2].text(T0 * 1e6 + 1, 27.5, "cfg_rs_high 28.28 ns", color="C3", fontsize=8)
ax[3].set_ylabel(f"phase {P} peak,\ngate level (A)"); ax[3].set_xlabel("t (us)")
for a in ax[1:]:
    a.legend(fontsize=8, loc="upper right")
fig.tight_layout()
fig.savefig(HERE / "a236_item3.png", dpi=130)
print("a236_item3.png")
