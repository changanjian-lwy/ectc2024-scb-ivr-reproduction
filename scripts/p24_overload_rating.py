"""D89: item 10's two open rows from existing records, no new co-simulation.

(1) Overload rating. The final configuration's limit suspends under an overload and the loop carries it (A256), so
the steady peak then follows the load. On the four boards' 125 % rows the gate-record peak at full load (the 50 us
before the step) and in the overload (the last 60 us) gives the peak's slope per ampere of load; extrapolated, the
load where it reaches A240's 200 A budget. Books: a phase current between a fixed valley and its peak has
d(peak) = 2 d(I_load / 4) - d(valley).
(2) A train that starts while the limit is suspended. Replays A256's up/down count (n_cap 6) on A258's arm-s
trains, which ran unprotected: while armed a pulse counts as limited when ocp_fires cut it; while suspended when its
controller turn-off current reaches THR, i.e. the 110 A crossing came at least t_ns + t_drv (11 ns) before the
controller's own turn-off (the recorded cut currents are 158.6-172.0 A). The replay is first checked against the
recorded suspension and re-arm of the same records, then started from the ceiling (6 on every phase) at the train.

Records: A258 run_c_{k_N0,o125_N75,o125_S75h} (release records-a258), A257 run_s_o125_N13 (records-a257), A258
run_s_pr_{N75,S75h}. Writes symbolic_derivations/03_P24_native/diagnostics/D89_overload_rating.{json,png}.
  python3 scripts/p24_overload_rating.py"""
from __future__ import annotations

import bisect
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TA = ROOT / "experiments" / "track_A_periodic_steady_state"
DIAG = ROOT / "symbolic_derivations" / "03_P24_native" / "diagnostics"
A58, A57 = TA / "A258_p24_limit_count_cap" / "cosim", TA / "A257_p24_limit_on_n13_overload" / "cosim"
OVER = {"N0": A58 / "run_c_k_N0.json", "N75": A58 / "run_c_o125_N75.json", "S75h": A58 / "run_c_o125_S75h.json",
        "N13": A57 / "run_s_o125_N13.json"}
TRAIN = {"N75": A58 / "run_s_pr_N75.json", "S75h": A58 / "run_s_pr_S75h.json"}
I_FULL, I_LIM, N = 250.0, 200.0, 4
THR = (160.0, 165.0, 168.0)                       # would-be cut: controller turn-off current, inside the cut range
T_TRAIN = 300e-6
INK, COL = "#3d3d3a", {"N0": "#2a78d6", "N75": "#eb6834", "S75h": "#8a5cc2", "N13": "#2f9e6e"}


def window(d, key, fld, t0, t1):
    return [e[fld] for e in d[key] if t0 <= e["t_s"] * 1e6 < t1]


def rating(b, f):
    d = json.loads(f.read_text())
    step, te = d["cfg"]["load_step"], d["t_end_s"] * 1e6
    t, di = step["t_us"], step["i_a"]
    full, over = (t - 50, t), (te - 60, te)
    pk = {w: window(d, "gate_offs_last", "i_max_a", *span) for w, span in (("full", full), ("over", over))}
    va = {w: window(d, "lowoffs_last", "i_a", *span) for w, span in (("full", full), ("over", over))}
    slope = (max(pk["over"]) - max(pk["full"])) / di
    d_mean, d_val = np.mean(pk["over"]) - np.mean(pk["full"]), np.mean(va["over"]) - np.mean(va["full"])
    return {"record": str(f.relative_to(TA)), "step_a": di, "t_step_us": t,
            "peak_full_a": max(pk["full"]), "peak_over_a": max(pk["over"]),
            "peak_step_20us_a": max(window(d, "gate_offs_last", "i_max_a", t, t + 20)),
            "suspended_us": [round(1e6 * x["t_s"], 2) for x in d["ocp_susp"]], "fires": len(d["ocp_fires"]),
            "slope_a_per_a": slope, "mean_peak_rise_a": d_mean, "valley_shift_a": d_val,
            "triangle_rise_a": 2 * di / N - d_val,
            "load_at_limit_a": I_FULL + di + (I_LIM - max(pk["over"])) / slope}


def replay(d, thr, t_from, cap=6, start=None, n=6):
    """A256's count: armed -> a hit iff ocp_fires cut the pulse; suspended -> iff its turn-off current >= thr.
    Returns the suspend / re-arm instants (us) and the per-phase counts at each pulse."""
    cut = sorted((e["t_s"], e["phase"]) for e in d["ocp_fires"])
    cnt = dict(start) if start else {p: 0 for p in range(1, N + 1)}
    susp, log, trace = bool(start), [], []
    for e in d["highoffs_last"]:
        if e["t_s"] < t_from:
            continue
        p = e["phase"]
        if susp:
            hit = e["i_a"] >= thr
        else:
            i = bisect.bisect_left(cut, (e["t_s"] - 0.5e-9, 0))
            hit = i < len(cut) and abs(cut[i][0] - e["t_s"]) < 0.5e-9 and cut[i][1] == p
        cnt[p] = cnt[p] + 1 if hit else max(cnt[p] - 1, 0)
        if cap is not None:                                  # A258's ceiling; None = A256's count
            cnt[p] = min(cnt[p], cap)
        if not susp and cnt[p] >= n:
            susp = True
            log.append((1, 1e6 * e["t_s"]))
        elif susp and not any(cnt.values()):
            susp = False
            log.append((0, 1e6 * e["t_s"]))
        trace.append((1e6 * e["t_s"], max(cnt.values())))
    return log, trace


