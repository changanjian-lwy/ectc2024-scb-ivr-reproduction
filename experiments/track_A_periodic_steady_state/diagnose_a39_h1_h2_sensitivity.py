"""A39 diagnostic driver: is H1's peak-current-vs-IL1_INIT sensitivity really
linear over a wide range, or does it saturate like H2's does? And what
physical quantity actually differs between TON1 and TON2 that explains H2's
near-zero (~0.016 A/A) sensitivity vs H1's implied ~0.92 A/A?

This is PURELY DIAGNOSTIC (A39 BOUNDARY.md): nothing is solved, no locked
parameter is retuned, no swept value is promoted to a default. Two things are
produced:

1. A wide IL1_INIT sweep (-20 A to +40 A, 13 points), with IL2_INIT/IL3_INIT
   frozen at A38's solved/seed values and IL4_INIT/VCk_INIT frozen at A38's
   values, reading iL1 at H1's own fixed-TON1 falling edge for each point.
2. One representative run at A38's exact best_candidate operating point
   (which already contains A36's solved IL1_INIT=5.2947 A for H1 alongside
   A38's IL2_INIT=21.205095337 A for H2 in the SAME four-phase run), from
   which TON1 and TON2 are directly compared in the .raw waveforms: inductor
   current di/dt at window start/end, flying-capacitor voltage (VC1 vs VC2)
   trajectory, switch IR drop (Ron*I) at the higher currents involved, and
   the actual inductor current at each phase's own turn-on admission instant.

Netlist template: A38's own final .cir (READ ONLY -- never modified,
overwritten, or deleted; A39 writes only its own new files under
A39_solver_work/ and A39_h1_h2_peak_sensitivity_diagnostic/).
"""

from __future__ import annotations

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

WORK = TRACK / "A39_solver_work"
OUT = TRACK / "A39_h1_h2_peak_sensitivity_diagnostic"
RUNNER = PROJECT / "tools" / "ltspice_runner.sh"

TARGET_PEAK = 125.0

# Frozen state for the Part-1 sweep, read from A38's own best_candidate.json
# (not retyped): IL2_INIT/IL3_INIT at A38's solved/seed values, IL4_INIT and
# all three VCk_INIT at A38's frozen values. Only IL1_INIT is swept.
IL2_INIT_FIXED = A38_BEST["il2_init_a"]
IL3_INIT_FIXED = A38_BEST["il3_init_a"]
IL4_INIT_FIXED = A38_BEST["frozen"]["IL4_INIT"]
VC1_INIT_FIXED = A38_BEST["frozen"]["VC1_INIT"]
VC2_INIT_FIXED = A38_BEST["frozen"]["VC2_INIT"]
VC3_INIT_FIXED = A38_BEST["frozen"]["VC3_INIT"]
IL1_INIT_A36_SOLVED = A38_BEST["frozen"]["IL1_INIT"]  # 5.2947, A36's solved value

_PARAM_LINE_OLD = (
    ".param IL1_INIT=5.2947 IL2_INIT=21.205095337 "
    "IL3_INIT=56.3205656631 IL4_INIT=84.1447433786"
)
_VC_LINE_OLD = (
    ".param VC1_INIT=36.000066454 VC2_INIT=23.9999142326 "
    "VC3_INIT=12.0006048777"
)


def make_case(index: int, il1: float, il2: float, il3: float, il4: float,
              vc1: float, vc2: float, vc3: float) -> Path:
    text = SOURCE.read_text()
    if text.count(_PARAM_LINE_OLD) != 1:
        raise RuntimeError("A38 template's IL*_INIT .param line changed")
    if text.count(_VC_LINE_OLD) != 1:
        raise RuntimeError("A38 template's VCk_INIT .param line changed")
    new_il = (
        f".param IL1_INIT={il1:.12g} IL2_INIT={il2:.12g} "
        f"IL3_INIT={il3:.12g} IL4_INIT={il4:.12g}"
    )
    new_vc = f".param VC1_INIT={vc1:.12g} VC2_INIT={vc2:.12g} VC3_INIT={vc3:.12g}"
    text = text.replace(_PARAM_LINE_OLD, new_il, 1)
    text = text.replace(_VC_LINE_OLD, new_vc, 1)
    path = WORK / f"iter_{index:02d}.cir"
    path.write_text(text)
    return path


