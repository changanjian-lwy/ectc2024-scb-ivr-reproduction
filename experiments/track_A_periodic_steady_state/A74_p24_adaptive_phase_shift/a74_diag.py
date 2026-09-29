"""A74 BOUNDARY Section 8: diagnostic reruns 0d/1d. Gate (bit-identical to runs 0/1) and per-phase
low-side turn-off / high-side turn-on statistics over the last 50 cycles. Writes a74_diag.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PAIRS = {"r0d_fixed_rs20_diag": "r0_fixed_rs20", "r1d_adaptive_rs20_diag": "r1_adaptive_rs20"}
LAST = 50


def load(name):
    return json.loads((HERE / f"run_{name}.json").read_text())


def stats(xs):
    return None if not xs else {"mean": float(np.mean(xs)), "min": float(np.min(xs)), "max": float(np.max(xs))}


def main():
    out = {}
    for diag, orig in PAIRS.items():
        a, b = load(orig), load(diag)
        dv = max(abs(x - y) for s, r in zip(a["sections"], b["sections"]) for x, y in zip(s["v"] + s["i"], r["v"] + r["i"]))
        gate = {"sections": [a["sections_total"], b["sections_total"]], "max_abs_diff_v_i": dv,
                "end_y_equal": a["end"]["y"] == b["end"]["y"],
                "pass": bool(dv == 0.0 and a["sections_total"] == b["sections_total"] and a["end"]["y"] == b["end"]["y"])}
        e = b["end"]; tot = b["sections_total"] - 1; n = len(b["sections"][-1]["i"])
        lo = [x for x in e["lowoffs_last"] if x["cycle"] >= tot - LAST and x["mode"] == "P"]
        on = [x for x in e["turnons_last"] if x["cycle"] >= tot - LAST and x["mode"] == "P"]
        ph = {}
        for k in range(1, n + 1):
            lk = [x for x in lo if x["phase"] == k]; ok = [x for x in on if x["phase"] == k]
            ph[k] = {
                "lowoff_how": sorted({x["how"] for x in lk}),
                "lowoff_i_a": stats([x["i_a"] for x in lk]),
                "lowoff_t_since_ref_ns": stats([x["t_since_ref_s"] * 1e9 for x in lk]),
                "lowoff_vds_high_v": stats([x["vds_high_v"] for x in lk]),
                "lowoff_states_first": lk[0]["states"] if lk else None,
                "turnon_how": sorted({x["how"] for x in ok}),
                "turnon_vds_v": stats([x["vds_v"] for x in ok]),
                "turnon_vds_min_since_lo_v": stats([x["vds_min_v"] for x in ok]),
                "turnon_t_since_lo_ns": stats([x["t_since_lo_s"] * 1e9 for x in ok]),
                "turnon_i_a": stats([x["i_a"] for x in ok]),
            }
        out[diag] = {"gate_vs": orig, "gate": gate, "phases": ph}
        print(f"== {diag}: gate {gate}")
        for k, r in ph.items():
            f = lambda s, key="mean": None if s is None else round(s[key], 3)
            print(f"  phase {k}: low-off {r['lowoff_how']} i {f(r['lowoff_i_a'])} A at t_ref+{f(r['lowoff_t_since_ref_ns'])} ns "
                  f"Vds_high {f(r['lowoff_vds_high_v'])} | turn-on {r['turnon_how']} after {f(r['turnon_t_since_lo_ns'])} ns, "
                  f"i {f(r['turnon_i_a'])} A, Vds {f(r['turnon_vds_v'])} V, min Vds since low-off {f(r['turnon_vds_min_since_lo_v'])} V")
    (HERE / "a74_diag.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
