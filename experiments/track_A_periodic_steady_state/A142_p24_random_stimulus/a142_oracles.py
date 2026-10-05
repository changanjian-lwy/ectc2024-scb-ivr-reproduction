"""A142 event-level oracles on one cosim record (any module count) and their classification (BOUNDARY Section 2).
Window: where the turn-on and high-off lists overlap (each keeps the last 6000 events), from mode P + 20 us on.
Raw hits per module: duplicate turn-ons (same phase < 20 ns: floor_first = off-grid then on-grid, race = on-grid then
off-grid < 1 ns, other), order (turn-ons not in the interleave order 1..N, the second of a duplicate dropped), alt
(two turn-ons or two high-offs of one phase in a row), spike (a high-off current > 10 A above both adjacent periods of
its phase), how (a turn-on not predictive, how != 0). Known classes (not defects; Section 2): K1 race duplicates; K2
order hits within a falling line ramp + 2 us with dv < -5.5 V and |dv| / slew >= 4 V/us; K3 restarts (how 3) whose
phase's previous low-off current was positive; K4 spikes inside a line ramp + 1 us or a load step + 1 us; K5 (C13)
floor-first duplicates < 0.5 LSB apart (the floor's report rounds to t_lo, so floor_late cannot order them). Every other
hit is NEW; spikes within 60 ns after a floor-first duplicate count with it."""
from __future__ import annotations

import json
from pathlib import Path

N = 4
DUP_S, RACE_S, SPIKE_A, AFTER_S = 20e-9, 1e-9, 10.0, 60e-9


def module(md, t_lo, lsb, tdrv):
    def grid(t):
        q = (t - tdrv) / lsb
        return abs(q - round(q)) < 1e-3
    on = sorted((x for x in md["turnons_last"] if x["t_s"] >= t_lo), key=lambda x: x["t_s"])
    ho = sorted((x for x in md["highoffs_last"] if x["t_s"] >= t_lo), key=lambda x: x["t_s"])
    lo = sorted(md["lowoffs_last"], key=lambda x: x["t_s"])
    ev, last, keep = [], {}, []
    for x in on:
        a = last.get(x["phase"])
        if a is not None and x["t_s"] - a["t_s"] < DUP_S:
            dt = x["t_s"] - a["t_s"]
            kind = ("dup_floor_first" if not grid(a["t_s"]) and grid(x["t_s"]) else
                    "dup_race" if grid(a["t_s"]) and not grid(x["t_s"]) and dt < RACE_S else "dup_other")
            ev.append({"t_s": a["t_s"], "phase": x["phase"], "kind": kind, "dt_ns": dt * 1e9})
            continue
        last[x["phase"]] = x
        keep.append(x)
    for a, b in zip(keep, keep[1:]):
        if (b["phase"] - a["phase"]) % N != 1:
            ev.append({"t_s": b["t_s"], "phase": b["phase"], "kind": "order", "prev": a["phase"]})
    for k in range(1, N + 1):
        s = sorted([(x["t_s"], "on") for x in keep if x["phase"] == k] + [(x["t_s"], "ho") for x in ho if x["phase"] == k])
        ev += [{"t_s": b[0], "phase": k, "kind": "alt", "what": b[1]} for a, b in zip(s, s[1:]) if a[1] == b[1]]
        y = [(x["t_s"], x["i_a"]) for x in ho if x["phase"] == k]
        for i in range(1, len(y) - 1):
            ex = y[i][1] - max(y[i - 1][1], y[i + 1][1])
            if ex > SPIKE_A:
                ev.append({"t_s": y[i][0], "phase": k, "kind": "spike", "excess_a": ex, "i_a": y[i][1]})
    for x in keep:
        if x["how"] != 0:
            prev = [q for q in lo if q["phase"] == x["phase"] and q["t_s"] < x["t_s"]]
            ev.append({"t_s": x["t_s"], "phase": x["phase"], "kind": "how", "how": x["how"],
                       "lo_prev_a": prev[-1]["i_a"] if prev else None})
    return ev, len(keep), max((x["i_a"] for x in ho), default=float("nan"))


def classify(e, cfg, dups):
    ls, ld = cfg.get("line_step"), cfg.get("load_step")
    t = e["t_s"]
    k = e["kind"]
    if k == "dup_race":
        return "K1"
    if k == "order" and ls and ls["dv"] < -5.5 and -ls["dv"] / max(ls["slew_us"], 1e-9) >= 4.0 \
            and ls["t_us"] * 1e-6 <= t <= (ls["t_us"] + ls["slew_us"] + 2.0) * 1e-6:
        return "K2"
    if k == "how" and e["how"] == 3 and (e["lo_prev_a"] or 0.0) > 0.0:
        return "K3"
    if k == "spike":
        if any(d["module"] == e["module"] and d["phase"] == e["phase"] and 0 < t - d["t_s"] < AFTER_S for d in dups):
            return "FF"
        if ls and ls["t_us"] * 1e-6 <= t <= (ls["t_us"] + ls["slew_us"] + 1.0) * 1e-6:
            return "K4"
        if ld and ld["t_us"] * 1e-6 <= t <= (ld["t_us"] + 1.0) * 1e-6:
            return "K4"
    if k == "dup_floor_first":                    # C13: K5 = tie, both commands in one LSB (a_tlo == t_lo)
        return "K5" if e["dt_ns"] < 0.5 * cfg["t_clk_ns"] / 2 ** cfg["fb"] else "FF"
    return "NEW"


def check(path):
    return check_dict(json.loads(Path(path).read_text()), Path(path).name)


def check_dict(d, name):
    """check() on a loaded record (A147 reads each record once)."""
    cfg = d["cfg"]
    mods = [d] + d.get("modules_rest", [])
    t0 = max(max(md[k][0]["t_s"] for md in mods for k in ("turnons_last", "highoffs_last") if md[k]),
             (d.get("t_mode_p_s") or 0.0) + 20e-6)
    ev, n_on, pk = [], 0, []
    for i, md in enumerate(mods):
        e, n, p = module(md, t0, d["lsb_s"], cfg["t_drv_ns"] * 1e-9)
        ev += [dict(x, module=i + 1) for x in e]
        n_on += n
        pk.append(p)
    ff = [e for e in ev if e["kind"] == "dup_floor_first"]
    for e in ev:
        e["cls"] = classify(e, cfg, ff)
    ts = [s["t_us"] * 1e-6 for s in (cfg.get("line_step"), cfg.get("load_step")) if s]
    t_dist = min(ts) if ts else None
    post = [q["i_a"] for md in mods for q in md["highoffs_last"] if t_dist is not None and q["t_s"] >= t_dist]
    tail = d["sections"][-100:]
    late = [sum(d["late_fires"])] + [sum(m["late_fires"]) for m in d.get("modules_rest", [])]
    return {"file": name, "status": d["status"], "src_modified": d["provenance"].get("cosim_sources_modified"),
            "t0_us": t0 * 1e6, "t_dist_us": t_dist and t_dist * 1e6, "t_lo_timed_us": (d.get("t_lo_timed_s") or 0) * 1e6,
            "n_on": n_on, "overlaps": d["overlaps"], "late": int(sum(late)),
            "peak_post": max(post) if post else None, "peak_window": max(pk),
            "vo_end": sum(q["vo"] for q in tail) / len(tail),
            "ladder_dev_end": max(max(abs(v / q["vin_v"] - (3 - j) / 4) for j, v in enumerate(q["vcs_v"])) for q in tail),
            "events": sorted(ev, key=lambda e: e["t_s"])}
