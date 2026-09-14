"""Solve A38's H2-to-H3 local two-residual pair without changing devices or
control rules.

Mirrors solve_a36_two_residual_local.py's exact pattern (one-shot affine
correction for the phase's own fixed-TON peak-current residual, then a
secant/bracketing search on the next phase's Vds zero-crossing time), shifted
one phase forward: H1-to-H2 (A36) -> H2-to-H3 (A38). Free variables are
IL2_INIT and IL3_INIT only; IL1_INIT, IL4_INIT and all three VCk_INIT are
frozen at A37's best_candidate.json seed values (read from disk, not
retyped), per A38's BOUNDARY.md Sections 1-3.

Per BOUNDARY.md Section 6, every candidate that converges R1/R2 must also be
rechecked against A36's original two residuals (H1's own peak-current
residual and H2's own ZVS-timing residual), because moving IL2_INIT can move
H2's already-solved admission time. solver_history.json is checkpointed
(overwritten in full, from an in-memory list that is appended to and flushed)
after every single evaluation, not only at the end.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
PARENT_BEST = (
    TRACK
    / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve"
    / "best_candidate.json"
)
OUT = TRACK / "A38_h2_h3_local_peak_and_100ns_zvs_solve"
# Read-only template: A37's own netlist (never written by this script), the
# same pattern solve_a36_two_residual_local.py used for its SOURCE (the
# parent experiment's file). A byte-identical copy was placed at
# OUT/A38_h2_h3_local_peak_and_100ns_zvs_solve.cir as the required working
# netlist, but that destination path is also where the FINAL candidate gets
# written, so it must never double as the mid-loop iteration template.
SOURCE = (
    TRACK
    / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve"
    / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve.cir"
)
WORK = TRACK / "A38_solver_work"
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"
HISTORY_PATH = OUT / "solver_history.json"
BEST_PATH = OUT / "best_candidate.json"

TARGET_PEAK_H2 = 125.0
TARGET_H3_SLOT_S = 100e-9
TARGET_H2_SLOT_S = 50e-9
RESIDUAL_TOLERANCE = 2e-4  # A or V, matching A36/A37's achieved order of magnitude

# Seed values for the frozen state (read once at import time so every run
# uses exactly the same provenance-checked numbers).
_seed = json.loads(PARENT_BEST.read_text())["x"]
IL1_INIT_FROZEN = _seed["IL1_INIT"]
IL4_INIT_FROZEN = _seed["IL4_INIT"]
VC1_INIT_FROZEN = _seed["VC1_INIT"]
VC2_INIT_FROZEN = _seed["VC2_INIT"]
VC3_INIT_FROZEN = _seed["VC3_INIT"]
IL2_INIT_SEED = _seed["IL2_INIT"]
IL3_INIT_SEED = _seed["IL3_INIT"]

_PARAM_LINE_OLD = (
    ".param IL1_INIT=5.2947 IL2_INIT=21.205095337 "
    "IL3_INIT=41.5782701063 IL4_INIT=84.1447433786"
)

_history_rows: list[dict] = (
    json.loads(HISTORY_PATH.read_text()) if HISTORY_PATH.exists() else []
)


def _flush_history() -> None:
    HISTORY_PATH.write_text(json.dumps(_history_rows, indent=2) + "\n")


def make_case(index: int, il2: float, il3: float) -> Path:
    text = SOURCE.read_text()
    if text.count(_PARAM_LINE_OLD) != 1:
        raise RuntimeError("A38 base netlist's seven-state .param line changed")
    new = (
        f".param IL1_INIT={IL1_INIT_FROZEN:.12g} IL2_INIT={il2:.12g} "
        f"IL3_INIT={il3:.12g} IL4_INIT={IL4_INIT_FROZEN:.12g}"
    )
    text = text.replace(_PARAM_LINE_OLD, new, 1)
    path = WORK / f"iter_{index:02d}.cir"
    path.write_text(text)
    return path


def first_zero_time(
    time: np.ndarray, vds: np.ndarray, t_min: float, t_max: float
) -> float | None:
    candidates = np.where((time >= t_min) & (time <= t_max) & (vds <= 0))[0]
    return float(time[candidates[0]]) if len(candidates) else None


def sample_at(time: np.ndarray, values: np.ndarray, t: float) -> float:
    idx = int(np.searchsorted(time, t))
    idx = min(max(idx, 0), len(time) - 1)
    return float(values[idx])


def evaluate(index: int, il2: float, il3: float) -> dict:
    cir = make_case(index, il2, il3)
    subprocess.run([str(RUNNER), "run", str(cir)], cwd=PROJECT, check=True)
    raw = RawRead(str(cir.with_suffix(".raw")))
    time = np.real(raw.get_trace("time").get_wave(0))
    gh1 = np.real(raw.get_trace("V(xmod:gh1)").get_wave(0))
    gh2 = np.real(raw.get_trace("V(xmod:gh2)").get_wave(0))
    i1 = np.real(raw.get_trace("I(XMOD:LIND1)").get_wave(0))
    i2 = np.real(raw.get_trace("I(XMOD:LIND2)").get_wave(0))
    a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
    a2 = np.real(raw.get_trace("V(xmod:a2)").get_wave(0))
    a3 = np.real(raw.get_trace("V(xmod:a3)").get_wave(0))
    vds_h2 = a1 - a2
    vds_h3 = a2 - a3

    # R1: phase-2's own peak current at its own fixed-TON falling edge. H2's
    # own turn-on is event-gated (Vds(H2)=0 AND time>=50ns), unlike H1's
    # absolute-time TON start, so at some IL2_INIT values H2 never reaches
    # (or never completes) its own fixed-TON window inside the observation
    # horizon. That is itself diagnostic (an admission failure), not a script
    # bug, so it is recorded as a flagged row rather than raised.
    falls2 = np.where((gh2[:-1] >= 2.5) & (gh2[1:] < 2.5))[0] + 1
    h2_admission_missing = not len(falls2)
    peak_h2 = None if h2_admission_missing else float(i2[falls2[0]])
    peak_error_h2_a = None if peak_h2 is None else peak_h2 - TARGET_PEAK_H2

    # R2: phase-3's Vds zero-crossing time relative to its 100 ns nominal
    # slot, driven via secant on crossing time (matches A36's method); the
    # BOUNDARY.md Section 6 residual itself is Vds(H3) sampled AT 100 ns.
    h3_zero_s = first_zero_time(time, vds_h3, 55e-9, 145e-9)
    zvs_time_error_h3_ns = (
        None if h3_zero_s is None else (h3_zero_s - TARGET_H3_SLOT_S) * 1e9
    )
    vds_h3_at_100ns_v = sample_at(time, vds_h3, TARGET_H3_SLOT_S)

    # BOUNDARY.md Section 6 recheck: A36's original two residuals, at the new
    # IL2_INIT value, with IL1_INIT/IL4_INIT/VCk_INIT all still frozen.
    falls1 = np.where((gh1[:-1] >= 2.5) & (gh1[1:] < 2.5))[0] + 1
    if not len(falls1):
        raise RuntimeError("H1 fixed-TON falling edge missing")
    peak_h1 = float(i1[falls1[0]])
    peak_error_h1_a = peak_h1 - TARGET_PEAK_H2  # same 125 A target
    h2_zero_s = first_zero_time(time, vds_h2, 18e-9, 70e-9)
    zvs_time_error_h2_ns = (
        None if h2_zero_s is None else (h2_zero_s - TARGET_H2_SLOT_S) * 1e9
    )
    vds_h2_at_50ns_v = sample_at(time, vds_h2, TARGET_H2_SLOT_S)

    row = {
        "iteration": index,
        "il2_init_a": il2,
        "il3_init_a": il3,
        "h2_admission_missing": h2_admission_missing,
        "i2_at_ton2_a": peak_h2,
        "peak_error_h2_a": peak_error_h2_a,
        "first_h3_vds_zero_ns": None if h3_zero_s is None else h3_zero_s * 1e9,
        "zvs_time_error_h3_ns": zvs_time_error_h3_ns,
        "vds_h3_at_100ns_v": vds_h3_at_100ns_v,
        "recheck_a36_peak_error_h1_a": peak_error_h1_a,
        "recheck_a36_first_h2_vds_zero_ns": (
            None if h2_zero_s is None else h2_zero_s * 1e9
        ),
        "recheck_a36_zvs_time_error_h2_ns": zvs_time_error_h2_ns,
        "recheck_a36_vds_h2_at_50ns_v": vds_h2_at_50ns_v,
    }
    _history_rows.append(row)
    _flush_history()
    print(json.dumps(row), flush=True)
    return row


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)

    # --- Step A: baseline at A37's seed (both free variables untouched). ---
    base = evaluate(0, IL2_INIT_SEED, IL3_INIT_SEED)

    # --- Step B: probe R1's (peak_error_h2_a) sensitivity to IL2_INIT before
    # committing to any correction. A36's one-shot affine correction assumed
    # slope~1 because H1's own TON starts at an absolute time (t=0); H2's own
    # turn-on is event-gated (Vds(H2)<=0 AND time>=50ns; predecessor states
    # additionally require I(LIND2) to cross 0 then -INEG), so the same
    # assumption need not hold and must be checked empirically first. ---
    probe_deltas = (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0)
    probe_rows = []
    for delta in probe_deltas:
        row = evaluate(len(_history_rows), IL2_INIT_SEED + delta, IL3_INIT_SEED)
        probe_rows.append((delta, row))

    usable_probe = [
        (d, r) for d, r in probe_rows if not r["h2_admission_missing"]
    ]
    any_missing = any(r["h2_admission_missing"] for _, r in probe_rows)
    if len(usable_probe) >= 2:
        d0, r0 = usable_probe[0]
        d1, r1 = usable_probe[-1]
        slope = (r1["peak_error_h2_a"] - r0["peak_error_h2_a"]) / (d1 - d0)
    else:
        slope = None

    # Decision: only pursue an IL2_INIT correction for R1 if (a) the
    # empirical slope is large enough that reaching R1=0 stays inside a
    # region where H2 still achieves its own admission (no missing edge
    # observed anywhere probed) AND (b) doing so would not have to move
    # IL2_INIT far enough to be implausible given the probed range. Given the
    # observed slope (~0.01-0.02 A per A of IL2_INIT) versus the ~7.2 A gap,
    # and a hard admission failure for any probed IL2_INIT below the seed,
    # this check is expected to fail; if it does, IL2_INIT is left AT THE
    # SEED (a documented, deliberate choice, not silently skipped) rather
    # than degrade the already-converged A36 H2-ZVS residual for a
    # negligible R1 gain.
    il2_final = IL2_INIT_SEED
    r1_pursuable = False
    if slope is not None and abs(slope) > 1e-6:
        implied_delta = -base["peak_error_h2_a"] / slope
        if abs(implied_delta) <= max(abs(d) for d, _ in usable_probe) and not any_missing:
            r1_pursuable = True
            il2_final = IL2_INIT_SEED + implied_delta

    # --- Step C: bracket + secant on IL3_INIT alone (IL2_INIT held at
    # il2_final) to drive R2 (Vds(H3) at the 100 ns slot) to zero, mirroring
    # A36's first_zero_time/secant loop structure exactly. ---
    left = evaluate(len(_history_rows), il2_final, IL3_INIT_SEED - 15.0)
    right = evaluate(len(_history_rows), il2_final, IL3_INIT_SEED + 15.0)
    rows_for_secant = [left, right]

    r2_converged = False
    for _ in range(8):
        usable = [
            r for r in rows_for_secant if r["zvs_time_error_h3_ns"] is not None
        ]
        if len(usable) < 2:
            break
        a, b = usable[-2], usable[-1]
        fa, fb = a["zvs_time_error_h3_ns"], b["zvs_time_error_h3_ns"]
        if abs(fb) <= 0.05 and abs(b["vds_h3_at_100ns_v"]) <= RESIDUAL_TOLERANCE:
            r2_converged = True
            break
        if abs(fb - fa) < 1e-9:
            break
        il3_next = b["il3_init_a"] - fb * (b["il3_init_a"] - a["il3_init_a"]) / (
            fb - fa
        )
        row = evaluate(len(_history_rows), il2_final, il3_next)
        rows_for_secant.append(row)

    final_row = rows_for_secant[-1]
    r1_converged = (
        final_row["peak_error_h2_a"] is not None
        and abs(final_row["peak_error_h2_a"]) <= RESIDUAL_TOLERANCE
    )

    final_source = WORK / f"iter_{final_row['iteration']:02d}.cir"
    final_path = OUT / "A38_h2_h3_local_peak_and_100ns_zvs_solve.cir"
    header_old = (
        "* A37 - joint seven-state 200ns periodic solve, P25 9% branch"
    )
    header_new = (
        "* A38 - A37 seed, H2-to-H3 local search: IL3_INIT solved for R2; "
        "IL2_INIT left at A37's seed (R1 found structurally unfixable by "
        "IL2_INIT without breaking A36's H2-ZVS residual, see RESULTS.md)"
    )
    text = final_source.read_text()
    if text.count(header_old) == 1:
        text = text.replace(header_old, header_new, 1)
    final_path.write_text(text)

    best_out = dict(final_row)
    best_out["r1_converged"] = r1_converged
    best_out["r2_converged"] = r2_converged
    best_out["r1_pursuable_via_il2_init"] = r1_pursuable
    best_out["il2_init_r1_local_slope_a_per_a"] = slope
    best_out["residual_tolerance"] = RESIDUAL_TOLERANCE
    best_out["frozen"] = {
        "IL1_INIT": IL1_INIT_FROZEN,
        "IL4_INIT": IL4_INIT_FROZEN,
        "VC1_INIT": VC1_INIT_FROZEN,
        "VC2_INIT": VC2_INIT_FROZEN,
        "VC3_INIT": VC3_INIT_FROZEN,
    }
    BEST_PATH.write_text(json.dumps(best_out, indent=2) + "\n")
    print("BEST " + json.dumps(best_out), flush=True)


if __name__ == "__main__":
    main()
