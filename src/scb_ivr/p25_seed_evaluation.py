"""D21: keep unreachable trajectories distinct from defined return residuals."""
from dataclasses import dataclass
from .p25_shooting_contract import ShootingContract, SectionSeed
from .p25_period_attempt import PeriodAttempt, attempt_period
from .p25_periodic_section import ReturnTolerance, StateReturn, compare_sections


@dataclass(frozen=True)
class SeedEvaluation:
    status: str
    seed: SectionSeed
    attempt: PeriodAttempt
    state_return: StateReturn | None
    scope: str = "FIXED_DESIGN_REFERENCE; conditional sampled trajectory, not paper validation"


def evaluate_seed(contract: ShootingContract, seed: SectionSeed, *, return_tolerance: ReturnTolerance,
                  stage_horizons_s, intervals, voltage_root, current_root, electrical, direction):
    """Do not replace failed segments with an arbitrary optimizer penalty.

    Invalid configuration/seed raises explicitly. An admissible seed whose
    trajectory is blocked yields no residual. Only a reached SH1 section can
    be compared. State return does not certify frequency/power/peak matching.
    """
    if not isinstance(return_tolerance,ReturnTolerance):
        raise ValueError("explicit dimensionally separate return tolerances required")
    initial=contract.make_candidate(seed)
    contract.assert_frozen(initial,contract.model,contract.ports)
    model=contract.model
    result=attempt_period(initial,model.components,contract.ports,model.control,model.reverse_model,
        stage_horizons_s=stage_horizons_s,intervals=intervals,voltage_root=voltage_root,
        current_root=current_root,electrical=electrical,direction=direction)
    if result.end is None:
        return SeedEvaluation("TRAJECTORY_UNRESOLVED_NO_RETURN_RESIDUAL",seed,result,None)
    closure=compare_sections(initial,result.end,start_model=model,end_model=model,tolerance=return_tolerance)
    status="CONDITIONAL_STATE_RETURN" if closure.state_returns else "SECTION_REACHED_STATE_NOT_RETURNED"
    return SeedEvaluation(status,seed,result,closure)
