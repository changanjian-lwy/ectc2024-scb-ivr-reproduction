"""A209: synthesize the frozen RTL (a scratch copy with one port connection rewritten, BOUNDARY Section 1) with yosys
and ABC, and read size and the longest path from the logs.
Needs: tmp/venv_yosys (yowasp-yosys < 0.50, liberty-parser, numpy; the yowasp build cannot open paths with spaces or
non-ASCII characters, so everything runs in a temporary directory, and its standard output stops at ABC, so yosys's
own log file is read) and the two liberty files in tmp/a209/ (sky130hd_tt.lib, nangate45_typ.lib; from
OpenROAD-flow-scripts' platforms, not in the repository). Timing: a209_sta.py on the mapped netlist.
  tmp/venv_yosys/bin/python a209_synth.py [--jobs 3] -> a209_summary.json, logs in tmp/a209/logs/"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a209_sta as STA  # noqa: E402

PROJECT = HERE.parents[2]
RTL = PROJECT / "src" / "scb_ivr" / "cosim" / "rtl"
LIBS = {"sky130": PROJECT / "tmp" / "a209" / "sky130hd_tt.lib", "nangate45": PROJECT / "tmp" / "a209" / "nangate45_typ.lib"}
YOSYS = PROJECT / "tmp" / "venv_yosys" / "bin" / "yowasp-yosys"
PORT_OLD = ".lo_add(IS_FIRST ? lo_add : {TW{1'b0}}),"
PORT_NEW = ".lo_add(IS_FIRST ? lo_add : $signed({TW{1'b0}})),"
T_CLK_PS = 4000.0
LIBC = {}
FILES = "rtl/sync2.v rtl/scb_phase.v rtl/scb_vff.v rtl/scb_dep.v rtl/scb_ctrl.v"
TOPS = {   # name: (top module, chparam, extra sources, libraries)
    "ctrl": ("scb_ctrl", "-set N 4 -set TW 32 -set FB 7 -set CW 8", "", ("sky130", "nangate45")),
    "phase_first": ("scb_phase", "-set TW 32 -set FB 7 -set CW 8 -set FIRST 1", "", ("sky130", "nangate45")),
    "phase_rest": ("scb_phase", "-set TW 32 -set FB 7 -set CW 8 -set FIRST 0", "", ("sky130", "nangate45")),
    "vff": ("scb_vff", "-set N 4 -set TW 32", "", ("sky130", "nangate45")),
    "dep": ("scb_dep", "", "", ("sky130",)),
    "multi": ("scb_multi", "", " rtl/scb_multi.v", ()),
    "add32": ("add32", "", "", ("sky130", "nangate45")),          # plausibility row for a209_sta (not repository RTL)
}
ADD32 = """module add32(input clk, input [31:0] a, input [31:0] b, output reg [32:0] y);
    reg [31:0] ra, rb;
    always @(posedge clk) begin ra <= a; rb <= b; y <= ra + rb; end
