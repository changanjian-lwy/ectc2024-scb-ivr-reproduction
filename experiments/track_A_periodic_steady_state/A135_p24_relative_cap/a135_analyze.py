"""A135 analysis against BOUNDARY Section 2 -> a135_summary.json: identity, L0 against A129 / f100, lock (A106's ladder
deviation against the same row of A129's g125 + 0.5 points, Vo +-1 %), post-step peaks (t >= 1000 us), the matrix rule
with the start-up split off (m / j rows: t >= 800 us), recovery; per L the row table, start-up peaks, and phase 1's
end Ton against phases 2-4's (the cap is idle when they match)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import step_stats, window_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a134_analyze", HERE.parent / "A134_p24_inductance_cap_lock" / "a134_analyze.py")
A134 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A134)
A133, A129 = A134.A133, A134.A129
COS, IDENT = HERE / "cosim", PROJECT / "tmp" / "identity_a135"
T_STEP = 1000e-6
A124_ROWS = A133.STEP_ROWS                                            # the seven step rows
MATRIX_ROWS = A133.MATRIX_ROWS
MS = (0.7, 0.85, 1.0, 1.15, 1.3)
load = A134.load


def tons(d, n=200):
    """Each phase's mean Ton (ns) over the last n periods, from its turn-on -> high-side turn-off pairs."""
    t0 = d["sections"][-n]["t_s"]
    out = []
    for k in range(1, 5):
        on = [r["t_s"] for r in d["turnons_last"] if r["phase"] == k and r["t_s"] >= t0]
        off = [r["t_s"] for r in d["highoffs_last"] if r["phase"] == k and r["t_s"] >= t0]
        ds = [b - a for a, b in zip(on, [next((x for x in off if x > a), None) for a in on]) if b is not None]
        out.append(float(np.mean(ds) * 1e9))
    return out


def stats(d, row):
    pk_s = 800e-6 if row[0] in "mj" else T_STEP
    pk = max(q["i_a"] for q in d["highoffs_last"] if q["t_s"] >= pk_s)
    late = sum(d["late_fires"])
    st = step_stats(d, t_step=T_STEP)
    back = st["back_within_1pct_us"] if (d["cfg"].get("line_step") or d["cfg"].get("load_step")) else 0.0
    runaway = pk > 400 or late > 100 or (not np.isfinite(back) and pk > 300)
    pre = [q["i_a"] for q in d["highoffs_last"] if q["t_s"] < pk_s]
    lk = A134.lock(d, dev_ref=A134.dev_ref(row) if not row.startswith("x_") else None)
    return {"peak_after_a": float(pk), "ipk_a": float(d["ipk_a"]), "startup_peak_a": float(d["ipk_a"]) if d["ipk_a"] > pk else None,
            "late": late, "overlaps": d["overlaps"], "runaway": bool(runaway), "back_us": float(back), "extreme_mv": st["extreme_mv"],
            "t_lo_timed_us": (d.get("t_lo_timed_s") or 0) * 1e6, "ton_end_ns": tons(d), **lk, "pre_peak_recorded_a": max(pre) if pre else None}


def matrix_ok(d, x, w0, row):
    w = window_stats(d)
    ok = w["overlaps"] == 0 and x["late"] <= 100 and x["peak_after_a"] <= 200.0
    if row[0] in "mj":
        ok &= all(abs(p["hs_on_vds_v"] - q["hs_on_vds_v"]) <= 0.5 for p, q in zip(w["phases"], w0["phases"]))
    if row[0] == "m":
        ok &= all(p["ls_on_vds_max_v"] <= 0.0 for p in w["phases"])
    if row == "j30":
        ok &= all(p["i_off_sd_a"] <= 0.5 for p in w["phases"])
    if row.startswith("s_"):
        ok &= np.isfinite(x["back_us"]) and x["back_us"] <= 60.0
    return bool(ok)


