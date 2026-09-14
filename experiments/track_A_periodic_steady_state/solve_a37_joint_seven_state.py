"""Joint seven-state, fifteen-residual solve for A37 (see BOUNDARY.md).

Follows the same idioms as solve_a36_two_residual_local.py: drives
tools/ltspice_runner.sh, parses the .raw output with spicelib.RawRead, edits
the .param lines of a copied .cir, and records solver_history.json /
best_candidate.json in the same style.

Unlike A36 (2 residuals, 2 free variables, a hand-rolled secant update), A37
runs ONE joint scipy.optimize.least_squares solve over all seven free
variables (IL1_INIT..IL4_INIT, VC1_INIT..VC3_INIT) against the full fifteen
residuals defined in this experiment's BOUNDARY.md Section 6 -- 4 peak-current
residuals, 4 ZVS-timing residuals, 7 periodicity residuals -- with no
pre-weighting and no dropped residuals, per Mihai's 2026-09-14 decision
recorded there. scipy has no analytic Jacobian available (LTspice is a black
box), so this uses a finite-difference Jacobian.

Method note: an earlier run of this script used method="lm" (classical
Levenberg-Marquardt/MINPACK). That run did not respect the intended max_nfev
budget the way scipy's docs describe for "trf"/"dogbox" (it was still going
past 120 residual evaluations, plateaued around residual_norm~209, well
short of any real convergence) before the host session was torn down
externally. This is now believed to be a real numerical-method finding, not
a physics/netlist bug: two of the four peak-current residuals (H3, H4) are
structurally pinned at exactly -125 A whenever the rotating state machine's
upstream ZVS admission is missed (see `_first_fall_value`/`missed_admission`
below), which makes the local residual surface flat in those two components
over most of the seven-dimensional neighborhood explored -- a finite-
difference Jacobian gets no usable gradient from a flat region, which is
consistent with MINPACK's lm needing many more evaluations than expected and
never settling. This script now uses method="trf" (Trust Region Reflective),
which scipy documents as properly honoring max_nfev as a hard cap, so a
budget-exhausted outcome is reached predictably instead of running
indefinitely.

Recovery note: this script also supports rebuilding solver_history.json from
already-completed A37_solver_work/iter_NNN.{cir,raw} pairs on disk (via
`recover_from_disk`) without re-invoking LTspice, and checkpoints every
evaluation to solver_history.json immediately (not only at the end), so an
external interruption (e.g. the host session being torn down) does not lose
completed LTspice runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import subprocess

import numpy as np
from scipy.optimize import least_squares
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
OUT = TRACK / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve"
SOURCE = OUT / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve.cir"
WORK = TRACK / "A37_solver_work"
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"
HISTORY_PATH = OUT / "solver_history.json"

TARGET_PEAK = 125.0
PHASE_S = 50e-9
T_S = 200e-9
EPS_S = 2e-12  # matches the netlist's own {T0+2p} / {T0+T+2p} sample offset

IL_ANCHOR = (
    ".param IL1_INIT=5.2947 IL2_INIT=21.20509533697147 "
    "IL3_INIT=41.5782701063 IL4_INIT=84.1447433786"
)
VC_ANCHOR = ".param VC1_INIT=36.000066454 VC2_INIT=23.9999142326 VC3_INIT=12.0006048777"

PARAM_NAMES = [
    "IL1_INIT", "IL2_INIT", "IL3_INIT", "IL4_INIT",
    "VC1_INIT", "VC2_INIT", "VC3_INIT",
]

# Order matches BOUNDARY.md Section 6 exactly: 4 peak + 4 ZVS-timing + 7 periodic.
RESIDUAL_NAMES = [
    "peak_error_h1_a", "peak_error_h2_a", "peak_error_h3_a", "peak_error_h4_a",
    "zvs_error_h2_v", "zvs_error_h3_v", "zvs_error_h4_v", "zvs_error_h1_v",
    "periodic_error_il1_a", "periodic_error_il2_a",
    "periodic_error_il3_a", "periodic_error_il4_a",
    "periodic_error_vc1_v", "periodic_error_vc2_v", "periodic_error_vc3_v",
]

CALL_LOG: list[dict] = []

_PARAM_RE = re.compile(
    r"^\.param IL1_INIT=(?P<il1>\S+) IL2_INIT=(?P<il2>\S+) "
    r"IL3_INIT=(?P<il3>\S+) IL4_INIT=(?P<il4>\S+)\s*$",
    re.MULTILINE,
)
_VC_RE = re.compile(
    r"^\.param VC1_INIT=(?P<vc1>\S+) VC2_INIT=(?P<vc2>\S+) VC3_INIT=(?P<vc3>\S+)\s*$",
    re.MULTILINE,
)


def make_case(index: int, x: np.ndarray) -> Path:
    il1, il2, il3, il4, vc1, vc2, vc3 = (float(v) for v in x)
    text = SOURCE.read_text()
    if text.count(IL_ANCHOR) != 1:
        raise RuntimeError("A37 IL_INIT anchor line changed")
    if text.count(VC_ANCHOR) != 1:
        raise RuntimeError("A37 VC_INIT anchor line changed")
    new_il = (
        f".param IL1_INIT={il1:.12g} IL2_INIT={il2:.12g} "
        f"IL3_INIT={il3:.12g} IL4_INIT={il4:.12g}"
    )
    new_vc = f".param VC1_INIT={vc1:.12g} VC2_INIT={vc2:.12g} VC3_INIT={vc3:.12g}"
    text = text.replace(IL_ANCHOR, new_il, 1)
    text = text.replace(VC_ANCHOR, new_vc, 1)
    path = WORK / f"iter_{index:03d}.cir"
    path.write_text(text)
    return path


def params_from_cir(cir_path: Path) -> np.ndarray:
    text = cir_path.read_text()
    m_il = _PARAM_RE.search(text)
    m_vc = _VC_RE.search(text)
    if not m_il or not m_vc:
        raise RuntimeError(f"{cir_path}: could not recover IL/VC .param values")
    return np.array([
        float(m_il["il1"]), float(m_il["il2"]), float(m_il["il3"]), float(m_il["il4"]),
        float(m_vc["vc1"]), float(m_vc["vc2"]), float(m_vc["vc3"]),
    ])


def _interp_at(time: np.ndarray, wave: np.ndarray, t: float) -> float:
    return float(np.interp(t, time, wave))


def _first_fall_value(gate: np.ndarray, value: np.ndarray) -> float | None:
    """Value of `value` at the first VG->0 falling edge of `gate` (fixed-TON
    high-side turn-off), matching solve_a36_two_residual_local.py's method."""
    falls = np.where((gate[:-1] >= 2.5) & (gate[1:] < 2.5))[0] + 1
    if not len(falls):
        return None
    return float(value[falls[0]])


