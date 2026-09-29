"""D05: local complementarity for explicit ideal/constant-drop reverse models.

Mathematical surrogates, NOT measured GaN models. Enumerates boundary-active
OFF channels at one instant. Singular active sets remain unresolved; never
use a pseudoinverse to silently assign a unique branch-current distribution.
"""
from dataclasses import dataclass
from itertools import combinations
from math import isfinite

import numpy as np

from .p25_event_guards import Snapshot
from .p25_cycle_modes import cycle_mode, current_signs
from .p25_nodal_contract import Components, SWITCHES, incidence, inductor_incidence


@dataclass(frozen=True)
class ReverseModel:
    kind: str
    drop_v: tuple[float, ...]  # H1..H3,L1..L3, nonnegative constants
    declaration: str  # explicit project assumption or cited model source

    def __post_init__(self):
        if self.kind not in {"ideal_zero_drop", "constant_drop_surrogate"}:
            raise ValueError("D05 is not a real-GaN constitutive model")
        if not isinstance(self.drop_v, tuple) or len(self.drop_v) != 6:
            raise ValueError("six explicit reverse drops required")
        if not all(isfinite(x) and x >= 0 for x in self.drop_v):
            raise ValueError("finite nonnegative drops required")
        if self.kind == "ideal_zero_drop" and any(self.drop_v):
            raise ValueError("ideal zero-drop model requires declared zeros")
        if not self.declaration.strip():
            raise ValueError("model assumption must be declared")


@dataclass(frozen=True)
class Tolerances:
    voltage_v: float
    current_a: float
    voltage_rate_v_s: float

    def __post_init__(self):
        if not all(isfinite(x) and x >= 0 for x in
                   (self.voltage_v, self.current_a, self.voltage_rate_v_s)):
            raise ValueError("explicit separate finite nonnegative V/A/(V/s) tolerances required")


@dataclass(frozen=True)
class LocalCandidate:
    reverse_active: tuple[str, ...]
    dv_v_s: np.ndarray
    di_a_s: np.ndarray
    gate_current_a: np.ndarray  # drain->source; unrestricted sign when ON
    reverse_current_a: np.ndarray  # positive source->drain; zero for ON gates
    gap_v: np.ndarray  # Vds + drop; relevant only to OFF channels
    gap_rate_v_s: np.ndarray
    kcl_residual_a: np.ndarray
    input_current_a: float
    reverse_loss_w: float
    energy_rate_w: float
    net_power_w: float


@dataclass(frozen=True)
class LocalResolution:
    status: str
    candidates: tuple[LocalCandidate, ...]
    singular_active_sets: tuple[tuple[str, ...], ...]
    rejected_active_sets: tuple[tuple[str, ...], ...]


def paper_mode_violations(state: Snapshot, mode: str, *, tolerance_a: float) -> tuple[str, ...]:
    """Closed current-sign domains, not event timing or a full feasibility test.

    Rising phase entry current is not forcibly zeroed. Equality is a
    boundary requiring directional event checks, not proof of strict interior.
    """
    if not isfinite(tolerance_a) or tolerance_a < 0:
        raise ValueError("explicit finite nonnegative current tolerance required")
    # Preserve the two original optional reverse-submode aliases. Additional
    # prime intervals are not invented by the main-mode cyclic extension.
    main = {"M2_PRIME_OPTIONAL": "M2", "M5_PRIME_OPTIONAL": "M5"}.get(mode, mode)
    spec = cycle_mode(main)
    failures = []
    if state.gates != spec.gates:
        failures.append("GATE_PATTERN")
    signs = current_signs(main)
    for k, (sign, current) in enumerate(zip(signs, state.current_a), 1):
        if sign and sign*current < -tolerance_a:
            failures.append(f"iL{k}_SIGN")
    return tuple(failures)