def main():
    c, R = {}, {}
    same = lambda a, b: all(a[k] == b[k] for k in ("sections", "turnons_last", "lowoffs_last", "highoffs_last"))
    c["1_identity"] = all(same(load(A129 / f"run_g125_{r}.json"), load(IDENT / f"run_g125_{r}.json")) for r in ("n0", "l_p48_1us"))
    for f in sorted(COS.glob("run_*.json")):
        name = f.stem[4:]
        row = name.split("_", 1)[1]
        R[name] = stats(load(f), row)
    for m in MS:
        tag = f"r{round(m * 100):03d}"
        w0 = window_stats(load(COS / f"run_{tag}_n0.json"))
        for row in MATRIX_ROWS:
            R[f"{tag}_{row}"]["matrix_ok"] = matrix_ok(load(COS / f"run_{tag}_{row}.json"), R[f"{tag}_{row}"], w0, row)
    ok2 = True
    for row in ("n0", "s_p62", "s_m62") + MATRIX_ROWS:
        a, b = A133.tail(load(A129 / f"run_g125_{row}.json")), A133.tail(load(COS / f"run_r100_{row}.json"))
        ra, rb = A134.lock(load(A129 / f"run_g125_{row}.json"))["rails_end_v"], R[f"r100_{row}"]["rails_end_v"]
        ok2 &= max(abs(p - q) for p, q in zip(a["valley_mean_a"] + a["peak_a"], b["valley_mean_a"] + b["peak_a"])) <= 0.2
        ok2 &= max(abs(p - q) for p, q in zip(ra, rb)) <= 0.02
    d2 = {row: R[f"r100_{row}"]["peak_after_a"] - R[f"f100_{row}"]["peak_after_a"] for row in A124_ROWS}
    c["2_l0_unchanged"] = bool(ok2 and all(abs(v) <= 7.0 for v in d2.values()))
    rr = {k: v for k, v in R.items() if k.startswith("r")}
    c["3_no_lock"] = all(not v.get("locked_ph", False) for v in rr.values())
    c["4_peaks"] = all(R[f"r{round(m * 100):03d}_{row}"]["peak_after_a"] <= 200.0 for m in MS for row in A124_ROWS) and \
        all(R[f"r{round(m * 100):03d}_{row}"]["matrix_ok"] for m in MS for row in MATRIX_ROWS)
    c["5_recovery"] = all(np.isfinite(R[f"r{round(m * 100):03d}_{row}"]["back_us"]) and R[f"r{round(m * 100):03d}_{row}"]["late"] <= 100
                          and R[f"r{round(m * 100):03d}_{row}"]["overlaps"] == 0 for m in MS for row in A124_ROWS)
    per_l = {}
    for m in MS:
        tag = f"r{round(m * 100):03d}"
        rows = {row: R[f"{tag}_{row}"] for row in A124_ROWS + ("n0",) + MATRIX_ROWS}
        per_l[m] = {"a124_pk_max_a": max(rows[r]["peak_after_a"] for r in A124_ROWS),
                    "fail_peak": [r for r in A124_ROWS if rows[r]["peak_after_a"] > 200.0],
                    "fail_matrix": [r for r in MATRIX_ROWS if not rows[r]["matrix_ok"]],
                    "locked": [r for r, x in rows.items() if x.get("locked_ph")],
                    "back_max_us": max(rows[r]["back_us"] for r in A124_ROWS),
                    "late_max": max(x["late"] for x in rows.values()),
                    "startup_max_a": max((x["startup_peak_a"] or 0) for x in rows.values()),
                    "ton_n0_ns": rows["n0"]["ton_end_ns"]}
    out = {"criteria": c, "l0_peak_delta_vs_f100_a": d2, "per_l": {str(k): v for k, v in per_l.items()}, "runs": R}
    (HERE / "a135_summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("criteria:", " ".join(f"{k}={'P' if v else 'F'}" for k, v in c.items()))
    print("L0 r - f post-step peak (A):", " ".join(f"{k}:{v:+.1f}" for k, v in d2.items()))
    for m, p in per_l.items():
        print(f"r L x{m:4.2f}: A124 pk {p['a124_pk_max_a']:5.1f} >200 {','.join(p['fail_peak']) or '-'} | matrix fail {','.join(p['fail_matrix']) or '-'} | "
              f"lock {','.join(p['locked']) or '-'} | back max {p['back_max_us']:.1f} us | late max {p['late_max']} | start-up {p['startup_max_a']:.0f} A | "
              f"n0 Ton {'/'.join(f'{t:.1f}' for t in p['ton_n0_ns'])}")
    for k in sorted(x for x in R if "x_l_p80" in x):
        print(f"{k}: {R[k]['peak_after_a']:.1f} A, back {R[k]['back_us']:.1f} us")


if __name__ == "__main__":
    main()
