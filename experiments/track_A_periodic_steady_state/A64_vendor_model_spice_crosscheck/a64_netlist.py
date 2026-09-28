"""A64 - LTspice netlist builder: A59's four-phase SCB with EPC's EPC2067 vendor model.

Topology (node names are A52's / the Python descriptor's, so A59's 20-state
`z*` transcribes coordinate by coordinate, A52 `ic_mapping` discipline):

    V_SRC   src -> 0        48 V (post-ramp; A59's z* is at t0 = 115 T + d_rise/2)
    R_SRC   src -> src_r    source_resistance_ohm
    L_SRC   src_r -> vin    source_inductance_h, Rser=0 (explicit: LTspice adds 1 mOhm otherwise)
    divider vin-tap3-tap2-tap1-0: 4 x divider_capacitance_f, each || divider_leakage_ohm
    diodes  tap3-a1, tap2-a2, tap1-a3 at diode_off_resistance_ohm (A59 runs diodes OFF)
    SH1..4  vin-a1, a1-a2, a2-a3, a3-x4   (drain = first node, source = second)
    SL1..4  x1..x4 -> 0                   (drain = x_k, source = ground)
    C1..C3  a1-x1, a2-x2, a3-x3           flying_capacitances_f
    LIND1..4 x_k -> out                   phase_inductance_h, Rser = phase_inductor_resistance_ohm
    C_OUT, R_LOAD out -> 0                output_capacitance_f, Vout^2/P = 4 mOhm

Each high-side switch = 2 x EPC2067, each low-side = 3 x EPC2067 (P24
Table 3), vendor subcircuit `EPC2067 gatein drainin sourcein`. No separate
Coss capacitor: the vendor model carries its own charge-based capacitances.

Metering-only additions (no physics): a 0 V source in series with each
switch group (drain side), so the group's drain current can be integrated
against its Vds for the per-edge breakdown. The headline loss is still
source-side P_in - P_out (BOUNDARY Section 4).

Gate drive (PROJECT_DECISION, BOUNDARY Section 2): one floating 0/5 V
PULSE source per device, referenced to that device's own source node,
through R_drv. Command edges are 0.1 ns ramps that START at the commanded
window boundary (every command is therefore delayed by a uniform 0.05 ns at
its 50 % point; the 0.1 ns ramp has to sit somewhere, and starting at the
boundary keeps the t = 0 gate state exactly the ideal one).

Time: period-start time tau = t - t0, t0 = A51 BASE_PERIOD_INDEX * T +
d_rise/2 (A58 `period_start_s`), the instant A59's z* is taken. Phase p
(0-based) has its commanded on-edge at pT/4 (+kT) and its off-edge Ton_cmd
later; windows are centered on the edges (A58 `commanded_pwm_mode`), so

    high ON  [pT/4,                      pT/4 + Ton - (dr+df)/2)
    low  ON  [pT/4 + Ton + (df-dr)/2,    pT/4 + T - dr)            (mod T)

`schedule_selfcheck` verifies these intervals against A58's own
`commanded_pwm_mode` by sampling. Netlist time is tau - origin_s: origin 0
for a start from A59's z*, origin QUIET_S for a warm restart.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACK = HERE.parent
A59_DIR = TRACK / "A59_nonlinear_coss_epc2067"
MODEL_FILE = HERE / "vendor" / "EPC2067.lib"
#: subcircuit name -> git-ignored model file. EPC2067 = the vendor block as
#: distributed (the BOUNDARY's model, default). EPC2067X = the same block with
#: its three charge-defined capacitors written in x (fetch_epc2067_model.x_form):
#: LTspice 26.0.2 integrates `Q=f(v(a,b))` capacitors charge-conservingly only
#: as far as the Newton tolerance forces it (A64 RESULTS, model check), so
#: EPC2067X is run at the accepted points as a check (`xcheck` stage).
MODEL_FILES = {"EPC2067": MODEL_FILE, "EPC2067X": HERE / "vendor" / "EPC2067X.lib"}
DEFAULT_MODEL = "EPC2067"

A59_RECORDS = {
    "zvs": A59_DIR / "runs" / "zvs_r1.950_f0.650.json",
    "baseline": A59_DIR / "runs" / "baseline_r2.150_f1.150.json",
}
NHS, NLS = 2, 3
GATE_V = 5.0
EDGE_S = 0.1e-9
PERIOD_S = 200e-9
#: Sampling / restart instant inside the period (period-start time tau).
#: Every gate has then been static for >= ~15 ns (last edge: the phase-1
#: off-edge at Ton + df/2 <= ~20 ns; next: the phase-2 on-edge at
#: T/4 - dr/2 >= ~48.7 ns), so node voltages, inductor currents and gate
#: states are quiet and a DC-constrained restart from them is seamless.
#: PROJECT_DECISION (checked in RESULTS).
QUIET_S = 35e-9
STATE_NAMES = ("src", "src_r", "vin", "tap3", "tap2", "tap1", "a1", "a2", "a3",
               "x1", "x2", "x3", "x4", "out", "LPAR_IN", "L1", "L2", "L3", "L4", "I_VSTEP")
NODE_STATES = ("src_r", "vin", "tap3", "tap2", "tap1", "a1", "a2", "a3",
               "x1", "x2", "x3", "x4", "out")
INDUCTOR_STATES = {"LPAR_IN": "L_SRC", "L1": "LIND1", "L2": "LIND2", "L3": "LIND3", "L4": "LIND4"}
HIGH_BRANCHES = (("vin", "a1"), ("a1", "a2"), ("a2", "a3"), ("a3", "x4"))
LOW_BRANCHES = (("x1", "0"), ("x2", "0"), ("x3", "0"), ("x4", "0"))
DEVICE_LETTERS = "abc"


def load_a59(design: str) -> dict:
    record = json.loads(A59_RECORDS[design].read_text())
    boundary = record["full_boundary"]
    regulated = record["regulated"]
    return {
        "design": design,
        "source_record": str(A59_RECORDS[design].relative_to(TRACK)),
        "boundary": boundary,
        "ton_cmd_s": regulated["ton_cmd_s"],
        "dead_time_rise_s": record["dead_time_rise_s"],
        "dead_time_fall_s": record["dead_time_fall_s"],
        "z_star": dict(zip(STATE_NAMES, regulated["z_star"])),
        "a59_p_a_w": record["accounting"]["p_a_w"],
        "a59_p_b_w": record["accounting"]["p_b_w"]["fig8_25C"],
        "a59_other_resistive_w": record["accounting"]["energy_balance"]["other_resistive_w"],
        "a59_load_power_w": regulated["load_power_w"],
    }


def check_variable_names(a59: dict) -> None:
    """z* ordering must be A51's `variable_names` (imported through A59, read-only)."""
    if str(A59_DIR) not in sys.path:
        sys.path.insert(0, str(A59_DIR))
    import a59_nonlinear as N  # noqa: PLC0415

    b = a59["boundary"]
    boundary = N.build_nl_boundary(phase_inductance_h=b["phase_inductance_h"],
                                   dead_time_rise_s=a59["dead_time_rise_s"],
                                   dead_time_fall_s=a59["dead_time_fall_s"],
                                   ton_cmd_s=a59["ton_cmd_s"])
    names = tuple(N.M.variable_names(boundary))
    if names != STATE_NAMES:
        raise RuntimeError(f"variable ordering changed: {names}")