def train(b, f):
    d = json.loads(f.read_text())
    rec = [(x["on"], 1e6 * x["t_s"]) for x in d["ocp_susp"]]
    t_ov = d["cfg"]["load_step"]["t_us"] * 1e-6                # armed at the overload's start; the run had no ceiling
    check = {thr: replay(d, thr, t_ov, cap=None)[0] for thr in THR}
    hs = [e for e in d["highoffs_last"] if T_TRAIN <= e["t_s"] < T_TRAIN + 60e-6]
    from_cap = {thr: replay(d, thr, T_TRAIN, start={p: 6 for p in range(1, N + 1)})[0] for thr in THR}
    g = [(1e6 * e["t_s"] - 300.0, e["i_max_a"]) for e in d["gate_offs_last"] if e["t_s"] >= T_TRAIN]
    return {"record": str(f.relative_to(TA)), "recorded": rec,
            "check": {str(t): v[:2] for t, v in check.items()},
            "hit_fraction_60us": {str(t): sum(e["i_a"] >= t for e in hs) / len(hs) for t in THR},
            "rearm_us_into_train": {str(t): (v[0][1] - 300.0 if v else None) for t, v in from_cap.items()},
            "unprotected_first_over_200_us": next((t for t, i in g if i > I_LIM), None),
            "cut_current_range_a": [min(e["i_a"] for e in d["ocp_fires"]), max(e["i_a"] for e in d["ocp_fires"])]}


def figure(rt, tr):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    a = ax[0]
    x = np.linspace(I_FULL, 1.5 * I_FULL, 50)
    for b, r in rt.items():
        x0, x1 = I_FULL, I_FULL + r["step_a"]
        a.plot([x0, x1], [r["peak_full_a"], r["peak_over_a"]], "o", color=COL[b], ms=7)
        a.plot(x, r["peak_full_a"] + r["slope_a_per_a"] * (x - x0), "-", color=COL[b], lw=1.6,
               label=f"{b}: {r['slope_a_per_a']:.3f} A per A, 200 A at {100 * r['load_at_limit_a'] / I_FULL:.1f} %")
    a.axhline(I_LIM, color=INK, lw=1, ls="--")
    a.text(I_FULL + 2, I_LIM + 1.5, "200 A budget (A240 q1)", color=INK, fontsize=9)
    a.set_xticks([250, 281.25, 312.5, 343.75, 375])
    a.set_xticklabels(["100 %", "112.5 %", "125 %", "137.5 %", "150 %"])
    a.set_xlabel("load per module (250 A = 100 %)")
    a.set_ylabel("largest gate-record turn-off current (A)")
    a.set_title("(a) suspended limit: peak against load\n(dots: records at 100 / 125 %; lines: extrapolated)",
                fontsize=10, loc="left")
    a.legend(fontsize=8, loc="lower right", frameon=False)
    a.set_ylim(140, 225)
    b_ = ax[1]
    for b, f in TRAIN.items():
        d = json.loads(f.read_text())
        _, trace = replay(d, THR[-1], T_TRAIN, start={p: 6 for p in range(1, N + 1)})
        t, c = zip(*[(t - 300.0, c) for t, c in trace if t < 320.0])
        b_.step(t, c, where="post", color=COL[b], lw=4.0 if b == "N75" else 1.4, alpha=0.45 if b == "N75" else 1.0,
                label=f"{b}: count from the ceiling (replay, {THR[-1]:.0f} A)")
        u = tr[b]["unprotected_first_over_200_us"]
        b_.axvline(u, color=COL[b], lw=1, ls=":")
        b_.text(u + 0.2, 5.4 if b == "N75" else 4.6, f"{b} unprotected train\nfirst > 200 A: {u:.1f} us",
                color=INK, fontsize=8)
    b_.set_xlim(0, 16)
    b_.set_ylim(-0.3, 6.6)
    b_.set_xlabel("time into the 1 MHz train (us)")
    b_.set_ylabel("largest per-phase count (re-arm at 0 on every phase)")
    b_.set_title("(b) a train that starts while the limit is suspended\n(A258 arm-s trains, count replayed; the boards coincide)",
                 fontsize=10, loc="left")
    b_.legend(fontsize=8, loc="center right", frameon=False)
    for s in ax:
        s.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(DIAG / "D89_overload_rating.png", dpi=150)


def main():
    rt = {b: rating(b, f) for b, f in OVER.items()}
    tr = {b: train(b, f) for b, f in TRAIN.items()}
    worst = min(rt, key=lambda b: rt[b]["load_at_limit_a"])
    out = {"rating": rt, "worst": worst, "rating_a": rt[worst]["load_at_limit_a"], "train": tr, "thr_a": THR}
    (DIAG / "D89_overload_rating.json").write_text(json.dumps(out, indent=1) + "\n")
    figure(rt, tr)
    for b, r in rt.items():
        print(f"{b:5s} peak {r['peak_full_a']:.1f} -> {r['peak_over_a']:.1f} A, slope {r['slope_a_per_a']:.3f}, "
              f"mean rise {r['mean_peak_rise_a']:.1f} (triangle {r['triangle_rise_a']:.1f}), "
              f"200 A at {r['load_at_limit_a']:.1f} A ({100 * r['load_at_limit_a'] / I_FULL:.1f} %)")
    for b, r in tr.items():
        print(f"{b:5s} recorded {[(o, round(t, 2)) for o, t in r['recorded']]}, replay check "
              f"{ {t: [(o, round(x, 2)) for o, x in v] for t, v in r['check'].items()} }")
        print(f"      hits {[round(v, 2) for v in r['hit_fraction_60us'].values()]}, re-arm into train "
              f"{[round(v, 2) for v in r['rearm_us_into_train'].values()]} us, unprotected > 200 A at "
              f"{r['unprotected_first_over_200_us']:.2f} us")


if __name__ == "__main__":
    main()
