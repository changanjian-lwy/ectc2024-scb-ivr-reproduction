"""A134 analysis against BOUNDARY Section 2 -> a134_summary.json: per run the post-step peak, the whole-run peak, lock
(A106's ladder deviation and Vo over the last 200 periods), runaway / recovery; the f tolerance table over L (A129's
g125 at L0, A133's fl07 / fl12 / fl13 step rows) and the z / c mechanism arms. Post hoc (marked _ph): lock with the
deviation measured against the same row of A129's g125 (+0.5 points), since s_p62 sits at 0.94 % at L0. `trace RUN T0_US T1_US`: the per-period
table of the diagnosis (each phase's valley, slot in T/4 from phase 1's low-side turn-off, turn-off -> turn-on delay,
V_DS and current at the turn-on, Ton, peak, high-side reverse-conduction time; rails, Vo)."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / "src"))
from scb_ivr.cosim.matrix import window_stats  # noqa: E402

spec = importlib.util.spec_from_file_location("a133_analyze", HERE.parent / "A133_p24_inductance_tolerance" / "a133_analyze.py")
A133 = importlib.util.module_from_spec(spec); spec.loader.exec_module(A133)
COS, A133_COS, A129 = HERE / "cosim", HERE.parent / "A133_p24_inductance_tolerance" / "cosim", A133.A129
T_STEP = 800e-6
STEP_ROWS = A133.STEP_ROWS + ("n0",)                                # A133 lists the seven step rows only
MATRIX_ROWS = A133.MATRIX_ROWS
LS = (0.7, 0.85, 0.9, 1.0, 1.05, 1.1, 1.2, 1.3)


def load(p):
    return json.loads(Path(p).read_text())


def path(arm, m, row):
    """Record of arm at L x m: A134's own, or the earlier one it reuses (A129 g125 at L0, A133 fl07 / fl12 / fl13)."""
    if arm == "f" and m == 1.0:
        return A129 / f"run_g125_{row}.json"
    own = COS / f"run_{arm}l{round(m * 100):03d}_{row}.json"
    if own.exists():
        return own
    old = A133_COS / f"run_fl{round(m * 10):02d}_{row}.json"
    return old if arm == "f" and old.exists() else None


def lock(d, n=200, dev_ref=None):
    secs = d["sections"][-n:]
    dev = max(max(abs(v / s["vin_v"] - (3 - j) / 4) for j, v in enumerate(s["vcs_v"])) for s in secs)
    vo = float(np.mean([s["vo"] for s in secs]))
    rails = np.mean([A133.rails(s) for s in secs], axis=0)
    out = {"locked": bool(dev > 0.01 or abs(vo - 1.0) > 0.01), "ladder_dev": float(dev), "vo_end": vo,
           "rails_end_v": [float(x) for x in rails]}
    if dev_ref is not None:
        out["locked_ph"] = bool(dev > dev_ref + 0.005 or abs(vo - 1.0) > 0.01)
    return out


DEV_REF = {}


def dev_ref(row):
    if row not in DEV_REF:
        DEV_REF[row] = lock(load(A129 / f"run_g125_{row}.json"))["ladder_dev"]
    return DEV_REF[row]


def matrix_ok(d, x, w0, row):
    """A129's rule (A133's matrix_ok) with the whole-run peak replaced by the peak at t >= 800 us."""
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


def judge(arm, m, ref_tail):
    rows, n0p = {}, path(arm, m, "n0")
    n0 = load(n0p) if n0p else None
    w0 = window_stats(n0) if n0 else None
    for row in STEP_ROWS + MATRIX_ROWS:
        p = path(arm, m, row)
        if p is None:
            continue
        d = load(p)
        x = A133.disturbance(d)
        x.update(lock(d, dev_ref=dev_ref(row)), src=str(p.relative_to(PROJECT)),
                 startup_peak_a=float(d["ipk_a"]) if d["ipk_a"] > x["peak_after_a"] else None, t_lo_timed_us=(d.get("t_lo_timed_s") or 0) * 1e6)
        for sfx, lk in (("", x["locked"]), ("_ph", x["locked_ph"])):
            if row == "n0":
                bal = A133.balanced(d, ref_tail)
                x.update(balanced=bal[0], checks=bal[1])
                x["ok_func" + sfx] = x["ok_spec" + sfx] = bool(bal[0] and not lk)
            elif row in MATRIX_ROWS:
                x["matrix_ok"] = matrix_ok(d, x, w0, row)
                x["ok_func" + sfx] = bool(x["overlaps"] == 0 and x["late"] <= 100 and not lk and not x["runaway"])
                x["ok_spec" + sfx] = bool(x["matrix_ok"] and not lk)
            else:
                func = x["overlaps"] == 0 and not x["runaway"] and np.isfinite(x["back_us"]) and not lk
                x["ok_func" + sfx] = bool(func)
                x["ok_spec" + sfx] = bool(func and x["peak_after_a"] <= 200.0)
        rows[row] = x
    return rows


