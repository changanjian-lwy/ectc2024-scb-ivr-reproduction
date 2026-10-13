"""A209: a small static timing estimate on a yosys JSON netlist mapped to a liberty library (BOUNDARY Section 5).
Each cell arc: delay and output transition from the library's tables at the driving transition and the load (the
sum of the input-pin capacitances it drives; no wire), the worse of rise and fall on every arc. Paths start at
flip-flop outputs (clock-to-Q, clock transition SLEW0) and module inputs, and end at flip-flop inputs and module
outputs; setup time is not added. Typical corner. An estimate from below: no wires, no clock tree."""
from __future__ import annotations

import json

import numpy as np
from liberty.parser import parse_liberty

SLEW0 = 0.05          # ns, transition at clock pins and module inputs


def _unit(lib):
    t = str(lib["time_unit"]).strip('"')
    tu = {"1ns": 1.0, "1ps": 1e-3, "10ps": 1e-2, "100ps": 0.1}[t]
    n, u = lib["capacitive_load_unit"]
    cu = float(n) * {"ff": 1e-3, "pf": 1.0}[str(u).strip('"').lower()]       # -> pF
    return tu, cu


def load_lib(path):
    lib = parse_liberty(open(path).read())
    tu, cu = _unit(lib)
    cells = {}
    for c in lib.get_groups("cell"):
        d = {"seq": bool(c.get_groups("ff") or c.get_groups("latch")), "cap": {}, "dir": {}, "clock": set(), "arcs": {}}
        for p in c.get_groups("pin"):
            name = str(p.args[0]).strip('"')
            d["dir"][name] = str(p["direction"]).strip('"')
            if p.get("capacitance") is not None:
                d["cap"][name] = float(p["capacitance"]) * cu
            if str(p.get("clock")).strip('"') == "true":
                d["clock"].add(name)
            for tm in p.get_groups("timing"):
                tabs = {g.group_name: g for g in tm.groups}
                if "cell_rise" not in tabs and "cell_fall" not in tabs:
                    continue
                arc = []
                for kind in (("cell_rise", "cell_fall"), ("rise_transition", "fall_transition")):
                    arc.append([(np.asarray(tabs[k].get_array("index_1")[0], float) * tu, np.asarray(tabs[k].get_array("index_2")[0], float) * cu,
                                 np.asarray(tabs[k].get_array("values"), float) * tu) for k in kind if k in tabs])
                for rel in str(tm["related_pin"]).strip('"').split():
                    d["arcs"].setdefault((rel, name), []).append(arc)
        cells[str(c.args[0]).strip('"')] = d
    return cells


def _look(tabs, slew, load):
    best = 0.0
    for i1, i2, v in tabs:
        a = np.array([np.interp(load, i2, row) for row in v]) if v.ndim == 2 and v.shape[1] == i2.size else v.ravel()
        best = max(best, float(np.interp(slew, i1, a)))
    return best


