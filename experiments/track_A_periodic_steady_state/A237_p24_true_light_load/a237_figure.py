"""A237's two findings from the records: Vo after a release to a true current load (N0: 0 / 5 / 25 A) against the
4 mOhm base's "no load" (A229 z_N0_0_t0_b), and phase 2's swing after N75's re-application (cw5_N75 against A229 w5_N75_b).
    python3 a237_figure.py -> a237_light_load.png"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
COS, A29C = HERE / "cosim", HERE.parent / "A229_p24_kd_band" / "cosim"


def vo(path):
    r = json.loads(path.read_text())
    s = [q for q in r["sections"] if q["t_s"] >= 290e-6]
    return [q["t_s"] * 1e6 for q in s], [q["vo"] for q in s]


def phase(path, k, t0=378e-6, t1=412e-6):
    r = json.loads(path.read_text())
    lead = r["driver"].get("hs_on_lead_ns", 0.0)
    lo = [x for x in r["lowoffs_last"] if x["phase"] == k]
    on = [x for x in r["turnons_last"] if x["phase"] == k and t0 <= x["t_s"] < t1]
    dly = [(x["t_s"] * 1e6, (x["t_s"] - min(lo, key=lambda y: abs(y["t_s"] - x["t_s"]))["t_s"]) * 1e9 + lead) for x in on]
    pk = [(e["t_s"] * 1e6, e["i_max_a"]) for e in r["gate_offs_last"] if e["phase"] == k and t0 <= e["t_s"] < t1]
    return dly, pk


fig, ax = plt.subplots(3, 1, figsize=(8.0, 9.0))
for f, c, lab in ((A29C / "run_z_N0_0_t0_b.json", "0.5", "4 mOhm base, \"no load\" (A229 z_N0_0_t0_b)"),
                  (COS / "run_c0_N0.json", "C3", "0 A (c0_N0)"), (COS / "run_c2_N0.json", "C1", "5 A (c2_N0)"),
                  (COS / "run_c10_N0.json", "C0", "25 A (c10_N0)")):
    ax[0].plot(*vo(f), lw=0.8, color=c, label=lab)
ax[0].axhline(1.05, color="k", lw=0.6, ls="--"); ax[0].axhline(1.01, color="k", lw=0.6, ls=":")
ax[0].text(292, 1.051, "VRD 11.1: +50 mV for <= 25 us", fontsize=8); ax[0].text(292, 1.011, "1 %", fontsize=8)
ax[0].set_ylabel("Vo (V)"); ax[0].set_xlabel("t (us); 250 A released at 300 us")
ax[0].set_title("N0, plant V7, final configuration: release to a true current load\nA237 cosim/run_c{0,2,10}_N0.json",
                fontsize=9)
ax[0].legend(fontsize=7, loc="center right")
for f, c, lab in ((A29C / "run_w5_N75_b.json", "0.5", "4 mOhm base (A229 w5_N75_b)"),
                  (COS / "run_cw5_N75.json", "C3", "true current (A237 cw5_N75)")):
    dly, pk = phase(f, 2)
    ax[1].plot(*zip(*pk), ".", ms=3, color=c, label=lab)
    ax[2].plot(*zip(*dly), ".", ms=3, color=c, label=lab)
ax[1].set_ylabel("phase 2 peak,\ngate level (A)"); ax[1].legend(fontsize=7)
ax[1].set_title("N75, 12.5 A -> 250 A at 380 us: phase 2", fontsize=9)
ax[2].set_ylabel("phase 2 turn-on delay after\nlow-side turn-off (ns)"); ax[2].set_xlabel("t (us)")
fig.tight_layout()
fig.savefig(HERE / "a237_light_load.png", dpi=130)
print("a237_light_load.png")