def run_case(path: Path) -> None:
    subprocess.run([str(RUNNER), "run", str(path)], cwd=PROJECT, check=True)


def falling_edge_idx(gate: np.ndarray, level: float = 2.5) -> int | None:
    idx = np.where((gate[:-1] >= level) & (gate[1:] < level))[0] + 1
    return int(idx[0]) if len(idx) else None


def rising_edge_idx(gate: np.ndarray, level: float = 2.5) -> int | None:
    idx = np.where((gate[:-1] < level) & (gate[1:] >= level))[0] + 1
    return int(idx[0]) if len(idx) else None


# ---------------------------------------------------------------------------
# Part 1: wide IL1_INIT sweep
# ---------------------------------------------------------------------------

def part1_sweep() -> list[dict]:
    il1_values = [-20.0, -15.0, -10.0, -5.0, 0.0, 5.2947, 10.0, 15.0, 20.0,
                  25.0, 30.0, 35.0, 40.0]
    rows: list[dict] = []
    for i, il1 in enumerate(il1_values):
        cir = make_case(
            i, il1, IL2_INIT_FIXED, IL3_INIT_FIXED, IL4_INIT_FIXED,
            VC1_INIT_FIXED, VC2_INIT_FIXED, VC3_INIT_FIXED,
        )
        run_case(cir)
        raw = RawRead(str(cir.with_suffix(".raw")))
        time = np.real(raw.get_trace("time").get_wave(0))
        gh1 = np.real(raw.get_trace("V(xmod:gh1)").get_wave(0))
        gh2 = np.real(raw.get_trace("V(xmod:gh2)").get_wave(0))
        i1 = np.real(raw.get_trace("I(XMOD:LIND1)").get_wave(0))

        f1 = falling_edge_idx(gh1)
        if f1 is None:
            raise RuntimeError(f"H1 fixed-TON1 falling edge missing at IL1_INIT={il1}")
        t_h1_off = float(time[f1])
        peak_h1 = float(i1[f1])

        # Diagnostic-only: does H2 still admit at all at this extreme IL1_INIT?
        f2 = falling_edge_idx(gh2)
        h2_admission_missing = f2 is None

        row = {
            "iteration": i,
            "il1_init_a": il1,
            "t_h1_off_ns": t_h1_off * 1e9,
            "i1_at_h1_off_a": peak_h1,
            "peak_error_h1_a": peak_h1 - TARGET_PEAK,
            "h2_admission_missing_at_this_il1": h2_admission_missing,
        }
        rows.append(row)
        print(json.dumps(row), flush=True)

    # local slope between consecutive points
    for k in range(1, len(rows)):
        d_i1 = rows[k]["il1_init_a"] - rows[k - 1]["il1_init_a"]
        d_peak = rows[k]["i1_at_h1_off_a"] - rows[k - 1]["i1_at_h1_off_a"]
        rows[k]["local_slope_a_per_a"] = d_peak / d_i1 if d_i1 else None
    rows[0]["local_slope_a_per_a"] = None

    (OUT / "part1_il1_sweep.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


# ---------------------------------------------------------------------------
# Part 2: time-resolved TON1 vs TON2 comparison at A38's exact solved point
# ---------------------------------------------------------------------------

def part2_waveform_comparison() -> dict:
    il1 = A38_BEST["frozen"]["IL1_INIT"]
    il2 = A38_BEST["il2_init_a"]
    il3 = A38_BEST["il3_init_a"]
    il4 = A38_BEST["frozen"]["IL4_INIT"]
    vc1 = A38_BEST["frozen"]["VC1_INIT"]
    vc2 = A38_BEST["frozen"]["VC2_INIT"]
    vc3 = A38_BEST["frozen"]["VC3_INIT"]

    cir = make_case(100, il1, il2, il3, il4, vc1, vc2, vc3)
    run_case(cir)
    raw = RawRead(str(cir.with_suffix(".raw")))
    time = np.real(raw.get_trace("time").get_wave(0))
    gh1 = np.real(raw.get_trace("V(xmod:gh1)").get_wave(0))
    gh2 = np.real(raw.get_trace("V(xmod:gh2)").get_wave(0))
    i1 = np.real(raw.get_trace("I(XMOD:LIND1)").get_wave(0))
    i2 = np.real(raw.get_trace("I(XMOD:LIND2)").get_wave(0))
    a1 = np.real(raw.get_trace("V(xmod:a1)").get_wave(0))
    a2 = np.real(raw.get_trace("V(xmod:a2)").get_wave(0))
    x1 = np.real(raw.get_trace("V(xmod:x1)").get_wave(0))
    x2 = np.real(raw.get_trace("V(xmod:x2)").get_wave(0))
    # LTspice's .raw only stores single-ended node traces (confirmed by
    # inspecting the actual trace list; the .save file's differential
    # V(a,b) syntax does not create its own stored trace), so VC1/VC2 (the
    # same quantities the netlist's own .meas VC1_I/VC2_I statements read)
    # are reconstructed here as the single-ended difference.
    vc1_t = a1 - x1  # V(a1,x1) = VC1
    vc2_t = a2 - x2  # V(a2,x2) = VC2
    vds_h2 = a1 - a2

    r1_on = rising_edge_idx(gh1, level=2.5)  # H1 admits unconditionally at t~0
    r1_off = falling_edge_idx(gh1)
    r2_on = rising_edge_idx(gh2)
    r2_off = falling_edge_idx(gh2)
    if r1_on is None or r1_off is None:
        raise RuntimeError("TON1 window not found in Part 2 run")
    if r2_on is None or r2_off is None:
        raise RuntimeError("TON2 window not found in Part 2 run")

    def window_slopes(t, y, i_start, i_end, n_edge=5):
        # di/dt near the start and near the end of the window, using a short
        # local finite-difference span (n_edge samples) at each edge, plus
        # the overall window-average slope for reference.
        i_start_end = min(i_start + n_edge, i_end)
        i_end_start = max(i_end - n_edge, i_start)
        slope_start = (y[i_start_end] - y[i_start]) / (t[i_start_end] - t[i_start])
        slope_end = (y[i_end] - y[i_end_start]) / (t[i_end] - t[i_end_start])
        slope_avg = (y[i_end] - y[i_start]) / (t[i_end] - t[i_start])
        return float(slope_start), float(slope_end), float(slope_avg)

    ton1_slope_start, ton1_slope_end, ton1_slope_avg = window_slopes(time, i1, r1_on, r1_off)
    ton2_slope_start, ton2_slope_end, ton2_slope_avg = window_slopes(time, i2, r2_on, r2_off)

    # Flying-capacitor voltage sag/rise across each phase's own TON window.
    vc1_at_ton1_start = float(vc1_t[r1_on])
    vc1_at_ton1_end = float(vc1_t[r1_off])
    vc2_at_ton2_start = float(vc2_t[r2_on])
    vc2_at_ton2_end = float(vc2_t[r2_off])

    # Switch IR drop (Ron*I) at peak current in each window (RHS = 7 mOhm,
    # EXTERNAL_DEVICE_DATA from GS61008T_typical_params.lib, read not retyped).
    rhs_ohm = 7e-3
    ir_drop_h1_at_peak_v = rhs_ohm * float(i1[r1_off])
    ir_drop_h2_at_peak_v = rhs_ohm * float(i2[r2_off])

    # Admission current: the inductor current AT the moment each phase's own
    # high side turns on. For H1 this is essentially IL1_INIT itself (H1
    # turns on unconditionally at the machine's cycle start, t~0, no prior
    # event). For H2 this is set by the negative-current-cutoff + Coss-
    # commutation admission chain (P1_M3->P1_M4->P1_M5->P2_M1 in the .machine
    # table), NOT by IL2_INIT directly.
    admission_current_h1_a = float(i1[r1_on])
    admission_current_h2_a = float(i2[r2_on])

    # Also record where I(LIND2) actually crosses 0 and -INEG before
    # admission, to show the negative-current-cutoff chain is real and
    # temporally distinct from anything analogous for phase 1.
    ineg = 0.09 * 125.0
    zero_cross_idx = np.where((i2[:-1] > 0) & (i2[1:] <= 0) & (time[1:] < time[r2_on]))[0]
    ineg_cross_idx = np.where((i2[:-1] > -ineg) & (i2[1:] <= -ineg) & (time[1:] < time[r2_on]))[0]
    t_i2_zero_ns = float(time[zero_cross_idx[-1] + 1]) * 1e9 if len(zero_cross_idx) else None
    t_i2_ineg_ns = float(time[ineg_cross_idx[-1] + 1]) * 1e9 if len(ineg_cross_idx) else None

    result = {
        "il1_init_a": il1,
        "il2_init_a": il2,
        "ton1_window_ns": [float(time[r1_on]) * 1e9, float(time[r1_off]) * 1e9],
        "ton2_window_ns": [float(time[r2_on]) * 1e9, float(time[r2_off]) * 1e9],
        "i1_at_ton1_start_a": admission_current_h1_a,
        "i1_at_ton1_end_a": float(i1[r1_off]),
        "i2_at_ton2_start_a": admission_current_h2_a,
        "i2_at_ton2_end_a": float(i2[r2_off]),
        "ton1_didt_start_a_per_ns": ton1_slope_start / 1e9,
        "ton1_didt_end_a_per_ns": ton1_slope_end / 1e9,
        "ton1_didt_avg_a_per_ns": ton1_slope_avg / 1e9,
        "ton2_didt_start_a_per_ns": ton2_slope_start / 1e9,
        "ton2_didt_end_a_per_ns": ton2_slope_end / 1e9,
        "ton2_didt_avg_a_per_ns": ton2_slope_avg / 1e9,
        "vc1_at_ton1_start_v": vc1_at_ton1_start,
        "vc1_at_ton1_end_v": vc1_at_ton1_end,
        "vc1_delta_v": vc1_at_ton1_end - vc1_at_ton1_start,
        "vc2_at_ton2_start_v": vc2_at_ton2_start,
        "vc2_at_ton2_end_v": vc2_at_ton2_end,
        "vc2_delta_v": vc2_at_ton2_end - vc2_at_ton2_start,
        "rhs_ohm": rhs_ohm,
        "ir_drop_h1_at_peak_v": ir_drop_h1_at_peak_v,
        "ir_drop_h2_at_peak_v": ir_drop_h2_at_peak_v,
        "ineg_a": ineg,
        "t_i2_zero_cross_ns": t_i2_zero_ns,
        "t_i2_ineg_cross_ns": t_i2_ineg_ns,
        "t_h2_admission_ns": float(time[r2_on]) * 1e9,
        "pre_admission_delay_zero_to_admit_ns": (
            None if t_i2_zero_ns is None else float(time[r2_on]) * 1e9 - t_i2_zero_ns
        ),
    }
    (OUT / "part2_waveform_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PART2 " + json.dumps(result), flush=True)
    return result


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    sweep_rows = part1_sweep()
    wf = part2_waveform_comparison()
    print("DONE", flush=True)
    print(json.dumps({"sweep_points": len(sweep_rows)}, indent=2))


if __name__ == "__main__":
    main()