endmodule
"""


def script(top, chparam, extra, lib):
    s = [f"read_verilog {'add32.v' if top == 'add32' else FILES + extra}"]
    if chparam:
        s.append(f"chparam {chparam} {top}")
    s += [f"hierarchy -top {top}", f"synth -top {top} -flatten", "check -assert", "stat"]
    if lib:
        s += [f"dfflibmap -liberty {lib}.lib", f"abc -liberty {lib}.lib -D {T_CLK_PS:g}", f"stat -liberty {lib}.lib",
              f"write_json {top}_{lib}.json"]
    return "\n".join(s) + "\n"


def parse(log):
    out = {"problems": None, "error": None}
    m = re.findall(r"found and reported (\d+) problems", log)
    out["problems"] = int(m[-1]) if m else None
    e = re.search(r"^ERROR: (.*)$", log, re.M)
    out["error"] = e.group(1)[:200] if e else None
    cells = re.findall(r"^\s*(\d+)\s+(?:[\d.eE+]+\s+)?cells$|Number of cells:\s+(\d+)", log, re.M)
    cells = [int(a or b) for a, b in cells]
    out["cells_generic"] = cells[0] if cells else None
    out["cells_mapped"] = cells[-1] if len(cells) > 1 else None
    a = re.findall(r"Chip area for (?:top )?module '[^']*':\s+([\d.]+)", log)
    out["area"] = float(a[-1]) if a else None
    return out


def one(work, logs, name, lib):
    top, chparam, extra, _ = TOPS[name]
    tag = f"{name}_{lib or 'generic'}"
    (work / f"{tag}.ys").write_text(script(top, chparam, extra, lib))
    t0 = time.time()
    r = subprocess.run([str(YOSYS), "-q", "-l", f"{tag}.log", f"{tag}.ys"], cwd=work, capture_output=True, text=True)
    log = (work / f"{tag}.log").read_text() if (work / f"{tag}.log").exists() else r.stdout + r.stderr
    (logs / f"{tag}.log").write_text(log)
    out = dict(parse(log), top=top, library=lib, exit=r.returncode)
    if lib and (work / f"{top}_{lib}.json").exists():
        t = STA.sta(work / f"{top}_{lib}.json", top, LIBC[lib])
        out.update(delay_ps=1e3 * t["delay_ns"], sta=t)
    else:
        out["delay_ps"] = None
    out["wall_s"] = round(time.time() - t0, 1)
    return tag, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="a209_"))
    (work / "rtl").mkdir()
    for f in RTL.glob("*.v"):
        shutil.copy(f, work / "rtl" / f.name)
    src = (work / "rtl" / "scb_ctrl.v").read_text()
    assert src.count(PORT_OLD) == 1
    (work / "rtl" / "scb_ctrl.v").write_text(src.replace(PORT_OLD, PORT_NEW))
    (work / "add32.v").write_text(ADD32)
    for lib, p in LIBS.items():
        shutil.copy(p, work / f"{lib}.lib")
        LIBC[lib] = STA.load_lib(p)
    logs = PROJECT / "tmp" / "a209" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    jobs = [(n, lib) for n, t in TOPS.items() for lib in (None,) + t[3]]
    ver = subprocess.run([str(YOSYS), "-V"], capture_output=True, text=True).stdout.strip().split("(")[0].strip()
    with ThreadPoolExecutor(a.jobs) as ex:
        res = dict(ex.map(lambda j: one(work, logs, *j), jobs))
    out = {"yosys": ver, "t_clk_ps": T_CLK_PS, "port_rewrite": {"old": PORT_OLD, "new": PORT_NEW}, "runs": res}
    g = lambda k: res.get(k, {})
    out["criteria"] = {"c1": bool(g("ctrl_generic").get("problems") == 0 and g("multi_generic").get("problems") == 0),
                       "c2": bool((g("ctrl_sky130").get("delay_ps") or 1e9) <= T_CLK_PS),
                       "c3": bool((g("ctrl_nangate45").get("delay_ps") or 1e9) <= T_CLK_PS),
                       "c4": bool(max(g("phase_first_sky130").get("delay_ps") or 1e9, g("phase_rest_sky130").get("delay_ps") or 1e9) <= T_CLK_PS)}
    (HERE / "a209_summary.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in res.items():
        t = v.get("sta") or {}
        print(f"{k:22s} exit {v['exit']} {v['wall_s']:7.1f} s | problems {v['problems']} | cells {v['cells_generic']} -> {v['cells_mapped']} | "
              f"area {v['area']} | delay {v['delay_ps']} ps over {t.get('depth_cells')} cells | {t.get('start')} -> {t.get('end')} | "
              f"flops {t.get('flops')} unmapped {t.get('unmapped')} | {v['error'] or ''}")
        for g in (t.get("by_end_register") or [])[:8]:
            print(f"      {g['delay_ns']:8.3f} ns  {g['start']} -> {g['end']}")
    print(out["criteria"])
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
