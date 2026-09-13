"""Reusable experiment requests; profiles select capabilities, not equations."""

from evidence import Evidence
from model_contracts import ExperimentRequest


R04A_LOCAL_BOUNDARY_REPLAY = ExperimentRequest(
    experiment_id="R04A_LOCAL_BOUNDARY_REPLAY",
    required_capabilities=frozenset(
        {
            "on_time",
            "phase_peak_current",
            "critical_inductance",
            "phase_local_three_interval_sequence",
            "single_phase_stiff_rail_boundary",
            "latched_event_memory",
            "ideal_switch_pair",
        }
    ),
    allowed_evidence=frozenset(
        {
            Evidence.P24_EXPLICIT,
            Evidence.P24_DERIVED,
            Evidence.PROJECT_DECISION,
            Evidence.EXPLORATORY_ASSUMPTION,
        }
    ),
)