def residuals_from_raw(raw_path: Path) -> tuple[np.ndarray, dict]:
    """Compute the 15 BOUNDARY.md residuals from an already-completed .raw
    file. Pure function of the .raw contents -- does not invoke LTspice."""
    raw = RawRead(str(raw_path))
    time = np.real(raw.get_trace("time").get_wave(0))

    i1 = np.real(raw.get_trace("I(xmod:lind1)").get_wave(0))
    i2 = np.real(raw.get_trace("I(xmod:lind2)").get_wave(0))
    i3 = np.real(raw.get_trace("I(xmod:lind3)").get_wave(0))
    i4 = np.real(raw.get_trace("I(xmod:lind4)").get_wave(0))

    gh1 = np.real(raw.get_trace("V(xmod:gh1)").get_wave(0))
    gh2 = np.real(raw.get_trace("V(xmod:gh2)").get_wave(0))
    gh3 = np.real(raw.get_trace("V(xmod:gh3)").get_wave(0))
    gh4 = np.real(raw.get_trace("V(xmod:gh4)").get_wave(0))

    vin = np.real(raw.get_trace("V(vin)").get_wave(0))
    a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
    a2 = np.real(raw.get_trace("V(xmod:a2)").get_wave(0))
    a3 = np.real(raw.get_trace("V(xmod:a3)").get_wave(0))
    x4 = np.real(raw.get_trace("V(xmod:x4)").get_wave(0))
    x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))
    x2 = np.real(raw.get_trace("V(xmod:x2)").get_wave(0))
    x3 = np.real(raw.get_trace("V(xmod:x3)").get_wave(0))

    vds_h1 = vin - a1
    vds_h2 = a1 - a2
    vds_h3 = a2 - a3
    vds_h4 = a3 - x4

    # A downstream phase's Hk can structurally never turn on within this
    # 205 ns window if an upstream phase missed its own ZVS slot (the
    # rotating state machine is sequential/shared, so one blocked admission
    # cascades and stalls every later phase in the same run). When that
    # happens there is no fixed-TON falling edge to measure the peak
    # current at, so no conduction occurred: the peak actually delivered is
    # 0 A, not an undefined quantity, and is recorded honestly as such
    # (flagged separately) rather than raising and losing the whole solve.
    missed_admission = {}
    peaks = []
    for name, gate, current in (
        ("h1", gh1, i1), ("h2", gh2, i2), ("h3", gh3, i3), ("h4", gh4, i4),
    ):
        value = _first_fall_value(gate, current)
        missed_admission[name] = value is None
        peaks.append(0.0 if value is None else value)
    peak_h1, peak_h2, peak_h3, peak_h4 = peaks

    # ZVS-timing residuals are sampled AT the nominal slot, not WHEN-triggered:
    # this is how a MISSED_ZVS_SLOT is measured rather than masked.
    zvs_h2 = _interp_at(time, vds_h2, 1 * PHASE_S)
    zvs_h3 = _interp_at(time, vds_h3, 2 * PHASE_S)
    zvs_h4 = _interp_at(time, vds_h4, 3 * PHASE_S)
    zvs_h1 = _interp_at(time, vds_h1, 4 * PHASE_S)

    vc1 = a1 - x1
    vc2 = a2 - x2
    vc3 = a3 - x3

    per_il1 = _interp_at(time, i1, T_S + EPS_S) - _interp_at(time, i1, EPS_S)
    per_il2 = _interp_at(time, i2, T_S + EPS_S) - _interp_at(time, i2, EPS_S)
    per_il3 = _interp_at(time, i3, T_S + EPS_S) - _interp_at(time, i3, EPS_S)
    per_il4 = _interp_at(time, i4, T_S + EPS_S) - _interp_at(time, i4, EPS_S)
    per_vc1 = _interp_at(time, vc1, T_S + EPS_S) - _interp_at(time, vc1, EPS_S)
    per_vc2 = _interp_at(time, vc2, T_S + EPS_S) - _interp_at(time, vc2, EPS_S)
    per_vc3 = _interp_at(time, vc3, T_S + EPS_S) - _interp_at(time, vc3, EPS_S)

    residuals = np.array([
        peak_h1 - TARGET_PEAK, peak_h2 - TARGET_PEAK,
        peak_h3 - TARGET_PEAK, peak_h4 - TARGET_PEAK,
        zvs_h2, zvs_h3, zvs_h4, zvs_h1,
        per_il1, per_il2, per_il3, per_il4,
        per_vc1, per_vc2, per_vc3,
    ])
    return residuals, missed_admission


