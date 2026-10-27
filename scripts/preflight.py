"""Pre-flight an experiment's registered criteria on existing records before its runs (scb-experiment pipeline
step 1; retrospective 2026-10-27). Each --stand-in maps the experiment's run file names to an existing record, with
{row} matching any row: "run_c_{row}.json=A256_p24_limit_suspends_on_overload/cosim/run_s_{row}.json" (the source is
relative to track_A_periodic_steady_state). The analysis runs on a copy in a sibling folder, so its HERE.parent
lookups still work; the copy is removed afterwards. Runs without a stand-in are left out, so the analysis must accept
missing records (they print "complete: False").
  python3 scripts/preflight.py A258_p24_limit_count_cap --stand-in "run_c_{row}.json=A256_.../cosim/run_s_{row}.json"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TA = PROJECT / "experiments" / "track_A_periodic_steady_state"


def outs(exp):
    """The run file names the experiment's cfgs will write."""
    return sorted(json.loads(f.read_text())["out"] for f in (exp / "cosim").glob("cfg_*.json"))


def resolve(pattern, src, names):
    """{run name: existing record} for the run names that match pattern; src may use the same {row}."""
    rx = re.compile("^" + re.escape(pattern).replace(re.escape("{row}"), "(?P<row>.+)") + "$")
    hits = {}
    for n in names:
        m = rx.match(n)
        if m:
            f = TA / src.format(row=m.groupdict().get("row", ""))
            if f.exists():
                hits[n] = f
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("experiment", help="folder name under track_A_periodic_steady_state")
    ap.add_argument("--stand-in", action="append", default=[], help="RUN_PATTERN=SOURCE_PATTERN, {row} a wildcard")
    ap.add_argument("--analysis", help="the analysis script (default: the folder's a*_analyze.py)")
    a = ap.parse_args()
    exp = TA / a.experiment
    script = Path(a.analysis) if a.analysis else next(exp.glob("a*_analyze.py"))
    names, used = outs(exp), {}
    for s in a.stand_in:
        pat, src = s.split("=", 1)
        used |= resolve(pat, src, names)
    tmp = TA / f".preflight_{exp.name}"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        (tmp / "cosim").mkdir(parents=True)
        for f in exp.iterdir():                                   # scripts and data, not the records
            if f.is_file():
                shutil.copy2(f, tmp / f.name)
        for f in (exp / "cosim").glob("cfg_*.json"):
            shutil.copy2(f, tmp / "cosim" / f.name)
        for n, f in used.items():
            (tmp / "cosim" / n).symlink_to(f)
        print(f"stand-ins {len(used)} of {len(names)} runs; without: {', '.join(n for n in names if n not in used) or 'none'}")
        env = dict(os.environ, PYTHONPATH=str(PROJECT / "src"))
        r = subprocess.run(["python3", str(tmp / script.name)], cwd=tmp, env=env, capture_output=True, text=True)
        print((r.stdout + r.stderr).strip()[-3000:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
