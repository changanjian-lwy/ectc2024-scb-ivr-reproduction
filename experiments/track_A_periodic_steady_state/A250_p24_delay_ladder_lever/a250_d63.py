"""A250 replays (BOUNDARY Section 1): D63 with the A250 block from the S75h 75 A start-up's state at mode P's entry
(A249 run_s_u_S75h_30), the record's Vin ramp, to 300 us; phases' delays from a record (per 1 us) or a law.
D57 thresholds over 3-20 V (a250_ith.py -> a250_ith.json); t_val = A124's D57 valley times
scaled by sqrt(L); t_sw0 1.65 ns (A248); the RTL's Ton clamps (4 ns, 2 x ton_ns).
  python3 a250_d63.py -> a250_summary.json"""
from __future__ import annotations

import bisect
import importlib.util
import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np

from scb_ivr.p24_valley_map import Design, ValleyMap

HERE = Path(__file__).resolve().parent
TA = HERE.parent
_s = importlib.util.spec_from_file_location("a249_trace", TA / "A249_p24_fixed_delay_oracle" / "a249_trace.py")
TR = importlib.util.module_from_spec(_s)
_s.loader.exec_module(TR)
REC = {"s": TR.START["s"], "l": TR.START["ref"]}
LF, T_VAL_N0, LF_N0 = 2.2e-9, (10.933272e-9, 10.933272e-9, 10.933272e-9, 9.706958e-9), 2.9333333e-9
T_SW0, T_END, T_BACK = 1.65e-9, 300e-6, 13.5e-9
RUNS = {"rec_s": ("s", None, True), "rec_l": ("l", None, True), "rec_s_noq": ("s", None, False),
        "rec_l_noq": ("l", None, False), "c11": (11.0e-9, None, True), "c135": (13.5e-9, None, True),
        "evt1": (T_BACK, 1.0e-9, True), "evt2": (T_BACK, 2.0e-9, True)}


def design(cfg, vin, clamp_q=True, t_evt=None):
    ith = json.loads((HERE / "a250_ith.json").read_text())[f"{LF * 1e9:.3f}"]
    t_val = tuple(t * math.sqrt(LF / LF_N0) for t in T_VAL_N0)
    return Design(lf=LF, cs=cfg["circuit"]["cs"], r_load=cfg["circuit"]["r_load"], vin=vin, i_tgt=cfg["i_target"],
                  mode="floor", floor_a=cfg["lo_floor_a"], kp_ns=cfg["kp_ns_per_v"], ki_ns=cfg["ki_ns_per_v"],
                  kd_ns=cfg["kd_ns_per_v"], kd_db=cfg["kd_db"], ton_cfg_ns=cfg["ton_ns"], smax=cfg["lo_smax"],
                  rs_low_ns=cfg["rs_low_ns"], t_tr=t_val, ith=tuple(tuple(x) for x in ith), t_val=t_val, t_sw0=T_SW0,
                  clamp_q=clamp_q, t_evt=t_evt)


def record_delays(d):
    """Per phase, (t_us grid, median delay s) of the learned turn-ons (a249_trace.turnons) per 1 us."""
    out = []
    for ph in (1, 2, 3, 4):
        on = TR.turnons(d, ph)
        t = np.array([x[0] * 1e6 for x in on]); dl = np.array([x[1] for x in on])
        grid = np.arange(math.floor(t.min()), math.ceil(t.max()) + 1)
        med = [float(np.median(dl[(t >= g) & (t < g + 1)])) if np.any((t >= g) & (t < g + 1)) else np.nan for g in grid]
        med = np.array(med); ok = ~np.isnan(med)
        out.append((grid[ok], med[ok] * 1e-9))
    return out


def start_state(d):
    sec, tp = d["sections"], d["t_mode_p_s"]
    x = min(sec, key=lambda z: abs(z["t_s"] - tp))
    val = []
    for ph in (1, 2, 3, 4):
        lo = [z for z in d["lowoffs_last"] if z["phase"] == ph and z["t_s"] <= x["t_s"]]
        val.append(lo[-1]["i_a"])
    return x["t_s"], {"vo": x["vo"], "vc": list(x["vcs_v"]), "ton": x["ton_lsb"] * d["lsb_s"], "valley": val}


