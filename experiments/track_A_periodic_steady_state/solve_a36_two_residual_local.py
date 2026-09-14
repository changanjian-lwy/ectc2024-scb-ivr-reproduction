"""Solve A35's two local residuals without changing devices or control rules."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
SOURCE = TRACK / "A35_hybrid_fixed_ton_event_zvs_slot_guard_09pct" / "A35_hybrid_fixed_ton_event_zvs_slot_guard_09pct.cir"
WORK = TRACK / "A36_solver_work"
OUT = TRACK / "A36_local_peak_and_50ns_zvs_solve"
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"
TARGET_PEAK = 125.0
TARGET_ZVS_S = 50e-9


def make_case(index: int, il1: float, il2: float) -> Path:
    text = SOURCE.read_text()
    old = ".param IL1_INIT=-.935685816243 IL2_INIT=4.75555393314"
    new = f".param IL1_INIT={il1:.12g} IL2_INIT={il2:.12g}"
    if text.count(old) != 1:
        raise RuntimeError("A35 initial-state anchor changed")
    text = text.replace(old, new, 1)
    path = WORK / f"iter_{index:02d}.cir"
    path.write_text(text)
    return path


def first_zero_time(time: np.ndarray, vds: np.ndarray) -> float | None:
    candidates = np.where((time >= 18e-9) & (time <= 70e-9) & (vds <= 0))[0]
    return float(time[candidates[0]]) if len(candidates) else None


def evaluate(index: int, il1: float, il2: float) -> dict:
    cir = make_case(index, il1, il2)
    subprocess.run([str(RUNNER), "run", str(cir)], cwd=PROJECT, check=True)
    raw = RawRead(str(cir.with_suffix(".raw")))
    time = np.real(raw.get_trace("time").get_wave(0))
    i1 = np.real(raw.get_trace("I(xmod:L1)").get_wave(0))
    gh1 = np.real(raw.get_trace("V(xmod:gh1)").get_wave(0))
    a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
    a2 = np.real(raw.get_trace("V(xmod:a2)").get_wave(0))
    vds = a1 - a2
    falls = np.where((gh1[:-1] >= 2.5) & (gh1[1:] < 2.5))[0] + 1
    if not len(falls):
        raise RuntimeError("H1 fixed-TON falling edge missing")
    peak = float(i1[falls[0]])
    zero = first_zero_time(time, vds)
    row = {
        "iteration": index,
        "il1_init_a": il1,
        "il2_init_a": il2,
        "i1_at_ton_a": peak,
        "peak_error_a": peak - TARGET_PEAK,
        "first_h2_vds_zero_ns": None if zero is None else zero * 1e9,
        "zvs_time_error_ns": None if zero is None else (zero - TARGET_ZVS_S) * 1e9,
    }
    print(json.dumps(row), flush=True)
    return row


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    rows = []

    # Peak residual is nearly affine in initial current over the fixed H1 TON.
    base = evaluate(0, -0.935685816243, 4.75555393314)
    rows.append(base)
    il1 = base["il1_init_a"] - base["peak_error_a"]

    # Bracket the phase-2 zero time using only IL2(0), then use secant updates.
    left = evaluate(1, il1, 12.0)
    right = evaluate(2, il1, 24.0)
    rows.extend((left, right))
    for index in range(3, 9):
        usable = [r for r in rows if r["zvs_time_error_ns"] is not None]
        if len(usable) < 2:
            raise RuntimeError("could not obtain two H2 zero-time points")
        a, b = usable[-2], usable[-1]
        fa, fb = a["zvs_time_error_ns"], b["zvs_time_error_ns"]
        if abs(fb) <= 0.02 and abs(b["peak_error_a"]) <= 0.05:
            break
        if abs(fb - fa) < 1e-9:
            raise RuntimeError("zero-time secant slope collapsed")
        il2 = b["il2_init_a"] - fb * (b["il2_init_a"] - a["il2_init_a"]) / (fb - fa)
        row = evaluate(index, il1, il2)
        rows.append(row)

    best = min(
        (r for r in rows if r["zvs_time_error_ns"] is not None),
        key=lambda r: abs(r["zvs_time_error_ns"]) + abs(r["peak_error_a"]),
    )
    final_source = WORK / f"iter_{best['iteration']:02d}.cir"
    final_path = OUT / "A36_local_peak_and_50ns_zvs_solve.cir"
    final_path.write_text(final_source.read_text().replace(
        "* A35 - hybrid fixed-TON, event-ZVS, phase-slot guard, P25 9%",
        "* A36 - A35 local two-residual solved initial-current candidate",
        1,
    ))
    (OUT / "solver_history.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "best_candidate.json").write_text(json.dumps(best, indent=2) + "\n")
    print("BEST " + json.dumps(best), flush=True)


if __name__ == "__main__":
    main()
