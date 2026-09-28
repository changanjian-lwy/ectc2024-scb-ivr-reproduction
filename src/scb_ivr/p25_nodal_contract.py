"""D03: P25 Fig1 three-phase topology, finite constant capacitors, ideal gates.

An instantaneous constrained derivative, NOT a transient/event solver.
No component defaults, no fixed output voltage, no automatic state projection.
OFF reverse channels are excluded: callers must stop before their admission.
See symbolic_derivations/02_P25_native/D03_SHARED_NODE_EQUATIONS.md.
"""
from dataclasses import dataclass
from math import isfinite

import numpy as np

from .p25_native_events import NativeBoundary
from .p25_cycle_modes import cycle_mode


NODES = ("vin", "a1", "a2", "x1", "x2", "x3", "out")
INTERNAL = NODES[1:]
SWITCHES = ("SH1", "SH2", "SH3", "SL1", "SL2", "SL3")
CAPACITORS = (*SWITCHES, "Cs1", "Cs2", "Co")
# Positive branch direction, matching Vds and the Fig1 series capacitor signs.
ENDS = (("vin", "a1"), ("a1", "a2"), ("a2", "x3"),
        ("x1", None), ("x2", None), ("x3", None),
        ("a1", "x1"), ("a2", "x2"), ("out", None))


def incidence():
    matrix = np.zeros((7, 9))
    for k, (positive, negative) in enumerate(ENDS):
        matrix[NODES.index(positive), k] = 1
        if negative is not None:
            matrix[NODES.index(negative), k] = -1
    return matrix


def inductor_incidence():
    matrix = np.zeros((7, 3))
    for phase in range(3):
        matrix[3 + phase, phase] = 1
        matrix[6, phase] = -1
    return matrix


@dataclass(frozen=True)
class Components:
    coss_f: tuple[float, ...]  # six effective bank capacitances, H1..H3,L1..L3
    snubber_f: tuple[float, ...]  # separate, same order; explicit zero allowed
    series_f: tuple[float, ...]  # Cs1,Cs2
    output_f: float  # one shared output capacitor, not one copy per module
    inductance_h: tuple[float, ...]
    winding_ohm: tuple[float, ...]
    source: str

    def __post_init__(self):
        for name, count in (("coss_f", 6), ("snubber_f", 6), ("series_f", 2),
                            ("inductance_h", 3), ("winding_ohm", 3)):
            values = getattr(self, name)
            if not isinstance(values, tuple) or len(values) != count:
                raise ValueError(f"{name}: explicit immutable {count}-entry tuple required")
            if not all(isfinite(v) and v >= 0 for v in values):
                raise ValueError(f"{name}: finite nonnegative values required")
        if any(v <= 0 for v in (*self.series_f, *self.inductance_h)):
            raise ValueError("positive series capacitance and inductance required")
        if any(a + b <= 0 for a, b in zip(self.coss_f, self.snubber_f)):
            raise ValueError("every switch bank must retain positive total capacitance")
        if not isfinite(self.output_f) or self.output_f <= 0 or not self.source.strip():
            raise ValueError("positive output capacitance and provenance required")

    def capacitances(self):
        return np.array([a+b for a, b in zip(self.coss_f, self.snubber_f)]
                        + list(self.series_f) + [self.output_f])


@dataclass(frozen=True)
class Rates:
    voltage_rate_v_s: np.ndarray  # a1,a2,x1,x2,x3,out
    current_rate_a_s: np.ndarray  # iL1,iL2,iL3
    capacitor_current_a: np.ndarray  # CAPACITORS, directed ENDS
    channel_current_a: np.ndarray  # SWITCHES, directed ENDS
    input_current_a: float  # includes displacement current at vin
    kcl_residual_a: np.ndarray  # INTERNAL
    constraint_voltage_error_v: np.ndarray  # active gate constraints
    constraint_rate_error_v_s: np.ndarray
    energy_rate_w: float
    supplied_minus_dissipated_w: float


def _vector(value, size, name):
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name}: finite {size}-entry vector required")
    return result


