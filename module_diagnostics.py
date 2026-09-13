"""Per-module and interface diagnostics for an assembled experiment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Callable

from model_contracts import AssemblyPlan, Module


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    owner_module: str
    status: CheckStatus
    observed: str
    expected: str
    claim_boundary: str

    def as_dict(self) -> dict:
        result = asdict(self)
        result["status"] = self.status.value
        return result


ModuleValidator = Callable[[Module], tuple[CheckResult, ...]]


def structural_diagnostics(plan: AssemblyPlan) -> tuple[CheckResult, ...]:
    """Checks that can be evaluated before SPICE runs."""

    results: list[CheckResult] = []
    provided = set().union(*(m.provides for m in plan.selected_modules))
    for module in plan.selected_modules:
        missing = module.requires - provided
        self_conflicts = module.conflicts_with & module.provides
        results.append(
            CheckResult(
                check_id=f"{module.module_id}:dependencies",
                owner_module=module.module_id,
                status=CheckStatus.PASS if not missing else CheckStatus.BLOCKED,
                observed="none" if not missing else ", ".join(sorted(missing)),
                expected="all declared dependencies supplied",
                claim_boundary="module interface only; not electrical validation",
            )
        )
        results.append(
            CheckResult(
                check_id=f"{module.module_id}:internal_conflict",
                owner_module=module.module_id,
                status=CheckStatus.PASS if not self_conflicts else CheckStatus.FAIL,
                observed=(
                    "none" if not self_conflicts else ", ".join(sorted(self_conflicts))
                ),
                expected="module must not provide a capability it declares incompatible",
                claim_boundary="provenance/semantic consistency check",
            )
        )
    return tuple(results)


def summarize(checks: tuple[CheckResult, ...]) -> dict:
    counts = {status.value: 0 for status in CheckStatus}
    for check in checks:
        counts[check.status.value] += 1
    failed_owners = sorted(
        {
            check.owner_module
            for check in checks
            if check.status in {CheckStatus.FAIL, CheckStatus.BLOCKED}
        }
    )
    return {
        "counts": counts,
        "failed_or_blocked_modules": failed_owners,
        "passed": not failed_owners,
    }