@dataclass
class Gate:
    name: str          # e.g. "H1A"
    side: str          # "high" / "low"
    phase: int         # 1..4
    drain: str
    source: str
    on_start_s: float  # commanded ON boundary, period-start time tau
    on_end_s: float
    on_at_zero: bool   # gate command is 5 V at netlist t = 0
    pulse: str = ""


def gate_windows(ton: float, dr: float, df: float, period: float = PERIOD_S) -> dict:
    """Commanded ON intervals in period-start time tau."""
    out = {}
    for p in range(4):
        base = p * period / 4
        out[("high", p + 1)] = (base, base + ton - 0.5 * (dr + df))
        out[("low", p + 1)] = (base + ton + 0.5 * (df - dr), base + period - dr)
    return out


def pulse_for(start: float, end: float, period: float) -> tuple[str, bool]:
    """PULSE string (netlist time) whose ramps START at the commanded boundaries.

    Returns (pulse, on_at_zero). If the ON interval contains netlist t = 0
    (mod T) the source starts at 5 V and the PULSE describes the OFF interval.
    """
    width = end - start
    if not (0 < width < period):
        raise ValueError("bad window")
    s = start % period
    if s > period - 1e-18:
        s = 0.0
    e = s + width
    if e <= period + 1e-18:
        # OFF at t = 0. For the phase-1 high gate of a z* start the ON command
        # begins exactly at t = 0: the gate is still 0 V there, its ramp starts at t = 0.
        return (f"PULSE(0 {GATE_V:g} {s:.15e} {EDGE_S:.3e} {EDGE_S:.3e} "
                f"{width - EDGE_S:.15e} {period:.15e})", False)
    off_start = e - period
    off_width = period - width
    return (f"PULSE({GATE_V:g} 0 {off_start:.15e} {EDGE_S:.3e} {EDGE_S:.3e} "
            f"{off_width - EDGE_S:.15e} {period:.15e})", True)


