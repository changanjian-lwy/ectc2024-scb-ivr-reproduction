"""A194 cosim cfgs: random stimuli on the final plant (V5) with the adopted start-up (A188), the cold trim table (A190)
and the lead by board class (A192: 9.5 ns slow, 8 ns otherwise), t_il 1.0 ns. One module.
Draws (numpy default_rng(194), 36 = 14 early + 22 settled):
- board: N0, N75, N13 (nominal devices, L x 1 / 0.75 / 1.3), F0 (fast), S0, S75, S80 (slow, L x 1 / 0.75 / 0.8);
- temperature: -40, 0, 25, 125 C (F0: 25, 125 only - the cold table has no fast corner);
- stimulus: rising line step 1-4.8 V over 1-40 us (35 %), falling 1-4.8 V over 1-40 us (25 %), falling 4.8-8 V over
  10-40 us (15 %), load step +-(20-62.5) A (25 %); slews log-uniform;
- instant: early = 146-300 us (from 2 us after the 144 us handover: lead ramp and settling), settled = 500 us + one
  period (uniform phase); end = instant + 400 us.
Cfg = the board's A186 25 C cfg with hand_vo_v 1.045 (A188); below 25 C ton_s += A190's table; S80 from A187's trims.
  python3 make_cfgs.py   draws.json, cosim/cfg_*.json, cosim/ORDER.txt"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TA = HERE.parent
A186 = TA / "A186_p24_vo_triggered_handover" / "cosim"
A190 = TA / "A190_p24_cold_trim_compensation"
DT = json.loads((A190 / "table.json").read_text())["dton_ns"]
S80 = json.loads((TA / "A187_p24_slow_corner_inductance_hot" / "trims.json").read_text())["boards"]["S80"]
COS = HERE / "cosim"
L0, PER0, HAND_VO, POST = 2.9333333199999997e-09, 0.5048, 1.045, 400.0
BOARDS = {"N0": "nominal", "N75": "nominal", "N13": "nominal", "F0": "fast", "S0": "slow", "S75": "slow", "S80": "slow"}
TEMPS = {"m40": -40.0, "c0": 0.0, "25": 25.0, "hot": 125.0}
LEAD = {"slow": 9.5, "nominal": 8.0, "fast": 8.0}
N_EARLY, N_SETTLED, SEED = 14, 22, 194


def board(b, tk):
    """The board's cfg at temperature key tk, without a stimulus."""
    if b == "S80":
        c = json.loads((A186 / "cfg_S75_25_p0.json").read_text())
        c = dict(c, circuit=dict(c["circuit"], L=L0 * S80[0]), ton_s_ns=S80[1], ton_ns=S80[2])
    else:
        c = json.loads((A186 / f"cfg_{b}_25_p0.json").read_text())
    corner = BOARDS[b]
    g = {k: v for k, v in c["gate"].items() if k != "temp"}
    ton_s = c["ton_s_ns"]
    if tk != "25":
        g["temp"] = TEMPS[tk]
    if tk in ("m40", "c0"):
        ton_s = round(ton_s + DT[corner][tk], 3)
    c = {k: v for k, v in c.items() if k not in ("line_step", "load_step")}
    return dict(c, gate=g, ton_s_ns=ton_s, hand_vo_v=HAND_VO, driver=dict(c["driver"], hs_on_lead_ns=LEAD[corner]))


def check_against_a190():
    """The cold cfgs built here equal A190's own (start-up part)."""
    for b, tk in (("S75", "m40"), ("N0", "c0"), ("S80", "c0"), ("N13", "m40")):
        a = json.loads((A190 / "cosim" / f"cfg_{b}_{tk}.json").read_text())
        m = board(b, tk)
        skip = ("out", "note", "t_end_us", "line_step", "load_step", "driver")
        diff = [k for k in set(a) | set(m) if k not in skip and a.get(k) != m.get(k)]
        assert not diff, (b, tk, diff, [(a.get(k), m.get(k)) for k in diff])
        assert {k: v for k, v in a["driver"].items() if k != "hs_on_lead_ns"} == {k: v for k, v in m["driver"].items() if k != "hs_on_lead_ns"}


def draws():
    rng = np.random.default_rng(SEED)
    out = []
    for k in range(N_EARLY + N_SETTLED):
        b = str(rng.choice(list(BOARDS)))
        tk = str(rng.choice(["25", "hot"] if BOARDS[b] == "fast" else list(TEMPS)))
        kind = str(rng.choice(["rise", "fall", "fall8", "load"], p=[0.35, 0.25, 0.15, 0.25]))
        d = {"k": k, "board": b, "temp": tk, "kind": kind, "stratum": "early" if k < N_EARLY else "settled"}
        if kind == "load":
            d["i_a"] = round(float(rng.choice([-1.0, 1.0]) * rng.uniform(20.0, 62.5)), 2)
        else:
            lo, hi, s0 = {"rise": (1.0, 4.8, 1.0), "fall": (1.0, 4.8, 1.0), "fall8": (4.8, 8.0, 10.0)}[kind]
            d["dv"] = round(float((1.0 if kind == "rise" else -1.0) * rng.uniform(lo, hi)), 3)
            d["slew_us"] = round(float(np.exp(rng.uniform(np.log(s0), np.log(40.0)))), 3)
        sc = {"N75": 0.75, "S75": 0.75, "S80": 0.8, "N13": 1.3}.get(b, 1.0)
        d["t_us"] = round(float(rng.uniform(146.0, 300.0) if k < N_EARLY else 500.0 + rng.uniform(0.0, PER0 * sc)), 4)
        out.append(d)
    return out


def main():
    check_against_a190()
    ds = draws()
    (HERE / "draws.json").write_text(json.dumps(ds, indent=1) + "\n")
    COS.mkdir(exist_ok=True)
    order = []
    for d in ds:
        name = f"r{d['k']:02d}_{d['board']}_{d['temp']}_{d['kind']}"
        c = board(d["board"], d["temp"])
        stim = ({"load_step": {"i_a": d["i_a"], "t_us": d["t_us"]}} if d["kind"] == "load" else
                {"line_step": {"dv": d["dv"], "slew_us": d["slew_us"], "t_us": d["t_us"]}})
        what = (f"load step {d['i_a']:+.2f} A" if d["kind"] == "load" else f"line step {d['dv']:+.3f} V over {d['slew_us']} us")
        c = dict(c, **stim, t_end_us=round(d["t_us"] + POST, 4), out=f"run_{name}.json",
                 note=f"A194 {name}: board {d['board']}, {TEMPS[d['temp']]:g} C, adopted start-up (A188 / A190), lead "
                      f"{c['driver']['hs_on_lead_ns']:g} ns, {what} at {d['t_us']} us ({d['stratum']})")
        (COS / f"cfg_{name}.json").write_text(json.dumps(c, indent=1) + "\n")
        order.append(name)
    (COS / "ORDER.txt").write_text("\n".join(order) + "\n")
    cnt = lambda key: {v: sum(1 for d in ds if d[key] == v) for v in sorted({d[key] for d in ds})}
    print(len(order), "cfgs |", cnt("board"), cnt("temp"), cnt("kind"))
    print("run-equivalents of 900 us:", round(sum(d["t_us"] + POST for d in ds) / 900.0, 1))


if __name__ == "__main__":
    main()