def sta(netlist_json, top, cells):
    mod = json.loads(open(netlist_json).read())["modules"][top]
    names = {}
    for n, d in mod["netnames"].items():
        for i, b in enumerate(d["bits"]):
            if isinstance(b, int) and (b not in names or names[b][0].startswith("$")):
                names[b] = (n, i, len(d["bits"]))
    label = lambda b: (f"{names[b][0]}[{names[b][1]}]" if names[b][2] > 1 else names[b][0]) if b in names else f"bit{b}"
    base = lambda b: names[b][0] if b in names else "?"
    inst = list(mod["cells"].items())
    driver, loadcap, unknown = {}, {}, {}
    seq_q, ends = {}, []                                       # FF output bit -> cell index; (bit, endpoint label, base)
    for k, (cn, c) in enumerate(inst):
        lc = cells.get(c["type"])
        if lc is None:
            unknown[c["type"]] = unknown.get(c["type"], 0) + 1
            is_seq = "DFF" in c["type"].upper()
            dirs = c.get("port_directions") or {p: ("output" if p in ("Q", "Y", "ZN", "Z") else "input") for p in c["connections"]}
        else:
            is_seq, dirs = lc["seq"], lc["dir"]
        outs = [p for p in c["connections"] if dirs.get(p) == "output"]
        q = next((b for p in outs for b in c["connections"][p] if isinstance(b, int)), None)
        for p, bits in c["connections"].items():
            for b in bits:
                if not isinstance(b, int):
                    continue
                if dirs.get(p) == "output":
                    driver[b] = (k, p)
                    if is_seq:
                        seq_q[b] = k
                else:
                    loadcap[b] = loadcap.get(b, 0.0) + (lc["cap"].get(p, 0.0) if lc else 0.0)
                    if is_seq and not (lc and p in lc["clock"]) and p not in ("C", "CLK", "CK"):
                        ends.append((b, label(q) if q is not None else cn, base(q) if q is not None else cn))
    for pn, p in mod["ports"].items():
        if p["direction"] == "output":
            ends += [(b, f"{pn}[{i}]", pn) for i, b in enumerate(p["bits"]) if isinstance(b, int)]
    arr, slew, prev = {}, {}, {}

    def start(b):
        if b in seq_q:
            k = seq_q[b]; c = inst[k][1]; lc = cells.get(c["type"])
            a = next((v for (rel, out), v in (lc["arcs"].items() if lc else []) if rel in lc["clock"] and b in c["connections"].get(out, [])), None)
            if a:
                return (max(_look(x[0], SLEW0, loadcap.get(b, 0.0)) for x in a), max(_look(x[1], SLEW0, loadcap.get(b, 0.0)) for x in a))
        return 0.0, SLEW0

    def solve(b0):
        stack = [b0]
        while stack:
            b = stack[-1]
            if b in arr:
                stack.pop(); continue
            if b not in driver or b in seq_q:
                arr[b], slew[b] = start(b); prev[b] = None; stack.pop(); continue
            k, out = driver[b]
            c = inst[k][1]; lc = cells.get(c["type"])
            ins = [(p, x) for p, bits in c["connections"].items() for x in bits
                   if isinstance(x, int) and p != out and (lc["dir"].get(p) if lc else "input") != "output"]
            todo = [x for _, x in ins if x not in arr]
            if todo:
                stack.extend(todo); continue
            best = (0.0, SLEW0, None)
            for p, x in ins:
                a = lc["arcs"].get((p, out)) if lc else None
                d = max(_look(t[0], slew[x], loadcap.get(b, 0.0)) for t in a) if a else 0.0
                s = max(_look(t[1], slew[x], loadcap.get(b, 0.0)) for t in a) if a else slew[x]
                if arr[x] + d >= best[0]:
                    best = (arr[x] + d, s, (k, p, x))
            arr[b], slew[b], prev[b] = best
            stack.pop()

    worst, groups = (0.0, None, None), {}
    for b, lab, bs in ends:
        solve(b)
        if arr[b] > worst[0]:
            worst = (arr[b], b, lab)
        if arr[b] > groups.get(bs, (0.0,))[0]:
            groups[bs] = (arr[b], b)
    path, b = [], worst[1]
    while b is not None and prev.get(b) is not None:
        k, p, x = prev[b]
        path.append(inst[k][1]["type"]); b = x

    def origin(b):
        while prev.get(b) is not None:
            b = prev[b][2]
        return label(b), base(b)

    top_groups = [{"end": g, "delay_ns": round(v[0], 3), "start": origin(v[1])[1]} for g, v in sorted(groups.items(), key=lambda kv: -kv[1][0])[:12]]
    return {"delay_ns": worst[0], "end": worst[2], "start": origin(worst[1])[0] if worst[1] is not None else None, "depth_cells": len(path),
            "cells": len(inst), "flops": len(set(seq_q.values())), "endpoints": len(ends), "unmapped": unknown, "by_end_register": top_groups}
