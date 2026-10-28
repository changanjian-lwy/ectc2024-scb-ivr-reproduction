"""A259 analysis (BOUNDARY Section 2), records cosim/run_f_*.json against arm d (run_d_*, no fault path) and the
final configuration's records:
- f1: every FAULT row trips; the shorts by under-voltage before the limit suspends;
- f2: whole run V_DS <= 40 V and gate-record peak <= 300 A on every FAULT row; <= 200 A on the shorts;
- f3: from 2 us after the shutdown to the end, every phase current within +-5 A (fault_trace);
- f4: IDENT rows never trip and equal their records (A246's same over A236's KEYS).
The ladder after the trip (max |rail - Vin / 4| in the trace's last sample) is reported, not scored.
  python3 a259_analyze.py -> a259_summary.json"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TA = HERE.parent
D = TA / "A259_p24_fault_trip" / "cosim"                       # arm d by its own path (preflight runs a copy)


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MC = _load("a259_make_cfgs", HERE / "make_cfgs.py")
A36 = _load("a256_analyze", TA / "A256_p24_limit_suspends_on_overload" / "a256_analyze.py").A36
V_LIM, PK_LIM, PK_SHORT, I_REST, T_REST = 40.0, 300.0, 200.0, 5.0, 2e-6


def fault_row(f):
    d = json.loads(f.read_text())
    t0 = d["cfg"]["short"]["t_us"] * 1e-6
    g = d["gate_offs_last"]
    susp = [x["t_s"] for x in d.get("ocp_susp", []) if x["on"] == 1 and x["t_s"] >= t0]
    fr = d.get("fault")
    m = {"peak_a": max(e["i_max_a"] for e in g), "vds_v": max(d["vds_max_v"]),
         "susp_us": round(1e6 * (susp[0] - t0), 3) if susp else None, "fault": fr}
    if fr is not None:
        m["trip_us"] = round(1e6 * (fr["t_s"] - t0), 3)
        tr = [s for s in d.get("fault_trace", []) if s["t_s"] >= fr["t_off_s"] + T_REST]
        m["rest_max_a"] = max((max(abs(x) for x in s["i"]) for s in tr), default=None)
        if tr:
            v = [d["cfg"].get("vin", 48.0)] + tr[-1]["vcs"] + [0.0]
            m["ladder_end_v"] = max(abs(v[q] - v[q + 1] - v[0] / 4) for q in range(4))
    return m


def main():
    res = {"fault_rows": {}, "ident_rows": {}, "criteria": {}}
    done = []
    for row in MC.FAULT_ROWS:
        f = HERE / "cosim" / f"run_f_{row}.json"
        if not f.exists():
            continue
        done.append(row)
        m = fault_row(f)
        m["arm_d"] = {k: v for k, v in fault_row(D / f"run_d_{row}.json").items() if k != "fault"}
        short = row.startswith("sh")
        fr = m["fault"]
        m["f1"] = fr is not None and (not short or (fr["cause"] == "uv" and m["susp_us"] is None))
        m["f2"] = m["vds_v"] <= V_LIM and m["peak_a"] <= (PK_SHORT if short else PK_LIM)
        m["f3"] = fr is not None and m.get("rest_max_a") is not None and m["rest_max_a"] <= I_REST
        res["fault_rows"][row] = m
    for row, (_, ref) in MC.IDENT.items():
        f = HERE / "cosim" / f"run_f_{row}.json"
        if not f.exists():
            continue
        done.append(row)
        d = json.loads(f.read_text())
        eq = A36.same(f, ref)
        res["ident_rows"][row] = {"same": eq, "fault": d.get("fault"), "f4": all(eq.values()) and d.get("fault") is None}
    fr, ir = res["fault_rows"].values(), res["ident_rows"].values()
    res["criteria"] = {"f1": all(m["f1"] for m in fr), "f2": all(m["f2"] for m in fr), "f3": all(m["f3"] for m in fr),
                       "f4": all(m["f4"] for m in ir), "complete": len(done) == len(MC.FAULT_ROWS) + len(MC.IDENT)}
    (HERE / "a259_summary.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    for row, m in res["fault_rows"].items():
        f = m["fault"] or {}
        print(f"{row:11s} trip {f.get('cause')} at {m.get('trip_us')} us (susp {m['susp_us']}), peak {m['peak_a']:.1f} A "
              f"(d {m['arm_d']['peak_a']:.1f}), V_DS {m['vds_v']:.1f} V (d {m['arm_d']['vds_v']:.1f}), rest "
              f"{m.get('rest_max_a')}, ladder {m.get('ladder_end_v')} | f1 {m['f1']} f2 {m['f2']} f3 {m['f3']}")
    for row, m in res["ident_rows"].items():
        print(f"{row:11s} f4 {m['f4']} (fault {m['fault']}, unequal {[k for k, v in m['same'].items() if not v]})")
    print("criteria", res["criteria"])


if __name__ == "__main__":
    main()
