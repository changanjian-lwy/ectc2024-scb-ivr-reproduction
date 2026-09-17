"""P25-native three-phase fixed-slot event-ring calibration.

This reuses the event order and the numerical device abstraction used by the
P24-primary/P25-supplement branch, but replaces the power-stage dimensions and
reported operating values with the P25 prototype values.  It is deliberately
not a startup model and it does not fill unpublished capacitor/snubber data.
"""
from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp


NP = 3
VIN = 12.0
VO = 1.0
FSW = 0.5e6
PERIOD = 1.0 / FSW
SLOT = PERIOD / NP
TON = NP * VO / VIN * PERIOD
LPHASE = 22e-9
RIND = 0.5e-3
RON_H = 7e-3
RON_L = 3.5e-3
RON_REV = 3e-3
ROFF = 1e12

# P25 omits the full capacitor suffixes and added snubber values.  These are
# the existing documented sensitivity baseline and device-plug-in values.
CFLY = 120e-6
COSS_H = 385e-12
COSS_L = 770e-12


def stamp_cap(cmat, p, n, value):
    """Stamp a capacitor; node -1 denotes an AC-stiff source/ground."""
    if p >= 0:
        cmat[p, p] += value
    if n >= 0:
        cmat[n, n] += value
    if p >= 0 and n >= 0:
        cmat[p, n] -= value
        cmat[n, p] -= value


# Node order: a1, a2, x1, x2, x3.  Current order: iL1, iL2, iL3.
C = np.zeros((5, 5))
stamp_cap(C, 0, 2, CFLY)
stamp_cap(C, 1, 3, CFLY)
stamp_cap(C, 0, -1, COSS_H)  # H1 is between VIN and a1.
stamp_cap(C, 0, 1, COSS_H)
stamp_cap(C, 1, 4, COSS_H)
for x in (2, 3, 4):
    stamp_cap(C, x, -1, COSS_L)
CINV = np.linalg.inv(C)

B = np.zeros((5, NP))
B[2:, :] = np.eye(NP)

# Positive branch voltage is drain-to-source voltage.
G = np.zeros((2 * NP, 5))
OFFSET = np.zeros(2 * NP)
G[0, 0] = -1.0
OFFSET[0] = VIN
G[1, 0] = 1.0
G[1, 1] = -1.0
G[2, 1] = 1.0
G[2, 4] = -1.0
G[3:, 2:] = np.eye(NP)
RON = np.r_[np.full(NP, RON_H), np.full(NP, RON_L)]
ALL_LOW = np.r_[np.zeros(NP, dtype=bool), np.ones(NP, dtype=bool)]


def vhigh(z, phase):
    return np.array([VIN - z[0], z[0] - z[1], z[1] - z[4]])[phase]


def rhs_ns(_ns, z, active, lphase=LPHASE):
    voltage = G @ z[:5] + OFFSET
    conductance = np.where(active, 1.0 / RON, 1.0 / ROFF)
    # Same zero-Qrr numerical reverse branch used in the P24 analytical audit.
    conductance += np.where(voltage < 0.0, 1.0 / RON_REV, 1.0 / ROFF)
    ib = conductance * voltage
    dv = CINV @ (-B @ z[5:] - G.T @ ib)
    di = (B.T @ z[:5] - VO - RIND * z[5:]) / lphase
    return 1e-9 * np.r_[dv, di]


def state_event(index, level, direction):
    def fn(_ns, z):
        return z[index] - level
    fn.direction = direction
    fn.terminal = True
    return fn


def high_vds_event(phase):
    def fn(_ns, z):
        return vhigh(z, phase)
    fn.direction = -1
    fn.terminal = True
    return fn


