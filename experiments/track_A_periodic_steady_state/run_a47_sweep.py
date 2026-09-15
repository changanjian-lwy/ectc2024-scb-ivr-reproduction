"""Run a directory of A47 LTspice cases with an adaptive solver-tolerance
escalation, and record which tier each case actually needed.

Why this exists: A47's nonlinear-Coss(V) stiff-capacitor-loop circuit (see
BOUNDARY.md "LTspice implementation note") converges promptly under the
base tolerance tier (`reltol=1e-5 abstol=1e-9 method=gear`, as written into
each generated .cir by build_a47_stage*.py) for most negative-current
percentages, but a minority of rows collapse to sub-attosecond timesteps
under that same tier while showing no sign of actual divergence (i.e. they
are simply numerically harder, not wrong). Rather than picking one
uniformly looser tolerance for every row (tried, and found to sometimes
behave WORSE for a specific row than the base tier -- solver convergence
here is not monotonic in tolerance looseness), each case is run under the
base tier with a wall-clock budget; if it does not finish in time, the case
file's `.options` line is escalated to the next looser tier and retried, up
to a fixed number of tiers. The tier actually used for each case is
recorded and reported, and rows that needed a looser tier than others are
never treated as a reason to change the row's *result*, only its runtime
solver settings -- see BOUNDARY.md for the specific rows this affected in
practice and the direct same-row tier-vs-tier comparison confirming the
physical answer does not change between tiers.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"

OPTIONS_RE = re.compile(r"^\.options .*$", re.MULTILINE)

TIERS = [
    (".options reltol=1e-5 abstol=1e-9 method=gear", 30),
    (".options reltol=1e-3 abstol=1e-7 method=gear itl4=500", 30),
    (".options reltol=1e-2 abstol=1e-6 method=gear itl4=2000", 45),
]


def run_case(cir: Path) -> tuple[int, float]:
    """Run one case, return (tier_index_used, wall_seconds)."""
    original = cir.read_text()
    for tier_idx, (options_line, budget_s) in enumerate(TIERS):
        text = OPTIONS_RE.sub(options_line, original, count=1)
        cir.write_text(text)
        for stale in (cir.with_suffix(".log"), cir.with_suffix(".raw"), cir.with_suffix(".db")):
            stale.unlink(missing_ok=True)

        proc = subprocess.Popen(
            [str(RUNNER), "run", str(cir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        start = time.monotonic()
        try:
            proc.wait(timeout=budget_s)
        except subprocess.TimeoutExpired:
            # ltspice_runner.sh execs a wine wrapper that spawns the real
            # LTspice.exe as a SEPARATE process not reachable via proc.kill()
            # (confirmed empirically: proc.kill() left LTspice.exe running
            # and consuming CPU well after this branch returned, silently
            # corrupting every subsequent tier's timing/result). Kill by the
            # case's own filename instead, which matches every process in
            # the wine/wrapper chain that has it on its command line.
            subprocess.run(["pkill", "-9", "-f", cir.name])
            proc.kill()
            proc.wait()
            time.sleep(1)
            elapsed = time.monotonic() - start
            print(f"  tier {tier_idx} ({options_line}) timed out after {elapsed:.1f}s, escalating", file=sys.stderr)
            continue
        elapsed = time.monotonic() - start

        log = cir.with_suffix(".log")
        if log.exists() and "Total elapsed time" in log.read_text(errors="replace"):
            return tier_idx, elapsed
        print(f"  tier {tier_idx} exited without completing cleanly, escalating", file=sys.stderr)

    raise RuntimeError(f"{cir.name} did not converge under any tolerance tier")


def main(case_dir: str) -> None:
    directory = Path(case_dir)
    cases = sorted(directory.glob("*.cir"))
    if not cases:
        raise SystemExit(f"no .cir files found in {directory}")
    summary = []
    for cir in cases:
        print(f"{cir.name} ...")
        tier_idx, elapsed = run_case(cir)
        print(f"  done: tier {tier_idx}, {elapsed:.1f}s")
        summary.append((cir.name, tier_idx, elapsed))
    print("\nSummary (case, tier_index_used, seconds):")
    for name, tier_idx, elapsed in summary:
        print(f"  {name}: tier {tier_idx}, {elapsed:.1f}s")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} <case directory>")
    main(sys.argv[1])
