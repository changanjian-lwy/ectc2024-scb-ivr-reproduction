"""A208 analysis (BOUNDARY Section 2).
 i1, i2 identity: a208_identity.json, written by `identity` from the regression log and the 14 us records in tmp/.
Per row (A207's numbers from a207_analyze.one, with the limit read from cfg "ton_min_ns"):
 r1 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V;
 r2 Vo within 1 V +- 10 mV over the last 20 us;
 r3 Vo within 1 V +- 50 mV at all times after the release;
 r4 over the last 20 us every low-side turn-off current within [-20, -12] A and no late fire.
A row "works" with r1, r2 and r4; r3 belongs to the size of the release. From the rows that work, A207's 75 % row and
A206's full-load run: the load ranges four equal modules cover (a207_analyze.coverage / system; a composition).
  python3 a208_analyze.py identity   -> a208_identity.json
  python3 a208_analyze.py            -> a208_summary.json"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
PROJECT = HERE.parents[2]
_s = importlib.util.spec_from_file_location("a207_analyze", TA / "A207_p24_load_range" / "a207_analyze.py")
A7 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(A7)
COS = HERE / "cosim"
A207_ROW = TA / "A207_p24_load_range" / "cosim" / "run_f75.json"
BAND_END, BAND_ALL, T_WIN = 0.010, 0.050, 20e-6
VALLEY = (-20.0, -12.0)


def one(path):
    m = A7.one(path)
    r = json.loads(Path(path).read_text())
    lsb, cfg = r["lsb_s"], r["cfg"]
    ts = np.array([q["t_s"] for q in r["sections"]]); vo = np.array([q["vo"] for q in r["sections"]])
    tl = np.array([q["ton_lsb"] for q in r["sections"]], float) * lsb * 1e9
    lim = round(cfg.get("ton_min_ns", 0.5 * cfg["ton_ns"]) * 1e-9 / lsb) * lsb * 1e9
    te = float(ts[-1])
    w10, w20 = ts >= te - A7.A6.WIN_US * 1e-6, ts >= te - T_WIN
    m.update(ton_min_ns=lim, at_ton_min=bool(tl[w10].max() <= lim + 1e-9), ton_reg_end_ns=[float(tl[w20].min()), float(tl[w20].max())])
    ev = cfg.get("load_step")
    if ev:
        aft = ts >= ev["t_us"] * 1e-6
        k = np.where(aft & (tl <= lim + 1e-9))[0]
        m.update(ton_reg_min_after_ns=float(tl[aft].min()), sections_at_limit=int(k.size),
                 t_at_limit_us=None if not k.size else 1e6 * float(ts[k[0]] - ev["t_us"] * 1e-6))
    lo = [e for e in r["lowoffs_last"] if e["t_s"] >= te - T_WIN]
    m["valley_end_a"] = {str(q): [min(e["i_a"] for e in lo if e["phase"] == q), max(e["i_a"] for e in lo if e["phase"] == q)]
                         for q in (1, 2, 3, 4) if any(e["phase"] == q for e in lo)}
    k0 = int(np.searchsorted(ts, te - T_WIN, side="right")) - 1
    m["late_end"] = (np.array(r["sections"][-1]["late"]) - np.array(r["sections"][k0]["late"])).tolist()
    va = [x for v in m["valley_end_a"].values() for x in v]
    crit = {"r1": m["criteria"]["r1"],
            "r2": bool(abs(vo[w20].min() - 1.0) <= BAND_END and abs(vo[w20].max() - 1.0) <= BAND_END)}
    if ev:
        crit["r3"] = bool(abs(vo[aft].min() - 1.0) <= BAND_ALL and abs(vo[aft].max() - 1.0) <= BAND_ALL)
    crit["r4"] = bool(len(m["valley_end_a"]) == 4 and min(va) >= VALLEY[0] and max(va) <= VALLEY[1] and not any(m["late_end"]))
    m["criteria"] = crit
    m["works"] = bool(crit["r1"] and crit["r2"] and crit["r4"])
    return m


def identity():
    log = (PROJECT / "tmp" / "logs" / "a208_regression.log").read_text()
    cases = re.findall(r"^(\S+)\s+(PASS|FAIL)", log, re.M)
    ref = json.loads((PROJECT / "tmp" / "a207" / "run_smoke.json").read_text())
    i2 = {}
    for n in ("absent", "default"):
        r = json.loads((PROJECT / "tmp" / "a208" / f"run_id_{n}.json").read_text())
        i2[n] = bool(r["sections"] == ref["sections"] and r["edges_log"] == ref["edges_log"] and r["snaps"] == ref["snaps"]
                     and r["gate_offs_last"] == ref["gate_offs_last"])
    out = {"i1": {"cases": dict(cases), "pass": bool(len(cases) == 4 and all(v == "PASS" for _, v in cases))},
           "i2": dict(i2, sections=len(ref["sections"]), edges=len(ref["edges_log"]), reference_commit=ref["provenance"]["git_commit"][:7],
                      **{"pass": all(i2.values())})}
    (HERE / "a208_identity.json").write_text(json.dumps(out, indent=1) + "\n")
    print(out)


def main():
    res = {"runs": {}}
    idf = HERE / "a208_identity.json"
    if idf.exists():
        res["criteria_identity"] = json.loads(idf.read_text())
    for f in sorted(COS.glob("run_*.json"), key=lambda p: (p.stem[4], -int(re.sub(r"\D", "", p.stem)))):
        res["runs"][f.stem[4:]] = one(f)
    ref = {"f75": one(A207_ROW) if A207_ROW.exists() else None, "full": one(A7.FULL) if A7.FULL.exists() else None}
    res["reference"] = {k: (None if v is None else {a: b for a, b in v.items() if a != "criteria"}) for k, v in ref.items()}
    pred = HERE / "a208_predictions.json"
    res["d63"] = json.loads(pred.read_text())["rows"] if pred.exists() else {}
    ok = [n for n, m in res["runs"].items() if m["works"]]
    res["lowest_working"] = min(ok, key=lambda n: res["runs"][n]["share"]) if ok else None
    pts = [(m["i_out_a"], m["loss_w"]) for n, m in res["runs"].items() if n in ok and "loss_w" in m]
    pts += [(v["i_out_a"], v["loss_w"]) for v in ref.values() if v is not None and "loss_w" in v]
    res["system"] = A7.system(pts) if len(pts) >= 2 else None
    (HERE / "a208_summary.json").write_text(json.dumps(res, indent=1) + "\n")
    print("identity", res.get("criteria_identity"))
    for n, m in [(k, v) for k, v in ref.items() if v][::-1] + list(res["runs"].items()):
        d = res["d63"].get(n, {})
        b = m.get("books_w") or {}
        print(f"{n:5s} {m['status'][:4]} Vo end {m['vo_end_v']:.4f} ({m['vo_end_min_v']:.4f}..{m['vo_end_max_v']:.4f}) after "
              f"{m.get('vo_after_min_v', float('nan')):.4f}..{m.get('vo_after_max_v', float('nan')):.4f} (D63 max {d.get('vo_max_v', float('nan')):.4f}) | "
              f"register {m['ton_reg_ns']:.2f} ns (D63 {d.get('register_ns', float('nan')):.2f}; end {m['ton_reg_end_ns'][0]:.2f}..{m['ton_reg_end_ns'][1]:.2f}; "
              f"lowest {m.get('ton_reg_min_after_ns', float('nan')):.2f}; limit {m['ton_min_ns']:.2f}, {m.get('sections_at_limit')} sections at it) "
              f"command {m.get('ton_cmd_ns', float('nan')):.2f} ns | T {m.get('period_ns', float('nan')):.1f} ns {m.get('f_mhz', float('nan')):.2f} MHz | "
              f"peak {[round(x, 1) for x in m.get('peak_a', [])]} post {m.get('post_pk')} | V_DS {m['vds_whole']:.1f} | valleys {m['valley_end_a']} late {m['late_end']} "
              f"holds {m['il_holds']} | Iout {m.get('i_out_a', float('nan')):.1f} A loss {m.get('loss_w', float('nan')):.2f} W "
              f"({' '.join(f'{k} {v:.2f}' for k, v in b.items() if v)}) eff {100 * m.get('eff_books', float('nan')):.2f} % | {m['criteria']} works {m['works']}")
    print("lowest working:", res["lowest_working"])
    if res["system"]:
        c = res["system"]
        print("module range", [round(x, 1) for x in c["i_module_range_a"]], "| covered:",
              " ".join(f"{q['modules_on']}: {q['from_a']:.0f}-{q['to_a']:.0f} A" for q in c["intervals"]),
              "| gaps:", " ".join(f"{a:.0f}-{b:.0f} A" for a, b in c["gaps_a"]))
        for q in c["rows"]:
            a, s = q["all_on"], q["shed"]
            print(f"total {q['i_total_a']:6.1f} A | all on: " + ("outside" if a is None else f"{a['i_module_a']:.1f} A each, {a['loss_w']:.1f} W, {100 * a['eff_books']:.2f} %")
                  + " | fewest loss: " + ("outside" if s is None else f"{s['modules_on']} on at {s['i_module_a']:.1f} A, {s['loss_w']:.1f} W, {100 * s['eff_books']:.2f} %"))


if __name__ == "__main__":
    identity() if sys.argv[1:2] == ["identity"] else main()
