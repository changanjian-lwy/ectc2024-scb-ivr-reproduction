"""Process check: the co-simulation's trajectory, not only its result, is the same before and after the clean-up.

    python3 scripts/cosim_trace_compare.py [--plant kernel2] [--cfg ARCHIVED_CFG]

Runs one archived configuration (default A92 n0) twice: with the archived A92 bridge and plant (copied verbatim into
tmp/trace/before/, plus the same checkpoint lines), and with the shared package (COSIM_TRACE). At every checkpoint
(after the plant is integrated to each gate edge and to each 4 ns window end) both update a running BLAKE2b hash of
t, the full state y, the diode flags and the Euler counter, and record it. The two lists must be identical; the
first differing checkpoint is reported otherwise. Writes tmp/trace/compare.json.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"
A92 = TA / "A92_verilog_error_based_correctors"
OSS_BIN = Path.home() / "tools" / "oss-cad-suite" / "bin"
HOOK = '''
    import hashlib as _hl
    _tr = {"h": _hl.blake2b(digest_size=16), "digests": []}

    def _ck():
        _tr["h"].update(np.float64(plant.t).tobytes() + np.asarray(plant.y, dtype=np.float64).tobytes()
                        + bytes(int(bool(x)) for x in plant.diode) + int(plant.euler_left).to_bytes(4, "little"))
        _tr["digests"].append(_tr["h"].hexdigest())
'''


def env():
    e = dict(os.environ)
    e["PATH"] = f"{OSS_BIN}:{e.get('PATH', '')}"
    e["PYTHONPATH"] = f"{PROJECT / 'src'}:{e.get('PYTHONPATH', '')}"
    return e


def before(cfg_src, out_dir):
    d = out_dir / "before"; d.mkdir(parents=True, exist_ok=True)
    br = (A92 / "cosim" / "test_cosim.py").read_text()
    reps = [('A88 = HERE.parent.parent / "A88_p24_predictive_low_side_turn_on"',
             f'A88 = Path({str(TA / "A88_p24_predictive_low_side_turn_on")!r})'),
            ("    def on_step():\n", HOOK + "\n    def on_step():\n"),
            ("            plant.integrate_to(ta, on_step)\n", "            plant.integrate_to(ta, on_step); _ck()\n"),
            ("        plant.integrate_to(t_win_end, on_step)\n", "        plant.integrate_to(t_win_end, on_step); _ck()\n"),
            ('    (cfg_path.parent / cfg["out"]).write_text(json.dumps(out))',
             '    (cfg_path.parent / "trace.json").write_text(json.dumps({"checkpoints": len(_tr["digests"]), '
             '"digests": _tr["digests"]}))\n    (cfg_path.parent / cfg["out"]).write_text(json.dumps(out))')]
    for a, b in reps:
        assert br.count(a) == 1, a
        br = br.replace(a, b)
    (d / "test_cosim.py").write_text(br)
    rn = (A92 / "cosim" / "run_cosim.py").read_text().replace('RTL = HERE.parent / "rtl"', f'RTL = Path({str(A92 / "rtl")!r})')
    (d / "run_cosim.py").write_text(rn)
    cfg = json.loads(cfg_src.read_text()); cfg["init_run"] = str((cfg_src.parent / cfg["init_run"]).resolve())
    (d / "cfg_trace.json").write_text(json.dumps(cfg, indent=1))
    t0 = time.time()
    with open(d / "log.txt", "w") as fh:
        subprocess.run([sys.executable, "run_cosim.py", "cfg_trace.json"], cwd=d, env=env(), stdout=fh, stderr=subprocess.STDOUT)
    return d / "trace.json", time.time() - t0


def shared(cfg_src, out_dir, plant):
    d = out_dir / plant; d.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(cfg_src.read_text()); cfg["init_run"] = str((cfg_src.parent / cfg["init_run"]).resolve())
    cfg["plant_impl"] = plant
    (d / "cfg_trace.json").write_text(json.dumps(cfg, indent=1))
    e = env(); e["COSIM_TRACE"] = str(d / "trace.json")
    t0 = time.time()
    subprocess.run([sys.executable, "-m", "scb_ivr.cosim.run", str(d / "cfg_trace.json"), "--jobs", "1"], env=e, cwd=PROJECT)
    return d / "trace.json", time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plant", default="kernel2")
    ap.add_argument("--cfg", type=Path, default=A92 / "cosim" / "cfg_n0_nominal.json")
    a = ap.parse_args()
    out_dir = PROJECT / "tmp" / "trace"; out_dir.mkdir(parents=True, exist_ok=True)
    (tb, wb), (tn, wn) = before(a.cfg, out_dir), shared(a.cfg, out_dir, a.plant)
    b, n = json.loads(tb.read_text())["digests"], json.loads(tn.read_text())["digests"]
    first = next((i for i, (x, y) in enumerate(zip(b, n)) if x != y), None)
    res = {"cfg": str(a.cfg), "plant": a.plant, "checkpoints_before": len(b), "checkpoints_after": len(n),
           "identical": first is None and len(b) == len(n), "first_difference": first,
           "final_digest_before": b[-1] if b else None, "final_digest_after": n[-1] if n else None,
           "wall_before_s": wb, "wall_after_s": wn}
    (out_dir / "compare.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