def _checkpoint() -> None:
    OUT.mkdir(exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(CALL_LOG, indent=2) + "\n")


def record(index: int, x: np.ndarray, residuals: np.ndarray, missed_admission: dict) -> dict:
    row = {
        "iteration": index,
        "x": {name: float(v) for name, v in zip(PARAM_NAMES, x)},
    }
    row.update({name: float(v) for name, v in zip(RESIDUAL_NAMES, residuals)})
    row["residual_norm"] = float(np.linalg.norm(residuals))
    row["missed_admission"] = missed_admission
    CALL_LOG.append(row)
    _checkpoint()  # incremental checkpoint: survives an external interruption
    print(json.dumps(row), flush=True)
    return row


def evaluate(index: int, x: np.ndarray) -> np.ndarray:
    cir = make_case(index, x)
    subprocess.run([str(RUNNER), "run", str(cir)], cwd=PROJECT, check=True)
    residuals, missed_admission = residuals_from_raw(cir.with_suffix(".raw"))
    record(index, x, residuals, missed_admission)
    return residuals


def recover_from_disk() -> int:
    """Rebuild CALL_LOG (and checkpoint it) from already-completed
    iter_NNN.{cir,raw} pairs in A37_solver_work, without invoking LTspice.
    Returns the highest recovered iteration index, or 0 if none exist."""
    cirs = sorted(WORK.glob("iter_*.cir"))
    highest = 0
    for cir in cirs:
        raw = cir.with_suffix(".raw")
        if not raw.exists():
            continue
        index = int(cir.stem.split("_")[1])
        x = params_from_cir(cir)
        residuals, missed_admission = residuals_from_raw(raw)
        record(index, x, residuals, missed_admission)
        highest = max(highest, index)
    return highest