def main():
    ref_tail = A133.tail(load(A129 / "run_g125_n0.json"))
    out = {"f": {}, "z": {}, "c": {}}
    for m in LS:
        out["f"][m] = judge("f", m, ref_tail)
    for arm in ("z", "c"):
        for m in (1.1, 1.2, 1.3):
            out[arm][m] = judge(arm, m, ref_tail)
    c = {}
    zc = [out[a][m][r] for a in ("z", "c") for m in (1.1, 1.2, 1.3) for r in ("n0", "s_p62")]
    ref_locks = [lock(load(A133_COS / "run_fl12_s_p62.json"))["locked"], lock(load(A133_COS / "run_fl13_n0.json"))["locked"]]
    c["1_mechanism"] = bool(all(not x["locked"] for x in zc) and all(ref_locks))
    c["1_mechanism_ph"] = bool(all(not x["locked_ph"] for x in zc) and all(ref_locks))
    c["2_f_s_p62_locks_l110"] = out["f"][1.1]["s_p62"]["locked"]
    tol = {}
    for m in LS:
        rs = out["f"][m]
        full = all(r in rs for r in STEP_ROWS + MATRIX_ROWS)
        tol[m] = {"rows": len(rs), "complete": full}
        for sfx in ("", "_ph"):
            tol[m].update({"func" + sfx: all(x["ok_func" + sfx] for x in rs.values()), "spec" + sfx: all(x["ok_spec" + sfx] for x in rs.values()),
                           "fail_func" + sfx: [r for r, x in rs.items() if not x["ok_func" + sfx]],
                           "fail_spec" + sfx: [r for r, x in rs.items() if not x["ok_spec" + sfx]]})
    c["3_tolerance"] = tol
    res = {"criteria": c, "runs": {a: {str(m): v for m, v in out[a].items()} for a in out}}
    (HERE / "a134_summary.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(f"1 mechanism {'P' if c['1_mechanism'] else 'F'} (post hoc {'P' if c['1_mechanism_ph'] else 'F'}; A133 refs locked {ref_locks}); "
          f"2 f s_p62 locks at 1.1: {c['2_f_s_p62_locks_l110']}")
    for m in LS:
        t, rs = tol[m], out["f"][m]
        pk = max(x["peak_after_a"] for x in rs.values())
        print(f"f L x{m:4.2f} rows {t['rows']:2d} func {'Y' if t['func'] else 'N'}/{'Y' if t['func_ph'] else 'N'}ph spec {'Y' if t['spec'] else 'N'}/"
              f"{'Y' if t['spec_ph'] else 'N'}ph pk {pk:5.1f} fail_ph {','.join(t['fail_spec_ph']) or '-'}")
    for arm in ("z", "c"):
        for m in (1.1, 1.2, 1.3):
            rs = out[arm][m]
            print(f"{arm} L x{m:3.1f} " + " ".join(f"{r}:{x['peak_after_a']:.0f}{'L' if x['locked_ph'] else ''}" for r, x in rs.items()))


def trace(f, t0, t1):
    d = load(f)
    secs = d["sections"]
    ev = {(key, k): [r for r in d[key] if r["phase"] == k] for key in ("lowoffs_last", "turnons_last", "highoffs_last") for k in range(1, 5)}
    nxt = lambda lst, a, b: next((r for r in lst if a <= r["t_s"] < b), None)
    rows = []
    for i in range(len(secs) - 1):
        s, T = secs[i], secs[i + 1]["t_s"] - secs[i]["t_s"]
        if not t0 <= s["t_s"] * 1e6 <= t1:
            continue
        l1 = [r for r in ev["lowoffs_last", 1] if r["t_s"] <= s["t_s"]][-1]
        v = s["vcs_v"]
        row = {"t_us": s["t_s"] * 1e6, "T_ns": T * 1e9, "vo": s["vo"], "rails_v": [s["vin_v"] - v[0], v[0] - v[1], v[1] - v[2], v[2]], "ph": []}
        for k in range(1, 5):
            lo = nxt(ev["lowoffs_last", k], l1["t_s"] - 1e-9, l1["t_s"] + 1.2 * T)
            on = nxt(ev["turnons_last", k], lo["t_s"], lo["t_s"] + T) if lo else None
            hf = nxt(ev["highoffs_last", k], on["t_s"], on["t_s"] + T) if on else None
            if not (lo and on and hf):
                row["ph"].append(None); continue
            row["ph"].append({"valley_a": lo["i_a"], "slot_t4": (lo["t_s"] - l1["t_s"]) / (T / 4), "delay_ns": (on["t_s"] - lo["t_s"]) * 1e9,
                              "von_v": on["vds_v"], "ion_a": on["i_a"], "ton_ns": (hf["t_s"] - on["t_s"]) * 1e9, "peak_a": hf["i_a"],
                              "rev_high_ns": secs[i + 1]["rev_time_s"][k - 1] * 1e9})
        rows.append(row)
        f1 = lambda p: "  ---  " if p is None else (f"{p['valley_a']:6.1f} {p['slot_t4']:4.2f} {p['delay_ns']:4.1f} {p['von_v']:5.1f} "
                                                     f"{p['ion_a']:6.1f} {p['ton_ns']:4.1f} {p['peak_a']:4.0f} {p['rev_high_ns']:3.1f}")
        print(f"{row['t_us']:7.2f} {row['T_ns']:4.0f} {'/'.join(f'{x:.2f}' for x in row['rails_v'])} {row['vo']:.3f} | " + " | ".join(f1(p) for p in row["ph"]))
    return rows


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "trace":
        r = trace(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
        if len(sys.argv) > 5:
            Path(sys.argv[5]).write_text(json.dumps(r, indent=1) + "\n")
    else:
        main()
