"""Speed and result check of the co-simulation, against archived runs.

    python3 scripts/cosim_benchmark.py --batch    # A92's 8 configurations with the default plant, at most 4 at a time
    python3 scripts/cosim_benchmark.py --plants   # A92 n0 with each implementation: the archived A92 bridge (the code
                                                  # before the clean-up), and the shared package's reference, fast,
                                                  # kernel (these 4 at once, one core each), then kernel2 alone

Everything is written to tmp/bench/ (archived folders are only read). Every output is compared with the archived
run bit for bit (scripts/cosim_regression.compare_full) and summarised with A89's summarize() (Ton, period, Vo,
dither, P_rev, ...), and the wall times are printed next to the archived ones. A summary goes to
tmp/bench/<mode>/benchmark.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
A92 = TA / "A92_verilog_error_based_correctors"
sys.path.insert(0, str(PROJECT / "scripts"))
sys.path.insert(0, str(TA / "A89_verilog_predicted_low_side"))
from cosim_regression import compare_full  # noqa: E402
from a89_analyze import summarize  # noqa: E402

OSS_BIN = Path.home() / "tools" / "oss-cad-suite" / "bin"
KEYS = ("ton_final_ns", "period_ns", "vo_v", "last20_max_di_a", "p_rev_w", "settle_1pct_us_after_handover", "ipk_a",
        "vds_max_v")


def env():
    e = dict(os.environ)
    e["PATH"] = f"{OSS_BIN}:{e.get('PATH', '')}"
    e["PYTHONPATH"] = f"{PROJECT / 'src'}:{e.get('PYTHONPATH', '')}"
    return e


def report(name, out, ref):
    cmp = compare_full(ref, out)
    s = summarize(out)
    row = {"bit_identical": cmp["pass"], "wall_s": cmp["wall_s"], "archived_wall_s": json.loads(ref.read_text())["wall_s"],
           **{k: s.get(k) for k in KEYS}}
    print(f"{name:28s} {'IDENTICAL' if row['bit_identical'] else 'DIFFERENT'}  wall {row['wall_s']:7.0f} s  "
          f"(archived {row['archived_wall_s']:6.0f} s)  Ton {row['ton_final_ns']:.3f}  T {row['period_ns']:.2f}  "
          f"Vo {row['vo_v']:.4f}  dither {row['last20_max_di_a']:.3f}  P_rev {row['p_rev_w']:.3f}", flush=True)
    return row


def batch():
    out_dir = PROJECT / "tmp" / "bench" / "batch"
    shutil.rmtree(out_dir, ignore_errors=True); out_dir.mkdir(parents=True)
    cfgs = sorted((A92 / "cosim").glob("cfg_*.json"))
    t0 = time.time()
    subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run", *map(str, cfgs), "--jobs", "4", "--out-dir", str(out_dir)],
                   env=env(), cwd=PROJECT, check=False)
    total = time.time() - t0
    rows = {}
    for c in cfgs:
        name = json.loads(c.read_text())["out"]
        rows[c.stem] = report(c.stem, out_dir / name, A92 / "cosim" / name)
    arch = [r["archived_wall_s"] for r in rows.values()]
    res = {"total_wall_s": total, "runs": rows, "archived_batch_wall_s_max": max(arch),
           "all_identical": all(r["bit_identical"] for r in rows.values())}
    print(f"\nbatch of {len(cfgs)}: {total:.0f} s in total (archived A92 batch: runs took up to {max(arch):.0f} s each, "
          f"all at once); all identical: {res['all_identical']}")
    (out_dir / "benchmark.json").write_text(json.dumps(res, indent=1, default=float))


def run_before(cfg_src: Path, out_dir: Path):
    """The archived A92 bridge and runner, copied verbatim into tmp (paths to A88's plant and A92's RTL made absolute)."""
    d = out_dir / "before"; d.mkdir(parents=True, exist_ok=True)
    br = (A92 / "cosim" / "test_cosim.py").read_text()
    old = 'A88 = HERE.parent.parent / "A88_p24_predictive_low_side_turn_on"'
    assert old in br
    (d / "test_cosim.py").write_text(br.replace(old, f'A88 = Path({str(TA / "A88_p24_predictive_low_side_turn_on")!r})'))
    rn = (A92 / "cosim" / "run_cosim.py").read_text()
    old = 'RTL = HERE.parent / "rtl"'
    assert old in rn
    (d / "run_cosim.py").write_text(rn.replace(old, f'RTL = Path({str(A92 / "rtl")!r})'))
    cfg = json.loads(cfg_src.read_text())
    cfg["init_run"] = str((cfg_src.parent / cfg["init_run"]).resolve())
    (d / "cfg_before.json").write_text(json.dumps(cfg, indent=1))
    with open(d / "log.txt", "w") as fh:
        subprocess.run([sys.executable, "run_cosim.py", "cfg_before.json"], cwd=d, env=env(), stdout=fh,
                       stderr=subprocess.STDOUT, check=False)
    return d / cfg["out"]


def run_shared(cfg_src: Path, out_dir: Path, impl: str):
    d = out_dir / impl; d.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(cfg_src.read_text())
    cfg["init_run"] = str((cfg_src.parent / cfg["init_run"]).resolve())
    cfg["plant_impl"] = impl
    path = d / f"cfg_{impl}.json"
    path.write_text(json.dumps(cfg, indent=1))
    subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run", str(path), "--jobs", "1"], env=env(), cwd=PROJECT, check=False)
    return d / cfg["out"]


def plants():
    out_dir = PROJECT / "tmp" / "bench" / "plants"
    shutil.rmtree(out_dir, ignore_errors=True); out_dir.mkdir(parents=True)
    cfg = A92 / "cosim" / "cfg_n0_nominal.json"
    ref = A92 / "cosim" / "run_n0_nominal.json"
    jobs = {"before (archived A92 code)": lambda: run_before(cfg, out_dir),
            "reference": lambda: run_shared(cfg, out_dir, "reference"),
            "fast": lambda: run_shared(cfg, out_dir, "fast"),
            "kernel": lambda: run_shared(cfg, out_dir, "kernel")}
    with ThreadPoolExecutor(max_workers=4) as pool:
        outs = dict(zip(jobs, pool.map(lambda f: f(), jobs.values())))
    outs["kernel2 (default, alone)"] = run_shared(cfg, out_dir, "kernel2")
    print()
    rows = {name: report(name, out, ref) for name, out in outs.items()}
    (out_dir / "benchmark.json").write_text(json.dumps(rows, indent=1, default=float))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--batch", action="store_true")
    g.add_argument("--plants", action="store_true")
    a = ap.parse_args()
    batch() if a.batch else plants()


if __name__ == "__main__":
    main()
