import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]/'experiments/track_A_periodic_steady_state/A55_joint_lphase_deadtime_total_loss_optimization'


class MeteringBoundaryTests(unittest.TestCase):
    def test_nondefault_deadtime_reaches_replay_unchanged(self):
        sys.path.insert(0, str(HERE))
        a = importlib.import_module('audit_accepted_orbit')
        original_monitor = a.P.PathResolvedMonitor
        # Inject failure before stepping; also check hooks recover on failure.
        with patch.object(a.P, 'evaluate_period_map_with_paths', side_effect=RuntimeError('sentinel')) as run:
            with self.assertRaisesRegex(RuntimeError, 'sentinel'):
                a.metered_orbit(dict(phase_inductance_h=0.621524e-9,
                                    dead_time_s=4.3e-9, z_star=[0.]*20))
        self.assertEqual(run.call_args.args[0].dead_time_s, 4.3e-9)
        self.assertEqual(run.call_args.args[0].phase_inductance_h, 0.621524e-9)
        self.assertIs(a.P.PathResolvedMonitor, original_monitor)


if __name__=='__main__':
    unittest.main()
