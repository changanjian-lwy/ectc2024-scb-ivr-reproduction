"""A249 trace (post hoc, BOUNDARY Section 4: c1 passes, c2 misses on p_S75h_100k): what the learner's per-period
adaptation bought there, and on the start-up row u_S75h_30 (passes, but the registered risk), against the fixed arms.
- train: each pulse's Vo minimum (the load returns to i_hi at 310 + 10 n us), Vo and Ton across the first release;
- start-up: the ladder's deviation max |rail - Vin / 4| after mode P;
- both: per window and phase, the period and the valley (low-side turn-offs), the actual delay (t_act - t_lo) and V_DS
  at the actual turn-on of the learned turn-ons.
  python3 a249_trace.py -> a249_trace.json"""
from __future__ import annotations

import bisect
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
COS = HERE / "cosim"
TRAIN = {"s": COS / "run_s_p_S75h_100k.json", "o": COS / "run_o_p_S75h_100k.json",
         "ref": TA / "A246_p24_held_report_floor" / "cosim" / "run_h_p_S75h_100k.json"}
START = {"s": COS / "run_s_u_S75h_30.json", "o": COS / "run_o_u_S75h_30.json",
         "ref": TA / "A245_p24_reverse_conduction_delay" / "cosim" / "run_r_u_S75h_30.json"}
TRAIN_WIN = ((300, 305), (305, 310), (310, 315), (315, 320))
START_WIN = ((96, 110), (110, 130), (130, 160), (250, 300))
MAX_GAP_NS = 60.0


def rails(x):
    v = np.array([x["vin_v"]] + list(x["vcs_v"]) + [0.0])
    return v[:-1] - v[1:]


def turnons(d, ph):
    """(t_act, actual delay ns, V_DS at the actual turn-on) of phase ph's learned turn-ons. A turn-on commanded with
    V_DS <= 0 (node already clamped) is not deferred and has no t_act_s; its command instant stands in."""
    lo = sorted((x["t_s"], x["i_a"]) for x in d["lowoffs_last"] if x["phase"] == ph)
    out = []
    for x in d["turnons_last"]:
        if x["phase"] != ph or x["how"] != 0:
            continue
        t, v = x.get("t_act_s", x["t_s"]), x.get("vds_act_v", x["vds_v"])
        j = bisect.bisect_left(lo, (t, -1e9)) - 1
        if j >= 0 and (t - lo[j][0]) * 1e9 <= MAX_GAP_NS:
            out.append((t, (t - lo[j][0]) * 1e9, v))
    return out


def windows(d, wins):
    res = {}
    for w0, w1 in wins:
        a, b, row = w0 * 1e-6, w1 * 1e-6, {}
        for ph in (1, 2, 3, 4):
            lo = [(x["t_s"], x["i_a"]) for x in d["lowoffs_last"] if x["phase"] == ph and a <= x["t_s"] < b]
            on = [t for t in turnons(d, ph) if a <= t[0] < b]
            row[ph] = {"period_ns": float(np.mean(np.diff([t for t, _ in lo])) * 1e9) if len(lo) > 1 else None,
                       "valley_a": float(np.mean([i for _, i in lo])) if lo else None,
                       "delay_ns": float(np.median([t[1] for t in on])) if on else None,
                       "vds_v": float(np.median([t[2] for t in on])) if on else None,
                       "vds_max_v": float(np.max([t[2] for t in on])) if on else None}
        res[f"{w0}-{w1}"] = row
    return res


def at(sec, t_us):
    return min(sec, key=lambda x: abs(x["t_s"] - t_us * 1e-6))


def train(d):
    sec = d["sections"]
    pulses = [min(x["vo"] for x in sec if (300 + 10 * n) * 1e-6 <= x["t_s"] < (310 + 10 * n) * 1e-6) for n in range(30)]
    first = {t: {"vo_v": at(sec, t)["vo"], "ton_lsb": at(sec, t)["ton_lsb"]} for t in (306.0, 307.5, 309.5, 310.0, 311.0)}
    return {"pulse_vo_min_v": pulses, "first_release": first, "windows": windows(d, TRAIN_WIN)}


def start(d):
    sec, tp = d["sections"], d["t_mode_p_s"]
    dev = [(x["t_s"] * 1e6, float(np.max(np.abs(rails(x) - x["vin_v"] / 4)))) for x in sec if x["t_s"] >= tp]
    worst = max(dev, key=lambda z: z[1])
    r140 = rails(at(sec, 140.0))
    return {"dev_max_v": worst[1], "dev_max_t_us": worst[0],
            "dev_v": {t: min(dev, key=lambda z: abs(z[0] - t))[1] for t in (110, 140, 160, 200, 250, 299)},
            "rails_140us_v": [float(r) for r in r140], "windows": windows(d, START_WIN)}


def main():
    out = {"train_p_S75h_100k": {k: train(json.loads(f.read_text())) for k, f in TRAIN.items()},
           "start_u_S75h_30": {k: start(json.loads(f.read_text())) for k, f in START.items()}}
    (HERE / "a249_trace.json").write_text(json.dumps(out, indent=1) + "\n")
    tr, st = out["train_p_S75h_100k"], out["start_u_S75h_30"]
    for k in tr:
        p = tr[k]["pulse_vo_min_v"]
        w = tr[k]["windows"]["305-310"]
        print(f"train {k:3s} pulse 1 {p[1] * 1e3:.1f} mV, min {min(p) * 1e3:.1f} mV at pulse {int(np.argmin(p))}, "
              f"Ton@310 {tr[k]['first_release'][310.0]['ton_lsb']}, ph3/4 delay {w[3]['delay_ns']:.1f}/{w[4]['delay_ns']:.1f} ns, "
              f"valley {w[3]['valley_a']:.1f}/{w[4]['valley_a']:.1f} A")
    for k in st:
        print(f"start {k:3s} dev max {st[k]['dev_max_v']:.2f} V at {st[k]['dev_max_t_us']:.0f} us, dev@140 {st[k]['dev_v'][140]:.2f}, "
              f"@299 {st[k]['dev_v'][299]:.2f}, rails@140 {[round(r, 2) for r in st[k]['rails_140us_v']]}")


if __name__ == "__main__":
    main()