def replay(name):
    src, t_evt, cq = RUNS[name]
    ds = json.loads(REC["s"].read_text())
    t0, st = start_state(ds)
    ts = np.array([x["t_s"] for x in ds["sections"]]); vin = np.array([x["vin_v"] for x in ds["sections"]])
    d = design(ds["cfg"], float(np.interp(t0, ts, vin)), cq, t_evt)
    m = ValleyMap(d)
    m.ton_min, m.ton_max = ds["cfg"]["ton_min_ns"] * 1e-9, 2.0 * ds["cfg"]["ton_ns"] * 1e-9
    s = m.init_state(st["ton"])
    s.update(vo=st["vo"], vc=list(st["vc"]), valley=list(st["valley"]), t=t0)
    rd = record_delays(json.loads(REC[src].read_text())) if isinstance(src, str) else None
    ph1 = record_delays(ds)[0]
    rows = []
    while s["t"] < T_END:
        t = s["t"]
        if rd is not None:
            tt = [float(np.interp(t * 1e6, g, v)) for g, v in rd]
        else:
            tt = [float(np.interp(t * 1e6, *ph1))] + [src] * 3
        m.d = replace(d, t_tr=tuple(tt))
        rec = m.period(s, float(np.interp(t, ts, vin)), 0.0)
        v_in = float(np.interp(t, ts, vin))
        rows.append({"t_us": t * 1e6, "dev_v": max(abs(r - v_in / 4) for r in rec["rails"]), "rails": rec["rails"],
                     "vo": rec["vo"], "valley": rec["valley"], "depth": rec["depth"], "ton_ns": rec["ton"] * 1e9,
                     "t_on_ns": list(tt)})
        if not all(math.isfinite(v) and abs(v) < 1000 for v in rec["valley"] + rec["peak"]):
            rows[-1]["diverged"] = True
            break
    return rows


def summary(rows):
    dev = [r["dev_v"] for r in rows]
    i = int(np.argmax(dev))
    at = lambda tu: min(rows, key=lambda r: abs(r["t_us"] - tu))
    return {"peak_dev_v": dev[i], "peak_t_us": rows[i]["t_us"], "dev_140_v": at(140)["dev_v"],
            "dev_299_v": at(299)["dev_v"], "rails_140_v": at(140)["rails"], "diverged": bool(rows[-1].get("diverged")),
            "periods": len(rows)}


def criteria(S):
    s, l = S["rec_s"], S["rec_l"]
    k1 = abs(s["peak_dev_v"] - 6.4) <= 0.4 * 6.4 and abs(s["peak_t_us"] - 137) <= 15 and s["dev_140_v"] >= 3.0
    k2 = l["dev_140_v"] <= 1.5
    k3 = any(S[e]["dev_140_v"] <= 1.5 and S[e]["peak_dev_v"] <= l["peak_dev_v"] for e in ("evt1", "evt2"))
    return {"k1": bool(k1), "k2": bool(k2), "k3": bool(k3)}


def main():
    res = {n: replay(n) for n in RUNS}
    S = {n: summary(r) for n, r in res.items()}
    out = {"runs": S, "criteria": criteria(S), "traces": {n: [{k: r[k] for k in ("t_us", "dev_v", "rails", "valley",
                                                                                  "depth", "t_on_ns")} for r in rows[::4]]
                                                         for n, rows in res.items()}}
    (HERE / "a250_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for n, x in S.items():
        print(f"{n:10s} peak {x['peak_dev_v']:.2f} V at {x['peak_t_us']:.0f} us, @140 {x['dev_140_v']:.2f}, "
              f"@299 {x['dev_299_v']:.2f}, rails@140 {[round(v, 1) for v in x['rails_140_v']]}"
              + (" DIVERGED" if x["diverged"] else ""))
    print("criteria", out["criteria"])


if __name__ == "__main__":
    main()