def resolve_local_reverse(state: Snapshot, parts: Components, model: ReverseModel, *,
                          dvin_v_s: float, load_current_a: float,
                          other_modules_current_a: float, tolerances: Tolerances) -> LocalResolution:
    """Check vds+drop>=0, r>=0, (vds+drop)*r=0 on OFF channels.

    At a zero gap also enforce tangent complementarity: gdot>=0, r>=0,
    gdot*r=0. ON channels remain ideal bidirectional switches, not diodes.
    Finite tolerances only bound numerical checks, not physical thresholds.
    No current/voltage is projected or reset; no time integration is done.
    """
    if not isinstance(model, ReverseModel) or not isinstance(tolerances, Tolerances):
        raise ValueError("explicit reverse model and tolerances required")
    if state.boundary.output_boundary != "dynamic_Co_current_ports":
        raise ValueError("D03 dynamic output boundary required")
    if not all(isfinite(x) for x in (dvin_v_s, load_current_a, other_modules_current_a)):
        raise ValueError("finite explicit ports required")
    if state.boundary.nM == 1 and other_modules_current_a != 0:
        raise ValueError("other-module current in a single-module system")
    af = incidence()
    a = af[1:]
    b = inductor_incidence()[1:]
    v = np.array(state.voltage_v)
    i = np.array(state.current_a)
    branch_voltage = af.T @ np.r_[state.vin_v, v]
    gates = np.array((*state.gates.high, *state.gates.low))
    drops = np.array(model.drop_v)
    gaps = branch_voltage[:6]+drops
    for k, on in enumerate(gates):
        if on and abs(branch_voltage[k]) > tolerances.voltage_v:
            raise ValueError(f"{SWITCHES[k]} ON voltage inconsistent; no projection")
        if not on and gaps[k] < -tolerances.voltage_v:
            raise ValueError(f"{SWITCHES[k]} OFF reverse gap already violated; locate earlier boundary")
    boundary_indices = [k for k in range(6) if not gates[k] and abs(gaps[k]) <= tolerances.voltage_v]
    gate_indices = list(np.flatnonzero(gates))
    cvals = parts.capacitances()
    cfull = (af*cvals)@af.T
    c = cfull[1:, 1:]
    external = np.zeros(6)
    external[-1] = other_modules_current_a-load_current_a
    rhs = -cfull[1:, 0]*dvin_v_s-b@i+external
    di = (b.T@v-np.array(parts.winding_ohm)*i)/np.array(parts.inductance_h)
    accepted, singular, rejected = [], [], []
    for count in range(len(boundary_indices)+1):
        for reverse in combinations(boundary_indices, count):
            names = tuple(SWITCHES[k] for k in reverse)
            indices = gate_indices+list(reverse)
            s = a[:, indices]
            # Incidence rank is dimensionless; no mixed-unit KKT rank threshold.
            if np.linalg.matrix_rank(s) != len(indices):
                singular.append(names)
                continue
            sin = af[0, indices]
            kkt = np.block([[c, s], [s.T, np.zeros((len(indices), len(indices)))]])
            solution = np.linalg.solve(kkt, np.r_[rhs, -sin*dvin_v_s])
            dv = solution[:6]
            j = np.zeros(6)
            j[indices] = solution[6:]
            gap_rate = (af.T@np.r_[dvin_v_s, dv])[:6]
            # Reverse current r=-j must be nonnegative; unclamped boundary
            # branches must move into the feasible voltage half-space.
            if any(j[k] > tolerances.current_a or abs(gap_rate[k]) > tolerances.voltage_rate_v_s
                   for k in reverse) or any(gap_rate[k] < -tolerances.voltage_rate_v_s
                                           for k in boundary_indices if k not in reverse):
                rejected.append(names)
                continue
            jr = np.zeros(6)
            jr[list(reverse)] = -j[list(reverse)]
            jgate = np.zeros(6)
            jgate[gate_indices] = j[gate_indices]
            cap_current = cvals*(af.T@np.r_[dvin_v_s, dv])
            total = cap_current.copy()
            total[:6] += j
            iin = float(af[0]@total)
            loss = float(drops@jr)
            energy_rate = float(branch_voltage@cap_current+(np.array(parts.inductance_h)*i)@di)
            power = float(state.vin_v*iin+v[-1]*(other_modules_current_a-load_current_a)
                          - np.array(parts.winding_ohm)@(i*i)-loss)
            accepted.append(LocalCandidate(names, dv, di.copy(), jgate, jr, gaps.copy(),
                                           gap_rate, a@total+b@i-external, iin, loss, energy_rate, power))
    if singular:
        status = "DEGENERATE_ACTIVE_SETS_UNRESOLVED"
    elif not accepted:
        status = "NO_LOCAL_CANDIDATE"
    else:
        first = accepted[0]
        same_rate = all(np.max(np.abs(x.dv_v_s-first.dv_v_s)) <= tolerances.voltage_rate_v_s for x in accepted)
        same_current = all(np.max(np.abs(x.reverse_current_a-first.reverse_current_a)) <= tolerances.current_a
                           and np.max(np.abs(x.gate_current_a-first.gate_current_a)) <= tolerances.current_a
                           for x in accepted)
        status = "LOCAL_COMPLEMENTARITY_ONLY" if same_rate and same_current else "MULTIPLE_LOCAL_SOLUTIONS"
    return LocalResolution(status, tuple(accepted), tuple(singular), tuple(rejected))
