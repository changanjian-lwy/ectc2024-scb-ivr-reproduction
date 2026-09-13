import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ACTIVE_NETLISTS = (
    "paper_locked/02_ectc2024_main/spice/R04D1B2_GS61008T_device_only_commutation.cir",
    "paper_locked/02_ectc2024_main/spice/R04D2A_P24_interval2_to_IL1_zero_GS_plugin.cir",
    "paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir",
    "paper_locked/02_ectc2024_main/spice/R04D3C_P25_5pct_threshold_mapped_to_P24_commutation.cir",
    "paper_locked/02_ectc2024_main/spice/R04D3E_calibrated_ZVS_exit_acceptance.cir",
    "experiments/track_A_periodic_steady_state/A01_p24_2pct__first_periodic_seed_all_iL_zero/A01_P24_2pct_first_periodic_seed.cir",
    "experiments/track_A_periodic_steady_state/A02_device_coss_stage_revalidation/A02_Mode1_same_boundary_with_device_Coss.cir",
    "experiments/track_A_periodic_steady_state/A04_four_phase_readiness_supervisor/A04_four_phase_readiness_supervisor_2pct.cir",
    "experiments/track_A_periodic_steady_state/A05_four_phase_8pct_branch/A05_four_phase_readiness_supervisor_8pct.cir",
    "experiments/track_A_periodic_steady_state/A11_passive_balance_isolated/A11_passive_balance_control_vs_C1_plus_0p5V.cir",
    "experiments/track_A_periodic_steady_state/A12_passive_balance_long_horizon/A12_passive_balance_symmetric_20cycles.cir",
    "experiments/track_A_periodic_steady_state/A13_tighten_01_inductor_currents/A13_tighten_only_inductor_currents.cir",
    "experiments/track_A_periodic_steady_state/A14_tighten_02_C1/A14_tighten_only_C1_from_A13.cir",
    "experiments/track_A_periodic_steady_state/A15_tighten_03_C2/A15_tighten_only_C2_from_A14.cir",
    "experiments/track_A_periodic_steady_state/A16_tighten_04_C3/A16_tighten_only_C3_from_A15.cir",
)


class ActiveCossModuleAdoptionTests(unittest.TestCase):
    def test_active_netlists_use_shared_capacitance_module(self):
        for relative in ACTIVE_NETLISTS:
            text = (PROJECT / relative).read_text()
            self.assertIn("GS61008T_commutation_capacitance.lib", text, relative)
            self.assertNotIn(".param CH={NHS*GS61008T_COTR_0_50V}", text, relative)

    def test_snubber_default_is_explicitly_zero(self):
        library = (
            PROJECT
            / "paper_locked/04_component_models/GS61008T_commutation_capacitance.lib"
        ).read_text()
        self.assertIn(".param CH_SNUBBER=0", library)
        self.assertIn(".param CL_SNUBBER=0", library)


if __name__ == "__main__":
    unittest.main()
