"""A215: the repository's RTL through the synthesis front end as it is, and the final configuration's build mapped to
both libraries. The build is scb_ctrl inside a wrapper generated here (scb_ctrl_final: the option inputs tied to the
final configuration's values, TIES; the numeric settings stay inputs), once with cfg_ton_lat 16 ("final") and once
with 0 ("final0", the same controller without the registers). Timing: A209's estimate (a209_sta.py), read per end
register; reach(): which end registers a path from the Ton arithmetic's registers (ton_acc, p_term, scb_vff's)
arrives at within one clock, read from the netlist's connections. A flattened net carries every name it had in the
hierarchy (the new registers are also each phase's input "ton"), so a flip-flop is classified from all the names of
its output (classify). Tools as A209 (tmp/venv_yosys, tmp/a209/*.lib).
  tmp/venv_yosys/bin/python a215_synth.py [--jobs 2] -> a215_synth.json, logs in tmp/a215/logs/"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("a209_synth", HERE.parent / "A209_p24_rtl_synthesis" / "a209_synth.py")
S = importlib.util.module_from_spec(_s)
_s.loader.exec_module(S)
STA = S.STA
M_LAT = 16
T_CLK_NS = 4.0
PHASE_ALONE_NS = {"sky130": 10.2, "nangate45": 2.44}          # A209: scb_phase on its own (the file is unchanged)
TIES = {"cfg_start_s": "1'b1", "cfg_pred": "1'b1", "cfg_zvs_react": "1'b0", "cfg_trim": "1'b1", "cfg_fine": "1'b1",
        "cfg_vloop": "1'b1", "cfg_ext_ton": "1'b0", "ext_ton": "32'd0", "ext_slot": "32'd0", "ext_ref": "32'd0",
        "cfg_async": "1'b1", "fa_valid": "4'd0", "fa_tlo": "128'd0", "cfg_low_pred": "1'b1", "cfg_err_low": "1'b1",
        "cfg_err_high": "1'b1", "cfg_slot_follow": "1'b1", "cfg_slot_guard": "1'b1", "cfg_slot_avg": "1'b1",
        "cfg_slot_lo": "1'b1", "cfg_slot_trim": "1'b0", "cfg_lo_pred": "1'b1", "cfg_lo_adm": "1'b1", "cfg_lo_ff": "1'b0",
        "cfg_lo_floor": "1'b1", "cfg_slave_floor": "1'b0", "cfg_ph_floor": "1'b0", "cfg_floor_late": "1'b1",
        "cfg_vff": "1'b1", "cfg_vff_rel": "10'd320", "cfg_vff_rel_lp": "1'b1", "cfg_vff_seed": "2'd2",
        "cfg_vff_vs_kr": "16'sd0", "cfg_vff_vs_kt": "16'sd0", "cfg_dep": "1'b0"}
ARITH = ("ton_acc", "p_term", "u_vff.")                         # the Ton arithmetic's registers (name prefixes)
TOPS = {   # name: (top, chparam, extra sources, libraries)
    "ctrl": ("scb_ctrl", "-set N 4 -set TW 32 -set FB 7 -set CW 8", "", ()),
    "phase_first": ("scb_phase", "-set TW 32 -set FB 7 -set CW 8 -set FIRST 1", "", ()),
    "phase_rest": ("scb_phase", "-set TW 32 -set FB 7 -set CW 8 -set FIRST 0", "", ()),
    "vff": ("scb_vff", "-set N 4 -set TW 32", "", ()),
    "multi": ("scb_multi", "", " rtl/scb_multi.v", ()),
    "final": ("scb_ctrl_final", "", " final.v", ("sky130", "nangate45")),
    "final0": ("scb_ctrl_final0", "", " final0.v", ("sky130", "nangate45")),
}


def wrapper(src, name, lat):
    """scb_ctrl's port list without the tied inputs, around one scb_ctrl (N 4, TW 32, FB 7, CW 8)."""
    body = src[src.index(") (") + 3: src.index(");", src.index(") ("))]
    ties = dict(TIES, cfg_ton_lat=f"6'd{lat}")
    decl, conn = [], []
    for line in body.splitlines():
        m = re.match(r"\s*((?:input|output)\s+(?:wire|reg)\s*(?:signed\s*)?(?:\[[^\]]+\])?)\s*(\w+)\s*,?", line)
        if not m:
            continue
        d, n = m.groups()
        if n in ties:
            conn.append(f".{n}({ties[n]})")
        else:
            decl.append(f"    {d.replace('reg', 'wire')} {n}")
            conn.append(f".{n}({n})")
    assert all(any(c.startswith(f".{n}(") for c in conn) for n in ties), "a tied port does not exist"
    return (f"module {name} #(parameter N = 4, TW = 32, FB = 7, CW = 8, AW = 12, KW = 16, KPW = 24, FRAC = 16) (\n"
            + ",\n".join(decl) + "\n);\n    scb_ctrl #(.N(N), .TW(TW), .FB(FB), .CW(CW)) u (\n        "
            + ",\n        ".join(conn) + "\n    );\nendmodule\n")