def schedule_selfcheck(a59: dict, ton: float, dr: float, df: float, samples: int = 4000) -> int:
    """Sample A58's commanded_pwm_mode at t0 + tau and compare with gate_windows.

    Returns the number of disagreeing samples (must be 0); samples within 1 fs
    of a boundary are skipped.
    """
    if str(A59_DIR) not in sys.path:
        sys.path.insert(0, str(A59_DIR))
    import a59_nonlinear as N  # noqa: PLC0415

    b = a59["boundary"]
    boundary = N.build_nl_boundary(phase_inductance_h=b["phase_inductance_h"],
                                   dead_time_rise_s=dr, dead_time_fall_s=df, ton_cmd_s=ton)
    t0 = N.S.period_start_s(boundary)
    period = boundary.period_s
    windows = gate_windows(ton, dr, df, period)
    bad = 0
    for i in range(samples):
        tau = (i + 0.37) * period / samples
        mode = N.S.commanded_pwm_mode(t0 + tau, boundary)
        for (side, phase), (start, end) in windows.items():
            local = (tau - start) % period
            width = end - start
            if min(abs(local), abs(local - width), abs(period - local)) < 1e-15:
                continue
            ours = local < width
            theirs = (mode.high_side_on if side == "high" else mode.low_side_on)[phase - 1]
            bad += ours != theirs
    return bad


@dataclass
class Case:
    r_drv_ohm: float
    temp_c: float

    @property
    def tag(self) -> str:
        return f"R{self.r_drv_ohm:.1f}_T{self.temp_c:.0f}"


@dataclass
class NetlistSpec:
    design: str
    case: Case
    ton_s: float
    dr_s: float
    df_s: float
    n_periods: int                # number of sample-to-sample periods simulated
    max_step_s: float
    ic: dict                      # state name -> value (A59 z* names)
    origin_s: float = 0.0         # tau of netlist t = 0 (0: A59 z*; QUIET_S: warm restart)
    reltol: float = 1e-4
    extra_options: str = ""
    save_all_gates: bool = False  # save every device's drive (symmetry check); default: device A only
    model: str = DEFAULT_MODEL    # subcircuit name, see MODEL_FILES


def vdiff(first: str, second: str) -> str:
    """LTspice rejects V(node,0) inside .meas expressions."""
    return f"V({first})" if second == "0" else f"V({first},{second})"


