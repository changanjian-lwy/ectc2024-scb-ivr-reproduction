"""Independent accepted-orbit metering: power and actual switch branches.

The SCB flying-capacitor paths mean an enabled switch's channel current need
not equal that phase's inductor current. Measure v_branch/R from the actual
resistive descriptor, and keep the earlier phase-current estimate for audit.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import path_resolved_period as P
from asymmetric_ron_dynamics import D, M, asymmetric_ron_context, build_epc2067_boundary


@dataclass
class FullStateMonitor(P.PathResolvedMonitor):
    accepted: list = field(default_factory=list)

    def observe(self, step):
        super().observe(step)
        while self.accepted and self.accepted[-1].time_s > step.time_s + 1e-21:
            self.accepted.pop()
        self.accepted.append(step)


def metered_orbit(point):
    b = build_epc2067_boundary(phase_inductance_h=point['phase_inductance_h'],
                              dead_time_s=point.get('dead_time_s', 2.15e-9))
    original = P.PathResolvedMonitor
    P.PathResolvedMonitor = FullStateMonitor
    try:
        with asymmetric_ron_context():
            p, _, legacy = P.evaluate_period_map_with_paths(
                b, np.array(point['z_star']),
                coarse_step_s=point.get('coarse_step_s', 62.5e-12),
                sub_step_s=point.get('sub_step_s', 5e-12))
    finally:
        P.PathResolvedMonitor = original
    steps = p.monitor.accepted
    index = p.monitor.index
    dt = np.diff([s.time_s for s in steps])
    states = np.array([s.state for s in steps[1:]])
    out = states[:, index['out']]
    high = np.array([s.mode.high_side_on for s in steps[1:]])
    low = np.array([s.mode.low_side_on for s in steps[1:]])
    def channel_loss(pairs, flags, resistance):
        values = []
        for phase, (a, c) in enumerate(pairs):
            v = states[:, index[a]] - (states[:, index[c]] if c else 0)
            values.append(float(np.dot(dt, flags[:, phase] * v*v / resistance) / b.period_s))
        return values
    hs = channel_loss(D.HIGH_SIDE_BRANCHES, high, b.high_side_on_resistance_ohm)
    ls = channel_loss(D.LOW_SIDE_BRANCHES, low, b.low_side_on_resistance_ohm)
    currents = np.array([[s.state[index[f'L{k}']] for k in range(1, 5)] for s in steps])
    minima, maxima = currents.min(axis=0), currents.max(axis=0)
    entries = [float(p.turn_on_entry[k].state[index[f'L{k+1}']]) for k in range(4)]
    return dict(label=point.get('label'), phase_inductance_h=b.phase_inductance_h,
        dead_time_s=b.dead_time_s,
        full_boundary=asdict(b), simulated_modules=1,
        coarse_step_s=point.get('coarse_step_s', 62.5e-12),
        sub_step_s=point.get('sub_step_s', 5e-12),
        integrated_duration_s=float(sum(dt)), period_s=b.period_s,
        relative_closure=M.relative_residual(np.array(point['z_star']), p.z_next),
        natural_zvs_flags=list(p.natural_zvs_flags),
        high_side_turn_on_verdicts=[asdict(v) for v in p.turn_on],
        low_side_turn_on_verdicts=[asdict(v) for v in p.turn_off],
        modeled_high_channel_active_duration_s=(dt @ high).tolist(),
        modeled_low_channel_active_duration_s=(dt @ low).tolist(),
        phase_minimum_a=minima.tolist(), phase_maximum_a=maxima.tolist(),
        maximum_abs_phase_current_a=float(np.max(np.abs(currents))),
        negative_valley_to_positive_peak_ratio=(np.maximum(-minima, 0)/maxima).tolist(),
        current_at_high_side_deadtime_entry_a=entries,
        negative_entry_to_positive_peak_ratio=(np.maximum(-np.array(entries),0)/maxima).tolist(),
        average_output_v=float(np.dot(dt, out) / b.period_s),
        actual_load_power_w=float(np.dot(dt, out*out) / (b.period_s*b.load_resistance_ohm)),
        high_side_channel_loss_w=hs, low_side_channel_loss_w=ls,
        actual_branch_channel_loss_w=sum(hs)+sum(ls),
        legacy_phase_current_loss_proxy_w=legacy.modeled_loss_w,
        complete_total_loss=False)


def main():
    source = json.loads((HERE/'critical_boundary_result.json').read_text())
    points = source.get('refinement') or source['probes'][:2]
    result = dict(classification='ACTUAL_SWITCH_BRANCH_METERING_AUDIT',
        integration='right-endpoint backward-Euler; accepted samples only', points=[])
    for point in points:
        r = metered_orbit(point)
        result['points'].append(r)
        print(json.dumps({k:r[k] for k in ('label', 'actual_load_power_w',
              'actual_branch_channel_loss_w', 'natural_zvs_flags')}), flush=True)
    filename = ('refined_accepted_orbit_audit.json' if source.get('refinement')
                else 'accepted_orbit_audit.json')
    (HERE/filename).write_text(json.dumps(result, indent=2, default=str)+'\n')


if __name__ == '__main__':
    main()