def instantaneous_rates(boundary: NativeBoundary, parts: Components, mode: str, *,
                        voltage_v, current_a, vin_v: float, dvin_v_s: float,
                        load_current_a: float, other_modules_current_a: float,
                        constraint_tolerance_v: float, reverse_path_regime: str) -> Rates:
    """Solve KCL plus differentiated ideal gate constraints at one instant.

    The supplied state is not reset/projected. Mode-current signs and OFF
    reverse-conduction guards are not certified by this algebraic check.
    Both output currents are explicit ports: other modules inject into Co.
    """
    if not isinstance(boundary, NativeBoundary):
        raise ValueError("P25 native boundary required")
    if boundary.output_boundary != "dynamic_Co_current_ports":
        raise ValueError("requires declared dynamic_Co_current_ports output boundary")
    if reverse_path_regime != "off_reverse_channels_excluded_until_admission":
        raise ValueError("reverse-conduction model is not implemented in D03")
    gates = cycle_mode(mode).gates
    if not all(isfinite(x) for x in (vin_v, dvin_v_s, load_current_a,
                                    other_modules_current_a, constraint_tolerance_v)):
        raise ValueError("finite port inputs/tolerance required")
    if constraint_tolerance_v < 0:
        raise ValueError("constraint tolerance cannot be negative")
    if boundary.nM == 1 and other_modules_current_a != 0:
        raise ValueError("single-module system cannot inject other-module current")
    v = _vector(voltage_v, 6, "voltage")
    i = _vector(current_a, 3, "inductor current")
    af = incidence()
    a = af[1:, :]
    b = inductor_incidence()[1:, :]
    cvalues = parts.capacitances()
    cfull = (af * cvalues) @ af.T
    c = cfull[1:, 1:]
    active = np.array((*gates.high, *gates.low))
    s = a[:, :6][:, active]
    sin = af[0, :6][active]
    constraint = s.T @ v + sin * vin_v
    if np.max(np.abs(constraint)) > constraint_tolerance_v:
        raise ValueError("incompatible capacitor state at ideal gate closure; no projection allowed")
    external = np.zeros(6)
    external[-1] = other_modules_current_a - load_current_a
    rhs = -cfull[1:, 0]*dvin_v_s - b@i + external
    kkt = np.block([[c, s], [s.T, np.zeros((s.shape[1], s.shape[1]))]])
    solution = np.linalg.solve(kkt, np.r_[rhs, -sin*dvin_v_s])
    dv = solution[:6]
    channel = np.zeros(6)
    channel[active] = solution[6:]
    di = (b.T@v - np.array(parts.winding_ohm)*i) / np.array(parts.inductance_h)
    cap_current = cvalues * (af.T @ np.r_[dvin_v_s, dv])
    all_branch_current = cap_current.copy()
    all_branch_current[:6] += channel
    kcl = a @ all_branch_current + b@i - external
    iin = float(af[0] @ all_branch_current)
    cap_voltage = af.T @ np.r_[vin_v, v]
    energy_rate = float(cap_voltage @ cap_current + (np.array(parts.inductance_h)*i) @ di)
    power_balance = float(vin_v*iin + v[-1]*(other_modules_current_a-load_current_a)
                          - np.array(parts.winding_ohm) @ (i*i))
    return Rates(dv, di, cap_current, channel, iin, kcl, constraint,
                 s.T@dv + sin*dvin_v_s, energy_rate, power_balance)


def reduced_commutation_coefficients(parts: Components, mode: str) -> dict[str, float]:
    """Exact Schur reduction ONLY for fixed Vin and ideal nonworking low sides.

    Eliminates derivatives, not stored states. No equal-C assumption.
    dv_x/dt = -i_active/Ceff; dVds_target/dt = target_gain*dv_x/dt.
    M2 target=SL1; M5 target=SH2. Not a ZVS feasibility certificate.
    """
    h1, h2, h3, l1, l2, _l3, c1, c2, _co = parts.capacitances()
    if mode == "M2":
        k = h1 + h2*(h3+c2)/(h2+h3+c2)
        a1_over_x = c1/(c1+k)
        return {"ceff_f": l1+c1*k/(c1+k), "a1_over_x": a1_over_x,
                "a2_over_x": h2/(h2+h3+c2)*a1_over_x, "target_gain": 1.0}
    if mode == "M5":
        k = h3 + h2*(h1+c1)/(h2+h1+c1)
        a2_over_x = c2/(c2+k)
        a1_over_x = h2/(h1+h2+c1)*a2_over_x
        return {"ceff_f": l2+c2*k/(c2+k), "a1_over_x": a1_over_x,
                "a2_over_x": a2_over_x, "target_gain": a1_over_x-a2_over_x}
    raise ValueError("Schur reduction supports only M2 or M5")


def assert_continuous_energy_state(*, voltage_before_v, voltage_after_v,
                                   vin_before_v, vin_after_v,
                                   current_before_a, current_after_a,
                                   capacitor_tolerance_v, current_tolerance_a) -> None:
    """No-impulse event boundary: compare ALL capacitor voltages and L currents.

    This is necessary, not sufficient, for a valid topology transition.
    New gate constraints must be checked separately. No mixed-unit norm.
    """
    if not all(isfinite(x) for x in (vin_before_v, vin_after_v,
                                     capacitor_tolerance_v, current_tolerance_a)):
        raise ValueError("finite input/tolerances required")
    if capacitor_tolerance_v < 0 or current_tolerance_a < 0:
        raise ValueError("nonnegative separate voltage/current tolerances required")
    before = np.r_[vin_before_v, _vector(voltage_before_v, 6, "before voltage")]
    after = np.r_[vin_after_v, _vector(voltage_after_v, 6, "after voltage")]
    cap_delta = incidence().T @ (after-before)
    if np.any(np.abs(cap_delta) > capacitor_tolerance_v):
        name = CAPACITORS[int(np.argmax(np.abs(cap_delta)))]
        raise ValueError(f"capacitor voltage discontinuity: {name}; impulse model required")
    di = _vector(current_after_a, 3, "after current")-_vector(current_before_a, 3, "before current")
    if np.any(np.abs(di) > current_tolerance_a):
        phase = int(np.argmax(np.abs(di)))+1
        raise ValueError(f"inductor current discontinuity: L{phase}; no reset allowed")
