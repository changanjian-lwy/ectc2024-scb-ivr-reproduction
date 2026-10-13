"""A207 analysis (BOUNDARY Section 2), per row:
 r1 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V;
 r2 Vo within 1 V +- 10 mV over the last 20 us and within +- 50 mV at all times after the step.
With it: the controller's Ton register (sections "ton_lsb"; the gate command is that plus the driver's lead), period,
peaks and the plant's loss books over the last 10 us (a206_analyze.whole), the output power with the step's current
taken off, and D63's prediction of the same row. The floor: the module current at which the Ton register reaches its
limit, from the two passing rows nearest to it (linear in the register). From the passing rows and A206's full-load
run: the load ranges four equal modules cover with n of them on, their gaps, and the loss at sample loads (system();
a composition with idle modules at 0 W and equal sharing, not a run).
  python3 a207_analyze.py -> a207_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a206_analyze", TA / "A206_p24_low_side_zvs_turn_on" / "a206_analyze.py")
A6 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A6)
COS = HERE / "cosim"
FULL = TA / "A206_p24_low_side_zvs_turn_on" / "cosim" / "run_E_N0_steady_ls0p3_t.json"
I_LIM, V_LIM, BAND_END, BAND_ALL, T_END_WIN = 200.0, 40.0, 0.010, 0.050, 20e-6
I_FULL, N_MOD = 250.0, 4
TOTALS = (1000.0, 750.0, 500.0, 375.0, 250.0, 187.5, 125.0, 100.0)       # A, a four-module system's load


def one(path):
    w = A6.whole(path)
    r = json.loads(Path(path).read_text())
    ev = r["cfg"].get("load_step")
    t_ev, i_a = (ev["t_us"] * 1e-6, ev["i_a"]) if ev else (None, 0.0)
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    r_load = r["snap_circuit"]["r_load"]
    last = ts >= ts[-1] - T_END_WIN
    out = {k: w[k] for k in ("status", "commit", "sources_modified", "wall_s", "shoot_on", "overlaps", "forced", "il_holds",
                             "peak_whole", "vds_whole", "late_fires")}
    tl = np.array([q["ton_lsb"] for q in r["sections"]], float) * r["lsb_s"] * 1e9
    lim = round(0.5 * r["cfg"]["ton_ns"] * 1e-9 / r["lsb_s"]) * r["lsb_s"] * 1e9
    w10 = ts >= ts[-1] - A6.WIN_US * 1e-6
    out.update(share=None if ev is None else 1.0 + i_a / I_FULL, i_step_a=i_a, ton_min_ns=lim,
               ton_reg_ns=float(tl[w10].mean()), at_ton_min=bool(tl[w10].max() <= lim + 1e-9),
               lead_ns=r["cfg"]["driver"]["hs_on_lead_ns"],
               vo_end_v=float(vo[last].mean()), vo_end_min_v=float(vo[last].min()), vo_end_max_v=float(vo[last].max()),
               vo_slope_mv_per_us=1e-3 * float(np.polyfit(ts[last], vo[last], 1)[0]))
    if ev:
        aft = ts >= t_ev
        g = [e for e in r["gate_offs_last"] if e["t_s"] >= t_ev]
        out.update(vo_after_min_v=float(vo[aft].min()), vo_after_max_v=float(vo[aft].max()),
                   post_pk=max(e["i_max_a"] for e in g), t_vo_max_us=1e6 * float(ts[aft][np.argmax(vo[aft])] - t_ev))
        k_lim = np.where(aft & (tl <= lim + 1e-9))[0]
        out["t_at_limit_us"] = None if not k_lim.size else 1e6 * float(ts[k_lim[0]] - t_ev)
        if "late" in r["sections"][0]:
            k = int(np.searchsorted(ts, t_ev, side="right")) - 1
            out["late_after"] = (np.array(r["sections"][-1]["late"]) - np.array(r["sections"][k]["late"])).tolist()
    s = w.get("settled")
    if s:
        m = (ts > s["window_us"][0] * 1e-6) & (ts <= s["window_us"][1] * 1e-6)
        i_out = float(np.mean(vo[m] / r_load + i_a)); p_out = float(np.mean(vo[m] * (vo[m] / r_load + i_a)))
        out.update(ton_cmd_ns=s["ton_cmd_ns"], period_ns=s["period_ns"], f_mhz=1e3 / s["period_ns"], peak_a=s["peak_a"],
                   i_out_a=i_out, p_out_w=p_out, books_w=s["books_w"], loss_w=s["books_total_w"],
                   eff_books=p_out / (p_out + s["books_total_w"]))
    r1 = bool(w["status"] == "COMPLETED" and not w["shoot_on"] and not w["overlaps"] and not w["forced"]
              and w["peak_whole"] <= I_LIM and w["vds_whole"] <= V_LIM)
    r2 = bool(abs(out["vo_end_min_v"] - 1.0) <= BAND_END and abs(out["vo_end_max_v"] - 1.0) <= BAND_END
              and (ev is None or (abs(out["vo_after_min_v"] - 1.0) <= BAND_ALL and abs(out["vo_after_max_v"] - 1.0) <= BAND_ALL)))
    out["criteria"] = {"r1": r1, "r2": r2}
    return out


def coverage(i_lo, i_hi):
    """The total-load intervals N_MOD equal modules cover with n of them on, each inside [i_lo, i_hi], and the gaps
    between those intervals below N_MOD i_hi."""
    iv = [{"modules_on": n, "from_a": n * i_lo, "to_a": n * i_hi} for n in range(1, N_MOD + 1)]
    gaps, top = [], 0.0
    for q in iv:
        if q["from_a"] > top + 1e-9:
            gaps.append([top, q["from_a"]])
        top = max(top, q["to_a"])
    return {"i_module_range_a": [i_lo, i_hi], "intervals": iv, "gaps_a": gaps}


def system(points):
    """points: [(module current A, loss W)] of the rows that regulate, full load included. coverage() of that range,
    and for sample total loads: all modules on, and the number of modules on (1..N_MOD) with the least loss among
    those that keep every running module inside the tested range."""
    pts = sorted(points)
    i_lo, i_hi = pts[0][0], pts[-1][0]
    loss = lambda i: float(np.interp(i, [p[0] for p in pts], [p[1] for p in pts]))
    rows = []
    for tot in TOTALS:
        row = {"i_total_a": tot, "share": tot / (N_MOD * I_FULL)}
        per = tot / N_MOD
        row["all_on"] = ({"i_module_a": per, "loss_w": N_MOD * loss(per), "eff_books": tot / (tot + N_MOD * loss(per))}
                         if i_lo - 1e-6 <= per <= i_hi + 1e-6 else None)
        best = None
        for n in range(1, N_MOD + 1):
            per = tot / n
            if i_lo - 1e-6 <= per <= i_hi + 1e-6 and (best is None or n * loss(per) < best["loss_w"]):
                best = {"modules_on": n, "i_module_a": per, "loss_w": n * loss(per), "eff_books": tot / (tot + n * loss(per))}
        row["shed"] = best
        rows.append(row)
    return dict(coverage(i_lo, i_hi), rows=rows)


def main():
    res = {"runs": {}}
    for f in sorted(COS.glob("run_f*.json"), key=lambda p: -int(p.stem[5:])):
        res["runs"][f.stem[4:]] = one(f)
    full = one(FULL) if FULL.exists() else None
    res["full_load"] = None if full is None else {k: v for k, v in full.items() if k != "criteria"}
    pred = HERE / "a207_predictions.json"
    res["d63"] = json.loads(pred.read_text())["rows"] if pred.exists() else {}
    ok = [n for n, m in res["runs"].items() if all(m["criteria"].values())]
    res["lowest_passing"] = min(ok, key=lambda n: res["runs"][n]["share"]) if ok else None
    pts = [(m["i_out_a"], m["loss_w"]) for n, m in res["runs"].items() if n in ok and "loss_w" in m]
    if full is not None and "loss_w" in full:
        pts.append((full["i_out_a"], full["loss_w"]))
    res["system"] = system(pts) if len(pts) >= 2 else None
    reg = sorted([(m["ton_reg_ns"], m["i_out_a"]) for n, m in list(res["runs"].items()) + [("full", full or {})]
                  if m.get("criteria") and all(m["criteria"].values()) and "i_out_a" in m])
    if len(reg) >= 2:
        (t0, i0), (t1, i1) = reg[0], reg[1]
        lim = res["runs"][ok[0]]["ton_min_ns"]
        i_fl = i0 + (lim - t0) * (i1 - i0) / (t1 - t0)
        at = [m["i_out_a"] for m in res["runs"].values() if m["at_ton_min"] and "i_out_a" in m]
        res["floor"] = {"ton_limit_ns": lim, "from_rows_ns_a": [reg[0], reg[1]], "i_floor_a": i_fl, "share": i_fl / I_FULL,
                        "i_delivered_at_limit_a": [min(at), max(at)] if at else None, "coverage": coverage(i_fl, I_FULL)}
    (HERE / "a207_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    rows = ([("full", full)] if full else []) + list(res["runs"].items())
    for n, m in rows:
        d = res["d63"].get("f100" if n == "full" else n, {})
        b = m.get("books_w") or {}
        print(f"{n:5s} {m['status'][:4]} Vo end {m['vo_end_v']:.4f} ({m['vo_end_min_v']:.4f}..{m['vo_end_max_v']:.4f}, {m['vo_slope_mv_per_us']:+.3f} mV/us) "
              f"D63 {d.get('vo_end_v', float('nan')):.4f} | after {m.get('vo_after_min_v', float('nan')):.4f}..{m.get('vo_after_max_v', float('nan')):.4f} | "
              f"Ton register {m['ton_reg_ns']:.2f} ns (limit {m['ton_min_ns']:.2f}, at limit {m['at_ton_min']}, from {m.get('t_at_limit_us')} us) "
              f"command {m.get('ton_cmd_ns', float('nan')):.2f} ns T {m.get('period_ns', float('nan')):.1f} ns "
              f"{m.get('f_mhz', float('nan')):.2f} MHz | peak {m.get('peak_a')} post {m.get('post_pk')} whole {m['peak_whole']:.1f} | "
              f"V_DS {m['vds_whole']:.1f} | Iout {m.get('i_out_a', float('nan')):.1f} A loss {m.get('loss_w', float('nan')):.2f} W "
              f"({' '.join(f'{k} {v:.2f}' for k, v in b.items() if v)}) eff {100 * m.get('eff_books', float('nan')):.2f} % | "
              f"late {m.get('late_after')} holds {m['il_holds']} | {m.get('criteria', '')}")
    print("lowest passing:", res["lowest_passing"])
    for key in ("system", "floor"):
        c = (res.get(key) or {}).get("coverage", res.get(key)) if key == "floor" else res.get(key)
        if c:
            print(key, "module range", [round(x, 1) for x in c["i_module_range_a"]], "| covered:",
                  " ".join(f"{q['modules_on']}: {q['from_a']:.0f}-{q['to_a']:.0f} A" for q in c["intervals"]),
                  "| gaps:", " ".join(f"{a:.0f}-{b:.0f} A" for a, b in c["gaps_a"]))
    if res.get("floor"):
        f = res["floor"]
        print(f"floor: Ton register reaches {f['ton_limit_ns']:.2f} ns at {f['i_floor_a']:.1f} A ({100 * f['share']:.1f} %), from {f['from_rows_ns_a']}; "
              f"delivered at the limit {f['i_delivered_at_limit_a']}")
    if res["system"]:
        for q in res["system"]["rows"]:
            a, s = q["all_on"], q["shed"]
            print(f"total {q['i_total_a']:6.1f} A ({100 * q['share']:5.1f} %) | all on: "
                  + ("outside the range" if a is None else f"{a['i_module_a']:.1f} A each, {a['loss_w']:.1f} W, {100 * a['eff_books']:.2f} %")
                  + " | shed: " + ("outside the range" if s is None else
                                   f"{s['modules_on']} on at {s['i_module_a']:.1f} A, {s['loss_w']:.1f} W, {100 * s['eff_books']:.2f} %"))


if __name__ == "__main__":
    main()