_call_count = {"n": 0}


def residual_fn(x: np.ndarray) -> np.ndarray:
    _call_count["n"] += 1
    return evaluate(_call_count["n"], x)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)

    # Recover any already-completed LTspice runs from a prior interrupted
    # attempt before spending new simulation time.
    highest_recovered = recover_from_disk()
    _call_count["n"] = highest_recovered

    x0 = np.array([
        5.2947, 21.20509533697147, 41.5782701063, 84.1447433786,
        36.000066454, 23.9999142326, 12.0006048777,
    ])

    # "trf" (Trust Region Reflective) is scipy's general-purpose method for a
    # rectangular least-squares problem (15 residuals, 7 unknowns) and
    # properly honors max_nfev as a hard cap, unlike the "lm"/MINPACK path
    # tried first (see module docstring). diff_step is a relative
    # finite-difference step chosen to sit above LTspice's own reltol=1e-5
    # numerical noise floor while still being a local probe.
    result = least_squares(
        residual_fn, x0, method="trf", diff_step=1e-3, max_nfev=60,
    )

    # Evaluate once more at the reported solution so its residuals are on
    # record, but do NOT assume it is the best point: with no pre-weighting,
    # an optimizer minimizing the aggregate Euclidean norm can trade away
    # already-converged residuals for a smaller sum elsewhere, which is a
    # regression under this experiment's per-residual grading. Best is
    # therefore selected from the full CALL_LOG by (most residuals converged,
    # then smallest norm as a tiebreaker), matching how RESULTS.md grades it.
    evaluate(_call_count["n"] + 1, result.x)

    tol = 2e-4  # matches the order of magnitude A36 itself achieved and called converged
    def converged_count(row: dict) -> int:
        return sum(1 for name in RESIDUAL_NAMES if abs(row[name]) <= tol)

    best_row = dict(max(CALL_LOG, key=lambda r: (converged_count(r), -r["residual_norm"])))
    best_row["converged_residual_count"] = converged_count(best_row)
    best_row["residual_tolerance"] = tol
    best_row["final_solution"] = True
    best_row["optimizer_status"] = int(result.status)
    best_row["optimizer_message"] = str(result.message)
    best_row["optimizer_success"] = bool(result.success)
    best_row["optimizer_nfev"] = int(result.nfev)

    (OUT / "best_candidate.json").write_text(json.dumps(best_row, indent=2) + "\n")

    best_cir = WORK / f"iter_{best_row['iteration']:03d}.cir"
    SOURCE.write_text(best_cir.read_text())

    print("BEST " + json.dumps(best_row), flush=True)


if __name__ == "__main__":
    main()