def advance(t0_ns, t1_ns, z0, active, events=None, lphase=LPHASE,
            max_step_ns=1.0):
    sol = solve_ivp(
        lambda t, z: rhs_ns(t, z, active, lphase),
        (t0_ns, t1_ns), z0, method="Radau", events=events,
        rtol=2e-9, atol=1e-10, max_step=max_step_ns,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol


@dataclass
class RingResult:
    history: list
    final: np.ndarray
    initial: np.ndarray
    charge_a_ns: np.ndarray | None = None

    @property
    def passed(self):
        return len(self.history) == NP and not any("failure" in h for h in self.history)


def ring(initial, negative_target=2.2222222222):
    """Run one 2-us ring with immutable 0.5-MHz/three-phase fixed slots."""
    z = np.asarray(initial, dtype=float).copy()
    z_start = z.copy()
    history = []
    now_ns = 0.0
    for phase in range(NP):
        next_phase = (phase + 1) % NP
        slot_end = (phase + 1) * SLOT * 1e9
        record = {"phase": phase + 1, "slot_start_ns": now_ns,
                  "slot_end_ns": slot_end, "vds_start_v": float(vhigh(z, phase))}
        if vhigh(z, phase) > 1e-3:
            record["failure"] = "high-side Vds positive at fixed-slot entrance"
            history.append(record)
            return RingResult(history, z, z_start)

        active = ALL_LOW.copy()
        active[phase] = True
        active[NP + phase] = False
        high_end_ns = now_ns + TON * 1e9
        sol = advance(now_ns, high_end_ns, z, active)
        z = sol.y[:, -1]
        now_ns = high_end_ns
        record.update(high_off_ns=now_ns, peak_a=float(z[5 + phase]))

        active[phase] = False
        sol = advance(now_ns, slot_end, z, active,
                      state_event(2 + phase, 0.0, -1))
        if not len(sol.t_events[0]):
            record["failure"] = "active low-side zero absent before next slot"
            history.append(record)
            return RingResult(history, sol.y[:, -1], z_start)
        z = sol.y_events[0][0]
        now_ns = float(sol.t_events[0][0])
        record["active_low_on_ns"] = now_ns

        if z[5 + next_phase] < -negative_target:
            record["failure"] = "next-phase negative target already passed before Mode 4"
            record["next_current_a"] = float(z[5 + next_phase])
            history.append(record)
            return RingResult(history, z, z_start)

        sol = advance(now_ns, slot_end, z, ALL_LOW,
                      state_event(5 + next_phase, -negative_target, -1))
        if not len(sol.t_events[0]):
            record["failure"] = "next-phase negative target absent before next slot"
            record["next_current_at_slot_a"] = float(sol.y[5 + next_phase, -1])
            history.append(record)
            return RingResult(history, sol.y[:, -1], z_start)
        z = sol.y_events[0][0]
        now_ns = float(sol.t_events[0][0])
        record["next_low_release_ns"] = now_ns

        active = ALL_LOW.copy()
        active[NP + next_phase] = False
        sol = advance(now_ns, slot_end, z, active)
        z = sol.y[:, -1]
        now_ns = slot_end
        record.update(next_vds_slot_v=float(vhigh(z, next_phase)),
                      next_current_slot_a=float(z[5 + next_phase]))
        if vhigh(z, next_phase) > 1e-3:
            record["failure"] = "next high-side Vds positive at fixed slot"
            history.append(record)
            return RingResult(history, z, z_start)
        history.append(record)
    return RingResult(history, z, z_start)


def event_ring(initial, negative_target=2.2222222222,
               lphase=LPHASE, ton=TON, max_step_ns=1.0):
    """P25 textual event controller: SH turns on at the Vds-zero event.

    The resulting phase spacings and ring frequency are outputs.  They are not
    silently identified with the nominal 0.5-MHz value.
    """
    z = np.asarray(initial, dtype=float).copy()
    z_start = z.copy()
    history = []
    charge_a_ns = np.zeros(NP)
    ton_by_phase = np.broadcast_to(np.asarray(ton, dtype=float), (NP,))
    now_ns = 0.0
    def keep(sol):
        nonlocal charge_a_ns
        charge_a_ns += np.trapezoid(sol.y[5:], sol.t, axis=1)
        return sol
    for phase in range(NP):
        next_phase = (phase + 1) % NP
        start_ns = now_ns
        record = {"phase": phase + 1, "high_on_ns": start_ns,
                  "vds_start_v": float(vhigh(z, phase))}
        if vhigh(z, phase) > 1e-3:
            record["failure"] = "high-side Vds positive at event entrance"
            history.append(record)
            return RingResult(history, z, z_start, charge_a_ns)

        active = ALL_LOW.copy()
        active[phase] = True
        active[NP + phase] = False
        high_end_ns = now_ns + ton_by_phase[phase] * 1e9
        sol = keep(advance(now_ns, high_end_ns, z, active, lphase=lphase,
                           max_step_ns=max_step_ns))
        z = sol.y[:, -1]
        now_ns = high_end_ns
        record.update(high_off_ns=now_ns, peak_a=float(z[5 + phase]))

        active[phase] = False
        sol = keep(advance(now_ns, now_ns + 100.0, z, active,
                           state_event(2 + phase, 0.0, -1), lphase=lphase,
                           max_step_ns=max_step_ns))
        if not len(sol.t_events[0]):
            record["failure"] = "active low-side zero absent"
            history.append(record)
            return RingResult(history, sol.y[:, -1], z_start, charge_a_ns)
        z = sol.y_events[0][0]
        now_ns = float(sol.t_events[0][0])
        record["active_low_on_ns"] = now_ns

        if z[5 + next_phase] < -negative_target:
            record["failure"] = "next-phase negative target already passed"
            record["next_current_a"] = float(z[5 + next_phase])
            history.append(record)
            return RingResult(history, z, z_start, charge_a_ns)
        sol = keep(advance(now_ns, now_ns + 2.0e3, z, ALL_LOW,
                           state_event(5 + next_phase, -negative_target, -1),
                           lphase=lphase, max_step_ns=max_step_ns))
        if not len(sol.t_events[0]):
            record["failure"] = "next-phase negative target absent"
            history.append(record)
            return RingResult(history, sol.y[:, -1], z_start, charge_a_ns)
        z = sol.y_events[0][0]
        now_ns = float(sol.t_events[0][0])
        record["next_low_release_ns"] = now_ns

        active = ALL_LOW.copy()
        active[NP + next_phase] = False
        sol = keep(advance(now_ns, now_ns + 200.0, z, active,
                           high_vds_event(next_phase), lphase=lphase,
                           max_step_ns=max_step_ns))
        if not len(sol.t_events[0]):
            record["failure"] = "next high-side Vds-zero event absent"
            history.append(record)
            return RingResult(history, sol.y[:, -1], z_start, charge_a_ns)
        z = sol.y_events[0][0]
        now_ns = float(sol.t_events[0][0])
        record.update(next_high_on_ns=now_ns,
                      phase_spacing_ns=now_ns - start_ns,
                      next_current_at_zvs_a=float(z[5 + next_phase]))
        history.append(record)
    return RingResult(history, z, z_start, charge_a_ns)


def documented_seed(negative_target=2.2222222222):
    # Periodic-state ladder, not zero startup.  H1 is at its ZVS entrance;
    # inactive phase nodes are clamped low.  Other currents are the ideal
    # triangular positions separated by T/3 and are only an initial guess.
    return np.array([VIN, 4.0, 4.0, 0.0, 0.0,
                     -negative_target, 28.0, 58.0])


def main():
    print("P25 native fixed-slot calibration")
    print("NP", NP, "NM reported", 3, "Vin", VIN, "Vo", VO,
          "fsw_Hz", FSW, "slot_ns", SLOT * 1e9, "Ton_ns", TON * 1e9)
    print("L_nH", LPHASE * 1e9, "negative_target_A", 2.2222222222)
    result = ring(documented_seed())
    for row in result.history:
        print(row)
    print("passed", result.passed)
    print("state_return", (result.final - result.initial).tolist())
    event_result = event_ring(documented_seed())
    print("event_control")
    for row in event_result.history:
        print(row)
    print("event_passed", event_result.passed)
    if event_result.passed:
        elapsed = event_result.history[-1]["next_high_on_ns"]
        print("event_ring_period_ns", elapsed, "frequency_Hz", 1e9 / elapsed)
        print("event_state_return", (event_result.final - event_result.initial).tolist())


if __name__ == "__main__":
    main()
