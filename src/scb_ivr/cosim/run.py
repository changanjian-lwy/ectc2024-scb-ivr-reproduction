"""Run co-simulations of the P24 module.

    PYTHONPATH=src python3 -m scb_ivr.cosim.run CFG.json [CFG.json ...] [--jobs 4] [--out-dir DIR] [--t-end-us T]

Each configuration runs in its own process: Icarus Verilog builds rtl/, cocotb runs bridge.py. At most --jobs run
at a time (default 4, this machine's performance cores); configurations are started in the order given, so put the
decisive ones first. Output: cfg["out"] next to the configuration, or the same file name in --out-dir; the log
log_<stem>.txt next to the output. --t-end-us stops earlier (regression smoke runs). Every output carries
"provenance": the git commit, whether src/scb_ivr/cosim had uncommitted changes, the configuration's sha256, the
Python / numpy / scipy versions and the plant implementation. Build directories go to tmp/cosim_build/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]
PROJECT = HERE.parents[2]
OSS_BIN = Path.home() / "tools" / "oss-cad-suite" / "bin"
RTL = [HERE / "rtl" / "sync2.v", HERE / "rtl" / "scb_phase.v", HERE / "rtl" / "scb_ctrl.v"]


def provenance(cfg_path: Path) -> dict:
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=PROJECT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    import numpy
    import scipy
    status = git("status", "--porcelain", "--", "src/scb_ivr/cosim")
    return {"git_commit": git("rev-parse", "HEAD"), "cosim_sources_modified": None if status is None else bool(status),
            "cfg_sha256": hashlib.sha256(cfg_path.read_bytes()).hexdigest(), "cfg_path": str(cfg_path),
            "python": sys.version.split()[0], "numpy": numpy.__version__, "scipy": scipy.__version__}


def out_path(cfg_path: Path, out_dir: Path | None) -> Path:
    name = json.loads(cfg_path.read_text())["out"]
    return (out_dir / name) if out_dir else (cfg_path.parent / name)


def run_single(cfg_path: Path, out: Path | None, t_end_us: float | None) -> None:
    """One co-simulation in this process (called by the child processes)."""
    from cocotb_tools.runner import get_runner
    cfg = json.loads(cfg_path.read_text())
    tag = hashlib.sha256(f"{cfg_path}|{out}|{t_end_us}".encode()).hexdigest()[:10]
    build = PROJECT / "tmp" / "cosim_build" / f"{cfg_path.stem}-{tag}"
    runner = get_runner("icarus")
    runner.build(sources=RTL, hdl_toplevel="scb_ctrl", parameters={"N": 4, "TW": 32, "FB": int(cfg["fb"]), "CW": 8},
                 build_dir=build, always=True)
    env = {"COSIM_CFG": str(cfg_path), "COSIM_PROVENANCE": json.dumps(provenance(cfg_path))}
    if out is not None:
        env["COSIM_OUT"] = str(out)
    if t_end_us is not None:
        env["COSIM_T_END_US"] = str(t_end_us)
    runner.test(hdl_toplevel="scb_ctrl", test_module="bridge", build_dir=build, test_dir=HERE, extra_env=env,
                results_xml=str(build / "results.xml"))


def launch(cfg_path: Path, out_dir: Path | None, t_end_us: float | None) -> tuple[Path, int, float]:
    out = out_path(cfg_path, out_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    log = out.parent / f"log_{cfg_path.stem}.txt"
    env = dict(os.environ)
    env["PATH"] = f"{OSS_BIN}:{env.get('PATH', '')}"
    env["PYTHONPATH"] = f"{SRC}:{env.get('PYTHONPATH', '')}"
    cmd = [sys.executable, "-m", "scb_ivr.cosim.run", "--single", str(cfg_path), "--out", str(out)]
    if t_end_us is not None:
        cmd += ["--t-end-us", str(t_end_us)]
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env).returncode
    ok = rc == 0 and out.exists()
    print(f"{'done' if ok else 'FAILED'} {cfg_path.name} -> {out} ({time.time() - t0:.0f} s)", flush=True)
    return out, (0 if ok else (rc or 1)), time.time() - t0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cfgs", nargs="+", type=Path)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--t-end-us", type=float)
    ap.add_argument("--single", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--out", type=Path, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.single:
        run_single(a.cfgs[0].resolve(), a.out, a.t_end_us)
        return 0
    cfgs = [c.resolve() for c in a.cfgs]
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        res = list(pool.map(lambda c: launch(c, a.out_dir.resolve() if a.out_dir else None, a.t_end_us), cfgs))
    failed = [str(o) for o, rc, _ in res if rc]
    print(f"{len(res) - len(failed)} of {len(res)} done" + (f"; failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