def sample_times(spec: NetlistSpec) -> list[float]:
    """Netlist times of the quiet samples: tau = QUIET_S + kT."""
    first = (QUIET_S - spec.origin_s) % PERIOD_S
    return [first + k * PERIOD_S for k in range(spec.n_periods + 1)]


def build(spec: NetlistSpec, a59: dict) -> tuple[str, dict]:
    b = a59["boundary"]
    T = PERIOD_S
    if abs(b["switching_frequency_hz"] * T - 1.0) > 1e-12:
        raise RuntimeError("period mismatch")
    rload = b["vout_target_v"] ** 2 / b["module_power_w"]
    windows = gate_windows(spec.ton_s, spec.dr_s, spec.df_s, T)
    gates = []
    for (side, phase), (start, end) in windows.items():
        count = NHS if side == "high" else NLS
        drain, source = (HIGH_BRANCHES if side == "high" else LOW_BRANCHES)[phase - 1]
        pulse, on0 = pulse_for(start - spec.origin_s, end - spec.origin_s, T)
        for k in range(count):
            gates.append(Gate(name=f"{side[0].upper()}{phase}{DEVICE_LETTERS[k].upper()}",
                              side=side, phase=phase, drain=drain, source=source,
                              on_start_s=start, on_end_s=end, on_at_zero=on0, pulse=pulse))
    samples = sample_times(spec)
    tstop = samples[-1]

    lines = [
        f"* A64 {spec.design} {spec.case.tag} Ton={spec.ton_s:.6e} dr={spec.dr_s:.4e} df={spec.df_s:.4e}",
        "* Generated by a64_netlist.py -- do not edit by hand.",
        f"* Vendor model {spec.model} (EPCGaNLibrary.lib, (C) EPC) included from a git-ignored file.",
        f"* netlist t = 0 is period-start time tau = {spec.origin_s!r} s "
        "(tau = 0 <-> absolute t0 = 115 T + d_rise/2, A58 period_start_s)",
        f".include {MODEL_FILES[spec.model].name}",
        f".temp {spec.case.temp_c:g}",
        f".param RDRV={spec.case.r_drv_ohm!r} RLOAD={rload!r}",
        "",
        "* ---- source path, divider (diodes OFF), A59 boundary values",
        f"V_SRC src 0 {b['vin_target_v']!r}",
        f"R_SRC src src_r {b['source_resistance_ohm']!r}",
        f"L_SRC src_r vin {b['source_inductance_h']!r} Rser=0",
    ]
    for first, second, tag in (("vin", "tap3", "4"), ("tap3", "tap2", "3"),
                               ("tap2", "tap1", "2"), ("tap1", "0", "1")):
        lines.append(f"C_DIV{tag} {first} {second} {b['divider_capacitance_f']!r}")
        lines.append(f"R_DIV{tag} {first} {second} {b['divider_leakage_ohm']!r}")
    for anode, cathode, tag in (("tap3", "a1", "3"), ("tap2", "a2", "2"), ("tap1", "a3", "1")):
        lines.append(f"R_PD{tag} {anode} {cathode} {b['diode_off_resistance_ohm']!r}")
    lines.append("")
    lines.append("* ---- ladder: flying caps, phase inductors, output")
    for k, (a, x) in enumerate((("a1", "x1"), ("a2", "x2"), ("a3", "x3")), start=1):
        lines.append(f"C{k} {a} {x} {b['flying_capacitances_f'][k - 1]!r}")
    for k in range(1, 5):
        lines.append(f"LIND{k} x{k} out {b['phase_inductance_h']!r} "
                     f"Rser={b['phase_inductor_resistance_ohm']!r}")
    lines.append(f"C_OUT out 0 {b['output_capacitance_f']!r}")
    lines.append("R_LOAD out 0 {RLOAD}")
    lines.append("")
    lines.append("* ---- switches: metering 0 V source (drain side) + parallel EPC2067 devices")
    lines.append("* each device: floating 0/5 V PULSE referenced to its own source, through RDRV")
    for side, branches in (("H", HIGH_BRANCHES), ("L", LOW_BRANCHES)):
        for p, (drain, _source) in enumerate(branches, start=1):
            lines.append(f"V_A{side}{p} {drain} d{side.lower()}{p} 0")
    for g in gates:
        n = g.name.lower()
        lines.append(f"X{g.name} g{n} d{g.side[0]}{g.phase} {g.source} {spec.model}")
        lines.append(f"R_G{g.name} c{n} g{n} {{RDRV}}")
        lines.append(f"V_G{g.name} c{n} {g.source} {g.pulse}")
    lines.append("")

    t1, t2 = samples[-2], samples[-1]
    meas = [
        "* ---- LTspice's own integrals over the last sample period (cross-check of the Python ones)",
        f".meas tran EIN INTEG -V(src)*I(V_SRC) FROM {t1:.12e} TO {t2:.12e}",
        f".meas tran EOUT INTEG V(out)*V(out)/{rload!r} FROM {t1:.12e} TO {t2:.12e}",
    ]
    saves = ["V(src)", "I(V_SRC)"] + [f"V({s})" for s in NODE_STATES] + \
        [f"I({v})" for v in INDUCTOR_STATES.values()]
    for side in ("H", "L"):
        for p in range(1, 5):
            saves.append(f"I(V_A{side}{p})")
    for g in gates:
        if spec.save_all_gates or g.name.endswith("A"):
            n = g.name.lower()
            saves += [f"V(c{n})", f"I(V_G{g.name})", f"V(x{n}:gate)", f"V(x{n}:source)",
                      f"V(x{n}:drain)"]

    ic_nodes = " ".join(f"V({name})={spec.ic[name]!r}" for name in NODE_STATES)
    ic_currents = " ".join(f"I({INDUCTOR_STATES[name]})={spec.ic[name]!r}" for name in INDUCTOR_STATES)
    text = "\n".join(lines + meas) + f"""

.options plotwinsize=0 numdgt=15 reltol={spec.reltol!r} {spec.extra_options}
.save {' '.join(saves)}
.ic {ic_nodes}
.ic {ic_currents}
.tran 0 {tstop:.12e} 0 {spec.max_step_s:.6e}
.end
"""
    meta = {
        "design": spec.design,
        "case": {"r_drv_ohm": spec.case.r_drv_ohm, "temp_c": spec.case.temp_c},
        "ton_cmd_s": spec.ton_s,
        "dead_time_rise_s": spec.dr_s,
        "dead_time_fall_s": spec.df_s,
        "n_periods": spec.n_periods,
        "origin_s": spec.origin_s,
        "sample_times_s": samples,
        "max_step_s": spec.max_step_s,
        "reltol": spec.reltol,
        "extra_options": spec.extra_options,
        "rload_ohm": rload,
        "model": spec.model,
        "gates": [{"name": g.name, "side": g.side, "phase": g.phase, "drain": g.drain,
                   "source": g.source, "on_start_tau_s": g.on_start_s, "on_end_tau_s": g.on_end_s,
                   "on_at_netlist_zero": g.on_at_zero, "pulse": g.pulse} for g in gates],
        "ic": {k: spec.ic[k] for k in NODE_STATES + tuple(INDUCTOR_STATES)},
    }
    return text, meta


__all__ = ["load_a59", "check_variable_names", "build", "gate_windows", "pulse_for",
           "schedule_selfcheck", "Case", "NetlistSpec", "PERIOD_S", "STATE_NAMES",
           "NODE_STATES", "INDUCTOR_STATES", "HIGH_BRANCHES", "LOW_BRANCHES", "MODEL_FILE",
           "MODEL_FILES", "DEFAULT_MODEL",
           "QUIET_S", "sample_times", "NHS", "NLS", "GATE_V", "EDGE_S", "vdiff"]
