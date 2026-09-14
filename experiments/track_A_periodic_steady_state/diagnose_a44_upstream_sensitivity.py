"""A44 diagnostic driver: holding IL2_INIT fixed at A38's own seed value
(A39 already swept IL2_INIT itself and found H2's admission current pinned
near -1.29 A, moving only 0.014 A over a 2 A IL2_INIT probe), does
perturbing any of the OTHER six coupled state variables -- IL1_INIT,
IL3_INIT, IL4_INIT, VC1_INIT, VC2_INIT, VC3_INIT -- one at a time, move H2's
admission current or admission time instead?

This is PURELY DIAGNOSTIC (A44 BOUNDARY.md): nothing is solved, no locked
parameter is retuned, no swept value is promoted to a default. It reuses
A39's own measurement method exactly (same trace names, same edge-detection
functions, same admission definition: the inductor current I(XMOD:LIND2)
and time at the rising edge of the H2 gate V(xmod:gh2)), applied to a
different set of perturbed variables.

Netlist template: A38's own final .cir (READ ONLY -- never modified,
overwritten, or deleted; A44 writes only its own new files under
A44_solver_work/ and A44_h2_admission_upstream_state_sensitivity/).

Baseline seven-state seed (identical to A39 Part 2's single run, itself
byte-identical to A38's own best_candidate.json / A37's best_candidate.json
VCk values):
    IL1_INIT = 5.2947                  (A36 solved)
    IL2_INIT = 21.205095337             (A38 seed, held fixed throughout A44)
    IL3_INIT = 56.32056566312004        (A38 solved, full precision from
                                          A38's best_candidate.json "il3_init_a")
    IL4_INIT = 84.1447433786            (A37/A38 frozen)
    VC1_INIT = 36.000066454             (A37 solved)
    VC2_INIT = 23.9999142326            (A37 solved)
    VC3_INIT = 12.0006048777            (A37 solved)
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np
from spicelib import RawRead


TRACK = Path(__file__).resolve().parent
PROJECT = TRACK.parents[1]
A38_DIR = TRACK / "A38_h2_h3_local_peak_and_100ns_zvs_solve"
SOURCE = A38_DIR / "A38_h2_h3_local_peak_and_100ns_zvs_solve.cir"
A38_BEST = json.loads((A38_DIR / "best_candidate.json").read_text())

WORK = TRACK / "A44_solver_work"
OUT = TRACK / "A44_h2_admission_upstream_state_sensitivity"
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"

# Reuse A39's own edge-detection functions rather than reimplementing them.
# Importing this module does NOT execute its sweep/comparison (guarded by
# `if __name__ == "__main__":` in that file) and does NOT create any
# directories or run any simulation at import time.
_A39_SPEC = importlib.util.spec_from_file_location(
    "diagnose_a39_h1_h2_sensitivity", TRACK / "diagnose_a39_h1_h2_sensitivity.py"
)
_a39 = importlib.util.module_from_spec(_A39_SPEC)
_A39_SPEC.loader.exec_module(_a39)
falling_edge_idx = _a39.falling_edge_idx
rising_edge_idx = _a39.rising_edge_idx

# Baseline seven-state seed, read from A38's own best_candidate.json (not
# retyped from memory) and A39 Part 2's own frozen block (which itself reads
# from A38's best_candidate.json "frozen" dict) -- byte-identical to A39
# Part 2's single representative run.
BASELINE = {
    "IL1_INIT": A38_BEST["frozen"]["IL1_INIT"],
    "IL2_INIT": A38_BEST["il2_init_a"],
    "IL3_INIT": A38_BEST["il3_init_a"],
    "IL4_INIT": A38_BEST["frozen"]["IL4_INIT"],
    "VC1_INIT": A38_BEST["frozen"]["VC1_INIT"],
    "VC2_INIT": A38_BEST["frozen"]["VC2_INIT"],
    "VC3_INIT": A38_BEST["frozen"]["VC3_INIT"],
}

_PARAM_LINE_OLD = (
    ".param IL1_INIT=5.2947 IL2_INIT=21.205095337 "
    "IL3_INIT=56.3205656631 IL4_INIT=84.1447433786"
)
_VC_LINE_OLD = (
    ".param VC1_INIT=36.000066454 VC2_INIT=23.9999142326 "
    "VC3_INIT=12.0006048777"
)

# Perturbation steps per BOUNDARY.md Section 5: currents +/-1 A and +/-2 A;
# capacitor voltages +/-0.2 V and +/-0.5 V. All SENSITIVITY_ONLY.
CURRENT_STEPS = [-2.0, -1.0, 1.0, 2.0]
VOLTAGE_STEPS = [-0.5, -0.2, 0.2, 0.5]

VARIABLES = {
    "IL1_INIT": CURRENT_STEPS,
    "IL3_INIT": CURRENT_STEPS,
    "IL4_INIT": CURRENT_STEPS,
    "VC1_INIT": VOLTAGE_STEPS,
    "VC2_INIT": VOLTAGE_STEPS,
    "VC3_INIT": VOLTAGE_STEPS,
}


def make_case(tag: str, state: dict) -> Path:
    text = SOURCE.read_text()
    if text.count(_PARAM_LINE_OLD) != 1:
        raise RuntimeError("A38 template's IL*_INIT .param line changed")
    if text.count(_VC_LINE_OLD) != 1:
        raise RuntimeError("A38 template's VCk_INIT .param line changed")
    new_il = (
        f".param IL1_INIT={state['IL1_INIT']:.12g} "
        f"IL2_INIT={state['IL2_INIT']:.12g} "
        f"IL3_INIT={state['IL3_INIT']:.12g} "
        f"IL4_INIT={state['IL4_INIT']:.12g}"
    )
    new_vc = (
        f".param VC1_INIT={state['VC1_INIT']:.12g} "
        f"VC2_INIT={state['VC2_INIT']:.12g} "
        f"VC3_INIT={state['VC3_INIT']:.12g}"
    )
    text = text.replace(_PARAM_LINE_OLD, new_il, 1)
    text = text.replace(_VC_LINE_OLD, new_vc, 1)
    path = WORK / f"{tag}.cir"
    path.write_text(text)
    return path


def run_case(path: Path) -> None:
    subprocess.run([str(RUNNER), "run", str(path)], cwd=PROJECT, check=True)


def measure_h2_admission(cir: Path) -> dict:
    """Identical to A39 Part 2's admission measurement: the inductor
    current I(XMOD:LIND2) and time at the rising edge of the H2 gate
    V(xmod:gh2)."""
    raw = RawRead(str(cir.with_suffix(".raw")))
    time = np.real(raw.get_trace("time").get_wave(0))
    gh2 = np.real(raw.get_trace("V(xmod:gh2)").get_wave(0))
    i2 = np.real(raw.get_trace("I(XMOD:LIND2)").get_wave(0))
    r2_on = rising_edge_idx(gh2)
    r2_off = falling_edge_idx(gh2)
    if r2_on is None:
        return {"h2_admission_missing": True}
    return {
        "h2_admission_missing": False,
        "t_h2_admission_ns": float(time[r2_on]) * 1e9,
        "i2_at_admission_a": float(i2[r2_on]),
        "i2_at_ton2_end_a": float(i2[r2_off]) if r2_off is not None else None,
    }


def run_and_measure(tag: str, state: dict) -> dict:
    cir = make_case(tag, state)
    run_case(cir)
    meas = measure_h2_admission(cir)
    row = {"tag": tag, "state": state, **meas}
    print(json.dumps(row), flush=True)
    return row


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)

    results: dict = {"baseline": None, "variables": {}}

    baseline_row = run_and_measure("baseline", dict(BASELINE))
    results["baseline"] = baseline_row
    (OUT / "a44_results.json").write_text(json.dumps(results, indent=2) + "\n")

    base_i2 = baseline_row["i2_at_admission_a"]
    base_t = baseline_row["t_h2_admission_ns"]

    for var, steps in VARIABLES.items():
        var_rows = []
        for step in steps:
            state = dict(BASELINE)
            state[var] = BASELINE[var] + step
            tag = f"{var}_{'+' if step >= 0 else ''}{step:g}"
            row = run_and_measure(tag, state)
            row["perturbation"] = step
            if not row["h2_admission_missing"]:
                row["delta_i2_a"] = row["i2_at_admission_a"] - base_i2
                row["delta_t_ns"] = row["t_h2_admission_ns"] - base_t
                row["sensitivity_i2_per_unit"] = row["delta_i2_a"] / step
                row["sensitivity_t_per_unit"] = row["delta_t_ns"] / step
            var_rows.append(row)
            # checkpoint after every run in case of interruption
            results["variables"][var] = var_rows
            (OUT / "a44_results.json").write_text(json.dumps(results, indent=2) + "\n")
        results["variables"][var] = var_rows

    (OUT / "a44_results.json").write_text(json.dumps(results, indent=2) + "\n")
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