REGS = ("u.ton_ph_r", "u.lo_add_r")                             # the new registers
PHASE = "u.g_ph["


def aliases(netlist_json, top):
    """(module, bit -> every net name it has)."""
    mod = json.loads(open(netlist_json).read())["modules"][top]
    out = {}
    for n, d in mod["netnames"].items():
        for b in d["bits"]:
            if isinstance(b, int):
                out.setdefault(b, []).append(n)
    return mod, out


def inputs(module):
    """The input port names of one RTL module (a net named after one of them inside an instance comes from outside)."""
    src = (S.RTL / f"{module}.v").read_text()
    return set(re.findall(r"^\s*input\s+wire\s*(?:signed\s*)?(?:\[[^\]]+\])?\s*(\w+)", src, re.M))


IN_PHASE, IN_VFF = inputs("scb_phase"), inputs("scb_vff")


def classify(names):
    """(class, name) of a flip-flop output from all its net names: "reg" (the new registers), "arith" (the Ton
    arithmetic's registers: ton_acc, p_term and those declared in scb_vff), "phase" (declared in a scb_phase), else
    "other". A name that is an instance's input port does not count for that instance."""
    ns = [n for n in names if not n.startswith("$")]
    for n in ns:
        if n in REGS:
            return "reg", n
    for n in ns:
        if n in ("u.ton_acc", "u.p_term") or (n.startswith("u.u_vff.") and n[8:].split("[")[0] not in IN_VFF):
            return "arith", n
    for n in ns:
        if n.startswith(PHASE) and n.split(".u_ph.")[-1].split("[")[0] not in IN_PHASE:
            return "phase", n
    return "other", (min(ns, key=lambda n: (n.count("."), len(n))) if ns else "?")


def graph(netlist_json, top, cells):
    """(every bit's names, per cell: input bits, output bits, sequential?) of a mapped netlist."""
    mod, al = aliases(netlist_json, top)
    out = []
    for c in mod["cells"].values():
        lc = cells.get(c["type"])
        seq = lc["seq"] if lc else "DFF" in c["type"].upper()
        dirs = lc["dir"] if lc else {p: ("output" if p in ("Q", "Y", "ZN", "Z") else "input") for p in c["connections"]}
        clk = lc["clock"] if lc else {"C", "CLK", "CK"}
        ins = [b for p, bits in c["connections"].items() for b in bits if isinstance(b, int) and dirs.get(p) != "output" and p not in clk]
        outs = [b for p, bits in c["connections"].items() for b in bits if isinstance(b, int) and dirs.get(p) == "output"]
        out.append((ins, outs, seq))
    return al, out


def reach(netlist_json, top, cells):
    """(arithmetic registers' bits, the classified end registers a combinational path from one of them reaches)."""
    al, cl = graph(netlist_json, top, cells)
    loads = {}
    for k, (ins, outs, seq) in enumerate(cl):
        for b in ins:
            loads.setdefault(b, []).append(k)
    todo = [b for ins, outs, seq in cl if seq for b in outs if classify(al.get(b, []))[0] == "arith"]
    n_start, seen, ends = len(todo), set(todo), set()
    while todo:
        b = todo.pop()
        for k in loads.get(b, []):
            ins, outs, seq = cl[k]
            if seq:
                ends.update(classify(al.get(x, [])) for x in outs)
            else:
                for x in outs:
                    if x not in seen:
                        seen.add(x); todo.append(x)
    return n_start, sorted(ends)


