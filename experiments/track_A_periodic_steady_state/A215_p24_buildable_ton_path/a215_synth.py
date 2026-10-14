"""A215: the repository's RTL through the synthesis front end as it is, and the final configuration's build mapped to
both libraries. The build is scb_ctrl inside a wrapper generated here (scb_ctrl_final: the option inputs tied to the
final configuration's values, TIES; the numeric settings stay inputs), once with cfg_ton_lat 16 ("final") and once
with 0 ("final0", the same controller without the registers). Timing: A209's estimate (a209_sta.py), read per end
register; reach(): which end registers a path from the Ton arithmetic's registers (ton_acc, p_term, scb_vff's)
arrives at within one clock, read from the netlist's connections. Tools as A209 (tmp/venv_yosys, tmp/a209/*.lib).
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


def graph(netlist_json, top, cells):
    """(names of each bit, per cell: input bits, output bits, sequential?) of a mapped netlist."""
    mod = json.loads(open(netlist_json).read())["modules"][top]
    names = {}
    for n, d in mod["netnames"].items():
        for b in d["bits"]:
            if isinstance(b, int) and (b not in names or names[b].startswith("$")):
                names[b] = n
    out = []
    for c in mod["cells"].values():
        lc = cells.get(c["type"])
        seq = lc["seq"] if lc else "DFF" in c["type"].upper()
        dirs = lc["dir"] if lc else {p: ("output" if p in ("Q", "Y", "ZN", "Z") else "input") for p in c["connections"]}
        clk = lc["clock"] if lc else {"C", "CLK", "CK"}
        ins = [b for p, bits in c["connections"].items() for b in bits if isinstance(b, int) and dirs.get(p) != "output" and p not in clk]
        outs = [b for p, bits in c["connections"].items() for b in bits if isinstance(b, int) and dirs.get(p) == "output"]
        out.append((ins, outs, seq))
    return names, out


def reach(netlist_json, top, cells, prefixes=ARITH):
    """End registers (base names) that a combinational path from a register named with one of the prefixes reaches."""
    names, cl = graph(netlist_json, top, cells)
    loads = {}
    for k, (ins, outs, seq) in enumerate(cl):
        for b in ins:
            loads.setdefault(b, []).append(k)
    hit = lambda n: any(n == p or n.startswith(p) for p in prefixes)
    todo = [b for ins, outs, seq in cl if seq for b in outs if hit(names.get(b, "?"))]
    n_start, seen, ends = len(todo), set(todo), set()
    while todo:
        b = todo.pop()
        for k in loads.get(b, []):
            ins, outs, seq = cl[k]
            if seq:
                ends.update(names.get(x, "?") for x in outs)
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
        t = STA.sta(nl, top, S.LIBC[lib], n_groups=None)
        g = t.pop("by_end_register")
        ph = [x for x in g if x["end"].startswith("u.g_ph[")]
        rg = [x for x in g if x["end"].startswith(("u.ton_ph_r", "u.lo_add_r"))]
        other = [x for x in g if x not in ph and x not in rg]
        n0, ends = reach(nl, top, S.LIBC[lib], tuple("u." + p for p in ARITH))
        out.update(sta=t, delay_ns=t["delay_ns"], phase_ends=ph[:6], reg_ends=rg, other_ends=other[:14],
                   arith_starts=n0, arith_reaches_phase=sorted({e for e in ends if e.startswith("u.g_ph[")})[:20],
                   arith_reaches=len(ends))
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
                                  "final0_reaches_phase": len(g(f"final0_{lib}").get("arith_reaches_phase") or [])}
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
