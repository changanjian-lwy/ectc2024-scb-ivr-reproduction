"""Independent conductance-matrix identity for actual branch power metering."""
import runpy
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
A55 = ROOT / 'experiments/track_A_periodic_steady_state/A55_joint_lphase_deadtime_total_loss_optimization'


class BranchPowerTests(unittest.TestCase):
    def test_branch_power_equals_enabled_channel_matrix_dissipation(self):
        m = runpy.run_path(str(A55 / 'asymmetric_ron_dynamics.py'))
        D = m['D']
        b = m['build_epc2067_boundary']()
        off = D.Mode((False,)*4, (False,)*4, (False,)*3)
        base = m['assemble_descriptor'](b, off, 0)
        index = {name: n for n, name in enumerate(base.node_names)}
        # Deliberately non-equal branch voltages; phase-current substitution
        # cannot satisfy this identity for arbitrary capacitor/node states.
        v = np.linspace(-0.12, 0.25, len(base.node_names))
        for k in range(4):
            high = tuple(j == k for j in range(4))
            low = tuple(j != k for j in range(4))
            on = m['assemble_descriptor'](b, D.Mode(high, low, (False,)*3), 0)
            n = len(v)
            matrix_power = v @ (on.a[:n, :n]-base.a[:n, :n]) @ v
            branch_power = 0.
            for pairs, flags, r in ((D.HIGH_SIDE_BRANCHES, high, b.high_side_on_resistance_ohm),
                                    (D.LOW_SIDE_BRANCHES, low, b.low_side_on_resistance_ohm)):
                for (a, c), enabled in zip(pairs, flags):
                    if enabled:
                        voltage = v[index[a]]-(v[index[c]] if c else 0.)
                        branch_power += voltage**2/r
            self.assertAlmostEqual(matrix_power, branch_power, places=7)


if __name__ == '__main__':
    unittest.main()
