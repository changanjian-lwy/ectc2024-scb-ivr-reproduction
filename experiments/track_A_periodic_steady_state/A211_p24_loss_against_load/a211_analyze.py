"""A211 analysis (BOUNDARY Sections 1-2). Per row: a210_analyze.one (r1, r2, r4 with the board's valley band; the
loss books of the last 10 us). Curves: the plant's semiconductor loss against the module current for S75 and N75
at 25 C (A211's rows + A210's) and N0 (A206's full-load run, A207's 75 %, A208's 60-20 %), rows that work with every
high-side turn-on completed. Composition: four equal modules of one board class, equal sharing, an idle module at
0 W: for each system load the loss with all four on and with the number of modules on that loses least (each running
module inside its board's tested range; loss linear between the rows). Not a run.
  python3 a211_analyze.py -> a211_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a210_analyze", TA / "A210_p24_load_range_boards" / "a210_analyze.py")
A10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A10)
A8 = A10.A8
COS = HERE / "cosim"
N_MOD, I_FULL = 4, 250.0
SHARES = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1)
SAVE_MIN, SHARE_MAX = 0.20, 0.50
N0_ROWS = [TA / "A206_p24_low_side_zvs_turn_on" / "cosim" / "run_E_N0_steady_ls0p3_t.json",
           TA / "A207_p24_load_range" / "cosim" / "run_f75.json"] + \
          [TA / "A208_p24_ton_lower_limit" / "cosim" / f"run_m{p}.json" for p in (60, 50, 40, 30, 20)]


def point(m):
    return {"i_a": m["i_out_a"], "loss_w": m["loss_w"], "eff_books": m["eff_books"], "f_mhz": m["f_mhz"],
            "edges_high_w": m["books_w"]["edges_high"], "edges_low_w": m["books_w"]["edges_low"],
            "conduction_w": m["books_w"]["switches_high"] + m["books_w"]["switches_low"], "ton_reg_ns": m["ton_reg_ns"],
            "works": m["works"], "hs_incomplete_share": m.get("hs_incomplete_share", 0.0)}


def compose(curve):
    pts = sorted((p["i_a"], p["loss_w"]) for p in curve if p["works"] and not p["hs_incomplete_share"])
    i_lo, i_hi = pts[0][0], pts[-1][0]
    loss = lambda i: float(np.interp(i, [p[0] for p in pts], [p[1] for p in pts]))
    ok = lambda i: i_lo - 0.5 <= i <= i_hi + 0.5
    rows = []
    for s in SHARES:
        tot = s * N_MOD * I_FULL
        row = {"share": s, "i_total_a": tot, "all_on": None, "best": None, "saving": None}
        if ok(tot / N_MOD):
            row["all_on"] = {"i_module_a": tot / N_MOD, "loss_w": N_MOD * loss(tot / N_MOD)}
            row["all_on"]["eff_books"] = tot / (tot + row["all_on"]["loss_w"])
        for n in range(1, N_MOD + 1):
            if ok(tot / n) and (row["best"] is None or n * loss(tot / n) < row["best"]["loss_w"] - 1e-9):
                row["best"] = {"modules_on": n, "i_module_a": tot / n, "loss_w": n * loss(tot / n)}
        if row["best"]:
            row["best"]["eff_books"] = tot / (tot + row["best"]["loss_w"])
        if row["all_on"] and row["best"]:
            row["saving"] = 1.0 - row["best"]["loss_w"] / row["all_on"]["loss_w"]
        rows.append(row)
    pays = [r for r in rows if r["saving"] is not None and r["share"] <= SHARE_MAX and r["saving"] >= SAVE_MIN]
    return {"i_module_range_a": [i_lo, i_hi], "rows": rows,
            "shedding_pays": bool(pays), "pays_from_share": max((r["share"] for r in pays), default=None)}


def main():
    res = {"runs": {f.stem[4:]: A10.one(f) for f in sorted(COS.glob("run_e_*.json"))}}
    for m in res["runs"].values():
        m["criteria"] = {k: v for k, v in m["criteria"].items() if k != "r3"}       # r3 is not a criterion here
    curves = {"S75_25": [], "N75_25": [], "N0_25": []}
    for n, m in res["runs"].items():
        curves["_".join(n.split("_")[1:3])].append(dict(point(m), row=n))
    for f in sorted((TA / "A210_p24_load_range_boards" / "cosim").glob("run_r_*_25_*.json")):
        m = A10.one(f)
        curves["_".join(f.stem.split("_")[2:4])].append(dict(point(m), row="A210 " + f.stem[4:]))
    for f in N0_ROWS:
        if f.exists():
            m = A8.one(f)
            curves["N0_25"].append(dict(point(m), row=f.parent.parent.name[:4] + " " + f.stem[4:]))
    res["curves"] = {k: sorted(v, key=lambda p: -p["i_a"]) for k, v in curves.items() if v}
    res["system"] = {k: compose(v) for k, v in res["curves"].items() if sum(p["works"] and not p["hs_incomplete_share"] for p in v) >= 2}
    (HERE / "a211_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    for k, v in res["curves"].items():
        print(k)
        for p in v:
            print(f"   {p['i_a']:6.1f} A loss {p['loss_w']:6.2f} W (HS edges {p['edges_high_w']:.2f}, LS edges {p['edges_low_w']:.2f}, conduction {p['conduction_w']:.2f}) "
                  f"eff {100 * p['eff_books']:.2f} % {p['f_mhz']:.2f} MHz register {p['ton_reg_ns']:.2f} ns works {p['works']} incomplete {p['hs_incomplete_share']:.2f} | {p['row']}")
    for k, c in res["system"].items():
        print(k, "module range", [round(x, 1) for x in c["i_module_range_a"]], "| shedding pays:", c["shedding_pays"], "from", c["pays_from_share"])
        for r in c["rows"]:
            a, b = r["all_on"], r["best"]
            print(f"   {100 * r['share']:5.1f} % | all on: " + ("-" if a is None else f"{a['loss_w']:.1f} W {100 * a['eff_books']:.2f} %") + " | best: "
                  + ("-" if b is None else f"{b['modules_on']} on, {b['loss_w']:.1f} W {100 * b['eff_books']:.2f} %")
                  + (f" | saves {100 * r['saving']:.0f} %" if r["saving"] is not None else ""))
    print({n: m["criteria"] for n, m in res["runs"].items()})


if __name__ == "__main__":
    main()