def one(work, logs, name, lib):
    top, chparam, extra, _ = TOPS[name]
    tag = f"{name}_{lib or 'generic'}"
    (work / f"{tag}.ys").write_text(S.script(top, chparam, extra, lib))
    t0 = time.time()
    try:
        r = subprocess.run([str(S.YOSYS), "-q", "-l", f"{tag}.log", f"{tag}.ys"], cwd=work, capture_output=True, text=True, timeout=S.T_MAX_S)
    except subprocess.TimeoutExpired:
        return tag, {"top": top, "library": lib, "exit": None, "error": f"no result within {S.T_MAX_S} s", "problems": None}
    log = (work / f"{tag}.log").read_text() if (work / f"{tag}.log").exists() else r.stdout + r.stderr
    (logs / f"{tag}.log").write_text(log)
    out = dict(S.parse(log), top=top, library=lib, exit=r.returncode)
    nl = work / f"{top}_{lib}.json"
    if lib and nl.exists():
        _, al = aliases(nl, top)
        t = STA.sta(nl, top, S.LIBC[lib], n_groups=None, group=lambda b: "|".join(classify(al.get(b, []))))
        g = [dict(x, cls=x["end"].split("|")[0] if "|" in x["end"] else "port", end=x["end"].split("|")[-1], start=x["start"].split("|")[-1],
                  start_cls=x["start"].split("|")[0] if "|" in x["start"] else "input") for x in t.pop("by_end_register")]
        by = lambda c: [x for x in g if x["cls"] == c]
        n0, ends = reach(nl, top, S.LIBC[lib])
        out.update(sta=t, delay_ns=t["delay_ns"], phase_ends=by("phase")[:8], reg_ends=by("reg"), arith_ends=by("arith")[:10],
                   other_ends=by("other")[:10], port_ends=by("port")[:6], arith_starts=n0,
                   arith_reaches_phase=[n for c, n in ends if c == "phase"][:20],
                   arith_reaches={c: sum(1 for k, _ in ends if k == c) for c in ("reg", "arith", "phase", "other")})
    out["wall_s"] = round(time.time() - t0, 1)
    return tag, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="a215_"))
    (work / "rtl").mkdir()
    for f in S.RTL.glob("*.v"):
        shutil.copy(f, work / "rtl" / f.name)                   # the repository's files, unchanged
    src = (S.RTL / "scb_ctrl.v").read_text()
    (work / "final.v").write_text(wrapper(src, "scb_ctrl_final", M_LAT))
    (work / "final0.v").write_text(wrapper(src, "scb_ctrl_final0", 0))
    for lib, p in S.LIBS.items():
        shutil.copy(p, work / f"{lib}.lib")
        S.LIBC[lib] = STA.load_lib(p)
    logs = S.PROJECT / "tmp" / "a215" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    jobs = [(n, lib) for n, t in TOPS.items() for lib in (None,) + t[3]]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = dict(ex.map(lambda j: one(work, logs, *j), jobs))
    g = lambda k: res.get(k, {})
    crit = {"c4": bool(all(g(f"{n}_generic").get("problems") == 0 and not g(f"{n}_generic").get("error") for n in TOPS))}
    for lib in ("sky130", "nangate45"):
        f = g(f"final_{lib}")
        ph = max((x["delay_ns"] for x in f.get("phase_ends", [])), default=None)
        rg = max((x["delay_ns"] for x in f.get("reg_ends", [])), default=None)
        crit[f"c5_{lib}"] = bool(ph is not None and not f.get("arith_reaches_phase") and ph <= 1.5 * PHASE_ALONE_NS[lib])
        crit[f"c6_{lib}"] = bool(rg is not None and rg <= M_LAT * T_CLK_NS)
        crit[f"numbers_{lib}"] = {"phase_end_ns": ph, "register_end_ns": rg, "final0_ns": g(f"final0_{lib}").get("delay_ns"),
                                  "final0_reaches_phase": len(g(f"final0_{lib}").get("arith_reaches_phase") or []),
                                  "final0_phase_end_ns": max((x["delay_ns"] for x in g(f"final0_{lib}").get("phase_ends", [])), default=None),
                                  "arith_end_ns": max((x["delay_ns"] for x in f.get("arith_ends", [])), default=None)}
    crit["c5_45nm_fits_clock"] = bool((crit["numbers_nangate45"]["phase_end_ns"] or 1e9) <= T_CLK_NS)
    out = {"m_lat": M_LAT, "t_clk_ns": T_CLK_NS, "ties": TIES, "phase_alone_ns": PHASE_ALONE_NS, "runs": res, "criteria_synthesis": crit}
    (HERE / "a215_synth.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in res.items():
        print(f"{k:18s} exit {v.get('exit')} {v.get('wall_s')} s | problems {v.get('problems')} | cells {v.get('cells_generic')} -> "
              f"{v.get('cells_mapped')} | area {v.get('area')} | longest {v.get('delay_ns')} | {v.get('error') or ''}")
    print(json.dumps(crit))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
